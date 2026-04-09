---
name: reddit-lead-hunter
trigger_keywords: [Reddit, Lead Hunter, Reddit Scan, Social Listening, Lead Generation, Reddit Monitoring, Intent Score, Kaufintent, Reddit Leads, Community Monitoring]
tools_required: [web_search, search_and_read, write_file, run_python, send_message]
category: marketing
priority: 7
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
agent: researcher
---

# Reddit Lead Hunter

## Wann anwenden
Wenn der Benutzer Reddit nach potenziellen Kunden oder relevanten Diskussionen scannen moechte. Geeignet fuer Social Listening, Lead-Generierung und Community-Monitoring.

## Was dieser Skill macht
1. Scannt konfigurierte Subreddits nach neuen Posts
2. Filtert Spam, Konkurrenten und Low-Quality-Posts heraus
3. Bewertet jeden Post mit einem Intent-Score von 0-100
4. Draftet kontextbewusste Antworten im konfigurierten Ton
5. Verhindert Duplikate ueber den integrierten SeenPostStore
6. Kann kontinuierlich im Daemon-Modus laufen

## Voraussetzungen
- Reddit API Key (kostenlos: reddit.com/prefs/apps, Script-App)
- `pip install praw pydantic httpx`
- Umgebungsvariablen: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

## Nutzung

### Einmal-Scan
```
Scanne Reddit nach Leads fuer Cognithor in r/LocalLLaMA, r/SaaS und r/Python
```

### Konfigurierter Daemon
```bash
python reddit_lead_hunter_runner.py --config config.example.json
```

### Mit Slack-Benachrichtigung
```bash
python reddit_lead_hunter_runner.py --once --slack-webhook "https://hooks.slack.com/..."
```

## Konfiguration (config.example.json)
- `product_name` — Name deines Produkts
- `product_description` — Ein-Satz-Beschreibung fuer die KI-Scoring-Prompts
- `reply_tone` — Gewuenschter Antwort-Stil (z.B. "helpful, technically credible")
- `subreddits` — Liste der zu ueberwachenden Subreddits
- `min_intent_score` — Minimum-Score fuer einen Lead (0-100, empfohlen: 65)
- `scan_interval_seconds` — Pause zwischen Scans (Standard: 1800 = 30 Min)
- `llm_provider` — ollama, openai, oder anthropic
- `llm_model` — Modellname (z.B. qwen2.5:27b)

## Enthaltene Dateien
- `reddit_lead_hunter.py` — Kern-Skill (Scan, Scoring, Drafting, Export)
- `reddit_lead_hunter_runner.py` — CLI Runner mit Daemon-Modus und Slack-Webhook
- `config.example.json` — Beispiel-Konfiguration
- `requirements.txt` — Python-Abhaengigkeiten
- `test_reddit_lead_hunter.py` — 54 Tests (komplett gemockt, kein API-Key noetig)

## Cognithor-Vorteile gegenueber Huntopic
- 16 LLM-Anbieter statt 1
- 5-Tier Memory verhindert Duplikate persistent
- 17 Notification-Channels (Slack, Telegram, Discord, ...)
- Lokaler Betrieb via Ollama (DSGVO-konform)
- Audit-Trail via Hashline Guard
