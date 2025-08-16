# 🔒 Security TODOs für NGÜ Spenden-App

## ✅ Bereits implementiert

- **Rate-Limiting**: Login (5/15min), Register (3/10min), Password-Reset (3/30min)
- **Session-Security**: HttpOnly, SameSite, umgebungsabhängiger Secure-Flag
- **CSRF-Schutz**: Flask-WTF aktiviert
- **SQL-Injection-Schutz**: SQLAlchemy mit Parameter-Binding
- **Passwort-Hashing**: Argon2id (models.py)

## 🔴 KRITISCH - Vor Production Launch

### 1. Demo-Mode entfernen
**Status**: Aktiv in `/login` Route (Zeilen 312-330)
**Problem**: Jeder kann sich mit beliebigen Daten einloggen
**Lösung**: Echte User-Authentifizierung implementieren
```python
# Entfernen:
# Create a demo user on the fly for testing
# Login the user (skip password check for demo)
```

### 2. Input-Validation verstärken
**Status**: Minimal (nur "@" in E-Mail)
**Problem**: XSS/Injection möglich
**Lösung**: 
- E-Mail-Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- HTML-Escaping in Templates prüfen
- WTForms-Validators nutzen

### 3. Zahlungs-Sicherheit
**Status**: Nicht implementiert
**Problem**: Stripe-Webhooks unsicher, Betrug möglich
**Lösung**:
```python
import stripe
# Webhook-Signature-Verification
stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
# Amount-Validation gegen Session
# Idempotenz-Keys verwenden
```

## 🟡 WICHTIG - Vor Launch

### 4. Security Headers
**Status**: Fehlen komplett
**Lösung**: Flask-Talisman einsetzen
```python
from flask_talisman import Talisman
Talisman(app, force_https=not app.debug)
```
- **HSTS**: HTTPS-Zwang
- **CSP**: Content Security Policy
- **X-Frame-Options**: Clickjacking-Schutz

### 5. Logging & Monitoring
**Status**: Nicht vorhanden
**Problem**: Angriffe unerkannt
**Lösung**: 
```python
import logging
# Failed Logins loggen
# Payment-Events loggen
# Rate-Limit-Violations loggen
```

### 6. E-Mail-Sicherheit
**Status**: Nicht implementiert
**Problem**: E-Mail-Spoofing möglich
**Lösung**:
- SPF/DKIM-Records setzen
- E-Mail-Templates escape
- Rate-Limiting für E-Mail-Versand

## 🟢 NICE-TO-HAVE - Nach Launch

### 7. 2FA (Two-Factor Authentication)
**Status**: Nicht implementiert
**Lösung**: Flask-Security oder pyotp

### 8. IP-Whitelisting für Admin
**Status**: Nicht implementiert
**Lösung**: Admin-Panel nur von bestimmten IPs

### 9. Database-Encryption
**Status**: Nicht implementiert
**Lösung**: Sensitive Felder verschlüsseln

### 10. Content Security Policy (CSP)
**Status**: Nicht implementiert
**Lösung**: Strikte CSP-Header
```
Content-Security-Policy: default-src 'self'; script-src 'self' js.stripe.com
```

## 📋 Implementierungs-Reihenfolge

### Sofort (vor User-Testing):
1. Demo-Mode entfernen
2. Input-Validation
3. Basic-Logging

### Vor Launch:
4. Stripe-Webhook-Security
5. Security Headers
6. E-Mail-Security

### Nach Launch:
7. 2FA
8. IP-Whitelisting
9. Erweiterte Monitoring

## 🔧 Notwendige Dependencies

```bash
# Für Security Headers
pip install Flask-Talisman==1.1.0

# Für erweiterte Validierung
pip install email-validator==2.1.0

# Für 2FA (später)
pip install pyotp==2.9.0
```

## 📚 Security-Ressourcen

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Stripe Security Guide](https://stripe.com/docs/security)

---
*Letzte Aktualisierung: 2025-08-16*
*Status: In Bearbeitung - Rate-Limiting & Session-Security implementiert*