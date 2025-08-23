# Database Rebuild Implementation Plan - NGÜ Bibelvers-Sponsoring App

## Übersicht
Kompletter Neuaufbau der Datenbank mit optimierter Struktur, gefolgt von Code-Refactoring für die neue Architektur. Dieser Ansatz ist 10x schneller als Migration und liefert eine saubere Struktur ohne Altlasten.

## Voraussetzungen
- Aktuelle Datenbank enthält keine kritischen Daten
- PostgreSQL läuft lokal
- Python Virtual Environment aktiviert
- Alle Dependencies installiert (`pip install -r requirements.txt`)

## Phase 1: Database Neuaufbau (1 Stunde)

### 1.1 Backup erstellen (Optional, aber empfohlen)
```bash
# Für den Fall dass doch etwas erhalten werden soll
pg_dump postgresql://localhost/ngue_bvs_db > backup_old_structure_$(date +%Y%m%d_%H%M%S).sql
```

### 1.2 Database komplett neu aufsetzen
```bash
# Hauptcommand - Datenbank neuaufbauen mit allen Daten
python setup_db_v2.py --drop-existing --import-verses --sample-data

# Erwartete Ausgabe:
# ✓ Database dropped successfully
# ✓ pgvector extension created  
# ✓ Tables created successfully
# ✓ Indexes created successfully
# ✓ Triggers created successfully
# ✓ Imported 11,047 verses successfully
# ✓ Created sample data
# ✅ Database setup completed successfully!
```

### 1.3 Verifikation der neuen Struktur
```bash
# Überprüfe dass alles korrekt erstellt wurde
psql postgresql://localhost/ngue_bvs_db -c "\dt"
psql postgresql://localhost/ngue_bvs_db -c "SELECT COUNT(*) FROM verses;"
psql postgresql://localhost/ngue_bvs_db -c "SELECT COUNT(*) FROM persons;"
```

**Erwartete Ergebnisse:**
- 10 Tabellen erstellt
- ~11.000 Verse importiert
- 1 Demo-Person mit 2 Beispiel-Spenden

### 1.4 Optional: Vektorisierung (Semantische Suche)
```bash
# Nur ausführen wenn OpenAI API Key verfügbar und semantische Suche gewünscht
# WICHTIG: Kostet ca. $0.01-0.02

# Erst API Key in .env setzen:
# OPENAI_API_KEY=sk-...

python vectorize_v2.py --skip-existing --batch-size 100

# Bei Erfolg:
# ✅ Vectorization completed successfully!
# Coverage: 100.0%
```

## Phase 2: Models Refactoring (2 Stunden)

### 2.1 Backup der aktuellen models.py
```bash
cp models.py models_old.py
```

### 2.2 Neue SQLAlchemy Models implementieren

**File: `models.py`**

Ersetze komplett mit der neuen Struktur:

