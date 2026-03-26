---
name: meeting-protokoll
trigger_keywords: [Protokoll, Mitschrift, Meeting Notes, Besprechungsnotizen, Transkript, Action Items, Entscheidungen, Nachbereitung, Follow-Up, was wurde besprochen]
tools_required: [media_transcribe_audio, media_extract_text, write_file, search_memory, email_send, vault_save]
category: productivity
priority: 6
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
---
# Meeting-Protokoll & Nachbereitung

## Wann anwenden
Wenn der Benutzer ein Meeting nachbereiten, ein Protokoll erstellen oder Action Items
aus einer Besprechung extrahieren moechte. Auch wenn eine Audio-Aufnahme transkribiert
werden soll.
Typische Trigger: "Erstelle ein Protokoll", "Was wurde besprochen?",
"Transkribiere das Meeting", "Fasse die Besprechung zusammen",
"Welche Action Items gibt es?", "Schick die Follow-Ups raus".

## Voraussetzungen
- Audio-Datei (MP3, WAV, M4A) ODER Text-Mitschrift ODER muendliche Zusammenfassung
- Optional: Teilnehmerliste, Meeting-Titel, Datum

## Ablauf

### 1. Eingabe verarbeiten
- **Audio vorhanden**: Transkribieren mit `media_transcribe_audio`.
  Ergebnis pruefen — bei schlechter Qualitaet den User informieren.
- **Dokument vorhanden**: Text extrahieren mit `media_extract_text`.
- **Muendliche Zusammenfassung**: Direkt vom User-Text arbeiten.

### 2. Kontext anreichern
Mit `search_memory` nach frueheren Meetings, Projekten oder Personen suchen
die im Transkript erwaehnt werden. Relevanten Kontext fuer die Zusammenfassung nutzen.

### 3. Strukturiertes Protokoll erstellen
Datei mit `write_file` erstellen: `~/.jarvis/workspace/protokoll-{titel}-{datum}.md`

Struktur:
```
# Meeting-Protokoll: {Titel}
Datum: {Datum} | Teilnehmer: {Liste}

## Zusammenfassung (3-5 Saetze)
[Kernaussagen des Meetings]

## Entscheidungen
- [E1]: {Entscheidung} — Verantwortlich: {Name}
- [E2]: ...

## Action Items
| # | Aufgabe | Verantwortlich | Deadline | Prioritaet |
|---|---------|---------------|----------|-----------|
| 1 | ...     | ...           | ...      | Hoch      |

## Offene Fragen
- [F1]: {Frage} — Klaerung durch: {Name}

## Naechstes Meeting
Vorschlag: {Datum/Zeitraum} | Themen: {Liste}
```

### 4. Im Vault speichern
Protokoll mit `vault_save` archivieren:
- Ordner: `meetings`
- Tags: Teilnehmer-Namen, Projekt-Name, Datum

### 5. Optional: Follow-Up E-Mails
Wenn gewuenscht, fuer jeden Action-Item-Verantwortlichen eine kurze
Follow-Up E-Mail entwerfen mit `email_send`:
- Betreff: "Action Item aus Meeting: {Titel}"
- Inhalt: Konkrete Aufgabe + Deadline + Kontext

## Bekannte Fallstricke
- Audio-Qualitaet: Bei schlechter Aufnahme wird das Transkript ungenau.
  Immer dem User die Moeglichkeit geben, zu korrigieren.
- Vertraulichkeit: Meeting-Inhalte nur lokal verarbeiten.
- Zu viele Action Items: Maximal 7-10 pro Meeting. Bei mehr priorisieren.
- Deadlines: Wenn keine genannt, realistische Vorschlaege machen (z.B. "naechste Woche").

## Qualitaetskriterien
- Alle Entscheidungen mit Verantwortlichem erfasst
- Action Items mit Deadline und Prioritaet
- Zusammenfassung in maximal 5 Saetzen
- Offene Fragen explizit benannt
- Naechstes Meeting vorgeschlagen
