# Datenmodell-Erweiterung: Gruppenspende

## Übersicht der Änderungen

Das bestehende Datenmodell wird minimal erweitert, um Gruppenspenden zu unterstützen. Die Änderungen sind bewusst schlank gehalten, um die Komplexität zu reduzieren.

## Geänderte Tabellen

### 1. Purchase-Tabelle (Hauptänderung)

**Neue Felder:**
```sql
ALTER TABLE purchase ADD COLUMN donation_type 
  ENUM('self', 'gift', 'group') NOT NULL DEFAULT 'self';
  
ALTER TABLE purchase ADD COLUMN group_article 
  ENUM('der', 'die', 'das') DEFAULT NULL;
  
ALTER TABLE purchase ADD COLUMN group_name 
  VARCHAR(80) DEFAULT NULL;
```

**Erweiterte Tabellendefinition:**
```sql
CREATE TABLE purchase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, -- FK zu User (nullable für Gäste)
    verse_id INTEGER NOT NULL, -- FK zu BibelVerse
    
    -- Bestehende Felder
    amount DECIMAL(10,2) NOT NULL DEFAULT 100.00,
    stripe_payment_id VARCHAR(255) UNIQUE,
    certificate_url VARCHAR(500),
    donation_receipt_url VARCHAR(500),
    donation_receipt_number VARCHAR(50) UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Geschenk-Felder (bereits vorhanden)
    is_gift BOOLEAN NOT NULL DEFAULT FALSE,
    recipient_salutation VARCHAR(20),
    recipient_first_name VARCHAR(100),
    recipient_last_name VARCHAR(100),
    recipient_email VARCHAR(255),
    gift_message TEXT,
    
    -- NEUE FELDER für Gruppenspenden
    donation_type ENUM('self', 'gift', 'group') NOT NULL DEFAULT 'self',
    group_article ENUM('der', 'die', 'das') DEFAULT NULL,
    group_name VARCHAR(80) DEFAULT NULL,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (verse_id) REFERENCES bibelverse(id)
);
```

**Constraints:**
```sql
-- Gruppenspende-Validation
ALTER TABLE purchase ADD CONSTRAINT chk_group_data 
CHECK (
  (donation_type = 'group' AND group_article IS NOT NULL AND group_name IS NOT NULL)
  OR 
  (donation_type != 'group' AND group_article IS NULL AND group_name IS NULL)
);

-- Geschenk-Validation (bereits vorhanden, erweitert)
ALTER TABLE purchase ADD CONSTRAINT chk_gift_data
CHECK (
  (donation_type = 'gift' AND recipient_first_name IS NOT NULL AND recipient_last_name IS NOT NULL)
  OR 
  (donation_type != 'gift')
);

-- is_gift Kompatibilität
ALTER TABLE purchase ADD CONSTRAINT chk_gift_compatibility
CHECK (
  (donation_type = 'gift' AND is_gift = TRUE)
  OR
  (donation_type != 'gift' AND is_gift = FALSE)
);
```

## Keine neuen Tabellen erforderlich!

Im Gegensatz zu komplexeren Lösungen benötigt diese Implementierung **keine neuen Tabellen**. Alle Gruppendaten werden direkt in der `purchase`-Tabelle gespeichert.

## Migration Script

```sql
-- Migration für bestehende Daten
-- Schritt 1: Neue Spalten hinzufügen
ALTER TABLE purchase ADD COLUMN donation_type ENUM('self', 'gift', 'group') DEFAULT 'self';
ALTER TABLE purchase ADD COLUMN group_article ENUM('der', 'die', 'das') DEFAULT NULL;
ALTER TABLE purchase ADD COLUMN group_name VARCHAR(80) DEFAULT NULL;

-- Schritt 2: Bestehende Daten migrieren
UPDATE purchase 
SET donation_type = 'gift' 
WHERE is_gift = TRUE;

UPDATE purchase 
SET donation_type = 'self' 
WHERE is_gift = FALSE;

-- Schritt 3: NOT NULL constraint für donation_type hinzufügen
ALTER TABLE purchase MODIFY COLUMN donation_type ENUM('self', 'gift', 'group') NOT NULL DEFAULT 'self';

-- Schritt 4: Constraints hinzufügen
ALTER TABLE purchase ADD CONSTRAINT chk_group_data 
CHECK (
  (donation_type = 'group' AND group_article IS NOT NULL AND group_name IS NOT NULL)
  OR 
  (donation_type != 'group' AND group_article IS NULL AND group_name IS NULL)
);
```