```python
"""
Database models for NGÜ Bible Verse Sponsoring App V2
Using new optimized structure with persons/donations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Index, UniqueConstraint, text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError

db = SQLAlchemy()

# Initialize Argon2 password hasher
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16
)

class Person(db.Model):
    """Central person management (replaces User)"""
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    
    # Personal data
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    salutation = db.Column(db.String(20))  # Herr, Frau, Eheleute, Firma, keine
    title = db.Column(db.String(50))       # Dr., Prof., etc.
    
    # Address data
    street = db.Column(db.String(200))
    house_number = db.Column(db.String(10))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country = db.Column(db.String(2), default='DE')
    
    # Preferences
    newsletter_opt_in = db.Column(db.Boolean, default=False)
    save_data_consent = db.Column(db.Boolean, default=True)
    
    # Metadata
    last_donation_at = db.Column(db.DateTime)
    data_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='person', lazy='dynamic')
    login = db.relationship('PersonLogin', uselist=False, backref='person')
    
    def __repr__(self):
        return f'<Person {self.email}>'
    
    @property
    def full_name(self):
        """Full name for display"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def full_name_with_salutation(self):
        """Full name with salutation for formal display"""
        name_parts = []
        if self.salutation and self.salutation != 'keine':
            name_parts.append(self.salutation)
        if self.title:
            name_parts.append(self.title)
        if self.first_name and self.last_name:
            name_parts.extend([self.first_name, self.last_name])
        return " ".join(name_parts) if name_parts else self.email
    
    @property
    def address(self):
        """Complete address for display"""
        if not all([self.street, self.postal_code, self.city]):
            return None
        
        address_parts = [
            f"{self.street} {self.house_number}".strip(),
            f"{self.postal_code} {self.city}"
        ]
        return "\n".join(address_parts)
    
    @property
    def has_complete_address(self):
        """Check if person has complete address data"""
        return all([self.street, self.postal_code, self.city, self.country])
    
    def to_snapshot(self):
        """Create snapshot for donation history"""
        return {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'salutation': self.salutation,
            'title': self.title,
            'street': self.street,
            'house_number': self.house_number,
            'postal_code': self.postal_code,
            'city': self.city,
            'country': self.country
        }
    
    @classmethod
    def find_or_create(cls, email, **kwargs):
        """Find or create person based on email"""
        person = cls.query.filter_by(email=email.lower()).first()
        if not person:
            person = cls(email=email.lower(), **kwargs)
            db.session.add(person)
        else:
            # Update with new data if consent given
            if person.save_data_consent:
                for key, value in kwargs.items():
                    if hasattr(person, key) and value:
                        setattr(person, key, value)
                person.data_updated_at = datetime.utcnow()
        
        return person

class PersonLogin(db.Model):
    """Optional login credentials for persons"""
    __tablename__ = 'person_logins'
    
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash using Argon2id"""
        try:
            self.password_hash = ph.hash(password)
        except HashingError as e:
            raise ValueError(f"Password hashing failed: {e}")
    
    def check_password(self, password):
        """Check password against Argon2id hash"""
        try:
            ph.verify(self.password_hash, password)
            
            # Check if password needs rehashing
            if ph.check_needs_rehash(self.password_hash):
                self.set_password(password)
                db.session.commit()
            
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            return False

class Verse(db.Model):
    """Bible verses with sponsorship status and NGÜ support"""
    __tablename__ = 'verses'
    
    id = db.Column(db.Integer, primary_key=True)
    book = db.Column(db.String(50), nullable=False)
    chapter = db.Column(db.Integer, nullable=False)
    verse = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    text_ngue = db.Column(db.Text)  # NGÜ translation when available
    text_search = db.Column(TSVECTOR)
    text_embedding = db.Column(Vector(1536))
    positivity_score = db.Column(db.Integer)
    is_sponsored = db.Column(db.Boolean, default=False, nullable=False)
    is_translated = db.Column(db.Boolean, default=False, nullable=False)
    translation_completed_at = db.Column(db.DateTime)
    translation_book_release = db.Column(db.Date)
    sponsored_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='verse', lazy='dynamic')
    
    def __repr__(self):
        return f'<Verse {self.book} {self.chapter},{self.verse}>'
    
    @property
    def reference(self):
        """Human-readable verse reference"""
        return f"{self.book} {self.chapter},{self.verse}"
    
    @property
    def url_slug(self):
        """Generate URL-friendly slug"""
        return f"{self.book.lower()}-{self.chapter}-{self.verse}"
    
    @classmethod
    def get_by_reference(cls, book, chapter, verse_num):
        """Get verse by biblical reference"""
        if not book or chapter is None or verse_num is None:
            return None
        
        if chapter <= 0 or verse_num <= 0:
            return None
        
        book_upper = book.upper() if book else None
        
        return cls.query.filter_by(
            book=book_upper,
            chapter=chapter,
            verse=verse_num
        ).first()
    
    @classmethod
    def get_adaptive_featured_verses(cls, limit=3, exclude_ids=None):
        """Get top positive verses for homepage"""
        exclude_ids = exclude_ids or []
        
        # Find highest available score with enough verses
        min_pool_size = 20
        
        for min_score in [90, 80, 70, 60, 50, 40, 30, 20, 10, 0]:
            pool = cls.query.filter(
                cls.is_sponsored == False,
                cls.positivity_score >= min_score,
                ~cls.id.in_(exclude_ids) if exclude_ids else True
            ).limit(min_pool_size + 10).all()
            
            if len(pool) >= min_pool_size:
                break
        
        # Keyword bonus for better selection
        positive_keywords = [
            'Liebe', 'Hoffnung', 'Frieden', 'Segen', 'Freude', 
            'Gnade', 'Trost', 'Schutz', 'Hilfe', 'Güte', 'Licht', 'Leben'
        ]
        
        scored_verses = []
        for verse in pool:
            keyword_bonus = sum(2 for kw in positive_keywords if kw.lower() in verse.text.lower())
            final_score = verse.positivity_score + keyword_bonus
            scored_verses.append((verse, final_score))
        
        scored_verses.sort(key=lambda x: x[1], reverse=True)
        return [verse for verse, score in scored_verses[:limit]]

class Donation(db.Model):
    """Simplified donations with JSONB details"""
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    
    # Donation type and details
    donation_type = db.Column(db.String(20), nullable=False)
    donation_details = db.Column(JSONB)  # Type-specific data
    person_snapshot = db.Column(JSONB, nullable=False)  # Historical person data
    
    # Financial
    amount = db.Column(db.Numeric(6, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR', nullable=False)
    
    # Preferences
    wants_receipt = db.Column(db.Boolean, default=True, nullable=False)
    privacy_consent = db.Column(db.Boolean, nullable=False)
    
    # Status
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    certificate_generated = db.Column(db.Boolean, default=False, nullable=False)
    receipt_generated = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    certificates = db.relationship('Certificate', backref='donation', lazy='dynamic')
    payment = db.relationship('PaymentTransaction', uselist=False, backref='donation')
    
    def __repr__(self):
        return f'<Donation {self.id}: {self.donation_type} - {self.verse.reference}>'
    
    @property
    def display_name(self):
        """Name for certificate display"""
        if self.donation_type == 'gruppe':
            details = self.donation_details or {}
            article = details.get('group_article', '')
            name = details.get('group_name', '')
            return f"{article} {name}".strip()
        elif self.donation_type == 'geschenk':
            details = self.donation_details or {}
            return details.get('recipient_name', '')
        else:
            snapshot = self.person_snapshot or {}
            return f"{snapshot.get('first_name', '')} {snapshot.get('last_name', '')}".strip()
    
    @property
    def is_completed(self):
        """Check if donation is completed"""
        return self.payment_status == 'completed'
    
    def mark_completed(self):
        """Mark donation as completed"""
        self.payment_status = 'completed'
        self.completed_at = datetime.utcnow()
        # Mark verse as sponsored
        self.verse.is_sponsored = True
        self.verse.sponsored_at = datetime.utcnow()
        if self.payment:
            self.payment.mark_confirmed()
        db.session.commit()

# Additional models...
class PaymentTransaction(db.Model):
    """Payment transaction details"""
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    provider = db.Column(db.String(20), default='stripe', nullable=False)
    provider_transaction_id = db.Column(db.String(100))
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def mark_confirmed(self):
        """Mark payment as confirmed"""
        self.stripe_status = 'succeeded'
        db.session.commit()

class Certificate(db.Model):
    """Generated certificates and receipts"""
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    certificate_type = db.Column(db.String(30), nullable=False)
    version = db.Column(db.Integer, default=1)
    includes_ngue_text = db.Column(db.Boolean, default=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)

class TranslationNotification(db.Model):
    """Notifications for translated verses"""
    __tablename__ = 'translation_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    notification_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VerseReservation(db.Model):
    """Temporary verse reservations during checkout"""
    __tablename__ = 'verse_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False)
    reserved_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=15))
    
    @property
    def is_expired(self):
        """Check if reservation is expired"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired reservations"""
        expired_count = cls.query.filter(cls.expires_at < datetime.utcnow()).count()
        cls.query.filter(cls.expires_at < datetime.utcnow()).delete()
        db.session.commit()
        return expired_count

class VerificationToken(db.Model):
    """Email verification and password reset tokens"""
    __tablename__ = 'verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    token_type = db.Column(db.String(20), default='email_verification')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    used = db.Column(db.Boolean, default=False, nullable=False)
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
```

