# Account-Erstellung aus Donation-Daten

**Status:** TODO - Noch zu implementieren  
**Priorität:** Mittel  
**Datum:** 15. August 2025  
**Abhängigkeiten:** User-Model mit Adress-Feldern (✅), Donation-Model (✅)

## Überblick

Ermögliche Guest-Spendern nach erfolgreicher Spende die Erstellung eines User-Accounts mit allen bereits eingegebenen Daten. Keine erneute Dateneingabe erforderlich!

## Anforderungen

### User Journey
1. **Guest-Spende**: User spendet ohne Account
2. **Spende abgeschlossen**: Payment erfolgreich, Zertifikate generiert
3. **Account-Angebot**: "Möchten Sie einen Account erstellen?"
4. **Vorausgefüllte Registrierung**: Alle Daten aus Spende übernommen
5. **Account-Verknüpfung**: Spende wird mit neuem Account verknüpft

### Business-Vorteile
- ✅ **Conversion-Optimierung**: Einfache Account-Erstellung nach positiver Erfahrung
- ✅ **Datenqualität**: Bereits validierte und verwendete Daten
- ✅ **User Experience**: Keine doppelte Dateneingabe
- ✅ **Kundenbindung**: Account für zukünftige Spenden

## Technische Spezifikation

### 1. Success-Page mit Account-Angebot

```python
@app.route('/payment/success')
def payment_success():
    """
    Success-Seite mit optionalem Account-Erstellungs-Angebot
    """
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        payment = PaymentTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if payment and payment.donation:
            donation = payment.donation
            
            # Prüfe ob Guest-Spende (kein User-Account)
            is_guest_donation = (donation.user_id is None)
            
            return render_template('payment-success.html',
                                 donation=donation,
                                 verse=donation.verse,
                                 show_account_offer=is_guest_donation)
    
    return render_template('payment-success.html')
```

### 2. Account-Erstellungs-Route

```python
@app.route('/register-from-donation/<int:donation_id>')
def register_from_donation(donation_id):
    """
    Zeige Registrierungs-Formular mit Daten aus Spende
    """
    donation = Donation.query.get_or_404(donation_id)
    
    # Sicherheits-Checks
    if donation.user_id is not None:
        flash('Diese Spende ist bereits mit einem Account verknüpft.')
        return redirect(url_for('dashboard'))
    
    if not donation.is_completed:
        flash('Account kann nur für abgeschlossene Spenden erstellt werden.')
        return redirect(url_for('index'))
    
    # Prüfe ob Email bereits registriert ist
    existing_user = User.query.filter_by(email=donation.donor_email).first()
    if existing_user:
        flash('Ein Account mit dieser E-Mail-Adresse existiert bereits.')
        return redirect(url_for('login'))
    
    # Daten aus Donation für Registrierung vorbereiten
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
                         donation=donation)
```

### 3. Account-Erstellungs-Handler

```python
@app.route('/register-from-donation/<int:donation_id>', methods=['POST'])
def register_from_donation_submit(donation_id):
    """
    Verarbeite Account-Erstellung aus Donation-Daten
    """
    donation = Donation.query.get_or_404(donation_id)
    
    # Sicherheits-Checks (erneut)
    if donation.user_id is not None:
        flash('Diese Spende ist bereits mit einem Account verknüpft.')
        return redirect(url_for('dashboard'))
    
    # Form-Daten
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    accept_terms = request.form.get('accept_terms')
    
    # Validierung
    if not password or len(password) < 8:
        flash('Das Passwort muss mindestens 8 Zeichen lang sein.')
        return redirect(request.url)
    
    if password != password_confirm:
        flash('Die Passwörter stimmen nicht überein.')
        return redirect(request.url)
    
    if not accept_terms:
        flash('Sie müssen den Nutzungsbedingungen zustimmen.')
        return redirect(request.url)
    
    # Prüfe erneut ob Email verfügbar ist
    existing_user = User.query.filter_by(email=donation.donor_email).first()
    if existing_user:
        flash('Ein Account mit dieser E-Mail-Adresse existiert bereits.')
        return redirect(url_for('login'))
    
    try:
        # User erstellen mit Daten aus Donation
        user = User(
            email=donation.donor_email,
            first_name=donation.donor_first_name,
            last_name=donation.donor_last_name,
            salutation=donation.donor_salutation,
            title=donation.donor_title,
            street=donation.donor_street,
            house_number=donation.donor_house_number,
            postal_code=donation.donor_postal_code,
            city=donation.donor_city,
            country=donation.donor_country,
            newsletter_opt_in=donation.newsletter_opt_in,
            is_verified=False  # E-Mail-Verifizierung erforderlich
        )
        
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Um user.id zu bekommen
        
        # Donation mit User verknüpfen
        donation.user_id = user.id
        db.session.commit()
        
        # E-Mail-Verifizierung senden
        send_verification_email(user)
        
        # User automatisch einloggen
        login_user(user)
        
        flash('Account erfolgreich erstellt! Bitte verifizieren Sie Ihre E-Mail-Adresse.')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Account creation failed: {e}")
        flash('Fehler bei der Account-Erstellung. Bitte versuchen Sie es erneut.')
        return redirect(request.url)
```

