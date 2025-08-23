# Test-Karten und IBANS für Stripe Zahlungen im Test-Modus.

Die Test-Daten wurden im Test-Script ausgegeben! Hier sind sie
   nochmal übersichtlich:

  🏦 SEPA Test-IBANs

  Für SEPA-Lastschrift Testing verwenden Sie diese IBANs:

  ✅ Erfolgreiche Zahlungen:
  DE89370400440532013000  (Deutschland)
  AT483200000012345864    (Österreich)
  NL02ABNA0123456789      (Niederlande)
  FR1420041010050500013M02606  (Frankreich)

  ❌ Fehlgeschlagene Zahlung:
  DE62370400440532013001  (Deutschland - Decline)

  💳 3D Secure Test-Karten

  Für Kartenzahlungen mit 3D Secure:

  ✅ Erfolgreiche Zahlungen:
  4000 0027 6000 3184  (3DS2 Authentication Required)
  4000 0025 0000 3155  (3DS2 Frictionless)
  4242 4242 4242 4242  (Standard Success, 3DS Optional)

  ❌ Fehlgeschlagene Zahlungen:
  4000 0000 0000 0002  (Generic Decline)
  4000 0000 0000 9995  (Insufficient Funds)
  4000 0000 0000 0069  (Expired Card)

  📋 Zusätzliche Karten-Details:

  Für alle Test-Karten können Sie verwenden:
  - CVC: Beliebige 3-stellige Zahl (z.B. 123)
  - Ablaufdatum: Beliebiges zukünftiges Datum (z.B. 12/25)
  - Name: Beliebiger Name

  🔧 Wo Sie diese verwenden:

  1. Starten Sie die App: python app.py
  2. Navigieren Sie zu: http://localhost:5000/vers-auswaehlen
  3. Fügen Sie Verse zum Warenkorb hinzu
  4. Auf der Payment-Seite: Geben Sie die Test-IBANs oder
    Kartennummern ein

  Die Test-Daten funktionieren nur in Stripes Test-Environment
  (mit pk_test_ und sk_test_ Keys)!





