# Database Refactoring Plan - NGÜ Bibelvers-Sponsoring App

## Übersicht
Dieses Dokument beschreibt die komplette Umstrukturierung der Datenbank zur Eliminierung von Redundanzen, Implementierung eines email-basierten Personensystems ohne obligatorische User-Accounts, und Vorbereitung für NGÜ-Übersetzungstexte.

## Ziele
1. **Eliminierung der Datenredundanz** zwischen `users` und `donations.donor_*` Feldern
2. **Email-basiertes System** ohne obligatorische User-Accounts
3. **Historische Korrektheit** durch Snapshot-Pattern
4. **NGÜ-Übersetzungs-Support** mit automatischen Benachrichtigungen
5. **DSGVO-Konformität** und Datenschutz

## Phase 1: Backup und Vorbereitung

### 1.1 Vollständiges Backup
```bash
# Backup der aktuellen Datenbank
pg_dump postgresql://localhost/ngue_bvs_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 1.2 Test-Datenbank erstellen
```bash
createdb ngue_bvs_db_test
pg_dump postgresql://localhost/ngue_bvs_db | psql postgresql://localhost/ngue_bvs_db_test
```

## Phase 2: Neue Tabellenstruktur

### 2.1 Neue `persons` Tabelle (ersetzt `users`)

```sql
-- Neue Tabelle für Personen (ohne Login-Zwang)
CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    
    -- Personendaten
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    salutation VARCHAR(20), -- 'Herr', 'Frau', 'Eheleute', 'Firma', 'keine'
    title VARCHAR(50),      -- 'Dr.', 'Prof.', etc.
    
    -- Adressdaten
    street VARCHAR(200),
    house_number VARCHAR(10),
    postal_code VARCHAR(10),
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'DE',
    
    -- Präferenzen
    newsletter_opt_in BOOLEAN DEFAULT FALSE,
    save_data_consent BOOLEAN DEFAULT TRUE, -- Darf für Vorausfüllung gespeichert werden
    
    -- Metadata
    last_donation_at TIMESTAMP,
    data_updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indizes
