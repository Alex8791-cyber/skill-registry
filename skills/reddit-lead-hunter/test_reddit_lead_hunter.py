"""
tests/test_reddit_lead_hunter.py
==================================
Vollständige Test-Suite für den Reddit Lead Hunter Skill.

Ausführen:
    pytest tests/test_reddit_lead_hunter.py -v
    pytest tests/test_reddit_lead_hunter.py -v --tb=short  # Kurzausgabe

Alle externen Abhängigkeiten (Reddit API, LLM) werden gemockt.
Kein Netzwerkzugriff nötig.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch, call

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.reddit_lead_hunter import (
    IntentScorer,
    LeadHunterConfig,
    LLMClient,
    RedditLead,
    RedditLeadHunterSkill,
    ReplyDrafter,
    ScanResult,
    SeenPostStore,
)


# ---------------------------------------------------------------------------
# Fixtures & Hilfsfunktionen
# ---------------------------------------------------------------------------

def make_config(**overrides: Any) -> LeadHunterConfig:
    """Erstellt eine Test-Konfiguration mit sicheren Dummy-Credentials."""
    defaults = dict(
        product_name="Cognithor",
        product_description="Open-source Agent Operating System",
        subreddits=["LocalLLaMA", "SaaS"],
        min_intent_score=60,
        posts_per_subreddit=10,
        llm_provider="ollama",
        llm_model="test-model",
        llm_base_url="http://localhost:11434",
        reddit_client_id="test_client_id",
        reddit_client_secret="test_client_secret",
        reddit_user_agent="test:cognithor:v1",
    )
    defaults.update(overrides)
    return LeadHunterConfig(**defaults)


def make_mock_post(
    post_id: str = "abc123",
    title: str = "Looking for an agent framework with memory and security",
    body: str = "I need something that handles multiple LLM providers and has proper audit trails.",
    subreddit_name: str = "LocalLLaMA",
    score: int = 42,
    num_comments: int = 8,
    author: str = "test_user",
    created_utc: float = 1700000000.0,
    permalink: str = "/r/LocalLLaMA/comments/abc123/test_post/",
) -> MagicMock:
    """Erstellt einen Mock für ein praw.models.Submission-Objekt."""
    post = MagicMock()
    post.id = post_id
    post.title = title
    post.selftext = body
    post.subreddit.display_name = subreddit_name
    post.score = score
    post.num_comments = num_comments
    post.author = author
    post.created_utc = created_utc
    post.permalink = permalink
    return post


# ---------------------------------------------------------------------------
# Tests: LeadHunterConfig
# ---------------------------------------------------------------------------

class TestLeadHunterConfig(unittest.TestCase):

    def test_basic_creation(self) -> None:
        config = make_config()
        self.assertEqual(config.product_name, "Cognithor")
        self.assertEqual(config.subreddits, ["LocalLLaMA", "SaaS"])

    def test_subreddit_r_prefix_stripped(self) -> None:
        config = make_config(subreddits=["r/LocalLLaMA", "r/SaaS", "MachineLearning"])
        self.assertEqual(config.subreddits, ["LocalLLaMA", "SaaS", "MachineLearning"])

    def test_min_intent_score_validation(self) -> None:
        with self.assertRaises(Exception):
            make_config(min_intent_score=-1)
        with self.assertRaises(Exception):
            make_config(min_intent_score=101)

    def test_posts_per_subreddit_validation(self) -> None:
        with self.assertRaises(Exception):
            make_config(posts_per_subreddit=5)  # unter minimum 10
        with self.assertRaises(Exception):
            make_config(posts_per_subreddit=501)

    def test_from_json(self) -> None:
        data = {
            "product_name": "TestProduct",
            "product_description": "A test product",
            "subreddits": ["Python"],
            "reddit_client_id": "id",
            "reddit_client_secret": "secret",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp_path = f.name
        try:
            config = LeadHunterConfig.from_json(tmp_path)
            self.assertEqual(config.product_name, "TestProduct")
        finally:
            os.unlink(tmp_path)

    def test_env_loading(self) -> None:
        with patch.dict(os.environ, {
            "REDDIT_CLIENT_ID": "env_client_id",
            "REDDIT_CLIENT_SECRET": "env_secret",
        }):
            config = LeadHunterConfig(
                product_name="Test",
                product_description="Test desc",
            )
            self.assertEqual(config.reddit_client_id, "env_client_id")


# ---------------------------------------------------------------------------
# Tests: RedditLead
# ---------------------------------------------------------------------------

class TestRedditLead(unittest.TestCase):

    def _make_lead(self, **overrides: Any) -> RedditLead:
        defaults = dict(
            post_id="xyz789",
            subreddit="LocalLLaMA",
            title="Best agent framework in 2025?",
            body="Looking for something with memory and security",
            url="https://reddit.com/r/LocalLLaMA/comments/xyz789",
            author="some_user",
            created_utc=1700000000.0,
            upvotes=15,
            num_comments=3,
            intent_score=75,
            score_reasoning="User is actively looking for an agent framework",
            reply_draft="Hey! Cognithor might be exactly what you need...",
        )
        defaults.update(overrides)
        return RedditLead(**defaults)

    def test_content_hash_generated(self) -> None:
        lead = self._make_lead()
        self.assertIsInstance(lead.content_hash, str)
        self.assertEqual(len(lead.content_hash), 16)

    def test_content_hash_deterministic(self) -> None:
        lead1 = self._make_lead()
        lead2 = self._make_lead()
        self.assertEqual(lead1.content_hash, lead2.content_hash)

    def test_content_hash_differs_on_different_content(self) -> None:
        lead1 = self._make_lead(post_id="aaa")
        lead2 = self._make_lead(post_id="bbb")
        self.assertNotEqual(lead1.content_hash, lead2.content_hash)

    def test_detected_at_is_iso_format(self) -> None:
        lead = self._make_lead()
        # Sollte ISO-Datetime sein
        datetime.fromisoformat(lead.detected_at)

    def test_to_dict_serializable(self) -> None:
        lead = self._make_lead()
        d = lead.to_dict()
        # Muss JSON-serialisierbar sein
        json_str = json.dumps(d)
        restored = json.loads(json_str)
        self.assertEqual(restored["post_id"], "xyz789")
        self.assertEqual(restored["intent_score"], 75)

    def test_to_notification_text_contains_key_fields(self) -> None:
        lead = self._make_lead()
        text = lead.to_notification_text()
        self.assertIn("75/100", text)
        self.assertIn("LocalLLaMA", text)
        self.assertIn("https://reddit.com", text)
        self.assertIn("Cognithor", text)

    def test_to_notification_text_score_stars(self) -> None:
        lead_high = self._make_lead(intent_score=100)
        lead_low = self._make_lead(intent_score=0)
        self.assertIn("★★★★★", lead_high.to_notification_text())
        self.assertIn("☆☆☆☆☆", lead_low.to_notification_text())


# ---------------------------------------------------------------------------
# Tests: ScanResult
# ---------------------------------------------------------------------------

class TestScanResult(unittest.TestCase):

    def _make_result(self, leads: list = None) -> ScanResult:
        return ScanResult(
            started_at="2025-01-01T10:00:00+00:00",
            finished_at="2025-01-01T10:02:00+00:00",
            subreddits_scanned=["LocalLLaMA", "SaaS"],
            posts_checked=100,
            posts_skipped_duplicate=40,
            posts_skipped_low_score=55,
            leads_found=leads or [],
        )

    def test_lead_count_empty(self) -> None:
        result = self._make_result()
        self.assertEqual(result.lead_count, 0)

    def test_lead_count_with_leads(self) -> None:
        mock_leads = [MagicMock(), MagicMock(), MagicMock()]
        result = self._make_result(leads=mock_leads)
        self.assertEqual(result.lead_count, 3)

    def test_summary_contains_counts(self) -> None:
        result = self._make_result()
        summary = result.summary()
        self.assertIn("100", summary)
        self.assertIn("40", summary)
        self.assertIn("55", summary)
        self.assertIn("0 Leads", summary)


# ---------------------------------------------------------------------------
# Tests: SeenPostStore
# ---------------------------------------------------------------------------

class TestSeenPostStore(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_file = tempfile.mktemp(suffix=".json")
        self.store = SeenPostStore(self.tmp_file)

    def tearDown(self) -> None:
        self.store.clear()

    def test_unseen_post_not_seen(self) -> None:
        self.assertFalse(self.store.already_seen("post123"))

    def test_mark_seen_makes_it_seen(self) -> None:
        self.store.mark_seen("post123")
        self.assertTrue(self.store.already_seen("post123"))

    def test_count_increments(self) -> None:
        self.assertEqual(self.store.count(), 0)
        self.store.mark_seen("a")
        self.store.mark_seen("b")
        self.assertEqual(self.store.count(), 2)

    def test_duplicate_mark_does_not_increase_count(self) -> None:
        self.store.mark_seen("a")
        self.store.mark_seen("a")
        self.assertEqual(self.store.count(), 1)

    def test_persistence_across_instances(self) -> None:
        self.store.mark_seen("persistent_post")
        # Neue Instanz, gleiche Datei
        store2 = SeenPostStore(self.tmp_file)
        self.assertTrue(store2.already_seen("persistent_post"))

    def test_clear_removes_all(self) -> None:
        self.store.mark_seen("a")
        self.store.mark_seen("b")
        self.store.clear()
        self.assertEqual(self.store.count(), 0)
        self.assertFalse(os.path.exists(self.tmp_file))

    def test_corrupted_file_starts_fresh(self) -> None:
        with open(self.tmp_file, "w") as f:
            f.write("{not: valid json}")
        store = SeenPostStore(self.tmp_file)
        self.assertEqual(store.count(), 0)


# ---------------------------------------------------------------------------
# Tests: LLMClient
# ---------------------------------------------------------------------------

class TestLLMClient(unittest.TestCase):

    def setUp(self) -> None:
        self.config = make_config()

    def test_ollama_call_success(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"score": 80, "reasoning": "High intent"}'}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client.post", return_value=mock_response):
            client = LLMClient(self.config)
            result = client.complete("Test prompt")
            self.assertIn("score", result)

    def test_openai_compat_call_success(self) -> None:
        config = make_config(llm_provider="openai", llm_api_key="sk-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test reply"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client.post", return_value=mock_response):
            client = LLMClient(config)
            result = client.complete("Test prompt")
            self.assertEqual(result, "Test reply")

    def test_anthropic_call_success(self) -> None:
        config = make_config(llm_provider="anthropic", llm_api_key="sk-ant-test")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Anthropic reply"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client.post", return_value=mock_response):
            client = LLMClient(config)
            result = client.complete("Test prompt")
            self.assertEqual(result, "Anthropic reply")

    def test_context_manager(self) -> None:
        with patch("httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            with LLMClient(self.config) as client:
                pass
            mock_instance.close.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: IntentScorer
# ---------------------------------------------------------------------------

class TestIntentScorer(unittest.TestCase):

    def _make_scorer(self) -> tuple[IntentScorer, MagicMock]:
        config = make_config()
        mock_llm = MagicMock(spec=LLMClient)
        scorer = IntentScorer(mock_llm, config)
        return scorer, mock_llm

    def test_valid_score_returned(self) -> None:
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = '{"score": 75, "reasoning": "Clear need for agent framework"}'
        post = make_mock_post()
        score, reasoning = scorer.score(post)
        self.assertEqual(score, 75)
        self.assertIn("agent", reasoning.lower())

    def test_score_clamped_to_100(self) -> None:
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = '{"score": 150, "reasoning": "Too high"}'
        score, _ = scorer.score(make_mock_post())
        self.assertEqual(score, 100)

    def test_score_clamped_to_zero(self) -> None:
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = '{"score": -50, "reasoning": "Too low"}'
        score, _ = scorer.score(make_mock_post())
        self.assertEqual(score, 0)

    def test_invalid_json_returns_zero(self) -> None:
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = "Das ist kein JSON!"
        score, reasoning = scorer.score(make_mock_post())
        self.assertEqual(score, 0)
        self.assertIn("fehlgeschlagen", reasoning.lower())

    def test_json_embedded_in_text_parsed(self) -> None:
        """LLM gibt manchmal JSON in Text ein — muss trotzdem funktionieren."""
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = 'Sure! Here is the result: {"score": 65, "reasoning": "Relevant"} Hope that helps!'
        score, _ = scorer.score(make_mock_post())
        self.assertEqual(score, 65)

    def test_body_truncated_to_1000_chars(self) -> None:
        scorer, mock_llm = self._make_scorer()
        mock_llm.complete.return_value = '{"score": 50, "reasoning": "OK"}'
        long_body = "x" * 5000
        post = make_mock_post(body=long_body)
        scorer.score(post)
        # Im Prompt sollte der Body auf 1000 Zeichen begrenzt sein
        prompt_used = mock_llm.complete.call_args[0][0]
        # 1000 'x' drin, aber nicht 5000
        self.assertIn("x" * 100, prompt_used)
        self.assertNotIn("x" * 1001, prompt_used)


# ---------------------------------------------------------------------------
# Tests: ReplyDrafter
# ---------------------------------------------------------------------------

class TestReplyDrafter(unittest.TestCase):

    def test_draft_returns_string(self) -> None:
        config = make_config()
        mock_llm = MagicMock(spec=LLMClient)
        mock_llm.complete.return_value = "Great question! Cognithor could help here..."
        drafter = ReplyDrafter(mock_llm, config)
        result = drafter.draft(make_mock_post())
        self.assertIsInstance(result, str)
        self.assertIn("Cognithor", result)

    def test_draft_fallback_on_error(self) -> None:
        import httpx
        config = make_config()
        mock_llm = MagicMock(spec=LLMClient)
        mock_llm.complete.side_effect = httpx.HTTPError("Connection refused")
        drafter = ReplyDrafter(mock_llm, config)
        result = drafter.draft(make_mock_post())
        self.assertIn("konnte nicht generiert werden", result)

    def test_product_name_in_prompt(self) -> None:
        config = make_config(product_name="SuperAgent")
        mock_llm = MagicMock(spec=LLMClient)
        mock_llm.complete.return_value = "Reply text"
        drafter = ReplyDrafter(mock_llm, config)
        drafter.draft(make_mock_post())
        prompt = mock_llm.complete.call_args[0][0]
        self.assertIn("SuperAgent", prompt)


# ---------------------------------------------------------------------------
# Tests: RedditLeadHunterSkill (Integration, vollständig gemockt)
# ---------------------------------------------------------------------------

class TestRedditLeadHunterSkill(unittest.TestCase):

    def _make_skill(
        self,
        config: LeadHunterConfig = None,
        score: int = 75,
        notification_callback=None,
    ) -> tuple[RedditLeadHunterSkill, SeenPostStore]:
        config = config or make_config()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            seen_path = f.name
        os.unlink(seen_path)  # SeenPostStore legt Datei selbst an
        seen_store = SeenPostStore(seen_path)

        # Alle externen Abhängigkeiten mocken
        with patch("praw.Reddit"):
            skill = RedditLeadHunterSkill(
                config=config,
                seen_store=seen_store,
                notification_callback=notification_callback,
            )
            # LLM-Responses mocken
            skill._scorer = MagicMock()
            skill._scorer.score.return_value = (score, f"Score {score} — relevant post")
            skill._drafter = MagicMock()
            skill._drafter.draft.return_value = "Hey! Cognithor is exactly what you need."

        return skill, seen_store

    def _inject_reddit_posts(
        self, skill: RedditLeadHunterSkill, posts_per_sub: list[list]
    ) -> None:
        """Injiziert Mock-Posts pro Subreddit."""
        subreddit_mocks = []
        for posts in posts_per_sub:
            sub_mock = MagicMock()
            sub_mock.new.return_value = posts
            subreddit_mocks.append(sub_mock)
        skill._reddit.subreddit.side_effect = subreddit_mocks

    # --- Basis-Funktionalität ---

    def test_scan_once_returns_scan_result(self) -> None:
        skill, _ = self._make_skill()
        post = make_mock_post()
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertIsInstance(result, ScanResult)

    def test_high_score_post_becomes_lead(self) -> None:
        skill, _ = self._make_skill(score=80)
        post = make_mock_post(post_id="high_score_post")
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.lead_count, 1)
        self.assertEqual(result.leads_found[0].post_id, "high_score_post")
        self.assertEqual(result.leads_found[0].intent_score, 80)

    def test_low_score_post_excluded(self) -> None:
        config = make_config(min_intent_score=60)
        skill, _ = self._make_skill(config=config, score=30)
        post = make_mock_post(post_id="low_score")
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.lead_count, 0)
        self.assertEqual(result.posts_skipped_low_score, 1)

    def test_duplicate_post_skipped(self) -> None:
        skill, seen_store = self._make_skill(score=90)
        post = make_mock_post(post_id="dup_post")
        seen_store.mark_seen("dup_post")
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.lead_count, 0)
        self.assertEqual(result.posts_skipped_duplicate, 1)

    def test_short_title_post_skipped(self) -> None:
        skill, _ = self._make_skill(score=90)
        post = make_mock_post(title="Hi")  # Unter 15 Zeichen
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.lead_count, 0)

    # --- Notification-Callback ---

    def test_notification_callback_called_for_lead(self) -> None:
        callback = MagicMock()
        skill, _ = self._make_skill(score=75, notification_callback=callback)
        post = make_mock_post()
        self._inject_reddit_posts(skill, [[post], []])
        skill.scan_once()
        callback.assert_called_once()
        lead_arg = callback.call_args[0][0]
        self.assertIsInstance(lead_arg, RedditLead)

    def test_notification_callback_not_called_for_low_score(self) -> None:
        callback = MagicMock()
        config = make_config(min_intent_score=80)
        skill, _ = self._make_skill(config=config, score=30, notification_callback=callback)
        post = make_mock_post()
        self._inject_reddit_posts(skill, [[post], []])
        skill.scan_once()
        callback.assert_not_called()

    def test_failing_callback_does_not_crash_scan(self) -> None:
        def bad_callback(lead):
            raise RuntimeError("Notification service down")

        skill, _ = self._make_skill(score=75, notification_callback=bad_callback)
        post = make_mock_post()
        self._inject_reddit_posts(skill, [[post], []])
        # Darf keine Exception werfen
        result = skill.scan_once()
        self.assertEqual(result.lead_count, 1)  # Lead trotzdem gezählt

    # --- Multi-Subreddit ---

    def test_multiple_subreddits_scanned(self) -> None:
        config = make_config(subreddits=["LocalLLaMA", "SaaS", "Python"])
        skill, _ = self._make_skill(config=config, score=70)
        posts = [make_mock_post(f"post_{i}", subreddit_name=sub) for i, sub in enumerate(config.subreddits)]
        self._inject_reddit_posts(skill, [[posts[0]], [posts[1]], [posts[2]]])
        result = skill.scan_once()
        self.assertEqual(result.posts_checked, 3)
        self.assertEqual(result.lead_count, 3)
        self.assertEqual(len(result.subreddits_scanned), 3)

    def test_subreddit_error_does_not_crash_skill(self) -> None:
        config = make_config(subreddits=["LocalLLaMA", "PrivateSub"])
        skill, _ = self._make_skill(config=config, score=75)
        good_sub = MagicMock()
        good_sub.new.return_value = [make_mock_post("good_post")]
        bad_sub = MagicMock()
        bad_sub.new.side_effect = Exception("Subreddit banned")
        skill._reddit.subreddit.side_effect = [good_sub, bad_sub]
        result = skill.scan_once()
        # Skill läuft weiter trotz Fehler in einem Subreddit
        self.assertGreaterEqual(result.posts_checked, 0)

    # --- Lead-Felder ---

    def test_lead_has_correct_url_format(self) -> None:
        skill, _ = self._make_skill(score=75)
        post = make_mock_post(permalink="/r/LocalLLaMA/comments/abc/test/")
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertTrue(result.leads_found[0].url.startswith("https://reddit.com"))

    def test_lead_has_correct_subreddit(self) -> None:
        skill, _ = self._make_skill(score=75)
        post = make_mock_post(subreddit_name="LocalLLaMA")
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.leads_found[0].subreddit, "LocalLLaMA")

    def test_deleted_author_handled(self) -> None:
        skill, _ = self._make_skill(score=75)
        post = make_mock_post()
        post.author = None
        self._inject_reddit_posts(skill, [[post], []])
        result = skill.scan_once()
        self.assertEqual(result.leads_found[0].author, "[deleted]")

    # --- Export ---

    def test_export_leads_json(self) -> None:
        skill, _ = self._make_skill()
        with patch("praw.Reddit"):
            leads = [
                RedditLead(
                    post_id="p1", subreddit="LocalLLaMA", title="Test",
                    body="Body", url="https://reddit.com/r/test",
                    author="user", created_utc=0, upvotes=5, num_comments=2,
                    intent_score=75, score_reasoning="Relevant", reply_draft="Reply",
                )
            ]
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
                export_path = f.name
            skill.export_leads_json(leads, export_path)
            with open(export_path, encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["post_id"], "p1")
            os.unlink(export_path)

    # --- Context Manager ---

    def test_context_manager_closes_llm(self) -> None:
        skill, _ = self._make_skill()
        skill._llm = MagicMock(spec=LLMClient)
        with skill:
            pass
        skill._llm.close.assert_called_once()

    # --- Statistiken ---

    def test_scan_result_counts_are_accurate(self) -> None:
        config = make_config(min_intent_score=60)
        skill, seen_store = self._make_skill(config=config)
        skill._scorer.score.side_effect = [
            (80, "High intent"),   # → Lead
            (30, "Low intent"),    # → Skipped
            (75, "Medium-high"),   # → Lead
        ]
        seen_post = make_mock_post(post_id="seen")
        new_posts = [
            make_mock_post(post_id="new1"),
            make_mock_post(post_id="new2"),
            make_mock_post(post_id="new3"),
        ]
        seen_store.mark_seen("seen")
        self._inject_reddit_posts(skill, [[seen_post] + new_posts, []])
        result = skill.scan_once()
        self.assertEqual(result.posts_skipped_duplicate, 1)
        self.assertEqual(result.posts_skipped_low_score, 1)
        self.assertEqual(result.lead_count, 2)


# ---------------------------------------------------------------------------
# Tests: Config-Validierung (Edge Cases)
# ---------------------------------------------------------------------------

class TestConfigEdgeCases(unittest.TestCase):

    def test_empty_subreddits_list_allowed(self) -> None:
        config = make_config(subreddits=[])
        self.assertEqual(config.subreddits, [])

    def test_whitespace_in_subreddit_stripped(self) -> None:
        config = make_config(subreddits=["  LocalLLaMA  ", "r/ SaaS "])
        self.assertIn("LocalLLaMA", config.subreddits)


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
