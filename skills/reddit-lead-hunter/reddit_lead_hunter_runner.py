"""
reddit_lead_hunter_runner.py
============================
CLI-Runner für den Reddit Lead Hunter Skill.

Verwendung:
    python reddit_lead_hunter_runner.py --config config.json
    python reddit_lead_hunter_runner.py --subreddits LocalLLaMA SaaS --min-score 65
    python reddit_lead_hunter_runner.py --once   # einzelner Scan, kein Daemon

Umgebungsvariablen (alternativ zu config.json):
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    COGNITHOR_LLM_PROVIDER, COGNITHOR_LLM_MODEL, COGNITHOR_LLM_BASE_URL
"""

import argparse
import json
import logging
import os
import sys

# Damit der Skill-Import auch ohne installiertes Paket funktioniert
sys.path.insert(0, os.path.dirname(__file__))

from skills.reddit_lead_hunter import (
    LeadHunterConfig,
    RedditLead,
    RedditLeadHunterSkill,
    SeenPostStore,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("reddit_lead_hunter.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("cognithor.runner")


# ---------------------------------------------------------------------------
# Notification-Callbacks
# ---------------------------------------------------------------------------

def console_notification(lead: RedditLead) -> None:
    """Gibt Lead direkt in der Konsole aus (Default)."""
    print("\n" + lead.to_notification_text())


def file_notification(lead: RedditLead, output_path: str = "leads_output.jsonl") -> None:
    """Hängt jeden Lead als JSON-Zeile an eine JSONL-Datei an."""
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(lead.to_dict(), ensure_ascii=False) + "\n")


def build_slack_notification(webhook_url: str) -> callable:
    """Erstellt einen Slack-Webhook-Callback. Benötigt: pip install httpx"""
    import httpx

    def _notify(lead: RedditLead) -> None:
        text = lead.to_notification_text()
        # Markdown → Slack mrkdwn (minimales Mapping)
        slack_text = text.replace("**", "*")
        httpx.post(webhook_url, json={"text": slack_text}, timeout=10)

    return _notify


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Cognithor Reddit Lead Hunter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--config", help="Pfad zur JSON-Konfigurationsdatei")
    p.add_argument("--product-name", default="Cognithor", help="Produktname")
    p.add_argument(
        "--product-description",
        default="Open-source Agent Operating System for AI agents",
        help="Kurze Produktbeschreibung",
    )
    p.add_argument(
        "--subreddits",
        nargs="+",
        default=["LocalLLaMA", "SaaS", "agentframework", "MachineLearning"],
        help="Subreddits ohne 'r/'",
    )
    p.add_argument("--min-score", type=int, default=60, help="Minimaler Intent-Score (0-100)")
    p.add_argument("--posts-per-sub", type=int, default=100)
    p.add_argument("--interval", type=int, default=1800, help="Scan-Interval in Sekunden")
    p.add_argument("--llm-provider", default="ollama")
    p.add_argument("--llm-model", default="qwen2.5:27b")
    p.add_argument("--llm-url", default="http://localhost:11434")
    p.add_argument("--once", action="store_true", help="Einzelner Scan, dann beenden")
    p.add_argument("--export", help="Leads als JSON exportieren nach <PFAD>")
    p.add_argument("--slack-webhook", help="Slack Webhook URL für Notifications")
    p.add_argument("--seen-db", default=".cognithor_reddit_seen.json")
    p.add_argument("--debug", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Konfiguration aufbauen
    if args.config:
        config = LeadHunterConfig.from_json(args.config)
    else:
        config = LeadHunterConfig(
            product_name=args.product_name,
            product_description=args.product_description,
            subreddits=args.subreddits,
            min_intent_score=args.min_score,
            posts_per_subreddit=args.posts_per_sub,
            scan_interval_seconds=args.interval,
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            llm_base_url=args.llm_url,
        )

    # Notification-Callbacks aufbauen
    callbacks = [console_notification]
    if args.slack_webhook:
        callbacks.append(build_slack_notification(args.slack_webhook))
    if args.export:
        callbacks.append(lambda lead: file_notification(lead, args.export))

    def combined_callback(lead: RedditLead) -> None:
        for cb in callbacks:
            cb(lead)

    seen_store = SeenPostStore(args.seen_db)

    logger.info(
        "Konfiguration: Produkt='%s' | Subreddits=%s | min_score=%d | LLM=%s/%s",
        config.product_name,
        config.subreddits,
        config.min_intent_score,
        config.llm_provider,
        config.llm_model,
    )

    with RedditLeadHunterSkill(
        config=config,
        seen_store=seen_store,
        notification_callback=combined_callback,
    ) as skill:
        if args.once:
            result = skill.scan_once()
            print(f"\n{'═' * 60}")
            print(result.summary())
            if args.export and result.leads_found:
                skill.export_leads_json(result.leads_found, args.export)
        else:
            skill.run_continuous()


if __name__ == "__main__":
    main()