### 4. E-Mail-Verifizierung

```python
def send_verification_email(user):
    """
    Sende E-Mail-Verifizierung für neuen Account
    """
    from itsdangerous import URLSafeTimedSerializer
    
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='email-verification')
    
    verification_url = url_for('verify_email', token=token, _external=True)
    
    # E-Mail-Template
    html_body = render_template('emails/verify-account.html',
                              user=user,
                              verification_url=verification_url)
    
    # E-Mail senden
    msg = Message(
        subject='NGÜ Bibelvers-Sponsoring: E-Mail-Adresse bestätigen',
        recipients=[user.email],
        html=html_body,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    
    mail.send(msg)

@app.route('/verify-email/<token>')
def verify_email(token):
    """
    Verifiziere E-Mail-Adresse
    """
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    
    try:
        email = serializer.loads(token, salt='email-verification', max_age=3600)  # 1 Stunde
    except SignatureExpired:
        flash('Der Verifizierungslink ist abgelaufen.')
        return redirect(url_for('index'))
    except BadSignature:
        flash('Ungültiger Verifizierungslink.')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        flash('E-Mail-Adresse erfolgreich verifiziert!')
        
        if current_user.is_authenticated and current_user.id == user.id:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login'))
    else:
        flash('Benutzer nicht gefunden.')
        return redirect(url_for('index'))
```

## Template-Implementierung

### payment-success.html erweitern
```html
{% if show_account_offer %}
<div class="card mt-4">
    <div class="card-header bg-success text-white">
        <h5 class="mb-0">
            <i class="fas fa-user-plus me-2"></i>
            Account erstellen und Vorteile nutzen
        </h5>
    </div>
    <div class="card-body">
        <h6>Ihre Vorteile mit einem NGÜ-Account:</h6>
        <ul class="mb-3">
            <li>Übersicht über alle Ihre gesponserten Verse</li>
            <li>Zertifikate und Spendenbescheinigungen jederzeit herunterladen</li>
            <li>Schnellerer Checkout bei zukünftigen Spenden</li>
            <li>Exklusive Updates zum NGÜ-Übersetzungsprojekt</li>
        </ul>
        
        <div class="alert alert-info">
            <i class="fas fa-magic me-2"></i>
            <strong>Einfach:</strong> Alle Ihre Daten sind bereits ausgefüllt - Sie müssen nur noch ein Passwort wählen!
        </div>
        
        <div class="d-grid gap-2 d-md-flex">
            <a href="{{ url_for('register_from_donation', donation_id=donation.id) }}" 
               class="btn btn-success">
                <i class="fas fa-user-plus me-2"></i>
                Account erstellen
            </a>
            <button class="btn btn-outline-secondary" onclick="this.parentElement.parentElement.parentElement.style.display='none'">
                <i class="fas fa-times me-2"></i>
                Nein, danke
            </button>
        </div>
    </div>
</div>
{% endif %}
```

