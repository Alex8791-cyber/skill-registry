---
name: workflow-recorder
trigger_keywords: [Workflow, Automatisierung, automatisieren, Ablauf aufnehmen, Prozess erstellen, immer wenn, jedes Mal wenn, wiederholbar, Routine, Vorlage erstellen, Skill erstellen, neuer Skill]
tools_required: [write_file, create_skill, search_memory, save_to_memory, list_skills, read_file]
category: automation
priority: 7
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
---
# Workflow-Recorder — "Zeig mir einmal, dann mach ich's immer"

## Wann anwenden
Wenn der Benutzer einen wiederholbaren Prozess beschreibt oder einen Ablauf automatisieren
moechte. Der Skill zeichnet die Schritte auf und erstellt daraus einen neuen Cognithor-Skill.
Typische Trigger: "Automatisiere das", "Mach daraus einen Workflow",
"Jedes Mal wenn X, dann Y", "Erstelle einen Skill der das macht",
"Das mache ich immer so: ...", "Kannst du dir das merken und wiederholen?".

## Voraussetzungen
- Beschreibung des Ablaufs (muendlich oder als Liste)
- Optional: Trigger-Woerter wann der Workflow starten soll

## Ablauf

### 1. Ablauf verstehen
Den Benutzer nach dem Prozess fragen. Drei Methoden:

**Methode A — Beschreibung**: User beschreibt den Ablauf in eigenen Worten.
Rueckfragen stellen bis alle Schritte klar sind:
- "Was ist der erste Schritt?"
- "Welche Tools brauchst du dafuer?"
- "Wann ist der Ablauf fertig?"
- "Gibt es Bedingungen oder Verzweigungen?"

**Methode B — Beispiel**: User fuehrt den Ablauf einmal mit Cognithor durch.
Die genutzten Tools und Parameter aus den letzten Episodes extrahieren
mit `search_memory`.

**Methode C — Vorlage**: User gibt eine Schritt-fuer-Schritt-Liste.
Direkt in Skill-Format konvertieren.

### 2. Schritte formalisieren
Fuer jeden Schritt festlegen:
- **Aktion**: Was wird getan? (Tool-Name + Parameter)
- **Eingabe**: Was wird benoetigt? (User-Input, vorheriges Ergebnis, Datei)
- **Ausgabe**: Was kommt raus? (Datei, Text, Benachrichtigung)
- **Bedingung**: Wann wird der Schritt ausgefuehrt? (Immer, nur wenn X)

### 3. Tool-Mapping
Jeden Schritt einem MCP-Tool zuordnen:
- "E-Mail lesen" → `email_read`
- "Datei erstellen" → `write_file`
- "Im Web suchen" → `web_search` / `search_and_read`
- "Erinnerung setzen" → `set_reminder`
- "In Vault speichern" → `vault_save`
- "Shell-Befehl" → `exec_command`
- "Code ausfuehren" → `run_python`

Wenn kein passendes Tool existiert, dem User mitteilen und Alternative vorschlagen.

### 4. Trigger-Keywords definieren
Den User fragen: "Mit welchen Worten wuerdest du diesen Ablauf ausloesen?"
Mindestens 5 Keywords sammeln — deutsch und ggf. englisch.

### 5. Skill-Datei generieren
Mit `create_skill` oder `write_file` eine neue Skill-MD-Datei erstellen.

Vorlage:
```markdown
---
name: {slug}
trigger_keywords: [{keyword1}, {keyword2}, ...]
tools_required: [{tool1}, {tool2}, ...]
category: automation
priority: 5
---
# {Skill-Titel}

## Wann anwenden
{Beschreibung wann der Skill aktiviert wird}

## Ablauf
1. **{Schritt 1}** — Tool: `{tool_name}`
   {Was genau gemacht wird}

2. **{Schritt 2}** — Tool: `{tool_name}`
   {Was genau gemacht wird}

## Qualitaetskriterien
- {Woran erkennt man dass der Skill erfolgreich war}
```

### 6. Skill testen
Den User fragen: "Soll ich den Workflow jetzt einmal ausfuehren um zu pruefen
ob alles funktioniert?"

Bei Ja: Den neuen Skill einmal durchlaufen und Ergebnis pruefen.
Bei Fehlern: Skill-Datei korrigieren und erneut testen.

### 7. Bestaetigung
Dem User mitteilen:
- Name und Trigger-Keywords des neuen Skills
- Wie er aktiviert wird
- Dass er jederzeit mit "Bearbeite Skill {name}" geaendert werden kann
- Dass er mit "Deaktiviere Skill {name}" ausgeschaltet werden kann

## Bekannte Fallstricke
- Zu komplexe Workflows: Maximal 7 Schritte. Bei mehr in Sub-Skills aufteilen.
- Vage Beschreibungen: Immer nach konkreten Beispielen fragen.
  "Mach das automatisch" ist nicht genug — "Was genau soll automatisch passieren?"
- Fehlende Tools: Ehrlich sagen wenn ein Schritt nicht automatisierbar ist.
- Trigger-Kollision: Pruefen ob die Keywords mit bestehenden Skills kollidieren
  mit `list_skills`.
- Sicherheit: Keine Skills erstellen die destruktive Operationen ohne Bestaetigung
  ausfuehren (rm, delete, send).

## Qualitaetskriterien
- Neuer Skill erfolgreich erstellt und in der Registry
- Mindestens 5 aussagekraeftige Trigger-Keywords
- Jeder Schritt mit konkretem Tool-Mapping
- Skill einmal erfolgreich getestet
- User weiss wie er den Skill aendern/deaktivieren kann
