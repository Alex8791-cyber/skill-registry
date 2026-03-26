---
name: vertrag-pruefer
trigger_keywords: [Vertrag, pruefen, Vertragspruefung, AGB, Klausel, Risiko, juristisch, Kuendigungsfrist, Haftung, Vertragsanalyse, NDA, SLA, Dienstleistungsvertrag, Mietvertrag, Arbeitsvertrag]
tools_required: [media_extract_text, analyze_document, search_memory, vault_save, web_search]
category: legal
priority: 6
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
---
# Vertrags-Pruefer

## Wann anwenden
Wenn der Benutzer einen Vertrag, AGB, NDA oder aehnliches Dokument pruefen lassen moechte.
Typische Trigger: "Pruefe diesen Vertrag", "Was steht in den AGB?",
"Gibt es Risiken im Vertrag?", "Kuendigungsfristen?", "Ist der NDA ok?".

## Voraussetzungen
- Dateipfad zum Vertragsdokument (PDF, DOCX, TXT)
- Optional: Art des Vertrags, besondere Aufmerksamkeitspunkte

## WICHTIGER DISCLAIMER
Dieser Skill ersetzt KEINE rechtliche Beratung. Die Analyse ist eine erste Orientierung.
Fuer verbindliche Rechtsauskuenfte muss ein Anwalt konsultiert werden. Diesen Disclaimer
IMMER am Anfang der Analyse anzeigen.

## Ablauf

### 1. Text extrahieren
Mit `media_extract_text` den Vertragstext aus dem Dokument extrahieren.
Bei gescannten PDFs den User auf OCR-Bedarf hinweisen.

### 2. Vertragstyp klassifizieren
Anhand des Inhalts erkennen:
- **Arbeitsvertrag** — Verguetung, Arbeitszeit, Kuendigung, Wettbewerbsverbot
- **Mietvertrag** — Miete, Nebenkosten, Kuendigung, Renovierung
- **Dienstleistungsvertrag** — Leistung, Verguetung, Haftung, Kuendigung
- **NDA** — Gegenstand, Dauer, Vertragsstrafe, Ausnahmen
- **SLA** — Verfuegbarkeit, Reaktionszeiten, Vertragsstrafen, Eskalation
- **Kaufvertrag** — Gegenstand, Preis, Gewaehrleistung, Ruecktritt
- **Lizenzvertrag** — Umfang, Dauer, Gebuehren, Nutzungsrechte
- **Sonstiger** — Allgemeine Analyse

### 3. Strukturierte Pruefung — 7 Dimensionen

#### A. Parteien & Laufzeit
- Wer sind die Vertragsparteien?
- Vertragsbeginn und -ende
- Automatische Verlaengerung? Unter welchen Bedingungen?

#### B. Kernleistungen & Pflichten
- Was muss jede Partei leisten?
- Sind die Leistungen konkret und messbar definiert?
- Gibt es Leistungsaenderungsklauseln?

#### C. Verguetung & Kosten
- Gesamtkosten (einmalig + laufend)
- Zahlungsbedingungen und Faelligkeiten
- Preisanpassungsklauseln (Inflation, Index?)
- Versteckte Kosten (Setup, Kuendigung, Extras)

#### D. Kuendigung & Ausstieg
- Ordentliche Kuendigungsfrist
- Ausserordentliche Kuendigung — welche Gruende?
- Folgen der Kuendigung (Rueckgabe, Abfindung, Daten)
- Mindestvertragslaufzeit / Lock-in

#### E. Haftung & Risiken
- Haftungsbeschraenkungen — sind sie angemessen?
- Vertragsstrafen — Hoehe und Ausloeser
- Gewaehrleistung und Gewaehrleistungsausschluss
- Force Majeure Klausel vorhanden?
- Versicherungspflichten

#### F. Datenschutz & Vertraulichkeit
- DSGVO-Konformitaet (bei personenbezogenen Daten)
- Vertraulichkeitsklauseln — Umfang und Dauer
- Auftragsverarbeitungsvertrag (AVV) noetig?
- Datenweitergabe an Dritte?

#### G. Problematische Klauseln
Explizit auf diese Red Flags pruefen:
- Einseitige Aenderungsvorbehalte ("kann jederzeit aendern")
- Salvatorische Klauseln die zu weit gehen
- Automatische Verlaengerung mit langer Kuendigungsfrist
- Wettbewerbsverbote ohne Karenzentschaedigung
- Gerichtsstandsvereinbarungen im Ausland
- Schiedsklauseln die ordentlichen Rechtsweg ausschliessen
- Abtretungsverbote oder -genehmigungen

### 4. Risiko-Bewertung
Gesamtrisiko einschaetzen:
- **NIEDRIG** — Standardvertrag, faire Bedingungen
- **MITTEL** — Einzelne problematische Klauseln, verhandelbar
- **HOCH** — Mehrere Red Flags, anwaltliche Pruefung empfohlen
- **KRITISCH** — Erhebliche Risiken, von Unterschrift abraten

### 5. Ergebnis formatieren
```
## Vertragspruefung: {Dokumentname}

> DISCLAIMER: Diese Analyse ersetzt keine rechtliche Beratung.

### Vertragstyp: {Typ}
Parteien: {A} und {B} | Laufzeit: {X} | Kuendigung: {Frist}

### Zusammenfassung (3 Saetze)
{Kerninhalt}

### Risiko-Bewertung: {NIEDRIG/MITTEL/HOCH/KRITISCH}

### Red Flags
- [Klausel X, Seite Y]: {Problem} — Empfehlung: {Was tun}

### Wichtige Fristen
| Was | Frist | Hinweis |
|-----|-------|---------|
| Kuendigung | ... | ... |

### Empfehlung
{Konkrete Handlungsempfehlung: unterschreiben / verhandeln / ablehnen}
```

### 6. Im Vault speichern
Mit `vault_save` archivieren:
- Ordner: `vertraege`
- Tags: Vertragstyp, Parteien, Risiko-Level

### 7. Optional: Vergleich mit frueherem Vertrag
Wenn im Memory ein aehnlicher Vertrag gespeichert ist, Unterschiede herausarbeiten.

## Bekannte Fallstricke
- IMMER Disclaimer anzeigen — keine Rechtsberatung
- Nicht spekulieren ueber rechtliche Konsequenzen — nur Klauseln identifizieren
- Bei fremdsprachigen Vertraegen: Sprache erkennen, ggf. uebersetzen, aber auf
  moegliche Uebersetzungsfehler hinweisen
- Gescannte PDFs: OCR-Qualitaet kann schlecht sein, User warnen

## Qualitaetskriterien
- Disclaimer am Anfang
- Alle 7 Dimensionen abgedeckt
- Konkrete Seitenzahl/Klausel-Referenzen bei Findings
- Klare Risiko-Bewertung mit Begruendung
- Handlungsempfehlung (unterschreiben/verhandeln/ablehnen)
