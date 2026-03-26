---
name: marketplace-monitor
description: Überwacht Online-Marktplätze auf Angebote für bestimmte Produkte. Analysiert Preise, erkennt Fakes, und benachrichtigt bei guten Deals.
category: productivity
trigger_keywords:
  - marketplace
  - marktplatz
  - deal
  - angebot
  - preis überwachen
  - price monitor
  - günstig
  - cheap
tools_required:
  - web_search
  - search_and_read
  - deep_research
  - set_reminder
  - save_to_memory
priority: 5
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
---

# Marketplace Monitor

## Aufgabe
Überwache Online-Marktplätze für ein bestimmtes Produkt und berichte über Preise, Verfügbarkeit und verdächtige Angebote.

## Ablauf

### 1. Produkt und Marktplätze identifizieren
- Frage den User nach dem Produkt (z.B. "RTX 5090", "iPhone 16 Pro")
- Identifiziere relevante Marktplätze: eBay, Facebook Marketplace, Kleinanzeigen, Amazon
- Bestimme den aktuellen Marktpreis via web_search

### 2. Recherche durchführen
- Suche auf jedem Marktplatz mit search_and_read
- Sammle: Preis, Zustand, Verkäufer, Standort, Beschreibung
- Nutze deep_research für Preisvergleich und Marktanalyse

### 3. Fake-Erkennung
- Warnsignale: Preis >30% unter Marktpreis, neuer Verkäufer, keine Bewertungen
- Warnsignale: Stockfotos statt echte Bilder, unklare Beschreibung
- Warnsignale: "Nur Überweisung", keine Rückgabe, Druck auf schnellen Kauf

### 4. Bericht erstellen
Formatiere als übersichtliche Tabelle:
| Plattform | Preis | Zustand | Verkäufer | Bewertung | Risiko |
|-----------|-------|---------|-----------|-----------|--------|

### 5. Wiederkehrend einrichten
- Richte set_reminder ein für tägliche/wöchentliche Überprüfung
- Speichere bisherige Preise in save_to_memory für Preisverlauf

## Bekannte Fallstricke
- Marketplace-Seiten blockieren oft Scraping — verwende search_and_read mit verschiedenen Suchbegriffen
- Preise schwanken stark je nach Tageszeit und Wochentag
- Nicht alle Angebote sind öffentlich sichtbar (Facebook Login-Wall)
- Währungsunterschiede bei internationalen Angeboten beachten

## Qualitätskriterien
- Mindestens 3 Marktplätze durchsucht
- Marktpreis als Referenz ermittelt
- Jedes Angebot mit Risikobewertung versehen
- Ergebnisse als strukturierte Tabelle formatiert

## Beispiel-Aufruf
"Überwache Facebook Marketplace nach günstigen RTX 5090 Grafikkarten"
"Monitor eBay for cheap iPhone 16 Pro deals"
"Finde die besten Angebote für eine PS5 Pro auf Kleinanzeigen"