## SQLAlchemy Model Updates

### Purchase Model Erweiterung

```python
from sqlalchemy import Enum
from enum import Enum as PyEnum

class DonationType(PyEnum):
    SELF = "self"
    GIFT = "gift"
    GROUP = "group"

class GroupArticle(PyEnum):
    DER = "der"
    DIE = "die" 
    DAS = "das"

class Purchase(db.Model):
    __tablename__ = 'purchase'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('bibelverse.id'), nullable=False)
    
    # Bestehende Felder
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=100.00)
    stripe_payment_id = db.Column(db.String(255), unique=True)
    certificate_url = db.Column(db.String(500))
    donation_receipt_url = db.Column(db.String(500))
    donation_receipt_number = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Geschenk-Felder (bereits vorhanden)
    is_gift = db.Column(db.Boolean, nullable=False, default=False)
    recipient_salutation = db.Column(db.String(20))
    recipient_first_name = db.Column(db.String(100))
    recipient_last_name = db.Column(db.String(100))  
    recipient_email = db.Column(db.String(255))
    gift_message = db.Column(db.Text)
    
    # NEUE FELDER für Gruppenspenden
    donation_type = db.Column(Enum(DonationType), nullable=False, default=DonationType.SELF)
    group_article = db.Column(Enum(GroupArticle), nullable=True)
    group_name = db.Column(db.String(80), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='purchases')
    verse = db.relationship('BibelVerse', backref='sponsorships')
    
    @property
    def is_group_donation(self):
        return self.donation_type == DonationType.GROUP
    
    @property
    def sponsor_display_name(self):
        """Gibt den anzuzeigenden Namen des Sponsors zurück"""
        if self.donation_type == DonationType.GROUP:
            return f"{self.group_article.value.capitalize()} {self.group_name}"
        elif self.donation_type == DonationType.GIFT:
            return f"{self.recipient_first_name} {self.recipient_last_name}"
        else:
            # Einzelspende - User-Namen aus User-Tabelle oder GuestDonor
            if self.user:
                return f"{self.user.first_name} {self.user.last_name}"
            else:
                # Gast-Spender - Namen aus GuestDonor-Tabelle
                guest = GuestDonor.query.filter_by(purchase_id=self.id).first()
                return f"{guest.first_name} {guest.last_name}" if guest else "Unbekannt"
    
    @property
    def certificate_text(self):
        """Generiert den Zertifikat-Text basierend auf dem Spende-Typ"""
        sponsor_name = self.sponsor_display_name
        verse_ref = self.verse.reference
        
        if self.donation_type == DonationType.GROUP:
            return f"{sponsor_name} hat durch eine Spende von 100€ die Übersetzung von {verse_ref} ermöglicht."
        elif self.donation_type == DonationType.GIFT:
            # Für Geschenke: Empfänger hat durch Spende von [Spender] ...
            donor_name = f"{self.user.first_name} {self.user.last_name}" if self.user else "einem Spender"
            return f"{sponsor_name} hat durch eine Spende von {donor_name} die Übersetzung von {verse_ref} ermöglicht."
        else:
            return f"{sponsor_name} hat durch eine Spende von 100€ die Übersetzung von {verse_ref} ermöglicht."

    def __repr__(self):
        return f'<Purchase {self.id}: {self.donation_type.value} - {self.verse.reference}>'
```

## Form Validation

### WTForms Integration

