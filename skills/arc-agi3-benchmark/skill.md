---
name: ARC-AGI-3 Benchmark
trigger_keywords: [arc, arc-agi, benchmark, puzzle, spiel, reasoning, competition, wettbewerb]
tools_required: [arc_play, arc_status, arc_replay]
category: research
priority: 5
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [arc-agi3-integration]
---
# ARC-AGI-3 Benchmark Modus

## Wann anwenden
Wenn der User ARC-AGI-3 Interactive Reasoning Benchmark Games spielen oder analysieren moechte.

## Aktionen
1. **Einzelnes Game**: `arc_play` mit game_id (z.B. "ls20", "ft09", "vc33")
2. **Alle Games benchmarken**: `arc_play` mit mode="benchmark"
3. **Status abfragen**: `arc_status` fuer laufende Sessions
4. **Replay ansehen**: `arc_replay` fuer abgeschlossene Sessions

## Game-IDs
25 Games verfuegbar: ls20, ft09, vc33, bp35, sc25, cn04, ar25, wa30, lp85, s5i5, ka59, re86, sp80, r11l, m0r0, tr87, lf52, tu93, cd82, sk48, dc22, g50t, sb26, tn36, su15.

## Hinweise
- ARC-AGI-3 ist ein interaktiver Benchmark OHNE Instruktionen
- Der Agent muss Spielregeln selbst entdecken
- CNN Action Predictor lernt online waehrend des Spielens
- CLI: `python -m jarvis.arc --game ls20`