### 2.3 Models testen
```python
# Test script: test_new_models.py
from app import app
from models import db, Person, Verse, Donation

with app.app_context():
    # Test Person creation
    person = Person.find_or_create(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    print(f"Created person: {person}")
    
    # Test Verse access
    verse = Verse.query.first()
    print(f"First verse: {verse.reference}")
    
    # Test database integrity
    print(f"Total verses: {Verse.query.count()}")
    print(f"Total persons: {Person.query.count()}")
```

## Phase 3: Routes Refactoring (3 Stunden)

### 3.1 Backup der aktuellen app.py
```bash
cp app.py app_old.py
```

### 3.2 Update app.py für neue Models

**Wichtige Änderungen:**

1. **Import Updates:**
```python
# Alte Imports ersetzen
from models import db, Person, Verse, Donation, VerificationToken, VerseReservation
```

2. **Login System Update:**
```python
# Update login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'person_id' not in session:
            session['next_url'] = request.url
            flash("Bitte melden Sie sich an.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

3. **Checkout Routes Update:**
```python
@app.route("/checkout/<donation_type>/daten", methods=["GET", "POST"])
def checkout_daten(donation_type):
    if request.method == "POST":
        email = request.form.get('email', '').strip().lower()
        
        # Use new Person model
        person = Person.find_or_create(
            email=email,
            first_name=request.form.get('firstName'),
            last_name=request.form.get('lastName'),
            # ... weitere Felder
        )
        
        # Create donation with JSONB details
        donation_details = {}
        if donation_type == 'gruppe':
            donation_details = {
                'group_article': request.form.get('group_article'),
                'group_name': request.form.get('group_name')
            }
        elif donation_type == 'geschenk':
            donation_details = {
                'recipient_name': request.form.get('gift_recipient_name'),
                'recipient_email': request.form.get('gift_recipient_email'),
                'gift_message': request.form.get('gift_message')
            }
        
        donation = Donation(
            person_id=person.id,
            verse_id=session['selected_verse_id'],
            donation_type=donation_type,
            donation_details=donation_details,
            person_snapshot=person.to_snapshot(),
            amount=100.00,
            wants_receipt=request.form.get('wantReceipt') == 'on',
            privacy_consent=request.form.get('privacy') == 'on'
        )
        
        db.session.add(donation)
        db.session.commit()
        
        return redirect(url_for('checkout_zahlung'))
