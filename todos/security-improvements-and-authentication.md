# Security Improvements und Authentication

**Status:** TODO  
**Priorität:** Mittel  
**Datum:** 2025-08-16  
**Abhängigkeiten:** Database Models, Login-System

## Überblick

Verschiedene Sicherheitsverbesserungen am bestehenden Authentication-System und allgemeine Security-Härtung der Anwendung.

## Aktueller Stand

### ✅ Bereits implementiert
- **Flask-Login Integration**: Vollständige User-Session-Verwaltung
- **Argon2 Password Hashing**: Sichere Passwort-Speicherung in `models.py`
- **Rate Limiting**: Flask-Limiter für Login/Register/Password-Reset
- **Session Security**: HttpOnly, SameSite, CSRF-Protection
- **Input Validation**: Basis-Validierung für E-Mail und Passwort-Stärke

### ❌ Noch zu verbessern
- **In-Memory Login-Attempts**: Nicht persistent, nicht skalierbar
- **Security Headers**: Fehlen teilweise (siehe `docs/security-todos.md`)
- **Admin-Funktionen**: Keine Admin-Rollen oder -Berechtigungen
- **Account-Sicherheit**: Keine 2FA oder erweiterte Sicherheitsfeatures

## Prioritäre TODOs

### 🔴 Hoch: Login-Attempts Database Migration

**Problem:** Aktuell werden fehlgeschlagene Login-Versuche in einem In-Memory Dictionary gespeichert:

```python
# In app.py Zeile 86
login_attempts = {}  # TODO: Move to database table later
```

**Nachteile:**
- Daten gehen bei Server-Restart verloren
- Funktioniert nicht mit Multiple-Server-Deployments
- Memory-Leak: Dictionary wächst unendlich
- Keine Auditierung oder Logging

**Lösung:** Database-Table für persistente Login-Attempt-Tracking

#### Technische Spezifikation

```python
# models.py - Neue Tabelle
class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    user_agent = db.Column(db.String(500))
    attempt_count = db.Column(db.Integer, default=1, nullable=False)
    first_attempt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_attempt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    locked_until = db.Column(db.DateTime)  # NULL = nicht gesperrt
    success = db.Column(db.Boolean, default=False, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_email_locked', 'email', 'locked_until'),
        Index('idx_ip_locked', 'ip_address', 'locked_until'),
        Index('idx_last_attempt', 'last_attempt'),
    )
    
    @property
    def is_locked(self):
        """Check if still locked"""
        return self.locked_until and datetime.utcnow() < self.locked_until
    
    @classmethod
    def cleanup_old_attempts(cls, days=30):
        """Remove old login attempts older than X days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        old_attempts = cls.query.filter(cls.last_attempt < cutoff).all()
        for attempt in old_attempts:
            db.session.delete(attempt)
        db.session.commit()
        return len(old_attempts)
```

#### Neue Funktionen

```python
# app.py - Ersatz für check_rate_limit()
def check_login_rate_limit(email, ip_address=None):
    """Check if email/IP is rate limited with database persistence"""
    
    # Check email-based rate limiting
    email_attempt = LoginAttempt.query.filter_by(email=email).first()
    
    if email_attempt:
        # Check if still locked
        if email_attempt.is_locked:
            return False, f"Account gesperrt bis {email_attempt.locked_until.strftime('%H:%M')}"
        
        # Check if lock period expired
        if email_attempt.locked_until and not email_attempt.is_locked:
            # Reset attempts after lock period
            email_attempt.attempt_count = 0
            email_attempt.locked_until = None
    
    # Optional: IP-based rate limiting
    if ip_address:
        ip_attempts = LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.last_attempt > datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        if ip_attempts >= 20:  # 20 attempts per hour per IP
            return False, "Zu viele Versuche von dieser IP-Adresse"
    
    return True, ""

def record_login_attempt(email, ip_address, user_agent, success=False):
    """Record login attempt in database"""
    
    attempt = LoginAttempt.query.filter_by(email=email).first()
    
    if not attempt:
        # First attempt for this email
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            attempt_count=1,
            success=success
        )
        db.session.add(attempt)
    else:
        # Update existing attempt record
        attempt.last_attempt = datetime.utcnow()
        attempt.ip_address = ip_address  # Update latest IP
        attempt.user_agent = user_agent
        attempt.success = success
        
        if success:
            # Successful login - reset attempts
            attempt.attempt_count = 0
            attempt.locked_until = None
        else:
            # Failed login - increment attempts
            attempt.attempt_count += 1
            
            # Lock account after 5 failed attempts
            if attempt.attempt_count >= 5:
                attempt.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    db.session.commit()
    return attempt
```

