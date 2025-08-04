# User Journey: 

## Liste aller benötigten Seiten/Routes:

### Hauptflow:

1. **`/`** - Index-Seite (Homepage)
2. **`/verse-auswahl`** - Vers-Auswahl mit Top 3
3. **`/verse-suche/referenz`** - Suche nach Bibelstelle
4. **`/verse-suche/keyword`** - Suche nach Thema/Stichwort
5. **`/verse/{verse_id}/bestaetigung`** - Vers-Bestätigung
6. **`/checkout/daten`** - Datenerfassung
7. **`/checkout/zusammenfassung`** - Zahlungszusammenfassung
8. **`/checkout/stripe`** - Stripe-Weiterleitung
9. **`/checkout/erfolg`** - Danke-Seite
10. **`/checkout/fehler`** - Fehlermeldung bei Zahlungsproblemen

### User-Account:

1. **`/login`** - Login-Seite
2. **`/register`** - Registrierung
3. **`/dashboard`** - User-Dashboard
4. **`/dashboard/verse`** - Meine gesponserten Verse
5. **`/dashboard/downloads`** - Dokumente herunterladen
6. **`/dashboard/profil`** - Profil bearbeiten
7. **`/logout`** - Logout

### Informationsseiten:

1. **`/ueber-ngue`** - Über die NGÜ
2. **`/ueber-stiftung`** - Über die Peter-Schöffer-Stiftung
3. **`/transparenz`** - Wohin fließt meine Spende?
4. **`/faq`** - FAQ/Hilfe

### Rechtliches:

1. **`/impressum`** - Impressum
2. **`/datenschutz`** - Datenschutzerklärung

### API-Endpoints (für AJAX):

1. **`/api/verse/search`** - Vers-Suche API
2. **`/api/verse/similar/{verse_id}`** - Ähnliche Verse finden
3. **`/api/verse/reserve/{verse_id}`** - Vers temporär reservieren
4. **`/api/verse/release/{verse_id}`** - Reservierung aufheben

### Weitere:

1. **`/404`** - Seite nicht gefunden
2. **`/500`** - Serverfehler
3. **`/timeout`** - Session-Timeout
   

## Tabelle mit Entscheidungspunkten:

| Entscheidungspunkt           | Seite/Ort            | Optionen                                                     | Konsequenzen                                              |
| ---------------------------- | -------------------- | ------------------------------------------------------------ | --------------------------------------------------------- |
| **Vers-Auswahl-Methode**     | Vers-Auswahl-Seite   | 1. Top 3 wählen<br/>2. Nach Referenz suchen<br/>3. Nach Keyword suchen | Verschiedene Such-Interfaces                              |
| **Vers verfügbar?**          | Referenz-Suche       | 1. Ja<br/>2. Nein                                            | Ja: Vers anzeigen<br/>Nein: 3 Alternativen                |
| **Als Geschenk?**            | Vers-Bestätigung     | 1. Für mich<br/>2. Als Geschenk                              | Geschenk: Zusätzliche Empfängerdaten                      |
| **Spendenbescheinigung?**    | Datenerfassung       | 1. Ja (Default)<br/>2. Nein                                  | Ja: Vollständige Adressdaten<br/>Nein: Nur E-Mail         |
| **Newsletter?**              | Datenerfassung       | 1. Ja<br/>2. Nein                                            | Newsletter-Anmeldung                                      |
| **Datenschutz akzeptieren?** | Datenerfassung       | 1. Ja<br/>2. Nein                                            | Nein: Kann nicht fortfahren                               |
| **Zahlung erfolgreich?**     | Stripe-Return        | 1. Erfolg<br/>2. Fehler<br/>3. Abbruch                       | Erfolg: Danke-Seite<br/>Fehler/Abbruch: Fehlerbehandlung  |
| **Registrierung?**           | Danke-Seite          | 1. Jetzt registrieren<br/>2. Später/Nie                      | Registrierung: Account-Vorteile<br/>Nein: Session beenden |
| **Eingeloggt?**              | Verschiedene Seiten  | 1. Ja<br/>2. Nein                                            | Ja: Personalisierte Inhalte<br/>Nein: Gast-Modus          |
| **Cookie-Einwilligung?**     | Alle Seiten (Banner) | 1. Akzeptieren<br/>2. Ablehnen<br/>3. Anpassen               | Bestimmt Tracking-Verhalten                               |
| **Weitere Verse ansehen?**   | Keyword-Suche        | 1. Weitere laden<br/>2. Vers wählen                          | Lädt 3 zusätzliche Verse                                  |
| **Session-Timeout?**         | Checkout-Prozess     | 1. Fortfahren<br/>2. Neu starten                             | Nach 15 Min: Vers-Reservierung aufheben                   |

