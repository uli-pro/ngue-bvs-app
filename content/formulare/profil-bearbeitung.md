# Profil-Bearbeitung - Formular-Texte

## Überschrift:
**"Mein Profil"**

## Tabs/Bereiche:
- Persönliche Daten
- Adresse
- Einstellungen
- Passwort ändern

## Tab: Persönliche Daten

### Felder:
**Label:** Vorname *
**Wert:** {CURRENT_VORNAME}

**Label:** Nachname *
**Wert:** {CURRENT_NACHNAME}

**Label:** E-Mail-Adresse *
**Wert:** {CURRENT_EMAIL}
**Hinweis:** Bei Änderung ist eine erneute Bestätigung erforderlich

### Button:
**"Änderungen speichern"**

## Tab: Adresse

### Erklärung:
Diese Adresse wird für Spendenbescheinigungen verwendet

### Felder:
**Label:** Anrede
**Wert:** {CURRENT_ANREDE}

**Label:** Straße
**Wert:** {CURRENT_STRASSE}

**Label:** Hausnummer
**Wert:** {CURRENT_HAUSNR}

**Label:** PLZ
**Wert:** {CURRENT_PLZ}

**Label:** Ort
**Wert:** {CURRENT_ORT}

### Button:
**"Adresse speichern"**

## Tab: Einstellungen

### Newsletter:
☐ **Newsletter der Peter-Schöffer-Stiftung erhalten**
*Neuigkeiten zum NGÜ-Projekt, ca. 4x jährlich*

### Benachrichtigungen:
☐ **E-Mail-Benachrichtigungen bei neuen Features**
☐ **Jährliche Spenden-Zusammenfassung erhalten**

### Button:
**"Einstellungen speichern"**

## Tab: Passwort ändern

### Felder:
**Label:** Aktuelles Passwort *
**Type:** password

**Label:** Neues Passwort *
**Type:** password
**Hilfetext:** Mind. 8 Zeichen, inkl. Groß-/Kleinbuchstaben und Zahl

**Label:** Neues Passwort bestätigen *
**Type:** password

### Button:
**"Passwort ändern"**

## Erfolgsmeldungen:
- "Ihre Änderungen wurden gespeichert."
- "Ihre Adresse wurde aktualisiert."
- "Ihre Einstellungen wurden gespeichert."
- "Ihr Passwort wurde erfolgreich geändert."

## Fehlermeldungen:
- **Pflichtfeld leer:** "Dieses Feld ist erforderlich."
- **E-Mail bereits verwendet:** "Diese E-Mail-Adresse wird bereits von einem anderen Konto verwendet."
- **Altes Passwort falsch:** "Das aktuelle Passwort ist nicht korrekt."
- **Neues Passwort zu schwach:** "Das Passwort erfüllt nicht die Sicherheitsanforderungen."

## Konto-Aktionen (am Ende der Seite):
**Link:** "Konto löschen" (mit Bestätigungsdialog)

## Technische Hinweise:
- AJAX-Speicherung pro Tab
- E-Mail-Änderung erfordert Verifizierung
- Erfolgs-/Fehlermeldungen als Toast