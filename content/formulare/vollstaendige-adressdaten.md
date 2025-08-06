# Vollständige Adressdaten - Formular-Texte

## Überschrift:
**"Adressdaten für Spendenbescheinigung"**

## Erklärungstext:
Diese Angaben benötigen wir für Ihre steuerlich absetzbare Spendenbescheinigung

## Formularfelder:

### Anrede:
**Label:** Anrede *
**Optionen:** 
- Herr
- Frau
- Eheleute
- Firma

### Name:
**Label:** Vorname *
**Placeholder:** Max

**Label:** Nachname *
**Placeholder:** Mustermann

### Adresse:
**Label:** Straße *
**Placeholder:** Musterstraße

**Label:** Hausnummer *
**Placeholder:** 123

### Ort:
**Label:** PLZ *
**Placeholder:** 12345
**Validierung:** 5-stellige deutsche PLZ

**Label:** Ort *
**Placeholder:** Musterstadt

### Firmendaten (nur bei Anrede "Firma"):
**Label:** Firmenname *
**Placeholder:** Musterfirma GmbH

## Hinweis:
⚠️ **Wichtig:** Die Angaben müssen mit Ihren Steuerdaten übereinstimmen.

## Fehlermeldungen:
- **Pflichtfeld leer:** "Dieses Feld ist erforderlich."
- **PLZ ungültig:** "Bitte geben Sie eine gültige 5-stellige Postleitzahl ein."
- **Name zu kurz:** "Der Name muss mindestens 2 Zeichen lang sein."

## Technische Hinweise:
- Felder nur anzeigen wenn Spendenbescheinigung gewünscht
- PLZ-Validierung (5 Ziffern)
- Bei Anrede "Firma" zusätzliches Feld einblenden