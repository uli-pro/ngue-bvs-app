# NGÜ Bibelvers-Sponsoring Demo

Dies ist die **Demo-Version** der NGÜ Bibelvers-Sponsoring App, die für User-Feedback und Testing verwendet wird.

## Status
- ✅ Funktionale Demo mit statischen Daten
- ✅ Läuft auf Homeserver für User-Testing
- ✅ UI/UX-Design vollständig implementiert
- ⚠️ **NICHT für echte Spenden verwenden!**

## Demo-Features
- 17 HTML-Templates mit NGÜ-Design
- Bootstrap 5.3 responsive Design
- Interaktive Vers-Auswahl
- Checkout-Flow (ohne echte Zahlung)
- Account-System (Demo-Login)

## Starten
```bash
cd demo/
python app.py
```

## Unterschiede zur echten App
- **Keine Database**: Verwendet statische Demo-Daten
- **Keine Payments**: Stripe-Integration deaktiviert
- **Keine E-Mails**: PDF-Generation nur simuliert
- **Demo-Login**: admin@ngue.de / demo123

## Zweck
Diese Demo sammelt User-Feedback für:
- UI/UX-Design
- User-Journey-Flow
- Content und Texte
- Mobile Responsiveness

**Echte Entwicklung läuft in `/src/` Verzeichnis!**