#### Integration in Login-Route

```python
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Check rate limit
        allowed, message = check_login_rate_limit(email, ip_address)
        if not allowed:
            flash(message, "danger")
            return render_template("login.html")
        
        # ... existing validation ...
        
        user = User.query.filter_by(email=email.lower()).first()
        
        if user and user.check_password(password):
            # Successful login
            record_login_attempt(email, ip_address, user_agent, success=True)
            login_user(user, remember=remember)
            flash(f"Willkommen, {user.first_name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            # Failed login
            record_login_attempt(email, ip_address, user_agent, success=False)
            flash("Unbekannte E-Mail-Adresse oder falsches Passwort.", "danger")
            return render_template("login.html")
```

### 🟡 Mittel: Security Headers und HTTPS-Hardening

**Verweis:** Siehe `docs/security-todos.md` - Flask-Talisman Integration

### 🟡 Mittel: Admin-User-Management

**Anforderungen:**
- Admin-Rolle in User-Model
- Geschützte Admin-Routes
- User-Management-Interface
- Login-Attempt-Monitoring

```python
# models.py - User-Model erweitern
class User(UserMixin, db.Model):
    # ... existing fields ...
    role = db.Column(db.String(20), default='user', nullable=False)  # user, admin
    
    @property
    def is_admin(self):
        return self.role == 'admin'

# app.py - Admin-Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/login-attempts")
@flask_login_required
@admin_required
def admin_login_attempts():
    """View login attempts for security monitoring"""
    attempts = LoginAttempt.query.order_by(LoginAttempt.last_attempt.desc()).limit(100).all()
    return render_template("admin/login-attempts.html", attempts=attempts)
```

### 🟢 Niedrig: Erweiterte Sicherheitsfeatures

- **2FA Integration**: TOTP mit pyotp
- **Device Tracking**: Bekannte/unbekannte Geräte
- **Suspicious Activity Detection**: Ungewöhnliche Login-Muster
- **Account Recovery**: Sichere Wiederherstellungsoptionen

## Migration-Plan

### Phase 1: Database-Migration (1-2 Tage)
1. `LoginAttempt` Model zu `models.py` hinzufügen
2. Database-Migration erstellen und ausführen
3. Neue Funktionen `check_login_rate_limit()` und `record_login_attempt()` implementieren

### Phase 2: Integration (1 Tag)
1. Login-Route umstellen auf Database-Tracking
2. Altes `login_attempts = {}` Dictionary entfernen
3. Testing und Debugging

### Phase 3: Monitoring (1 Tag)
1. Admin-Interface für Login-Attempt-Monitoring
2. Cleanup-Job für alte Login-Attempts
3. Logging und Alerting

## Testing

### Unit Tests
```python
def test_login_attempt_tracking():
    """Test database-based login attempt tracking"""
    
def test_rate_limiting_persistence():
    """Test that rate limits survive server restart"""
    
def test_ip_based_rate_limiting():
    """Test IP-based rate limiting"""
```

### Security Tests
- Brute-force-Attack-Simulation
- Rate-Limit-Bypass-Versuche
- Session-Hijacking-Tests

## Nächste Schritte

### Sofort
1. `LoginAttempt` Model implementieren
2. Migration erstellen
3. Database-basierte Rate-Limiting-Funktionen schreiben

### Kurzfristig
1. In Login-Route integrieren
2. Alten Code entfernen
3. Admin-Monitoring hinzufügen

### Langfristig
1. Erweiterte Security-Features
2. Machine-Learning-basierte Anomalie-Erkennung
3. Integration mit externen Security-Services

---

**Priorität für MVP:** Mittel  
**Geschätzte Implementierungszeit:** 2-3 Tage

## Notizen

- **Backward Compatibility**: Alte In-Memory-Lösung parallel betreiben während Migration
- **Performance**: Indizes auf Login-Attempts-Tabelle für schnelle Lookups
- **Data Retention**: Automatische Bereinigung alter Login-Attempts
- **Privacy**: GDPR-konforme Speicherung von IP-Adressen und User-Agents