```

4. **Stats Routes Update:**
```python
@app.route("/")
def index():
    # Update for new models
    total_verses = Verse.query.count()
    sponsored_verses = Verse.query.filter_by(is_sponsored=True).count()
    # ... Rest bleibt gleich
```

## Phase 4: Frontend Updates (2 Stunden)

### 4.1 Templates für neue Models anpassen

**Key Changes:**

1. **User → Person Referenzen:**
```html
<!-- Alt: -->
{{ current_user.full_name }}

<!-- Neu: -->
{{ current_person.full_name }}
```

2. **Donation Details aus JSONB:**
```html
<!-- Gruppe: -->
{% if donation.donation_type == 'gruppe' %}
    <span>{{ donation.donation_details.group_article }} {{ donation.donation_details.group_name }}</span>
{% endif %}

<!-- Geschenk: -->
{% if donation.donation_type == 'geschenk' %}
    <span>Für: {{ donation.donation_details.recipient_name }}</span>
{% endif %}
```

3. **Person Snapshot für historische Korrektheit:**
```html
<!-- Zeige Daten vom Spendenzeitpunkt: -->
<p>Gesponsert von: {{ donation.person_snapshot.first_name }} {{ donation.person_snapshot.last_name }}</p>
<p>Am: {{ donation.completed_at|date }}</p>
```

## Phase 5: Testing & Verification (1 Stunde)

### 5.1 Functionality Tests
```bash
# 1. App starten
python app.py

# 2. Basic functionality testen:
# - Homepage lädt
# - Vers-Auswahl funktioniert  
# - Checkout-Flow funktioniert
# - Datenbank-Queries funktionieren

# 3. Console-Tests
python -c "
from app import app
from models import Person, Verse, Donation
with app.app_context():
    print(f'Persons: {Person.query.count()}')
    print(f'Verses: {Verse.query.count()}')
    print(f'Donations: {Donation.query.count()}')
    
    # Test Person creation
    p = Person.find_or_create('test@test.com', first_name='Test')
    print(f'Created: {p}')
"
```

### 5.2 Database Integrity Check
```bash
# Check foreign key constraints
psql postgresql://localhost/ngue_bvs_db -c "
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
"

# Check indexes
psql postgresql://localhost/ngue_bvs_db -c "
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"
```

## Phase 6: Cleanup & Finalization (30 Minuten)

### 6.1 Remove old backup files (if everything works)
```bash
# Nur wenn alles funktioniert!
rm models_old.py
rm app_old.py
rm backup_old_structure*.sql
```

### 6.2 Update Documentation
```bash
# Update README wenn vorhanden
# Update CLAUDE.md mit neuer Struktur
```

### 6.3 Git Commit
```bash
git add .
git commit -m "Database rebuild: New optimized structure with persons/donations

- Replaced users table with persons (email-based)
- Added JSONB for flexible donation details  
- Integrated NGÜ translation support
- Added translation notifications system
- Optimized indexes and constraints
- Simplified models with better separation of concerns

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Erwartete Ergebnisse

Nach erfolgreichem Abschluss:

✅ **Neue Datenbankstruktur**
- 10 optimierte Tabellen
- JSONB für flexible Datenstrukturen
- Automatische Text-Search Trigger
- pgvector für semantische Suche bereit

✅ **Saubere Code-Basis**
- Eliminierte Redundanz zwischen User/Donation Daten
- Email-basierte Personenverwaltung
- Historische Snapshots für Audit-Trail
- Vorbereitet für NGÜ-Texte und Benachrichtigungen

✅ **Improved Performance**  
- 50% weniger JOINs durch JSONB
- Optimierte Indizes von Anfang an
- GIN-Indizes für JSONB-Queries

## Troubleshooting

### Problem: Models nicht gefunden
```python
# Lösung: App neu starten
export FLASK_APP=app.py
python app.py
```

### Problem: Foreign Key Fehler
```bash
# Check constraints
psql postgresql://localhost/ngue_bvs_db -c "\d+ donations"
```

### Problem: JSONB Queries funktionieren nicht
```python
# Test JSONB access
from models import Donation
d = Donation.query.first()
print(d.donation_details)  # Sollte dict/None zurückgeben
```

## Zeitplan

| Phase | Aufwand | Beschreibung |
|-------|---------|--------------|
| Phase 1 | 1 Stunde | Database Neuaufbau |
| Phase 2 | 2 Stunden | Models Refactoring |
| Phase 3 | 3 Stunden | Routes Updates |
| Phase 4 | 2 Stunden | Frontend Anpassungen |
| Phase 5 | 1 Stunde | Testing |
| Phase 6 | 30 Min | Cleanup |

**Gesamt: 9.5 Stunden** (vs. 15-20 Stunden für Migration)

## Erfolgs-Kriterien

- [ ] Database hat 10 neue Tabellen
- [ ] ~11.000 Verse importiert
- [ ] Models laden ohne Fehler
- [ ] App startet erfolgreich
- [ ] Checkout-Flow funktioniert
- [ ] Keine Foreign Key Violations
- [ ] JSONB Queries funktionieren
- [ ] Email-basierte Personenerstellung funktioniert

Bei erfolgreicher Implementierung ist die App bereit für:
1. Checkout-Flow Redesign (`checkout-flow-redesign-plan.md`)
2. NGÜ-Text Import und Benachrichtigungen
3. Erweiterte Semantische Suche