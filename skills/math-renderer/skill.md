---
name: Mathematik Renderer
trigger_keywords: [formel, gleichung, mathe, math, berechnung, integral, ableitung, matrix, beweis, latex, equation, formula, rechnen, summe, bruch]
tools_required: [typst_render]
category: productivity
priority: 8
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [typst-integration]
---
# Mathematik Renderer

## Wann anwenden
Wenn der User mathematische Formeln, Gleichungen oder Berechnungen als PDF haben moechte.

## Typst Mathe-Syntax

Inline: `$x^2 + y^2 = z^2$`

Block:
```typst
$ integral_0^infinity e^(-x^2) dif x = sqrt(pi) / 2 $
```

## Symbole
| Mathe | Typst |
|-------|-------|
| Bruch | `a / b` oder `frac(a, b)` |
| Wurzel | `sqrt(x)` |
| Integral | `integral_a^b f(x) dif x` |
| Summe | `sum_(i=0)^n i^2` |
| Matrix | `mat(1, 2; 3, 4)` |
| Ableitung | `(dif f) / (dif x)` |
| Griechisch | `alpha`, `beta`, `gamma`, `pi`, `sigma`, `omega` |

## Vorgehen
1. Erkenne Mathe-Anfrage
2. Konvertiere in Typst-Syntax
3. Nutze `typst_render` mit `#set text(font: "New Computer Modern", size: 12pt)`
4. Einzelne Formeln: kompaktes Layout, Dokumente: A4 mit Nummerierung
