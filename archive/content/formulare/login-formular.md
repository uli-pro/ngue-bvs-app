# Login-Formular - Formular-Texte

## Überschrift:
**"Anmelden"**

## Unterüberschrift:
Melden Sie sich an, um Ihre gesponserten Verse zu verwalten

## Formularfelder:

### E-Mail:
**Label:** E-Mail-Adresse
**Placeholder:** ihre.email@beispiel.de
**Type:** email

### Passwort:
**Label:** Passwort
**Placeholder:** ••••••••
**Type:** password

### Angemeldet bleiben:
☐ **Angemeldet bleiben**
(Standard: nicht aktiviert)

## Buttons:
**Primär:** "Anmelden"
**Link:** "Passwort vergessen?"

## Alternativen:
**Noch kein Konto?** [Jetzt registrieren]

**Oder:** Als Gast fortfahren (keine Anmeldung erforderlich)

## Fehlermeldungen:
- **E-Mail/Passwort falsch:** "Die E-Mail-Adresse oder das Passwort ist falsch."
- **E-Mail nicht bestätigt:** "Bitte bestätigen Sie zuerst Ihre E-Mail-Adresse. [Bestätigungs-E-Mail erneut senden]"
- **Konto gesperrt:** "Ihr Konto wurde nach mehreren fehlgeschlagenen Anmeldeversuchen gesperrt. Bitte setzen Sie Ihr Passwort zurück."
- **Felder leer:** "Bitte geben Sie E-Mail und Passwort ein."

## Erfolgsmeldung:
"Willkommen zurück! Sie wurden erfolgreich angemeldet."

## Technische Hinweise:
- Rate-Limiting nach 5 Fehlversuchen
- Session-Cookie setzen
- HTTPS erforderlich