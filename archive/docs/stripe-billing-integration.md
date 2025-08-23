# Stripe-Billing-Details Integration

**Status:** TODO - Noch zu implementieren  
**Priorität:** Hoch  
**Datum:** 15. August 2025  
**Abhängigkeiten:** User-Model mit Adress-Feldern (✅), PaymentTransaction-Model (✅)

## Überblick

Automatische Übertragung aller User/Donation-Daten zu Stripe für nahtlose Payment-Experience. User soll bei Stripe-Checkout keine Daten mehr eingeben müssen.

## Anforderungen

### Payment Experience
- ✅ **Billing-Address**: Automatisch aus User/Donation-Daten
- ✅ **Customer-Info**: Name, Email automatisch gesetzt
- ✅ **Receipt-Email**: Automatisch konfiguriert
- ✅ **Metadata**: Donation-ID für Zuordnung
- ✅ **3D Secure**: Unterstützung für starke Authentifizierung

## Technische Spezifikation

### Stripe PaymentIntent mit Billing-Details

```python
def create_stripe_payment_intent(donation):
    """
    Erstelle Stripe PaymentIntent mit vollständigen Billing-Details
    
    Args:
        donation: Donation-Objekt mit allen User-Daten
        
    Returns:
        stripe.PaymentIntent: Konfigurierter PaymentIntent
    """
    
    # Billing-Details aus Donation zusammenbauen
    billing_details = {
        'name': f"{donation.donor_first_name} {donation.donor_last_name}".strip(),
        'email': donation.donor_email,
        'address': {
            'line1': f"{donation.donor_street} {donation.donor_house_number}".strip(),
            'city': donation.donor_city,
            'postal_code': donation.donor_postal_code,
            'country': donation.donor_country,
            'state': None  # Für DE/AT/CH nicht erforderlich
        }
    }
    
    # Metadata für Tracking und Webhook-Verarbeitung
    metadata = {
        'donation_id': str(donation.id),
        'donation_type': donation.donation_type,
        'verse_reference': donation.verse.reference,
        'project': 'ngue_bible_sponsoring'
    }
    
    # PaymentIntent erstellen
    try:
        payment_intent = stripe.PaymentIntent.create(
            # Basis-Konfiguration
            amount=int(donation.amount * 100),  # Stripe erwartet Cents
            currency=donation.currency.lower(),
            
            # Customer-Daten
            receipt_email=donation.donor_email,
            description=f"NGÜ Bibelvers-Sponsoring: {donation.verse.reference}",
            
            # Billing-Details
            metadata=metadata,
            
            # 3D Secure / SCA Compliance
            confirmation_method='manual',
            confirm=False,
            
            # Automatische Zahlungsmethoden
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never'  # Nur Karten, kein SEPA etc.
            }
        )
        
        return payment_intent
        
    except stripe.error.StripeError as e:
        # Stripe-Fehler behandeln
        raise PaymentError(f"Stripe PaymentIntent creation failed: {e}")
```

### Stripe Customer Management

```python
def get_or_create_stripe_customer(donation):
    """
    Hole bestehenden oder erstelle neuen Stripe Customer
    
    Args:
        donation: Donation-Objekt
        
    Returns:
        str: Stripe Customer ID
    """
    
    # Prüfe ob User bereits Stripe Customer ist
    if donation.user_id:
        user = donation.user
        existing_payments = PaymentTransaction.query.filter_by(
            provider='stripe'
        ).join(Donation).filter_by(user_id=user.id).first()
        
        if existing_payments and existing_payments.stripe_customer_id:
            return existing_payments.stripe_customer_id
    
    # Erstelle neuen Stripe Customer
    customer_data = {
        'email': donation.donor_email,
        'name': f"{donation.donor_first_name} {donation.donor_last_name}".strip(),
        'metadata': {
            'donation_id': str(donation.id),
            'user_id': str(donation.user_id) if donation.user_id else 'guest'
        }
    }
    
    if donation.donor_street:
        customer_data['address'] = {
            'line1': f"{donation.donor_street} {donation.donor_house_number}".strip(),
            'city': donation.donor_city,
            'postal_code': donation.donor_postal_code,
            'country': donation.donor_country
        }
    
    try:
        customer = stripe.Customer.create(**customer_data)
        return customer.id
        
    except stripe.error.StripeError as e:
        # Fallback: Ohne Customer fortfahren
        logger.warning(f"Stripe Customer creation failed: {e}")
        return None
```

### Stripe Elements Frontend-Integration

```javascript
// Frontend: Stripe Elements mit vorausgefüllten Daten
async function initializeStripePayment(clientSecret, billingDetails) {
    const stripe = Stripe('pk_...');  // Public Key
    
    const elements = stripe.elements({
        clientSecret: clientSecret,
        appearance: {
            theme: 'stripe',
            variables: {
                colorPrimary: '#0066cc'  // NGÜ-Farben
            }
        }
    });
    
    const paymentElement = elements.create('payment', {
        defaultValues: {
            billingDetails: billingDetails  // Automatisch vorausgefüllt
        }
    });
    
    paymentElement.mount('#payment-element');
    
    // Payment-Confirm ohne weitere Dateneingabe
    document.getElementById('submit-payment').addEventListener('click', async () => {
        const {error, paymentIntent} = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: `${window.location.origin}/payment/success`
            }
        });
        
        if (error) {
            showError(error.message);
        } else {
            // Payment erfolgreich - automatische Weiterleitung
            window.location.href = '/payment/success';
        }
    });
}
```

