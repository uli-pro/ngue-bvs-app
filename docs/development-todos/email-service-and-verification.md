# Email-Service und Benutzer-Verifizierung

**Status:** TODO  
**Priorität:** Hoch  
**Datum:** 2025-08-16  
**Abhängigkeiten:** Flask-Mail Konfiguration, SMTP-Server Setup

## Überblick

Aktuell ist die E-Mail-Verifizierung im Demo-Modus - es werden keine echten E-Mails versendet und Verifizierungs-Links funktionieren nicht. Für die Production-Version müssen wir ein vollständiges E-Mail-System implementieren für:

- Benutzer-Registrierung E-Mail-Verifizierung
- Passwort-Reset E-Mails
- Spenden-Bestätigungen
- Zertifikat-Versand

## Aktueller Stand

### ✅ Bereits implementiert
- **Database-Models**: `VerificationToken` und `ResetToken` in `models.py`
- **Token-Generierung**: `generate_verification_token()` in `app.py`
- **Verifizierungs-Logic**: `verify_user_email()` und `password_reset()` Funktionen
- **Demo-Modus**: Tokens werden in Flash-Messages angezeigt

### ❌ Noch fehlend
- **Flask-Mail Konfiguration**: SMTP-Server Settings
- **E-Mail-Templates**: HTML/Text Templates für verschiedene E-Mail-Typen
- **Echter E-Mail-Versand**: Integration in Registration und Password-Reset
- **Error-Handling**: Fehlgeschlagene E-Mail-Zustellung behandeln

## Anforderungen

### Funktionale Anforderungen
1. **Registrierungs-E-Mail**: Sofortiger Versand nach Account-Erstellung mit Verifizierungs-Link
2. **Passwort-Reset-E-Mail**: Sicherer Token-basierter Reset-Link mit Ablaufzeit
3. **Spenden-Bestätigungen**: Automatische Bestätigung nach erfolgreichem Payment
4. **Zertifikat-Versand**: PDF-Zertifikate als E-Mail-Attachment

### Technische Anforderungen
- **SMTP-Konfiguration**: Gmail, SendGrid, oder lokaler SMTP-Server
- **Template-System**: Jinja2 HTML/Text Templates
- **Rate-Limiting**: Schutz vor E-Mail-Spam
- **Queue-System**: Asynchroner E-Mail-Versand (optional für MVP)

## Technische Spezifikation

### Flask-Mail Konfiguration

```python
# In app.py
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)
```

### E-Mail-Templates Struktur

```
templates/email/
├── base.html                    # Base template für alle E-Mails
├── verification.html            # E-Mail-Verifizierung
├── verification.txt             # Text-Version
├── password-reset.html          # Passwort-Reset
├── password-reset.txt           # Text-Version
├── donation-confirmation.html   # Spenden-Bestätigung
└── donation-confirmation.txt    # Text-Version
```

### E-Mail-Service Funktionen

```python
def send_verification_email(user, token):
    """Send email verification to new user"""
    verification_url = url_for('verify_email', token=token, _external=True)
    html_body = render_template('email/verification.html', 
                               user=user, verification_url=verification_url)
    text_body = render_template('email/verification.txt', 
                               user=user, verification_url=verification_url)
    
    msg = Message(
        subject='NGÜ Bibelvers-Sponsoring - E-Mail bestätigen',
        recipients=[user.email],
        html=html_body,
        body=text_body
    )
    mail.send(msg)

def send_password_reset_email(user, token):
    """Send password reset email"""
    # Similar implementation
    
def send_donation_confirmation(donation):
    """Send donation confirmation with certificate"""
    # Implementation für Spenden-Bestätigung
```

## Implementierungs-Details

### Phase 1: Basic E-Mail-Setup
1. **Flask-Mail Installation**: `pip install Flask-Mail`
2. **SMTP-Konfiguration**: Environment-Variablen für E-Mail-Settings
3. **Base-Template**: Einheitliches Design für alle E-Mails
4. **Test-E-Mail**: Einfache Test-Funktion für SMTP-Verbindung

### Phase 2: Verifizierungs-E-Mails
1. **Verification-Template**: HTML/Text Templates erstellen
2. **Integration**: `send_verification_email()` in Registration einbauen
3. **Demo-Modus entfernen**: Flash-Messages durch echte E-Mails ersetzen
4. **Error-Handling**: Fehlgeschlagene E-Mails abfangen

### Phase 3: Passwort-Reset
1. **Reset-Template**: HTML/Text Templates für Passwort-Reset
2. **Integration**: E-Mail-Versand in `password_reset_request()` einbauen
3. **Security-Review**: Token-Sicherheit und Ablaufzeiten prüfen

### Phase 4: Spenden-E-Mails
1. **Confirmation-Template**: Spenden-Bestätigungs-E-Mails
2. **Certificate-Attachment**: PDF-Zertifikate als Anhang
3. **Integration**: E-Mail-Versand nach erfolgreichem Payment

## Testing

### Unit Tests
```python
def test_send_verification_email():
    """Test verification email sending"""
    # Mock flask-mail
    # Test template rendering
    # Test token generation

def test_email_templates():
    """Test all email templates render correctly"""
    # Test HTML/Text versions
    # Test variable substitution
```

### Integration Tests
```python
def test_registration_email_flow():
    """Test complete registration with email verification"""
    # Registration POST
    # Check email sent
    # Verify with token
    # Check user verified
```

### Manual Testing
- [ ] SMTP-Verbindung testen
- [ ] E-Mails in verschiedenen Clients prüfen (Gmail, Outlook, etc.)
- [ ] Spam-Filter testen
- [ ] Mobile E-Mail-Darstellung

## Environment-Variablen

```bash
# .env Erweiterung
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@ngue-sponsoring.org
```

## Nächste Schritte

### Sofortige Maßnahmen
1. **Flask-Mail Setup**: Dependencies und Konfiguration
2. **SMTP-Testing**: Verbindung zu E-Mail-Provider testen
3. **Base-Template**: Einheitliches E-Mail-Design erstellen

### Kurz-/Mittelfristig
1. **Demo-Modus ersetzen**: Echte E-Mails statt Flash-Messages
2. **Template-System**: Alle E-Mail-Templates implementieren
3. **Error-Handling**: Robuste Fehlerbehandlung

### Langfristig
1. **Queue-System**: Asynchroner E-Mail-Versand für bessere Performance
2. **Analytics**: E-Mail-Öffnungsraten und Klicks tracking
3. **Template-Management**: Admin-Interface für E-Mail-Templates

## Security-Überlegungen

- **Rate-Limiting**: Max 3 E-Mails pro E-Mail-Adresse pro Stunde
- **Token-Sicherheit**: Sichere Token-Generierung und Ablaufzeiten
- **SMTP-Credentials**: Sichere Speicherung von E-Mail-Zugangsdaten
- **Content-Sanitization**: Schutz vor E-Mail-Injection

---

**Priorität für MVP:** Hoch  
**Geschätzte Implementierungszeit:** 3-4 Tage

## Notizen

- **Provider-Wahl**: Gmail App-Passwords oder professioneller SMTP-Service (SendGrid, Mailgun)
- **Deliverability**: SPF/DKIM Records für bessere Zustellbarkeit
- **Backup-Strategie**: Was passiert bei E-Mail-Service-Ausfall?
- **User-Experience**: Klare Anweisungen für E-Mail-Verifizierung