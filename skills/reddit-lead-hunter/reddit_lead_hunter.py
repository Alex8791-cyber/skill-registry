"""
Cognithor Skill: Reddit Lead Hunter
====================================
Scannt Reddit 24/7 nach High-Intent-Posts für ein gegebenes Produkt/Service.
Bewertet jeden Post 0–100 (Intent Score), verhindert Duplikate via KnowledgeVault,
draftet kontextbewusste Antworten via LLM und pusht Leads an jeden Cognithor-Channel.

Abhängigkeiten:
    pip install praw>=7.7 pydantic>=2.0 httpx>=0.27

Reddit API-Keys:
    https://www.reddit.com/prefs/apps → "script" App anlegen
    → REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env

Autor: Cognithor / Alexander Söllner
Lizenz: Apache 2.0
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable

import httpx
import praw
import praw.models
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("cognithor.skills.reddit_lead_hunter")


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

class LeadHunterConfig(BaseModel):
    """Vollständige Konfiguration für einen Reddit-Lead-Hunter-Run."""

    # Produkt / Ziel
    product_name: str = Field(..., description="Name deines Produkts, z.B. 'Cognithor'")
    product_description: str = Field(
        ...,
        description="Ein-Satz-Beschreibung für die KI-Scoring-Prompts",
    )
    reply_tone: str = Field(
        default="helpful, direct, no sales pitch",
        description="Ton-Anweisung für Reply-Drafts",
    )

    # Reddit-Targeting
    subreddits: list[str] = Field(
        default_factory=lambda: ["LocalLLaMA", "SaaS", "MachineLearning"],
        description="Liste der Subreddits ohne 'r/'",
    )
    posts_per_subreddit: int = Field(default=100, ge=10, le=500)
    min_intent_score: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Posts unter diesem Score werden verworfen",
    )
    scan_interval_seconds: int = Field(
        default=1800,
        ge=60,
        description="Pause zwischen Scan-Zyklen (Default: 30 Min.)",
    )

    # LLM-Anbindung (Cognithor-intern oder direkt via HTTP)
    llm_provider: str = Field(default="ollama", description="z.B. 'ollama', 'openai', 'anthropic'")
    llm_model: str = Field(default="qwen2.5:27b", description="Modell-Name")
    llm_base_url: str = Field(default="http://localhost:11434", description="API-Endpoint")
    llm_api_key: str = Field(default="", description="API-Key (leer für lokale Modelle)")
    llm_timeout_seconds: int = Field(default=60)

    # Reddit API-Credentials (aus Umgebungsvariablen oder direkt)
    reddit_client_id: str = Field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", ""))
    reddit_client_secret: str = Field(default_factory=lambda: os.getenv("REDDIT_CLIENT_SECRET", ""))
    reddit_user_agent: str = Field(
        default_factory=lambda: os.getenv("REDDIT_USER_AGENT", "cognithor:reddit_lead_hunter:v1.0")
    )

    @field_validator("subreddits")
    @classmethod
    def strip_r_prefix(cls, v: list[str]) -> list[str]:
        return [s.lstrip("r/").strip() for s in v]

    @classmethod
    def from_env(cls, **overrides: Any) -> "LeadHunterConfig":
        """Lädt Konfiguration aus Umgebungsvariablen + optionalen Overrides."""
        return cls(**overrides)

    @classmethod
    def from_json(cls, path: str) -> "LeadHunterConfig":
        with open(path, encoding="utf-8") as f:
            return cls(**json.load(f))


# ---------------------------------------------------------------------------
# Datenmodelle
# ---------------------------------------------------------------------------

@dataclass
class RedditLead:
    """Ein bewerteter Reddit-Post als potentieller Lead."""

    post_id: str
    subreddit: str
    title: str
    body: str
    url: str
    author: str
    created_utc: float
    upvotes: int
    num_comments: int
    intent_score: int                    # 0–100
    score_reasoning: str                 # LLM-Begründung
    reply_draft: str                     # Vorgeschlagene Antwort
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Cognithor Audit-Felder
    content_hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.content_hash:
            raw = f"{self.post_id}:{self.title}:{self.body}"
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_notification_text(self) -> str:
        """Formatierter Text für Slack/Mail/Telegram-Channels."""
        stars = "★" * (self.intent_score // 20) + "☆" * (5 - self.intent_score // 20)
        return (
            f"🎯 **Reddit Lead gefunden** [{stars} {self.intent_score}/100]\n"
            f"📌 **r/{self.subreddit}** — {self.title}\n"
            f"🔗 {self.url}\n"
            f"👤 u/{self.author} · ⬆️ {self.upvotes} · 💬 {self.num_comments}\n\n"
            f"**Begründung:** {self.score_reasoning}\n\n"
            f"**Vorgeschlagene Antwort:**\n{self.reply_draft}\n"
            f"{'─' * 60}"
        )


@dataclass
class ScanResult:
    """Ergebnis eines einzelnen Scan-Zyklus."""

    started_at: str
    finished_at: str
    subreddits_scanned: list[str]
    posts_checked: int
    posts_skipped_duplicate: int
    posts_skipped_low_score: int
    leads_found: list[RedditLead]

    @property
    def lead_count(self) -> int:
        return len(self.leads_found)

    def summary(self) -> str:
        return (
            f"Scan abgeschlossen: {self.posts_checked} Posts geprüft, "
            f"{self.posts_skipped_duplicate} Duplikate, "
            f"{self.posts_skipped_low_score} unter Score-Grenze, "
            f"{self.lead_count} Leads gefunden."
        )


# ---------------------------------------------------------------------------
# Seen-Post-Store (ersetzt KnowledgeVault wenn nicht verfügbar)
# ---------------------------------------------------------------------------

class SeenPostStore:
    """
    Minimaler In-Memory + File-Backed Store für bereits gesehene Post-IDs.
    In Cognithor: durch KnowledgeVault.mark_seen() / .already_seen() ersetzen.
    """

    def __init__(self, persistence_path: str = ".cognithor_reddit_seen.json"):
        self._path = persistence_path
        self._seen: set[str] = set()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._seen = set(json.load(f))
            except (json.JSONDecodeError, OSError):
                self._seen = set()

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(list(self._seen), f)
        except OSError as e:
            logger.warning("SeenPostStore: Konnte nicht speichern: %s", e)

    def already_seen(self, post_id: str) -> bool:
        return post_id in self._seen

    def mark_seen(self, post_id: str) -> None:
        self._seen.add(post_id)
        self._save()

    def count(self) -> int:
        return len(self._seen)

    def clear(self) -> None:
        """Für Tests: Store leeren."""
        self._seen.clear()
        if os.path.exists(self._path):
            os.remove(self._path)


# ---------------------------------------------------------------------------
# LLM-Client (provider-agnostisch)
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Schlanker HTTP-Client für LLM-Calls.
    Unterstützt: Ollama, OpenAI-kompatible APIs, Anthropic.

    In Cognithor: durch den internen ProviderRouter ersetzen.
    """

    def __init__(self, config: LeadHunterConfig) -> None:
        self.config = config
        self._client = httpx.Client(timeout=config.llm_timeout_seconds)

    def _call_ollama(self, prompt: str) -> str:
        resp = self._client.post(
            f"{self.config.llm_base_url}/api/generate",
            json={
                "model": self.config.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()

    def _call_openai_compat(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.config.llm_api_key:
            headers["Authorization"] = f"Bearer {self.config.llm_api_key}"
        resp = self._client.post(
            f"{self.config.llm_base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": self.config.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _call_anthropic(self, prompt: str) -> str:
        resp = self._client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.config.llm_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.config.llm_model,
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    def complete(self, prompt: str) -> str:
        """Sendet Prompt an konfigurierten LLM-Provider."""
        provider = self.config.llm_provider.lower()
        try:
            if provider == "ollama":
                return self._call_ollama(prompt)
            elif provider == "anthropic":
                return self._call_anthropic(prompt)
            else:
                # OpenAI, Groq, Together, LM Studio, etc.
                return self._call_openai_compat(prompt)
        except httpx.HTTPError as e:
            logger.error("LLM-Call fehlgeschlagen: %s", e)
            raise

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Scoring & Reply-Drafting
# ---------------------------------------------------------------------------

SCORE_PROMPT_TEMPLATE = """
Du bist ein Experte für B2B-Lead-Qualifizierung. Deine Aufgabe ist es, einen Reddit-Post zu bewerten.

PRODUKT: {product_name}
BESCHREIBUNG: {product_description}

REDDIT-POST:
Subreddit: r/{subreddit}
Titel: {title}
Text: {body}

Bewerte den Kaufintent dieses Posts auf einer Skala von 0 bis 100:
- 0–20: Kein Bezug zum Produkt
- 21–40: Schwacher Bezug, kein konkretes Problem
- 41–60: Relevantes Thema, aber kein klares Kaufsignal
- 61–80: Klares Problem, das unser Produkt löst
- 81–100: Aktive Suche nach genau dieser Lösung

Antworte NUR im folgenden JSON-Format, ohne Erklärungen außerhalb:
{{"score": <int 0-100>, "reasoning": "<max. 1 Satz warum>"}}
""".strip()

REPLY_PROMPT_TEMPLATE = """
Du bist ein hilfreicher Experte, der auf Reddit antwortet.

PRODUKT: {product_name}
DEIN TON: {reply_tone}

REDDIT-POST:
Subreddit: r/{subreddit}
Titel: {title}
Text: {body}

Schreibe eine kurze, hilfreiche Reddit-Antwort (max. 150 Wörter):
- Erkenne das Problem des Users an
- Erkläre kurz wie {product_name} helfen kann
- Kein übertriebenes Verkaufsgespräch
- Subreddit-typischer Ton (informal, direkt)
- Füge am Ende den GitHub-Link ein: github.com/Alex8791-cyber/cognithor

Antworte NUR mit dem Antworttext, ohne Metakommentare.
""".strip()


class IntentScorer:
    """Bewertet einen Reddit-Post auf Kaufintent via LLM."""

    def __init__(self, llm: LLMClient, config: LeadHunterConfig) -> None:
        self.llm = llm
        self.config = config

    def score(self, post: praw.models.Submission) -> tuple[int, str]:
        """
        Gibt (score: int, reasoning: str) zurück.
        Bei LLM-Fehler: (0, "Scoring fehlgeschlagen").
        """
        body = (post.selftext or "")[:1000]  # Auf 1000 Zeichen kürzen
        prompt = SCORE_PROMPT_TEMPLATE.format(
            product_name=self.config.product_name,
            product_description=self.config.product_description,
            subreddit=post.subreddit.display_name,
            title=post.title,
            body=body,
        )
        try:
            raw = self.llm.complete(prompt)
            # JSON aus der Antwort extrahieren (robusteres Parsing)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError(f"Kein JSON in LLM-Antwort: {raw[:100]}")
            data = json.loads(raw[start:end])
            score = max(0, min(100, int(data.get("score", 0))))
            reasoning = str(data.get("reasoning", ""))
            return score, reasoning
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Scoring-Fehler für Post %s: %s", post.id, e)
            return 0, "Scoring fehlgeschlagen"


class ReplyDrafter:
    """Entwirft eine kontextbewusste Reddit-Antwort via LLM."""

    def __init__(self, llm: LLMClient, config: LeadHunterConfig) -> None:
        self.llm = llm
        self.config = config

    def draft(self, post: praw.models.Submission) -> str:
        body = (post.selftext or "")[:1000]
        prompt = REPLY_PROMPT_TEMPLATE.format(
            product_name=self.config.product_name,
            reply_tone=self.config.reply_tone,
            subreddit=post.subreddit.display_name,
            title=post.title,
            body=body,
        )
        try:
            return self.llm.complete(prompt)
        except httpx.HTTPError as e:
            logger.warning("Reply-Drafting fehlgeschlagen: %s", e)
            return "[Reply-Draft konnte nicht generiert werden]"


# ---------------------------------------------------------------------------
# Haupt-Skill-Klasse
# ---------------------------------------------------------------------------

class RedditLeadHunterSkill:
    """
    Cognithor Skill: Reddit Lead Hunter

    Scannt konfigurierte Subreddits, bewertet Posts und liefert qualifizierte
    Leads mit vorgenerierten Antwort-Drafts.

    Beispiel:
        config = LeadHunterConfig(
            product_name="Cognithor",
            product_description="Open-source Agent Operating System",
            subreddits=["LocalLLaMA", "SaaS", "agentframework"],
            min_intent_score=65,
        )
        skill = RedditLeadHunterSkill(config)
        result = skill.scan_once()
        for lead in result.leads_found:
            print(lead.to_notification_text())
    """

    def __init__(
        self,
        config: LeadHunterConfig,
        seen_store: SeenPostStore | None = None,
        notification_callback: Callable[[RedditLead], None] | None = None,
    ) -> None:
        self.config = config
        self.seen_store = seen_store or SeenPostStore()
        self.notification_callback = notification_callback
        self._llm = LLMClient(config)
        self._scorer = IntentScorer(self._llm, config)
        self._drafter = ReplyDrafter(self._llm, config)
        self._reddit = self._init_reddit()

    def _init_reddit(self) -> praw.Reddit:
        if not self.config.reddit_client_id:
            raise ValueError(
                "REDDIT_CLIENT_ID fehlt. Bitte in .env oder config setzen.\n"
                "App anlegen: https://www.reddit.com/prefs/apps"
            )
        return praw.Reddit(
            client_id=self.config.reddit_client_id,
            client_secret=self.config.reddit_client_secret,
            user_agent=self.config.reddit_user_agent,
        )

    def scan_once(self) -> ScanResult:
        """Führt einen einzelnen Scan-Zyklus durch und gibt das Ergebnis zurück."""
        started_at = datetime.now(timezone.utc).isoformat()
        leads: list[RedditLead] = []
        posts_checked = 0
        skipped_duplicate = 0
        skipped_low_score = 0

        logger.info(
            "Scan startet: %d Subreddits, min_score=%d",
            len(self.config.subreddits),
            self.config.min_intent_score,
        )

        for sub_name in self.config.subreddits:
            try:
                subreddit = self._reddit.subreddit(sub_name)
                posts = list(subreddit.new(limit=self.config.posts_per_subreddit))
            except Exception as e:
                logger.error("Fehler beim Abrufen von r/%s: %s", sub_name, e)
                continue

            for post in posts:
                posts_checked += 1

                # 1. Duplikat-Check
                if self.seen_store.already_seen(post.id):
                    skipped_duplicate += 1
                    continue

                # 2. Schnell-Filter: Posts ohne Text oder mit sehr wenig Inhalt
                if len(post.title) < 15:
                    self.seen_store.mark_seen(post.id)
                    skipped_low_score += 1
                    continue

                # 3. Intent-Scoring
                score, reasoning = self._scorer.score(post)
                self.seen_store.mark_seen(post.id)

                if score < self.config.min_intent_score:
                    skipped_low_score += 1
                    logger.debug("Post %s Score=%d (unter Grenze) — übersprungen", post.id, score)
                    continue

                # 4. Reply-Draft
                reply_draft = self._drafter.draft(post)

                # 5. Lead erstellen
                lead = RedditLead(
                    post_id=post.id,
                    subreddit=sub_name,
                    title=post.title,
                    body=(post.selftext or "")[:500],
                    url=f"https://reddit.com{post.permalink}",
                    author=str(post.author) if post.author else "[deleted]",
                    created_utc=post.created_utc,
                    upvotes=post.score,
                    num_comments=post.num_comments,
                    intent_score=score,
                    score_reasoning=reasoning,
                    reply_draft=reply_draft,
                )
                leads.append(lead)

                logger.info(
                    "Lead gefunden: r/%s | Score=%d | %s",
                    sub_name, score, post.title[:60],
                )

                # 6. Notification-Callback (Cognithor-Channel)
                if self.notification_callback:
                    try:
                        self.notification_callback(lead)
                    except Exception as e:
                        logger.warning("Notification-Callback fehlgeschlagen: %s", e)

        finished_at = datetime.now(timezone.utc).isoformat()
        result = ScanResult(
            started_at=started_at,
            finished_at=finished_at,
            subreddits_scanned=self.config.subreddits,
            posts_checked=posts_checked,
            posts_skipped_duplicate=skipped_duplicate,
            posts_skipped_low_score=skipped_low_score,
            leads_found=leads,
        )
        logger.info(result.summary())
        return result

    def run_continuous(self, max_cycles: int = 0) -> None:
        """
        Führt Scan-Zyklen in Endlosschleife durch.
        max_cycles=0 → läuft bis KeyboardInterrupt.
        """
        cycle = 0
        logger.info(
            "Reddit Lead Hunter gestartet. Interval: %ds | Strg+C zum Stoppen",
            self.config.scan_interval_seconds,
        )
        try:
            while True:
                self.scan_once()
                cycle += 1
                if max_cycles and cycle >= max_cycles:
                    break
                logger.info(
                    "Nächster Scan in %ds...", self.config.scan_interval_seconds
                )
                time.sleep(self.config.scan_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Reddit Lead Hunter gestoppt.")

    def export_leads_json(self, leads: list[RedditLead], path: str) -> None:
        """Exportiert Lead-Liste als JSON-Datei."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump([lead.to_dict() for lead in leads], f, indent=2, ensure_ascii=False)
        logger.info("%d Leads exportiert nach %s", len(leads), path)

    def close(self) -> None:
        self._llm.close()

    def __enter__(self) -> "RedditLeadHunterSkill":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
