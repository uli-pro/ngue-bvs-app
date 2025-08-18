# ENTWICKLUNGSAUFTRAG: Test-Driven Development (TDD)

## TESTORGANISATION:

- Erstelle Tests in: `/tests/[beschreibender_ordnername]/`
- Verwende aussagekräftige Verzeichnisnamen

## KRITISCHE DATENBANKREGELN:

⚠️ **NIEMALS die Datenbank löschen oder leeren**
 ⚠️ **NIEMALS Produktionsdaten manipulieren oder entfernen**
 ⚠️ **Bestehende Daten MÜSSEN unverändert bleiben**
 ✅ Verwende nur READ-Operationen auf bestehende Daten
 ✅ Neue Testdaten mit eindeutigen IDs/Namen erstellen

## TESTABDECKUNG (verpflichtend):

- **Core-Cases**: Normale Funktionalität
- **Edge-Cases**: Grenzwerte, leere Inputs, ungültige Daten usw.
- **Security**: Authentifizierung, Autorisierung, Input-Validation, usw.

## FEATURE-ANFORDERUNG: