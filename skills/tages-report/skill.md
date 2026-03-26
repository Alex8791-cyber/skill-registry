---
name: tages-report
trigger_keywords: [Tagesreport, Tagesbericht, Zusammenfassung heute, was habe ich gemacht, Tagesrueckblick, Daily Report, EOD, End of Day, Abend-Briefing, was wurde erledigt]
tools_required: [search_memory, get_recent_episodes, get_core_memory, calendar_upcoming, list_directory, create_chart, write_file]
category: productivity
priority: 6
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
---
# Tages-Report & Rueckblick

## Wann anwenden
Wenn der Benutzer einen Ueberblick ueber den Tag haben moechte — was erledigt wurde,
was offen ist, und was morgen ansteht.
Typische Trigger: "Was habe ich heute gemacht?", "Tagesbericht",
"Fasse den Tag zusammen", "EOD Report", "Was steht morgen an?".

## Voraussetzungen
- Keine — der Skill arbeitet aus Memory, Episodes und Kalender.

## Ablauf

### 1. Heutige Aktivitaeten sammeln
Mit `get_recent_episodes` die letzten 24 Stunden abrufen:
- Welche Tools wurden genutzt?
- Welche Aufgaben wurden bearbeitet?
- Welche Dateien erstellt oder geaendert?

### 2. Memory-Kontext laden
Mit `search_memory` nach heute relevanten Eintraegen suchen:
- Neue Erkenntnisse oder Entscheidungen
- Gespeicherte Notizen
- Kontakte mit denen interagiert wurde

### 3. Offene Aufgaben pruefen
Mit `search_memory` nach offenen To-Dos und Pendenzen suchen.
Aus den heutigen Episodes erkennen, was angefangen aber nicht abgeschlossen wurde.

### 4. Morgen-Vorschau
Mit `calendar_upcoming` die Termine fuer morgen laden.
Vorbereitungsbedarf identifizieren.

### 5. Report erstellen
Strukturierte Antwort (KEIN Datei-Export, direkte Antwort im Chat):

```
## Tages-Report — {Datum}

### Erledigt
- [Aufgabe 1]: {Kurzbeschreibung}
- [Aufgabe 2]: ...

### Offen / In Arbeit
- [Aufgabe]: {Status} — Naechster Schritt: {Was tun}

### Highlights
- {Wichtigste Erkenntnis oder Entscheidung des Tages}

### Morgen
- {Termin 1}: {Uhrzeit} — {Vorbereitung noetig?}
- {To-Do mit hoechster Prioritaet}
```

### 6. Optional: Als Datei speichern
Nur wenn explizit gewuenscht: `write_file` → `~/.jarvis/workspace/report-{datum}.md`

## Bekannte Fallstricke
- Leerer Tag: Wenn keine Episodes vorhanden, ehrlich sagen "Heute keine Aktivitaeten erfasst"
  statt etwas zu erfinden.
- Kalender nicht konfiguriert: Morgen-Vorschau ueberspringen wenn calendar_upcoming
  keine Ergebnisse liefert.
- Nicht zu detailliert: Maximal 7-10 erledigte Punkte. Bei mehr zusammenfassen.

## Qualitaetskriterien
- Klare Trennung: Erledigt / Offen / Morgen
- Konkrete naechste Schritte fuer offene Aufgaben
- Morgen-Vorschau mit Vorbereitungshinweisen
- Kompakt — soll in 30 Sekunden lesbar sein