CREATE INDEX idx_persons_email ON persons(email);
CREATE INDEX idx_persons_postal ON persons(postal_code);
```

### 2.2 Optionale Login-Funktionalität

```sql
-- Optionale Logins für Power-User
CREATE TABLE person_logins (
    person_id INTEGER PRIMARY KEY REFERENCES persons(id),
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.3 Erweiterte `verses` Tabelle

```sql
-- Verses mit NGÜ-Support
ALTER TABLE verses ADD COLUMN (
    -- NGÜ Übersetzung (wenn verfügbar)
    text_ngue TEXT,
    
    -- Übersetzungs-Tracking
    translation_completed_at TIMESTAMP,
    translation_book_release DATE,
    
    -- Sponsor-Tracking (vereinfacht)
    sponsored_at TIMESTAMP
);

-- Index für Übersetzungsstatus
CREATE INDEX idx_verses_translation ON verses(is_translated, book);
```

### 2.4 Neue `donations` Tabelle (vereinfacht)

```sql
-- Vereinfachte donations Tabelle
CREATE TABLE donations_new (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES persons(id) NOT NULL,
    verse_id INTEGER REFERENCES verses(id) NOT NULL,
    
    -- Spendenart und Details
    donation_type VARCHAR(20) NOT NULL CHECK (donation_type IN ('einzelperson', 'gruppe', 'geschenk')),
    donation_details JSONB, -- Typ-spezifische Details
    
    -- Historischer Snapshot
    person_snapshot JSONB NOT NULL, -- Person zum Spendenzeitpunkt
    
    -- Financials
    amount NUMERIC(6,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Präferenzen (aus dem Spendenformular)
    wants_receipt BOOLEAN DEFAULT TRUE,
    privacy_consent BOOLEAN NOT NULL,
    
    -- Status
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (
        payment_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded')
    ),
    certificate_generated BOOLEAN DEFAULT FALSE,
    receipt_generated BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_verse_donation UNIQUE (verse_id, payment_status) 
        DEFERRABLE INITIALLY DEFERRED -- Nur ein erfolgreicher Sponsor pro Vers
);

-- Indizes
CREATE INDEX idx_donations_person ON donations_new(person_id);
CREATE INDEX idx_donations_verse ON donations_new(verse_id);
CREATE INDEX idx_donations_status ON donations_new(payment_status);
CREATE INDEX idx_donations_type ON donations_new(donation_type);
CREATE INDEX idx_donations_details ON donations_new USING GIN (donation_details);
```

### 2.5 Translation Notifications Tabelle

```sql
-- Benachrichtigungen für übersetzte Verse
CREATE TABLE translation_notifications (
    id SERIAL PRIMARY KEY,
    donation_id INTEGER REFERENCES donations_new(id) NOT NULL,
    verse_id INTEGER REFERENCES verses(id) NOT NULL,
    person_id INTEGER REFERENCES persons(id) NOT NULL,
    
    -- Typ und Status
    notification_type VARCHAR(30) NOT NULL CHECK (
        notification_type IN ('verse_translated', 'book_completed', 'testament_completed')
    ),
    status VARCHAR(20) DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')
    ),
    
    -- Versand-Details
    sent_at TIMESTAMP,
    email_sent_to VARCHAR(255),
    certificate_url VARCHAR(500),
    
    -- Error Handling
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    next_retry_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Verhindere Duplikate
    CONSTRAINT unique_donation_notification UNIQUE(donation_id, notification_type)
);

-- Indizes
CREATE INDEX idx_notifications_status ON translation_notifications(status, next_retry_at);
CREATE INDEX idx_notifications_person ON translation_notifications(person_id);
```

### 2.6 Erweiterte Certificates Tabelle

```sql
-- Certificates mit Versionierung
ALTER TABLE certificates ADD COLUMN (
    version INTEGER DEFAULT 1,
    includes_ngue_text BOOLEAN DEFAULT FALSE,
    parent_certificate_id INTEGER REFERENCES certificates(id)
);

-- Neue certificate_types
-- 'sponsorship_initial' - Ursprüngliches Sponsoring-Zertifikat
-- 'translation_update' - Update mit NGÜ-Text
-- 'book_completion' - Benachrichtigung über Buchfertigstellung
-- 'donation_receipt' - Spendenbescheinigung
```

## Phase 3: Datenmigration

### 3.1 Migration der User-Daten zu Persons

```python
# Python Migration Script
def migrate_users_to_persons():
    """Migriere users zu persons Tabelle"""
    
    # 1. Erstelle persons aus users
    cursor.execute("""
        INSERT INTO persons (
            email, first_name, last_name, salutation, title,
            street, house_number, postal_code, city, country,
            newsletter_opt_in, created_at
        )
        SELECT 
            LOWER(email), first_name, last_name, salutation, title,
            street, house_number, postal_code, city, country,
            newsletter_opt_in, created_at
        FROM users
        WHERE email IS NOT NULL
    """)
    
    # 2. Erstelle person_logins für verifizierte User
    cursor.execute("""
        INSERT INTO person_logins (person_id, password_hash, is_verified)
        SELECT p.id, u.password_hash, u.is_verified
        FROM users u
        JOIN persons p ON LOWER(u.email) = p.email
        WHERE u.password_hash IS NOT NULL
    """)
    
    # 3. Erstelle persons aus donations für Guest-Spender
    cursor.execute("""
        INSERT INTO persons (
            email, first_name, last_name, salutation,
            street, house_number, postal_code, city, country,
            newsletter_opt_in, created_at
        )
        SELECT DISTINCT ON (LOWER(donor_email))
            LOWER(donor_email), donor_first_name, donor_last_name, donor_salutation,
            donor_street, donor_house_number, donor_postal_code, donor_city, donor_country,
            newsletter_opt_in, created_at
        FROM donations
        WHERE donor_email IS NOT NULL
        AND LOWER(donor_email) NOT IN (SELECT email FROM persons)
        ORDER BY LOWER(donor_email), created_at DESC
    """)
```

### 3.2 Migration der Donations

```python
def migrate_donations():
    """Migriere donations mit JSONB snapshots"""
    
    cursor.execute("""
        INSERT INTO donations_new (
            person_id, verse_id, donation_type, donation_details,
            person_snapshot, amount, currency, wants_receipt, privacy_consent,
            payment_status, certificate_generated, receipt_generated,
            created_at, completed_at
        )
        SELECT 
            p.id as person_id,
            d.verse_id,
            d.donation_type,
            -- donation_details als JSONB
            CASE 
                WHEN d.donation_type = 'gruppe' THEN
                    jsonb_build_object(
                        'group_article', d.group_article,
                        'group_name', d.group_name
                    )
                WHEN d.donation_type = 'geschenk' THEN
                    jsonb_build_object(
                        'recipient_name', d.gift_recipient_name,
                        'recipient_email', d.gift_recipient_email,
                        'gift_message', d.gift_message,
                        'direct_send', d.gift_direct_send
                    )
                ELSE NULL
            END as donation_details,
            -- person_snapshot als JSONB
            jsonb_build_object(
                'email', d.donor_email,
                'first_name', d.donor_first_name,
                'last_name', d.donor_last_name,
                'salutation', d.donor_salutation,
                'title', d.donor_title,
                'street', d.donor_street,
                'house_number', d.donor_house_number,
                'postal_code', d.donor_postal_code,
                'city', d.donor_city,
                'country', d.donor_country
            ) as person_snapshot,
            d.amount,
            d.currency,
            d.wants_receipt,
            d.privacy_consent,
            d.payment_status,
            d.certificate_generated,
            d.receipt_generated,
            d.created_at,
            d.completed_at
        FROM donations d
        JOIN persons p ON LOWER(d.donor_email) = p.email
    """)
```

### 3.3 Update Verse Status

```python
def update_verse_status():
    """Update verse sponsored status basierend auf donations"""
    
    cursor.execute("""
        UPDATE verses v
        SET 
            is_sponsored = TRUE,
            sponsored_at = d.completed_at
        FROM donations_new d
        WHERE v.id = d.verse_id
        AND d.payment_status = 'completed'
    """)
```

## Phase 4: Code-Anpassungen

### 4.1 Models Update (models.py)

```python
# Neue/Angepasste SQLAlchemy Models

class Person(db.Model):
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # ... weitere Felder
    
    # Relationships
    donations = db.relationship('Donation', backref='person', lazy='dynamic')
    login = db.relationship('PersonLogin', uselist=False, backref='person')
    
    def to_snapshot(self):
        """Erstelle Snapshot für Donation"""
        return {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'salutation': self.salutation,
            'street': self.street,
            'house_number': self.house_number,
            'postal_code': self.postal_code,
            'city': self.city,
            'country': self.country
        }
    
    @classmethod
    def find_or_create(cls, email, **kwargs):
        """Finde oder erstelle Person basierend auf Email"""
        person = cls.query.filter_by(email=email.lower()).first()
        if not person:
            person = cls(email=email.lower(), **kwargs)
            db.session.add(person)
        else:
            # Update mit neuen Daten wenn erlaubt
            if person.save_data_consent:
                for key, value in kwargs.items():
                    if hasattr(person, key) and value:
                        setattr(person, key, value)
                person.data_updated_at = datetime.utcnow()
        return person

class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    
    donation_type = db.Column(db.String(20), nullable=False)
    donation_details = db.Column(JSONB)
    person_snapshot = db.Column(JSONB, nullable=False)
    
    # ... weitere Felder
    
    @property
    def display_name(self):
        """Name für Zertifikat-Anzeige"""
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
```

### 4.2 Routes Update (app.py)

```python
# Angepasste checkout_daten Route

@app.route("/checkout/<donation_type>/daten", methods=["GET", "POST"])
def checkout_daten(donation_type):
    """Datenerfassung mit Auto-Fill basierend auf Email"""
    
    if request.method == "POST":
        email = request.form.get('email', '').strip().lower()
        
        # Finde oder erstelle Person
        person = Person.find_or_create(
            email=email,
            first_name=request.form.get('firstName'),
            last_name=request.form.get('lastName'),
            salutation=request.form.get('salutation'),
            street=request.form.get('street'),
            house_number=request.form.get('houseNumber'),
            postal_code=request.form.get('postalCode'),
            city=request.form.get('city'),
            country=request.form.get('country', 'DE'),
            newsletter_opt_in=request.form.get('newsletter') == 'on',
            save_data_consent=request.form.get('save_data') != 'off'
        )
        
        # Erstelle Donation
        donation = Donation(
            person_id=person.id,
            verse_id=session['selected_verse_id'],
            donation_type=donation_type,
            donation_details=build_donation_details(donation_type, request.form),
            person_snapshot=person.to_snapshot(),
            amount=100.00,
            wants_receipt=request.form.get('wantReceipt') == 'on',
            privacy_consent=request.form.get('privacy') == 'on'
        )
        
        db.session.add(donation)
        db.session.commit()
        
        # Speichere in Session für Zahlung
        session['pending_donation_id'] = donation.id
        
        return redirect(url_for('checkout_zahlung'))
    
    # GET Request - Check for existing person
    email = request.args.get('email', '').strip().lower()
    person = None
    prefill_data = {}
    
    if email:
        person = Person.query.filter_by(email=email).first()
        if person and person.save_data_consent:
            # Security Check mit PLZ
            if 'plz_verified' in session and session['plz_verified'] == email:
                prefill_data = {
                    'firstName': person.first_name,
                    'lastName': person.last_name,
                    'salutation': person.salutation,
                    'street': person.street,
                    'houseNumber': person.house_number,
                    'postalCode': person.postal_code,
                    'city': person.city,
                    'country': person.country,
                    'newsletter': person.newsletter_opt_in
                }
                flash(f"Willkommen zurück! Wir haben Ihre Daten vorausgefüllt.", "info")
            else:
                # Zeige nur Teildaten, fordere PLZ-Verifikation
                prefill_data = {
                    'firstName': person.first_name,
                    'lastName': person.last_name[0] + '***' if person.last_name else '',
                    'needsVerification': True,
                    'verificationEmail': email
                }
    
    return render_template("checkout-daten.html",
                         donation_type=donation_type,
                         verse=verse,
                         prefill_data=prefill_data)

# Neue Route für PLZ-Verifikation
@app.route("/api/verify-plz", methods=["POST"])
@csrf.exempt
def verify_plz():
    """Verifiziere PLZ für Daten-Vorausfüllung"""
    data = request.get_json()
    email = data.get('email', '').lower()
    plz = data.get('plz', '')
    
    person = Person.query.filter_by(email=email).first()
    if person and person.postal_code == plz:
        session['plz_verified'] = email
        return jsonify({
            'success': True,
            'data': {
                'firstName': person.first_name,
                'lastName': person.last_name,
                'salutation': person.salutation,
                'street': person.street,
                'houseNumber': person.house_number,
                'postalCode': person.postal_code,
                'city': person.city,
                'country': person.country
            }
        })
    
    return jsonify({'success': False, 'message': 'PLZ stimmt nicht überein'})
```

### 4.3 NGÜ Translation Import

```python
# Neue Funktion für NGÜ-Import

def import_ngue_translations(book_code, translations_file):
    """
    Importiere NGÜ-Übersetzungen für ein komplettes Buch
    
    Args:
        book_code: z.B. 'ISA' für Jesaja
        translations_file: CSV/JSON mit chapter, verse, text_ngue
    """
    
    import json
    from datetime import datetime
    
    with open(translations_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    updated_verses = []
    
    with db.session.begin():
        for trans in translations:
            verse = Verse.query.filter_by(
                book=book_code,
                chapter=trans['chapter'],
                verse=trans['verse']
            ).first()
            
            if verse and not verse.text_ngue:
                verse.text_ngue = trans['text']
                verse.is_translated = True
                verse.translation_completed_at = datetime.utcnow()
                updated_verses.append(verse.id)
        
        # Erstelle Benachrichtigungen für alle betroffenen Spender
        if updated_verses:
            donations = Donation.query.filter(
                Donation.verse_id.in_(updated_verses),
                Donation.payment_status == 'completed'
            ).all()
            
            for donation in donations:
                # Prüfe ob Benachrichtigung bereits existiert
                existing = TranslationNotification.query.filter_by(
                    donation_id=donation.id,
                    notification_type='verse_translated'
                ).first()
                
                if not existing:
                    notification = TranslationNotification(
                        donation_id=donation.id,
                        verse_id=donation.verse_id,
                        person_id=donation.person_id,
                        notification_type='verse_translated'
                    )
                    db.session.add(notification)
    
    print(f"Updated {len(updated_verses)} verses with NGÜ translation")
    print(f"Created notifications for {len(donations)} donations")
```

## Phase 5: Frontend-Anpassungen

### 5.1 Email-basierte Personenerkennung (JavaScript)

```javascript
// checkout-daten.js

document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    const plzModal = document.getElementById('plzVerificationModal');
    
    // Email-Change Handler
    emailInput.addEventListener('blur', async function() {
        const email = this.value.trim();
        if (!email || !email.includes('@')) return;
        
        // Check if person exists
        const response = await fetch(`/api/person/check?email=${encodeURIComponent(email)}`);
        const data = await response.json();
        
        if (data.exists && data.hasData) {
            // Person gefunden - zeige PLZ-Verifikation
            showPlzVerification(email);
        }
    });
    
    function showPlzVerification(email) {
        // Zeige Modal für PLZ-Eingabe
        document.getElementById('verifyEmail').textContent = email;
        plzModal.style.display = 'block';
        
        document.getElementById('verifyPlzBtn').onclick = async function() {
            const plz = document.getElementById('plzInput').value;
            
            const response = await fetch('/api/verify-plz', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email, plz: plz})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Fülle Formular aus
                fillForm(data.data);
                plzModal.style.display = 'none';
                showNotification('Ihre Daten wurden geladen. Bitte überprüfen Sie diese.');
            } else {
                showError('Die Postleitzahl stimmt nicht überein.');
            }
        };
    }
    
    function fillForm(data) {
        for (const [key, value] of Object.entries(data)) {
            const input = document.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            }
        }
    }
});
```

### 5.2 NGÜ-Text Anzeige im Zertifikat

```html
<!-- certificate_template.html -->

<div class="certificate-content">
    <h1>Sponsoring-Zertifikat</h1>
    
    <p class="verse-reference">{{ verse.reference }}</p>
    
    <!-- Original Schlachter Text -->
    <div class="verse-text schlachter">
        <h3>Schlachter 1951:</h3>
        <p>{{ verse.text }}</p>
    </div>
    
    {% if verse.text_ngue %}
    <!-- NGÜ Text wenn verfügbar -->
    <div class="verse-text ngue">
        <h3>Neue Genfer Übersetzung:</h3>
        <p>{{ verse.text_ngue }}</p>
        <small>Übersetzt am {{ verse.translation_completed_at|date }}</small>
    </div>
    {% else %}
    <div class="translation-pending">
        <p><em>Die NGÜ-Übersetzung dieses Verses ist noch in Arbeit.</em></p>
    </div>
    {% endif %}
    
    <div class="sponsor-info">
        <p>Gesponsert von: <strong>{{ donation.display_name }}</strong></p>
        <p>Am: {{ donation.completed_at|date }}</p>
    </div>
</div>
```

## Phase 6: Testing & Rollback Plan

### 6.1 Test-Suite

```python
# test_migration.py

def test_person_creation():
    """Test Person Erstellung und Deduplizierung"""
    person1 = Person.find_or_create(
        email="test@example.com",
        first_name="Max",
        last_name="Mustermann"
    )
    
    person2 = Person.find_or_create(
        email="TEST@EXAMPLE.COM",  # Unterschiedliche Schreibweise
        first_name="Maximilian"
    )
    
    assert person1.id == person2.id  # Selbe Person
    assert person2.first_name == "Maximilian"  # Updated

def test_donation_snapshot():
    """Test Donation Snapshot Erstellung"""
    person = Person(email="test@example.com", first_name="Max")
    donation = Donation(
        person=person,
        person_snapshot=person.to_snapshot()
    )
    
    # Ändere Person
    person.first_name = "Maximilian"
    
    # Snapshot bleibt unverändert
    assert donation.person_snapshot['first_name'] == "Max"

def test_ngue_import():
    """Test NGÜ Translation Import"""
    # Setup
    verse = Verse(book="ISA", chapter=1, verse=1, text="Original")
    donation = Donation(verse=verse, payment_status='completed')
    
    # Import
    verse.text_ngue = "NGÜ Text"
    verse.is_translated = True
    
    # Check Notification
    notifications = TranslationNotification.query.filter_by(
        donation_id=donation.id
    ).all()
    
    assert len(notifications) == 1
    assert notifications[0].notification_type == 'verse_translated'
```

### 6.2 Rollback Plan

```sql
-- Rollback Script falls nötig

-- 1. Sichere neue Daten
CREATE TABLE backup_persons AS SELECT * FROM persons;
CREATE TABLE backup_donations_new AS SELECT * FROM donations_new;

-- 2. Restore original structure
ALTER TABLE donations RENAME TO donations_backup;
ALTER TABLE donations_old RENAME TO donations;

ALTER TABLE users RENAME TO users_backup;
ALTER TABLE users_old RENAME TO users;

-- 3. Re-enable constraints
ALTER TABLE donations 
    ADD CONSTRAINT donations_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id);
```

## Phase 7: Deployment Checkliste

### Pre-Deployment
- [ ] Vollständiges Backup erstellt
- [ ] Test-Migration auf Staging erfolgreich
- [ ] Code-Review abgeschlossen
- [ ] Frontend-Tests erfolgreich
- [ ] API-Tests erfolgreich

### Deployment
- [ ] Maintenance Mode aktiviert
- [ ] Datenbank-Migration durchgeführt
- [ ] Code deployed
- [ ] Konfiguration aktualisiert
- [ ] Smoke Tests erfolgreich

### Post-Deployment
- [ ] Monitoring aktiviert
- [ ] Performance-Checks
- [ ] Erste echte Transaktionen überwacht
- [ ] Backup-Verifizierung
- [ ] Maintenance Mode deaktiviert

## Zeitplan

- **Phase 1-2**: 2 Stunden (Backup & neue Struktur)
- **Phase 3**: 3-4 Stunden (Datenmigration & Tests)
- **Phase 4**: 4-6 Stunden (Code-Anpassungen)
- **Phase 5**: 2-3 Stunden (Frontend)
- **Phase 6**: 2 Stunden (Testing)
- **Deployment**: 1 Stunde

**Gesamt**: ~15-20 Stunden Entwicklung + Testing

## Risiken & Mitigationen

1. **Datenverlust**: Vollständige Backups, Test auf Kopie
2. **Duplicate Emails**: LOWER() Funktion, Unique Constraint
3. **Performance**: Indizes auf allen Foreign Keys und häufig genutzten Spalten
4. **NGÜ Import Fehler**: Transaktionale Imports, Rollback-Möglichkeit
5. **Session-Probleme**: Graceful Degradation, Session-Migration

## Notizen

- Die `users` Tabelle wird NICHT gelöscht, sondern renamed zu `users_old` für Fallback
- Alle JSONB Felder sind vollständig durchsuchbar mit GIN Index
- PLZ-Verifikation ist optional konfigurierbar (kann deaktiviert werden)
- NGÜ-Texte werden separat vom Schlachter-Text gespeichert für maximale Flexibilität