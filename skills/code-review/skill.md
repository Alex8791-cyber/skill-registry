---
name: code-review
trigger_keywords: [Code Review, Review, Pull Request, PR, Diff, Code pruefen, Bugs finden, Security Check, Code-Qualitaet, Refactoring-Vorschlag]
tools_required: [git_diff, git_log, read_file, analyze_code, run_python, find_in_files, write_file]
category: development
priority: 6
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
agent: coder
---
# Code Review

## Wann anwenden
Wenn der Benutzer Code ueberpruefen lassen moechte — einen Diff, eine Datei, einen PR,
oder ein ganzes Verzeichnis.
Typische Trigger: "Review diesen Code", "Pruefe den PR", "Finde Bugs in X",
"Ist das sicher?", "Code-Qualitaet von X".

## Voraussetzungen
- Dateipfad(e) ODER Git-Branch/Commit-Range
- Optional: Fokus (Bugs, Security, Performance, Style)

## Ablauf

### 1. Code sammeln
- **Einzelne Datei**: `read_file` fuer den vollstaendigen Quellcode.
- **Git Diff**: `git_diff` fuer Aenderungen seit letztem Commit oder zwischen Branches.
- **Verzeichnis**: `find_in_files` um relevante Dateien zu identifizieren,
  dann `read_file` fuer jede.

### 2. Kontext verstehen
- `git_log` fuer die letzten 5-10 Commits — was wurde geaendert und warum?
- Projektstruktur erkennen: Sprache, Framework, Test-Pattern.

### 3. Statische Analyse
Mit `analyze_code` eine automatische Pruefung durchfuehren:
- Syntax-Fehler
- Unused Imports/Variables
- Typ-Fehler (wenn Typ-System vorhanden)

### 4. Manuelle Review — 5 Dimensionen
Jede Dimension bewerten (OK / Warnung / Kritisch):

#### Korrektheit
- Logik-Fehler, Off-by-One, Null-Checks fehlend
- Edge Cases nicht behandelt
- Race Conditions bei async Code

#### Sicherheit
- SQL Injection, XSS, Command Injection
- Hartcodierte Credentials oder Secrets
- Unsichere Deserialisierung
- Path Traversal

#### Performance
- N+1 Queries, fehlende Indizes
- Unnoetige Kopien grosser Datenstrukturen
- Blockierende I/O in async Context

#### Wartbarkeit
- Funktionen > 50 Zeilen → Aufteilen vorschlagen
- Verschachtelte if/else > 3 Ebenen → Early Return
- Magische Zahlen → Konstanten
- Fehlende Docstrings bei oeffentlichen APIs

#### Test-Abdeckung
- Gibt es Tests fuer den geaenderten Code?
- Sind Edge Cases getestet?
- Sind Mocks sinnvoll oder testen sie nur sich selbst?

### 5. Review-Ergebnis formatieren
Direkte Antwort im Chat:

```
## Code Review: {Datei/PR}

### Zusammenfassung
{1-2 Saetze Gesamteindruck}

### Kritisch (sofort fixen)
- **[Zeile X]**: {Problem} → {Loesung}

### Wichtig (sollte gefixt werden)
- **[Zeile Y]**: {Problem} → {Loesung}

### Vorschlaege (nice to have)
- **[Zeile Z]**: {Verbesserung}

### Positiv
- {Was gut gemacht wurde}

### Bewertung: {OK / Aenderungen noetig / Blockiert}
```

### 6. Optional: Fixes implementieren
Wenn gewuenscht, die kritischen Fixes direkt umsetzen:
- `run_python` fuer automatische Korrekturen
- Tests ausfuehren um Regressionen zu pruefen

## Bekannte Fallstricke
- Nicht ueber-reviewen: Maximal 10-15 Findings. Mehr ist nicht hilfreich.
- Style vs. Substanz: Style-Kommentare nur wenn sie Lesbarkeit stark beeinflussen.
- False Positives: Analyse-Tools produzieren Rauschen. Nur berichten was wirklich relevant ist.
- Kontext fehlt: Ohne Verstaendnis des Gesamtprojekts koennen Reviews daneben liegen.
  Immer zuerst Kontext sammeln.

## Qualitaetskriterien
- Jedes Finding mit Zeilennummer und konkretem Fix-Vorschlag
- Klare Priorisierung (Kritisch > Wichtig > Vorschlag)
- Mindestens ein positives Feedback
- Bewertung mit klarer Empfehlung
