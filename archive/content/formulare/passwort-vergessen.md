# Passwort-Vergessen - Formular-Texte

## Überschrift:
**"Passwort zurücksetzen"**

## Erklärungstext:
Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Link zum Zurücksetzen Ihres Passworts.

## Formularfeld:

### E-Mail:
**Label:** E-Mail-Adresse
**Placeholder:** ihre.email@beispiel.de
**Type:** email

## Button:
**"Link zum Zurücksetzen senden"**

## Zurück-Link:
[← Zurück zur Anmeldung]

## Erfolgsmeldung:
"Wir haben Ihnen eine E-Mail mit Anweisungen zum Zurücksetzen Ihres Passworts gesendet. Bitte prüfen Sie Ihr Postfach."

## Info-Box nach Versand:
ℹ️ **E-Mail nicht erhalten?**
- Prüfen Sie Ihren Spam-Ordner
- Stellen Sie sicher, dass Sie die richtige E-Mail-Adresse eingegeben haben
- [E-Mail erneut senden] (nach 60 Sekunden verfügbar)

## Fehlermeldungen:
- **E-Mail nicht gefunden:** "Diese E-Mail-Adresse ist nicht registriert. [Jetzt registrieren]"
- **E-Mail ungültig:** "Bitte geben Sie eine gültige E-Mail-Adresse ein."
- **Zu viele Versuche:** "Sie haben zu viele Anfragen gesendet. Bitte versuchen Sie es in 15 Minuten erneut."

## Passwort-Zurücksetzen-Formular (auf separater Seite nach Link-Klick):

### Überschrift:
**"Neues Passwort festlegen"**

### Felder:
**Label:** Neues Passwort *
**Placeholder:** Mindestens 8 Zeichen
**Type:** password

**Label:** Passwort bestätigen *
**Placeholder:** Passwort erneut eingeben
**Type:** password

### Button:
**"Passwort ändern"**

### Erfolgsmeldung:
"Ihr Passwort wurde erfolgreich geändert. Sie können sich jetzt mit Ihrem neuen Passwort anmelden."

## Technische Hinweise:
- Token mit 1 Stunde Gültigkeit
- Rate-Limiting: Max. 3 Anfragen pro Stunde
- Link nur einmal verwendbar