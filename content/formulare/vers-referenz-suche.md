# Vers-Referenz-Suche - Formular-Texte

## Überschrift:
**"Nach Bibelstelle suchen"**

## Erklärungstext:
Geben Sie die gewünschte Bibelstelle ein (z.B. "Psalm 23,1" oder "Jeremia 29,11")

## Formularfelder:

### Eingabefeld:
**Label:** Bibelstelle
**Placeholder:** z.B. Psalm 23,1
**Hilfetext:** Format: Buch Kapitel,Vers

## Button:
**"Vers suchen"**

## Beispiele unter dem Formular:
**Beispiele:**
- Genesis 1,1
- Psalm 139,14
- Jesaja 40,31
- Sprüche 3,5-6

## Fehlermeldungen:
- **Format ungültig:** "Bitte verwenden Sie das Format: Buch Kapitel,Vers"
- **Buch nicht gefunden:** "Das Buch '{BUCH}' wurde nicht gefunden. Bitte prüfen Sie die Schreibweise."
- **Vers nicht vorhanden:** "Der Vers {REFERENZ} existiert nicht. Bitte prüfen Sie Kapitel und Vers."
- **Bereits gesponsert:** "Dieser Vers wurde bereits gesponsert. Hier sind ähnliche Alternativen:"

## Technische Hinweise:
- Autocomplete für Buchnamen
- Flexible Eingabe erlauben (mit/ohne Leerzeichen, verschiedene Abkürzungen)
- Validierung gegen bekannte Bibelstellen-Liste