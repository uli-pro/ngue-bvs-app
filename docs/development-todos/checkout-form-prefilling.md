# Checkout-Formular Vorausfüllung für eingeloggte User

**Status:** TODO - Noch zu implementieren  
**Priorität:** Hoch  
**Datum:** 15. August 2025  
**Abhängigkeiten:** User-Model mit Adress-Feldern (✅ abgeschlossen)

## Überblick

Eingeloggte User sollen beim Checkout alle Formulare automatisch mit ihren gespeicherten Daten vorausgefüllt bekommen. Keine doppelte Dateneingabe!

## Anforderungen

### User Experience
- ✅ **Eingeloggte User**: Alle Felder vorausgefüllt
- ✅ **Gäste**: Leere Formulare
- ✅ **Editierbar**: User kann vorausgefüllte Daten ändern
- ✅ **Session-Persistenz**: Änderungen bleiben während Checkout erhalten

## Technische Spezifikation

### Flask-Routen implementieren

#### 1. Checkout-Daten Route
```python
@app.route('/checkout/daten')
@app.route('/checkout/daten/<donation_type>')  # einzelperson, gruppe, geschenk
def checkout_daten(donation_type='einzelperson'):
    """Checkout-Formular mit User-Daten vorausfüllen"""
    
    initial_data = {}
    
    # Wenn User eingeloggt ist, Daten vorausfüllen
    if current_user.is_authenticated:
        initial_data = {
            # Kontaktdaten
            'email': current_user.email,
            'salutation': current_user.salutation,
            'title': current_user.title,
            'firstName': current_user.first_name,
            'lastName': current_user.last_name,
            
            # Adressdaten
            'street': current_user.street,
            'houseNumber': current_user.house_number,
            'postalCode': current_user.postal_code,
            'city': current_user.city,
            'country': current_user.country,
            
            # Einstellungen
            'newsletter': current_user.newsletter_opt_in,
            'wantReceipt': True  # Default für Spendenbescheinigung
        }
    
    return render_template('checkout-daten.html', 
                         data=initial_data, 
                         donation_type=donation_type)
```

#### 2. Profil-Route
```python
@app.route('/profil')
@login_required
def profil():
    """User-Profil mit allen Daten"""
    
    user_data = {
        'email': current_user.email,
        'salutation': current_user.salutation,
        'title': current_user.title,
        'firstName': current_user.first_name,
        'lastName': current_user.last_name,
        'street': current_user.street,
        'houseNumber': current_user.house_number,
        'postalCode': current_user.postal_code,
        'city': current_user.city,
        'country': current_user.country,
        'newsletter': current_user.newsletter_opt_in
    }
    
    return render_template('profil.html', data=user_data)
```

#### 3. Registrierung nach Spende
```python
@app.route('/register-after-donation/<int:donation_id>')
def register_after_donation(donation_id):
    """Account-Erstellung mit Daten aus abgeschlossener Spende"""
    
    donation = Donation.query.get_or_404(donation_id)
    
    # Nur Guest-Donations erlauben
    if donation.user_id is not None:
        flash('Diese Spende ist bereits mit einem Account verknüpft.')
        return redirect(url_for('index'))
    
    # Daten aus Donation für Registrierung vorausfüllen
    registration_data = {
        'email': donation.donor_email,
        'firstName': donation.donor_first_name,
        'lastName': donation.donor_last_name,
        'salutation': donation.donor_salutation,
        'title': donation.donor_title,
        'street': donation.donor_street,
        'houseNumber': donation.donor_house_number,
        'postalCode': donation.donor_postal_code,
        'city': donation.donor_city,
        'country': donation.donor_country,
        'newsletter': donation.newsletter_opt_in
    }
    
    return render_template('register-from-donation.html', 
                         data=registration_data, 
                         donation_id=donation_id)
```

### Template-Anpassungen

#### checkout-daten.html erweitern
```html
<!-- Kontaktdaten -->
<input type="email" class="form-control" id="email" name="email" 
       value="{{ data.email or '' }}" required>

<select class="form-select" id="salutation" name="salutation" required>
    <option value="">Bitte wählen...</option>
    <option value="Herr" {{ 'selected' if data.salutation == 'Herr' else '' }}>Herr</option>
    <option value="Frau" {{ 'selected' if data.salutation == 'Frau' else '' }}>Frau</option>
    <option value="Eheleute" {{ 'selected' if data.salutation == 'Eheleute' else '' }}>Eheleute</option>
    <option value="Firma" {{ 'selected' if data.salutation == 'Firma' else '' }}>Firma</option>
    <option value="keine" {{ 'selected' if data.salutation == 'keine' else '' }}>Keine Anrede</option>
</select>

<input type="text" class="form-control" id="title" name="title" 
       value="{{ data.title or '' }}" placeholder="z.B. Dr., Prof.">

<input type="text" class="form-control" id="firstName" name="firstName" 
       value="{{ data.firstName or '' }}" required>

<input type="text" class="form-control" id="lastName" name="lastName" 
       value="{{ data.lastName or '' }}" required>

<!-- Adressdaten -->
<input type="text" class="form-control" id="street" name="street" 
       value="{{ data.street or '' }}" required>

<input type="text" class="form-control" id="houseNumber" name="houseNumber" 
       value="{{ data.houseNumber or '' }}" required>

<input type="text" class="form-control" id="postalCode" name="postalCode" 
       value="{{ data.postalCode or '' }}" required>

<input type="text" class="form-control" id="city" name="city" 
       value="{{ data.city or '' }}" required>

<select class="form-select" id="country" name="country" required>
    <optgroup label="Häufige Länder">
        <option value="DE" {{ 'selected' if data.country == 'DE' else '' }}>DE - Deutschland</option>
        <option value="AT" {{ 'selected' if data.country == 'AT' else '' }}>AT - Österreich</option>
        <option value="CH" {{ 'selected' if data.country == 'CH' else '' }}>CH - Schweiz</option>
        <!-- ... weitere Länder -->
    </optgroup>
</select>

<!-- Einstellungen -->
<input class="form-check-input" type="checkbox" id="newsletter" name="newsletter" 
       {{ 'checked' if data.newsletter else '' }}>

<input class="form-check-input" type="checkbox" id="wantReceipt" name="wantReceipt" 
       {{ 'checked' if data.wantReceipt else '' }}>
```