### Webhook-Verarbeitung

```python
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """
    Verarbeite Stripe Webhooks für Payment-Updates
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400
    
    # Payment erfolgreich
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        donation_id = payment_intent['metadata']['donation_id']
        
        # Donation als completed markieren
        donation = Donation.query.get(donation_id)
        if donation:
            donation.mark_completed()
            
            # PaymentTransaction aktualisieren
            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)
    
    # Payment fehlgeschlagen
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        donation_id = payment_intent['metadata']['donation_id']
        
        donation = Donation.query.get(donation_id)
        if donation:
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            donation.mark_failed(error_message)
    
    return 'OK', 200
```

## Payment-Flow Integration

### 1. Checkout-Prozess
```python
@app.route('/checkout/payment/<int:donation_id>')
def checkout_payment(donation_id):
    """
    Zeige Stripe-Payment-Formular mit vorausgefüllten Daten
    """
    donation = Donation.query.get_or_404(donation_id)
    
    # PaymentTransaction erstellen
    payment = donation.create_payment_transaction('stripe')
    
    # Stripe Customer erstellen/abrufen
    customer_id = get_or_create_stripe_customer(donation)
    if customer_id:
        payment.stripe_customer_id = customer_id
        db.session.commit()
    
    # PaymentIntent erstellen
    payment_intent = create_stripe_payment_intent(donation)
    
    # PaymentTransaction aktualisieren
    payment.update_stripe_data(payment_intent)
    
    # Billing-Details für Frontend
    billing_details = {
        'name': f"{donation.donor_first_name} {donation.donor_last_name}".strip(),
        'email': donation.donor_email,
        'address': {
            'line1': f"{donation.donor_street} {donation.donor_house_number}".strip(),
            'city': donation.donor_city,
            'postal_code': donation.donor_postal_code,
            'country': donation.donor_country
        }
    }
    
    return render_template('checkout-payment.html',
                         client_secret=payment_intent.client_secret,
                         billing_details=billing_details,
                         donation=donation)
```

### 2. Payment-Success-Handler
```python
@app.route('/payment/success')
def payment_success():
    """
    Behandle erfolgreiche Zahlung
    """
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        # PaymentTransaction finden
        payment = PaymentTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if payment and payment.donation:
            donation = payment.donation
            
            # Sicherstellen dass Donation als completed markiert ist
            if not donation.is_completed:
                donation.mark_completed()
            
            # PDF-Zertifikate generieren (async)
            generate_certificates_async.delay(donation.id)
            
            # Success-Seite mit Donation-Details
            return render_template('payment-success.html', 
                                 donation=donation,
                                 verse=donation.verse)
    
    # Fallback bei Problemen
    return render_template('payment-success.html')
```

## Error-Handling

### Stripe-Fehler-Kategorien
```python
def handle_stripe_error(error):
    """
    Kategorisiere und behandle Stripe-Fehler
    """
    if isinstance(error, stripe.error.CardError):
        # Karten-spezifische Fehler
        return {
            'type': 'card_error',
            'message': 'Ihre Karte wurde abgelehnt. Bitte versuchen Sie eine andere Zahlungsmethode.',
            'retry_possible': True
        }
    
    elif isinstance(error, stripe.error.RateLimitError):
        # Rate Limit
        return {
            'type': 'rate_limit',
            'message': 'Zu viele Anfragen. Bitte versuchen Sie es in wenigen Minuten erneut.',
            'retry_possible': True
        }
    
    elif isinstance(error, stripe.error.InvalidRequestError):
        # API-Fehler
        return {
            'type': 'api_error',
            'message': 'Ein technischer Fehler ist aufgetreten. Bitte kontaktieren Sie den Support.',
            'retry_possible': False
        }
    
    else:
        # Allgemeiner Fehler
        return {
            'type': 'general_error',
            'message': 'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.',
            'retry_possible': True
        }
```

## Configuration

### Flask-App-Config
```python
# config.py oder app.py
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Stripe konfigurieren
stripe.api_key = STRIPE_SECRET_KEY
```

### Environment Variables
```bash
# .env
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Testing

### Test-Szenarien
1. **PaymentIntent-Erstellung** mit korrekten Billing-Details
2. **Customer-Management** für neue und wiederkehrende Spender
3. **Webhook-Verarbeitung** für verschiedene Events
4. **Error-Handling** für verschiedene Stripe-Fehler
5. **End-to-End Payment** mit echten Test-Karten

### Stripe-Test-Karten
```python
# Für Tests verwenden
TEST_CARDS = {
    'success': '4242424242424242',
    'decline': '4000000000000002',
    '3d_secure': '4000002500003155',
    'insufficient_funds': '4000000000009995'
}
```

## Nächste Schritte

1. **Stripe-Account** einrichten und API-Keys generieren
2. **PaymentIntent-Service** implementieren
3. **Frontend Stripe Elements** integrieren
4. **Webhook-Endpoint** einrichten und testen
5. **Error-Handling** implementieren
6. **End-to-End Tests** mit Stripe-Test-Environment

---

**Priorität für MVP:** Hoch - Kern-Feature für Zahlungsabwicklung
**Geschätzte Implementierungszeit:** 2-3 Tage