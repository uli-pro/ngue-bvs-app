# Database Refactoring: Payment Transactions

**Datum:** 15. August 2025  
**Status:** Implementiert  

## Überblick

Die Donations-Tabelle wurde refactored, um Payment-Provider-spezifische Felder in eine separate `PaymentTransaction`-Tabelle auszulagern. Dies verbessert die Trennung von Business-Logic und Payment-Processing.

## Motivation

### Problem
- Donations-Tabelle hatte 62 Felder (davon 24 Stripe-spezifisch)
- Vermischung von Business-Logic und Payment-Provider-Details
- Unübersichtliche Tabellenstruktur
- Schwieriger Wechsel zu anderen Payment-Providern

### Lösung
- Auslagerung aller Payment-Provider-Felder in separate Tabelle
- Klare Trennung der Verantwortlichkeiten
- Provider-agnostische Architektur
- Rückwärtskompatibilität durch Property-Delegation

## Neue Tabellenstruktur

### Donations-Tabelle (vereinfacht auf ~38 Felder)

**Behaltene Felder:**
- Kern-Daten: `verse_id`, `user_id`, `donation_type`, `amount`, `currency`
- Donor-Informationen: Name, Adresse, Email
- Type-spezifische Felder: `group_name`, `gift_recipient`
- Preferences: `wants_receipt`, `newsletter_opt_in`, `privacy_consent`
- Status: `payment_status`, `certificate_generated`, `receipt_generated`
- Timestamps: `created_at`, `completed_at`

**Entfernte Felder (verschoben zu PaymentTransaction):**
- Alle `stripe_*` Felder (24 Felder)
- Payment-spezifische Timestamps
- Refund-Management-Felder
- Fee-Tracking-Felder

### PaymentTransaction-Tabelle (neu, ~28 Felder)

```python
class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    
    # Core
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'))
    
    # Provider info (future-proofing)
    provider = db.Column(db.String(20), default='stripe')
    provider_transaction_id = db.Column(db.String(100))
    
    # Stripe-specific fields
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_client_secret = db.Column(db.String(200))
    stripe_status = db.Column(db.String(20))
    stripe_payment_method_id = db.Column(db.String(100))
    stripe_payment_method_type = db.Column(db.String(20))
    stripe_setup_future_usage = db.Column(db.String(20))
    stripe_customer_id = db.Column(db.String(100))
    stripe_receipt_url = db.Column(db.String(500))
    stripe_receipt_number = db.Column(db.String(100))
    
    # Provider-agnostic fields
    provider_fee_amount = db.Column(db.Numeric(6, 2))
    net_amount = db.Column(db.Numeric(6, 2))
    
    # Refund management
    refund_status = db.Column(db.String(20), default='none')
    refund_amount = db.Column(db.Numeric(6, 2))
    refunded_at = db.Column(db.DateTime)
    stripe_refund_id = db.Column(db.String(100))
    
    # Error & retry
    last_error = db.Column(db.Text)
    stripe_last_error = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Metadata
    provider_metadata = db.Column(db.JSON)
    stripe_metadata = db.Column(db.JSON)
    statement_descriptor = db.Column(db.String(22))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
```

## Relationship

```python
# In Donation model
payment = db.relationship('PaymentTransaction', uselist=False, backref='donation', cascade='all, delete-orphan')

# In PaymentTransaction model  
# backref='donation' creates automatic donation attribute
```

## Rückwärtskompatibilität

Um schrittweise Migration zu ermöglichen, wurden Property-Delegationen implementiert:

```python
# In Donation model
@property
def stripe_payment_intent_id(self):
    """Backward compatibility property"""
    return self.payment.stripe_payment_intent_id if self.payment else None

@property  
def stripe_client_secret(self):
    """Backward compatibility property"""
    return self.payment.stripe_client_secret if self.payment else None

# ... weitere Properties für alle wichtigen Stripe-Felder
```

**Bedeutung:** Bestehender Code funktioniert weiterhin:
```python
# Alt (funktioniert weiterhin)
donation.stripe_payment_intent_id

# Neu (empfohlen für neuen Code)
donation.payment.stripe_payment_intent_id
```

## Neue Methoden

### PaymentTransaction-Methoden
```python
payment.mark_confirmed()           # Payment als bestätigt markieren
payment.mark_failed(error_msg)     # Payment als fehlgeschlagen markieren
payment.update_stripe_data(intent) # Stripe PaymentIntent Daten aktualisieren
payment.process_refund(amount, id) # Refund verarbeiten
```