#### profil.html erweitern
```html
<!-- Gleiche Feldstruktur wie checkout-daten.html, aber mit User-Daten -->
<!-- Bereits implementiert in aktueller profil.html -->
```

### Form-Handling

#### POST-Handler für Checkout
```python
@app.route('/checkout/daten', methods=['POST'])
def checkout_daten_submit():
    """Verarbeite Checkout-Formular und speichere in Session/Cart"""
    
    form_data = request.form.to_dict()
    
    # Validierung
    if not all([form_data.get('email'), form_data.get('firstName'), 
                form_data.get('lastName'), form_data.get('street')]):
        flash('Bitte füllen Sie alle Pflichtfelder aus.')
        return redirect(request.url)
    
    # In Session speichern für nächste Schritte
    session['checkout_data'] = form_data
    
    # Oder in DonationCartItem speichern
    cart_item = DonationCartItem.query.filter_by(
        session_id=session.get('cart_session_id'),
        verse_id=session.get('selected_verse_id')
    ).first()
    
    if cart_item:
        cart_item.temp_data = form_data
        db.session.commit()
    
    return redirect(url_for('checkout_zusammenfassung'))
```

#### POST-Handler für Profil-Update
```python
@app.route('/profil', methods=['POST'])
@login_required
def profil_update():
    """Update User-Profil mit neuen Daten"""
    
    form_data = request.form.to_dict()
    
    # User-Daten aktualisieren
    current_user.salutation = form_data.get('salutation')
    current_user.title = form_data.get('title')
    current_user.first_name = form_data.get('firstName')
    current_user.last_name = form_data.get('lastName')
    current_user.street = form_data.get('street')
    current_user.house_number = form_data.get('houseNumber')
    current_user.postal_code = form_data.get('postalCode')
    current_user.city = form_data.get('city')
    current_user.country = form_data.get('country')
    current_user.newsletter_opt_in = 'newsletter' in form_data
    
    db.session.commit()
    flash('Profil erfolgreich aktualisiert.')
    
    return redirect(url_for('profil'))
```

## Stripe-Integration

### Billing-Details automatisch setzen
```python
def create_stripe_payment_intent(donation):
    """Erstelle Stripe PaymentIntent mit Billing-Daten"""
    
    billing_details = {
        'name': f"{donation.donor_first_name} {donation.donor_last_name}",
        'email': donation.donor_email,
        'address': {
            'line1': f"{donation.donor_street} {donation.donor_house_number}".strip(),
            'city': donation.donor_city,
            'postal_code': donation.donor_postal_code,
            'country': donation.donor_country
        }
    }
    
    payment_intent = stripe.PaymentIntent.create(
        amount=int(donation.amount * 100),  # Cents
        currency=donation.currency.lower(),
        metadata={'donation_id': donation.id},
        receipt_email=donation.donor_email,
        shipping=billing_details,  # Für Stripe-Formulare
        # Weitere Stripe-Parameter...
    )
    
    return payment_intent
```

## Testing-Anforderungen

### Test-Szenarien
1. **Eingeloggte User**: Formular ist vorausgefüllt
2. **Gäste**: Formular ist leer
3. **Profil-Update**: Änderungen werden gespeichert und bei nächstem Checkout verwendet
4. **Account nach Spende**: Registrierung mit Donation-Daten funktioniert
5. **Stripe-Integration**: Billing-Details werden korrekt übertragen

### Test-Implementation
```python
def test_checkout_prefilling_for_logged_in_user():
    """Test dass eingeloggte User vorausgefüllte Formulare sehen"""
    
def test_checkout_empty_for_guests():
    """Test dass Gäste leere Formulare sehen"""
    
def test_profile_update_affects_next_checkout():
    """Test dass Profil-Änderungen beim nächsten Checkout sichtbar sind"""
    
def test_register_from_donation_data():
    """Test Account-Erstellung aus Donation-Daten"""
```

## Implementierungs-Reihenfolge

1. **Flask-Routen** für checkout/daten und profil anpassen
2. **Template-Updates** für Vorausfüllung
3. **Form-Handler** für POST-Requests
4. **Session-Management** für Checkout-Flow
5. **Stripe-Integration** mit Billing-Details
6. **Testing** aller Szenarien

## Nächste Schritte

1. Bestehende checkout-daten.html und profil.html Templates anpassen
2. Flask-Routen in app.py implementieren
3. Session-Management für Checkout-Flow einrichten
4. Integration mit Stripe-Billing-Details
5. Umfassende Tests schreiben

---

**Priorität für MVP:** Hoch - Essentiell für gute User Experience
**Geschätzte Implementierungszeit:** 1-2 Tage