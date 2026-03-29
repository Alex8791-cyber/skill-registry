---
name: Markdown zu PDF
trigger_keywords: [markdown, md, konvertieren, convert, pdf, export]
tools_required: [typst_render]
category: productivity
priority: 2
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [typst-integration]
---
# Markdown zu PDF Konvertierung

## Wann anwenden
Wenn der User Markdown-Text als hochwertiges PDF haben moechte.

## Konvertierung Markdown → Typst
| Markdown | Typst |
|----------|-------|
| `# Titel` | `= Titel` |
| `## Abschnitt` | `== Abschnitt` |
| `**fett**` | `*fett*` |
| `*kursiv*` | `_kursiv_` |
| `- Punkt` | `- Punkt` |
| Tabellen | `#table(columns: N, ...)` |

## Vorgehen
1. Konvertiere Markdown-Syntax zu Typst
2. Setze Seiteneinstellungen: `#set page(paper: "a4", margin: 2cm)`
3. Nutze `typst_render` um PDF zu erstellen
