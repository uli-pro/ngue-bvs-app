# Geschenk-Empfänger-Daten - Formular-Texte

## Überschrift:
**"Empfänger-Informationen"**

## Formularfelder:

### Name:
**Label:** Name des Empfängers *
**Placeholder:** Vor- und Nachname
**Hilfetext:** Wie soll der Name auf dem Zertifikat erscheinen?

### E-Mail:
**Label:** E-Mail-Adresse des Empfängers *
**Placeholder:** empfaenger@beispiel.de
**Hilfetext:** An diese Adresse wird das Zertifikat gesendet (wenn gewünscht)

### Versand-Option:
(siehe geschenk-versand-option.md - bereits erstellt)

### Persönliche Nachricht:
**Label:** Persönliche Nachricht (optional)
**Placeholder:** Ihre Nachricht an den Empfänger...
**Hilfetext:** Max. 500 Zeichen
**Textarea:** 4 Zeilen

## Beispiel-Nachrichten (als Inspiration):
**Beispiele:**
- "Zu deinem Geburtstag wünsche ich dir Gottes Segen!"
- "Dieser Vers soll dich auf deinem Lebensweg begleiten."
- "Mit diesem besonderen Geschenk möchte ich dir eine Freude machen."

## Fehlermeldungen:
- **Name fehlt:** "Bitte geben Sie den Namen des Empfängers ein."
- **E-Mail ungültig:** "Bitte geben Sie eine gültige E-Mail-Adresse ein."
- **Nachricht zu lang:** "Die Nachricht darf maximal 500 Zeichen lang sein."

## Technische Hinweise:
- Felder nur anzeigen wenn "Als Geschenk" gewählt
- E-Mail-Validierung
- Zeichenzähler für persönliche Nachricht