### Donation-Delegations-Methoden
```python
donation.create_payment_transaction(provider)  # Neue PaymentTransaction erstellen
donation.update_stripe_data(payment_intent)    # Delegiert an payment.update_stripe_data()
donation.process_refund(amount, refund_id)     # Delegiert an payment.process_refund()
```

## Vorteile der neuen Struktur

### ✅ Sauberkeit
- Donations-Tabelle fokussiert auf Business-Logic
- PaymentTransaction-Tabelle fokussiert auf Payment-Processing
- Klare Trennung der Verantwortlichkeiten

### ✅ Flexibilität
- Einfache Erweiterung für andere Payment-Provider (PayPal, etc.)
- Provider-agnostische Felder (provider_fee_amount statt stripe_fee_amount)
- Future-proofing durch generische Felder

### ✅ Erweiterbarkeit
- Möglichkeit für 1:n Beziehung (multiple Payment-Attempts pro Donation)
- Bessere Payment-Historie und Debugging
- Separate Indexierung für Payment-Queries

### ✅ Migration
- Schrittweise Migration möglich durch Rückwärtskompatibilität
- Bestehender Code funktioniert weiterhin
- Neue Features können sofort neue Struktur nutzen

## Migration-Strategie

### Phase 1: Struktureller Übergang (abgeschlossen)
1. ✅ PaymentTransaction-Model erstellt
2. ✅ Donations-Model: Stripe-Felder entfernt, Relationship hinzugefügt
3. ✅ Rückwärtskompatibilitäts-Properties implementiert

### Phase 2: Code-Migration (zukünftig)
1. Neuen Code schreiben, der direkt `donation.payment.*` verwendet
2. Bestehenden Code schrittweise umstellen
3. Rückwärtskompatibilitäts-Properties als `@deprecated` markieren

### Phase 3: Cleanup (später)
1. Alle Code-Stellen auf neue Struktur umgestellt
2. Rückwärtskompatibilitäts-Properties entfernen
3. Migration abgeschlossen

## Code-Beispiele

### Neue Payment Transaction erstellen
```python
# Neue Donation mit Payment
donation = Donation(...)
db.session.add(donation)
db.session.commit()

# Payment Transaction erstellen
payment = donation.create_payment_transaction('stripe')

# Stripe PaymentIntent Daten aktualisieren
payment.update_stripe_data(stripe_payment_intent)
```

### Payment-Status prüfen
```python
# Alt (funktioniert weiterhin)
if donation.stripe_status == 'succeeded':
    # ...

# Neu (empfohlen)
if donation.payment and donation.payment.is_completed:
    # ...
```

### Refund verarbeiten
```python
# Alt (funktioniert weiterhin)
donation.process_refund(50.00, 'ref_abc123')

# Neu (direkt)
if donation.payment:
    donation.payment.process_refund(50.00, 'ref_abc123')
```

## Database Migration

Für bestehende Daten wird eine Migrations-Datei benötigt:

```python
# migrations/versions/xxx_add_payment_transactions.py
def upgrade():
    # 1. PaymentTransaction Tabelle erstellen
    op.create_table('payment_transactions', ...)
    
    # 2. Bestehende Stripe-Daten von donations zu payment_transactions migrieren
    # (Falls bereits Daten vorhanden sind)
    
    # 3. Stripe-Felder aus donations Tabelle entfernen
    # (Nach erfolgreicher Datenmigration)
```

## Testing

Alle bestehenden Tests sollten weiterhin funktionieren durch die Rückwärtskompatibilität. Neue Tests sollten die neue Struktur verwenden:

```python
def test_payment_transaction_creation():
    donation = create_test_donation()
    payment = donation.create_payment_transaction('stripe')
    
    assert payment.provider == 'stripe'
    assert payment.donation_id == donation.id
    assert donation.payment == payment

def test_backward_compatibility():
    donation = create_test_donation()
    payment = donation.create_payment_transaction('stripe')
    payment.stripe_payment_intent_id = 'pi_test123'
    
    # Rückwärtskompatibilität testen
    assert donation.stripe_payment_intent_id == 'pi_test123'
```

## Fazit

Das Refactoring verbessert die Codebase erheblich durch:
- Saubere Trennung der Concerns
- Future-proofing für andere Payment-Provider  
- Bessere Testbarkeit und Wartbarkeit
- Schrittweise Migration ohne Breaking Changes

Die neue Struktur ist flexibler, erweiterbarer und wartungsfreundlicher, während die Rückwärtskompatibilität eine risikofreie Migration ermöglicht.