---
name: Typst Document Generation
trigger_keywords: [typst, pdf, bericht, rechnung, brief, report, invoice, letter, wissenschaftlich, vorlage, template]
tools_required: [typst_render, template_list, template_render]
category: productivity
priority: 3
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [typst-integration]
---
# Typst Document Generation

## Wann anwenden
Wenn der User hochwertige PDF-Dokumente erstellen moechte (Berichte, Briefe, Rechnungen, wissenschaftliche Arbeiten).

## Verfuegbare Templates
- **Brief**: Formeller Geschaeftsbrief (9 Variablen)
- **Rechnung**: Rechnung mit Positionen (9 Variablen)
- **Bericht**: Strukturierter Bericht mit Inhaltsverzeichnis (6 Variablen)
- **Lebenslauf**: Professioneller CV (8 Variablen)
- **Protokoll**: Besprechungsprotokoll (9 Variablen)
- **Angebot**: Geschaeftliches Angebot (12 Variablen)

## Vorgehen
1. `template_list` zeigt verfuegbare Vorlagen
2. `template_render` fuellt Vorlage mit Werten und kompiliert zu PDF
3. Fuer freie Dokumente: `typst_render` mit eigenem Typst-Code

## Grundsyntax
```typst
#set page(paper: "a4", margin: 2cm)
= Titel
== Abschnitt
Text. *Fett.* _Kursiv._
#table(columns: 2, [A], [B], [1], [2])
```