### register-from-donation.html erstellen
```html
{% extends "layout.html" %}

{% block title %}Account erstellen{% endblock %}

{% block main %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-6 col-md-8">
            <div class="card shadow">
                <div class="card-header text-center bg-success text-white">
                    <h3 class="mb-0">Account erstellen</h3>
                    <p class="mb-0">Basierend auf Ihrer Spende für {{ donation.verse.reference }}</p>
                </div>
                <div class="card-body">
                    <!-- Erfolgreiche Spende anzeigen -->
                    <div class="alert alert-success">
                        <h6><i class="fas fa-check-circle me-2"></i>Ihre Spende war erfolgreich!</h6>
                        <p class="mb-0">Vers: <strong>{{ donation.verse.reference }}</strong><br>
                        Betrag: <strong>{{ donation.amount }}€</strong></p>
                    </div>
                    
                    <!-- Vorausgefüllte Daten anzeigen -->
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle me-2"></i>Ihre Daten sind bereits ausgefüllt</h6>
                        <div class="row text-sm">
                            <div class="col-md-6">
                                <strong>{{ data.firstName }} {{ data.lastName }}</strong><br>
                                {{ data.email }}
                            </div>
                            <div class="col-md-6">
                                {{ data.street }} {{ data.houseNumber }}<br>
                                {{ data.postalCode }} {{ data.city }}
                            </div>
                        </div>
                    </div>
                    
                    <form method="POST" class="needs-validation" novalidate>
                        <!-- Passwort-Eingabe -->
                        <div class="mb-3">
                            <label for="password" class="form-label">Passwort wählen *</label>
                            <input type="password" class="form-control" id="password" 
                                   name="password" minlength="8" required>
                            <div class="form-text">
                                Mindestens 8 Zeichen, eine Zahl und ein Sonderzeichen empfohlen.
                            </div>
                            <div class="invalid-feedback">
                                Das Passwort muss mindestens 8 Zeichen lang sein.
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="password_confirm" class="form-label">Passwort bestätigen *</label>
                            <input type="password" class="form-control" id="password_confirm" 
                                   name="password_confirm" required>
                            <div class="invalid-feedback">
                                Die Passwörter stimmen nicht überein.
                            </div>
                        </div>
                        
                        <!-- Nutzungsbedingungen -->
                        <div class="mb-4">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="accept_terms" 
                                       name="accept_terms" required>
                                <label class="form-check-label" for="accept_terms">
                                    Ich akzeptiere die 
                                    <a href="/nutzungsbedingungen" target="_blank">Nutzungsbedingungen</a> 
                                    und 
                                    <a href="/datenschutz" target="_blank">Datenschutzerklärung</a> *
                                </label>
                                <div class="invalid-feedback">
                                    Sie müssen den Nutzungsbedingungen zustimmen.
                                </div>
                            </div>
                        </div>
                        
                        <!-- Submit Button -->
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-success btn-lg">
                                <i class="fas fa-user-plus me-2"></i>
                                Account erstellen
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Passwort-Matching-Validierung
document.addEventListener('DOMContentLoaded', function() {
    const password = document.getElementById('password');
    const passwordConfirm = document.getElementById('password_confirm');
    
    function validatePasswordMatch() {
        if (passwordConfirm.value !== password.value) {
            passwordConfirm.setCustomValidity('Passwords do not match');
        } else {
            passwordConfirm.setCustomValidity('');
        }
    }
    
    passwordConfirm.addEventListener('input', validatePasswordMatch);
    password.addEventListener('input', validatePasswordMatch);
});
</script>
{% endblock %}
```

## Dashboard-Integration

### Dashboard mit verknüpfter Spende anzeigen
```python
@app.route('/dashboard')
@login_required
def dashboard():
    """
    User-Dashboard mit Übersicht über Spenden
    """
    user_donations = current_user.donations.order_by(Donation.created_at.desc()).all()
    
    # Statistiken
    total_donated = sum(d.amount for d in user_donations if d.is_completed)
    sponsored_verses_count = len([d for d in user_donations if d.is_completed])
    
    return render_template('dashboard.html',
                         donations=user_donations,
                         total_donated=total_donated,
                         sponsored_verses_count=sponsored_verses_count)
```

## Testing

### Test-Szenarien
1. **Guest-Spende → Account-Angebot**: Success-Page zeigt Account-Option
2. **Vorausgefüllte Registrierung**: Alle Donation-Daten sind übernommen
3. **Account-Erstellung**: User wird erstellt und Donation verknüpft
4. **E-Mail-Verifizierung**: Funktioniert korrekt
5. **Dashboard-Integration**: Verknüpfte Spende ist sichtbar
6. **Edge-Cases**: Bereits existierende E-Mail, ungültige Tokens

### Test-Implementation
```python
def test_guest_donation_shows_account_offer():
    """Test dass Guest-Spenden Account-Angebot zeigen"""
    
def test_registration_prefilled_with_donation_data():
    """Test dass Registrierung mit Donation-Daten vorausgefüllt ist"""
    
def test_account_creation_links_donation():
    """Test dass Account-Erstellung Donation verknüpft"""
    
def test_existing_email_prevents_registration():
    """Test dass existierende E-Mail Account-Erstellung verhindert"""
```

## Implementierungs-Reihenfolge

1. **Payment-Success-Template** um Account-Angebot erweitern
2. **Register-from-Donation Route** implementieren
3. **Account-Creation Handler** programmieren
4. **E-Mail-Verifizierung** einrichten
5. **Dashboard-Integration** für verknüpfte Spenden
6. **Testing** aller Szenarien

## Nächste Schritte

1. Template-Erweiterungen implementieren
2. Flask-Routen programmieren
3. E-Mail-System einrichten
4. Dashboard-Integration
5. Umfassende Tests schreiben

---

**Priorität für MVP:** Mittel - Nice-to-have für bessere Conversion
**Geschätzte Implementierungszeit:** 1-2 Tage