```python
from wtforms import SelectField, StringField, RadioField
from wtforms.validators import DataRequired, Length, Optional

class DonationDetailsForm(FlaskForm):
    donation_type = RadioField(
        'Spende-Art',
        choices=[
            ('self', 'Als Einzelperson (für mich selbst)'),
            ('group', 'Als Gruppe (Familie, Jugendgruppe, Verein, etc.)'),
            ('gift', 'Als Geschenk für jemand anderen')
        ],
        default='self',
        validators=[DataRequired()]
    )
    
    # Gruppenspende-Felder
    group_article = SelectField(
        'Artikel',
        choices=[
            ('', 'Artikel wählen...'),
            ('der', 'Der'),
            ('die', 'Die'),
            ('das', 'Das')
        ],
        validators=[Optional()]
    )
    
    group_name = StringField(
        'Gruppenname',
        validators=[
            Optional(),
            Length(min=2, max=80, message='Gruppenname muss zwischen 2 und 80 Zeichen haben')
        ]
    )
    
    def validate(self):
        """Custom validation für Gruppenspenden"""
        if not super().validate():
            return False
            
        if self.donation_type.data == 'group':
            if not self.group_article.data:
                self.group_article.errors.append('Bitte wählen Sie einen Artikel aus')
                return False
                
            if not self.group_name.data or len(self.group_name.data.strip()) < 2:
                self.group_name.errors.append('Bitte geben Sie einen Gruppennamen ein')
                return False
                
        return True
```

## API Response Updates

### JSON Response für Gruppendaten

```python
def purchase_to_dict(purchase):
    """Konvertiert Purchase-Objekt zu Dictionary"""
    result = {
        'id': purchase.id,
        'verse_reference': purchase.verse.reference,
        'verse_text': purchase.verse.text_schlachter,
        'amount': float(purchase.amount),
        'donation_type': purchase.donation_type.value,
        'created_at': purchase.created_at.isoformat(),
        'certificate_url': purchase.certificate_url,
        'sponsor_display_name': purchase.sponsor_display_name
    }
    
    if purchase.donation_type == DonationType.GROUP:
        result.update({
            'group_article': purchase.group_article.value,
            'group_name': purchase.group_name,
            'is_group_donation': True
        })
    
    return result
```

## Database Indexes

Für Performance-Optimierung bei Gruppenspenden-Abfragen:

```sql
-- Index für donation_type für schnelle Filterung
CREATE INDEX idx_purchase_donation_type ON purchase(donation_type);

-- Index für Gruppenspenden-Suche
CREATE INDEX idx_purchase_group_name ON purchase(group_name) WHERE donation_type = 'group';

-- Composite Index für Berichterstattung
CREATE INDEX idx_purchase_type_date ON purchase(donation_type, created_at);
```

## Query Examples

### Häufige Datenbankabfragen

```python
# Alle Gruppenspenden
group_donations = Purchase.query.filter_by(donation_type=DonationType.GROUP).all()

# Gruppenspenden nach Artikel
die_groups = Purchase.query.filter(
    Purchase.donation_type == DonationType.GROUP,
    Purchase.group_article == GroupArticle.DIE
).all()

# Spenden-Statistiken
from sqlalchemy import func
stats = db.session.query(
    Purchase.donation_type,
    func.count(Purchase.id).label('count'),
    func.sum(Purchase.amount).label('total')
).group_by(Purchase.donation_type).all()

# Gruppenspenden mit Vers-Details
group_donations_with_verses = db.session.query(Purchase, BibelVerse).join(
    BibelVerse, Purchase.verse_id == BibelVerse.id
).filter(Purchase.donation_type == DonationType.GROUP).all()
```

## Backup & Recovery

### Daten-Export für Gruppenspenden

```sql
-- Export aller Gruppenspenden
SELECT 
    p.id,
    p.donation_type,
    p.group_article,
    p.group_name,
    p.amount,
    p.created_at,
    bv.reference as verse_reference,
    bv.text_schlachter as verse_text
FROM purchase p
JOIN bibelverse bv ON p.verse_id = bv.id
WHERE p.donation_type = 'group'
ORDER BY p.created_at DESC;
```

## Performance Considerations

1. **Minimale Schema-Änderungen**: Nur 3 neue Spalten
2. **Keine JOIN-Performance-Impact**: Alle Daten in einer Tabelle
3. **Effiziente Indizierung**: Gezielte Indexes für Gruppenspenden-Queries
4. **Backward Compatibility**: Bestehende Daten bleiben unberührt

## Zusammenfassung

Das erweiterte Datenmodell:
- ✅ **Minimal invasiv**: Nur 3 neue Spalten
- ✅ **Performant**: Keine zusätzlichen JOINs erforderlich
- ✅ **Konsistent**: Wiederverwendung bestehender Strukturen
- ✅ **Validiert**: Umfassende Constraints und Validierung
- ✅ **Skalierbar**: Unterstützt zukünftige Erweiterungen
- ✅ **Backward Compatible**: Bestehende Daten unverändert