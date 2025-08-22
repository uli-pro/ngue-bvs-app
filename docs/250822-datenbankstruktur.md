Hier ist eine vollständige Übersicht aller Tabellen in Ihrer NGÜ
   Bibelvers-Sponsoring App Datenbank:

  📊 Datenbank-Tabellenstruktur

  🟦 Haupt-Entitäten

  1. verses - Bibelverse (11.000+ Verse)
  - id (PK), book, chapter, verse, text
  - text_search (tsvector für Volltext), text_embedding (vector
    für KI-Suche)
  - positivity_score, is_sponsored, is_translated, created_at

  2. users - Benutzerkonten
  - id (PK), email (unique), password_hash
  - Name: first_name, last_name, salutation, title
  - Adresse: street, house_number, postal_code, city, country
  - Flags: is_verified, newsletter_opt_in, created_at

  3. donations - Spenden (zentrale Tabelle)
  - id (PK), verse_id (FK), user_id (FK, nullable)
  - donation_type, amount, currency
  - Spender-Daten: donor_email, donor_salutation,
    donor_first_name, donor_last_name, donor_street,
    donor_house_number, donor_postal_code, donor_city,
    donor_country, donor_title
  - Typ-spezifisch: group_name, group_article,
    gift_recipient_name, gift_recipient_email, gift_message,
    gift_direct_send
  - Status: payment_status, certificate_generated,
    receipt_generated, wants_receipt, newsletter_opt_in,
    privacy_consent
  - Timestamps: created_at, completed_at

  🟨 Payment & Transaktionen

  4. payment_transactions - Stripe-Zahlungen
  - id (PK), donation_id (FK), provider, provider_transaction_id
  - Stripe-Felder: stripe_payment_intent_id, stripe_client_secret,
      stripe_status, stripe_payment_method_id,
    stripe_payment_method_type, stripe_setup_future_usage,
    stripe_customer_id, stripe_receipt_url, stripe_receipt_number
  - Fees: provider_fee_amount, net_amount
  - Refunds: refund_status, refund_amount, refunded_at,
    stripe_refund_id
  - Errors: last_error, stripe_last_error, retry_count
  - Metadata: provider_metadata, stripe_metadata,
    statement_descriptor
  - Timestamps: created_at, confirmed_at, failed_at

  5. certificates - Generierte Zertifikate
  - id (PK), donation_id (FK), certificate_type
  - filename, file_path, generated_at, sent_at

  🟩 Session & Temporäre Daten

  6. sessions - Flask-Sessions
  - id (PK), session_id (unique), data (bytea), expiry

  7. donation_cart - Temporärer Warenkorb
  - id (PK), session_id, verse_id (FK), donation_type
  - temp_data (jsonb), created_at, expires_at

  8. verse_reservations - Vers-Reservierungen
  - id (PK), verse_id (FK), session_id
  - reserved_at, expires_at (15 min Standard)

  🟪 Authentifizierung & Tokens

  9. verification_tokens - E-Mail-Verifizierung
  - id (PK), user_id (FK), token (unique)
  - created_at, expires_at (24h), used

  10. reset_tokens - Passwort-Reset
  - id (PK), user_id (FK), token (unique)
  - created_at, expires_at (1h), used

---
  ★ Insight ─────────────────────────────────────
  Die Datenbankarchitektur zeigt eine durchdachte
  PostgreSQL-Implementierung mit modernen Features: pgvector für
  KI-gestützte semantische Suche, tsvector für deutsche
  Volltext-Suche, und JSONB für flexible Metadaten. Die
  Reservierungs-Mechanismen mit verse_reservations verhindern Race
   Conditions beim gleichzeitigen Sponsoring.
  ─────────────────────────────────────────────────

  Beziehungen zwischen Tabellen:

  - verses ← donations, donation_cart, verse_reservations
  - users ← donations, verification_tokens, reset_tokens
  - donations ← certificates, payment_transactions

  Die Datenbank enthält aktuell 10 Tabellen mit umfassender
  Indizierung für Performance und Integrität.