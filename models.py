"""
Database models for NGÜ Bible Verse Sponsoring App
Using SQLAlchemy with PostgreSQL
"""

from datetime import datetime, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError

db = SQLAlchemy()

# Initialize Argon2 password hasher with secure defaults
ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=1,      # Number of threads
    hash_len=32,        # Length of hash in bytes
    salt_len=16         # Length of salt in bytes
)

class Verse(db.Model):
    """Bible verses with sponsorship status"""
    __tablename__ = 'verses'
    
    id = db.Column(db.Integer, primary_key=True)
    book = db.Column(db.String(50), nullable=False)
    chapter = db.Column(db.Integer, nullable=False)
    verse = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    positivity_score = db.Column(db.Integer)  # 0-100
    is_sponsored = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='verse', lazy='dynamic')
    donation_cart_items = db.relationship('DonationCartItem', backref='verse', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('book', 'chapter', 'verse', name='uq_verse_reference'),
        Index('idx_verse_book_chapter', 'book', 'chapter'),
        Index('idx_verse_positivity', 'positivity_score'),
        Index('idx_verse_sponsored', 'is_sponsored'),
    )
    
    def __repr__(self):
        return f'<Vers {self.book} {self.chapter},{self.verse}>'
    
    @property
    def reference(self):
        """Human-readable verse reference"""
        return f"{self.book} {self.chapter},{self.verse}"
    
    @property
    def short_text(self, max_length=100):
        """Truncated text for display"""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."


class User(db.Model):
    """Optional user accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal data
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    salutation = db.Column(db.String(20))      # Herr, Frau, Eheleute, Firma, keine
    title = db.Column(db.String(50))           # Dr., Prof., etc.
    
    # Address data
    street = db.Column(db.String(200))
    house_number = db.Column(db.String(10))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country = db.Column(db.String(2), default='DE')
    
    # Account settings
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    newsletter_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
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
        """Check if user has complete address data"""
        return all([self.street, self.postal_code, self.city, self.country])
    
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
            
            # Check if password needs rehashing (parameters updated)
            if ph.check_needs_rehash(self.password_hash):
                self.set_password(password)
                db.session.commit()
            
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            return False


class Donation(db.Model):
    """Central donation table for all donation types"""
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL for guest donations
    
    # Donation type and amount
    donation_type = db.Column(db.String(20), nullable=False)  # 'individual', 'group', 'gift'
    amount = db.Column(db.Numeric(6, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR', nullable=False)
    
    # Donor contact data (always required)
    donor_email = db.Column(db.String(255), nullable=False)
    donor_salutation = db.Column(db.String(20))  # Herr, Frau, Eheleute, Firma
    donor_title = db.Column(db.String(50))
    donor_first_name = db.Column(db.String(100))
    donor_last_name = db.Column(db.String(100))
    donor_street = db.Column(db.String(200))
    donor_house_number = db.Column(db.String(10))
    donor_postal_code = db.Column(db.String(10))
    donor_city = db.Column(db.String(100))
    donor_country = db.Column(db.String(2), default='DE')
    
    # Type-specific fields
    group_name = db.Column(db.String(200))  # Only for 'group'
    group_article = db.Column(db.String(10))  # Der/Die/Das/kein
    
    gift_recipient_name = db.Column(db.String(200))  # Only for 'gift'
    gift_recipient_email = db.Column(db.String(255))
    gift_message = db.Column(db.Text)
    gift_direct_send = db.Column(db.Boolean, default=True)
    
    # Preferences
    wants_receipt = db.Column(db.Boolean, default=True, nullable=False)
    newsletter_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    privacy_consent = db.Column(db.Boolean, nullable=False)
    
    # Status and metadata
    payment_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, failed, cancelled
    certificate_generated = db.Column(db.Boolean, default=False, nullable=False)
    receipt_generated = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    certificates = db.relationship('Certificate', backref='donation', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('PaymentTransaction', uselist=False, backref='donation', cascade='all, delete-orphan')
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_donation_status', 'payment_status'),
        Index('idx_donation_type', 'donation_type'),
        Index('idx_donation_email', 'donor_email'),
        Index('idx_donation_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Donation {self.id}: {self.donation_type} - {self.verse.reference}>'
    
    @property
    def donor_full_name(self):
        """Full donor name for display"""
        if self.donor_first_name and self.donor_last_name:
            name_parts = []
            if self.donor_salutation and self.donor_salutation != 'keine':
                name_parts.append(self.donor_salutation)
            if self.donor_title:
                name_parts.append(self.donor_title)
            name_parts.extend([self.donor_first_name, self.donor_last_name])
            return " ".join(name_parts)
        return self.donor_email
    
    @property
    def donor_address(self):
        """Complete donor address"""
        if not all([self.donor_street, self.donor_postal_code, self.donor_city]):
            return None
        
        address_parts = [
            f"{self.donor_street} {self.donor_house_number}".strip(),
            f"{self.donor_postal_code} {self.donor_city}"
        ]
        return "\n".join(address_parts)
    
    @property
    def display_name(self):
        """Name for certificate display"""
        if self.donation_type == 'group':
            if self.group_article and self.group_article != 'kein':
                return f"{self.group_article} {self.group_name}"
            return self.group_name
        elif self.donation_type == 'gift':
            return self.gift_recipient_name
        else:
            return self.donor_full_name
    
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
        # Also mark payment as confirmed if exists
        if self.payment:
            self.payment.mark_confirmed()
        db.session.commit()
    
    def mark_failed(self, error_message=None):
        """Mark donation as failed"""
        self.payment_status = 'failed'
        # Also mark payment as failed if exists
        if self.payment:
            self.payment.mark_failed(error_message)
        db.session.commit()
    
    def create_payment_transaction(self, provider='stripe'):
        """Create a new payment transaction for this donation"""
        if not self.payment:
            self.payment = PaymentTransaction(donation_id=self.id, provider=provider)
            db.session.add(self.payment)
            db.session.commit()
        return self.payment


class PaymentTransaction(db.Model):
    """Payment transaction details for external payment providers"""
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    
    # Provider info (future-proofing for multiple providers)
    provider = db.Column(db.String(20), default='stripe', nullable=False)  # stripe, paypal, etc.
    provider_transaction_id = db.Column(db.String(100))  # Generic field for any provider
    
    # Payment Intent (Stripe-specific)
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_client_secret = db.Column(db.String(200))
    stripe_status = db.Column(db.String(20))                   # Original Stripe PaymentIntent status
    
    # Payment Method (Stripe-specific)
    stripe_payment_method_id = db.Column(db.String(100))
    stripe_payment_method_type = db.Column(db.String(20))      # card, sepa_debit, etc.
    stripe_setup_future_usage = db.Column(db.String(20))       # on_session, off_session
    
    # Customer Management (Stripe-specific)
    stripe_customer_id = db.Column(db.String(100))
    
    # Receipt Management (Stripe-specific)
    stripe_receipt_url = db.Column(db.String(500))
    stripe_receipt_number = db.Column(db.String(100))
    
    # Fee Tracking (provider-agnostic)
    provider_fee_amount = db.Column(db.Numeric(6, 2))          # Provider's fee in EUR/CHF
    net_amount = db.Column(db.Numeric(6, 2))                   # Amount after fees
    
    # Refund Management
    refund_status = db.Column(db.String(20), default='none')   # none, partial, full
    refund_amount = db.Column(db.Numeric(6, 2))
    refunded_at = db.Column(db.DateTime)
    stripe_refund_id = db.Column(db.String(100))               # Stripe-specific refund ID
    
    # Error & Retry Management
    last_error = db.Column(db.Text)                            # Generic error field
    stripe_last_error = db.Column(db.Text)                     # Stripe-specific error details
    retry_count = db.Column(db.Integer, default=0)
    
    # Metadata & Configuration
    provider_metadata = db.Column(db.JSON)                     # Generic metadata field
    stripe_metadata = db.Column(db.JSON)                       # Stripe-specific metadata
    statement_descriptor = db.Column(db.String(22))            # Custom text on credit card statement
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)                      # When payment was confirmed
    failed_at = db.Column(db.DateTime)                         # When payment failed
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_payment_provider', 'provider'),
        Index('idx_payment_status', 'stripe_status'),
        Index('idx_payment_stripe_intent', 'stripe_payment_intent_id'),
        Index('idx_payment_customer', 'stripe_customer_id'),
        Index('idx_payment_refund_status', 'refund_status'),
        Index('idx_payment_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PaymentTransaction {self.id}: {self.provider} for Donation {self.donation_id}>'
    
    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.stripe_status == 'succeeded' if self.provider == 'stripe' else False
    
    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.stripe_status in ['failed', 'canceled'] if self.provider == 'stripe' else False
    
    @property
    def is_refunded(self):
        """Check if payment has been refunded"""
        return self.refund_status in ['partial', 'full']
    
    @property
    def effective_amount(self):
        """Amount after refunds"""
        if self.refund_amount and self.donation:
            return self.donation.amount - self.refund_amount
        return self.donation.amount if self.donation else 0
    
    def mark_confirmed(self):
        """Mark payment as confirmed"""
        self.confirmed_at = datetime.utcnow()
        if self.provider == 'stripe':
            self.stripe_status = 'succeeded'
        db.session.commit()
    
    def mark_failed(self, error_message=None):
        """Mark payment as failed"""
        self.failed_at = datetime.utcnow()
        self.retry_count += 1
        if error_message:
            self.last_error = error_message
            if self.provider == 'stripe':
                self.stripe_last_error = error_message
        if self.provider == 'stripe':
            self.stripe_status = 'failed'
        db.session.commit()
    
    def update_stripe_data(self, payment_intent):
        """Update with data from Stripe PaymentIntent object"""
        self.stripe_payment_intent_id = payment_intent.id
        self.provider_transaction_id = payment_intent.id  # Generic field
        self.stripe_client_secret = payment_intent.client_secret
        self.stripe_status = payment_intent.status
        
        if hasattr(payment_intent, 'payment_method'):
            self.stripe_payment_method_id = payment_intent.payment_method
        if hasattr(payment_intent, 'payment_method_types') and payment_intent.payment_method_types:
            self.stripe_payment_method_type = payment_intent.payment_method_types[0]
        if hasattr(payment_intent, 'setup_future_usage'):
            self.stripe_setup_future_usage = payment_intent.setup_future_usage
        if hasattr(payment_intent, 'last_payment_error') and payment_intent.last_payment_error:
            error_msg = str(payment_intent.last_payment_error)
            self.stripe_last_error = error_msg
            self.last_error = error_msg
            
        if hasattr(payment_intent, 'charges') and payment_intent.charges.data:
            charge = payment_intent.charges.data[0]
            if hasattr(charge, 'balance_transaction'):
                # Fee and net amount from Stripe (convert from cents)
                self.provider_fee_amount = charge.balance_transaction.fee / 100
                self.net_amount = charge.balance_transaction.net / 100
            if hasattr(charge, 'receipt_url'):
                self.stripe_receipt_url = charge.receipt_url
            if hasattr(charge, 'receipt_number'):
                self.stripe_receipt_number = charge.receipt_number
        
        db.session.commit()
    
    def process_refund(self, refund_amount, refund_id=None):
        """Process a refund for this payment transaction"""
        self.refund_amount = refund_amount
        self.refunded_at = datetime.utcnow()
        
        if self.provider == 'stripe' and refund_id:
            self.stripe_refund_id = refund_id
        
        # Determine refund status
        if self.donation and refund_amount >= self.donation.amount:
            self.refund_status = 'full'
            # Mark verse as available again for full refunds
            self.donation.verse.is_sponsored = False
        else:
            self.refund_status = 'partial'
        
        db.session.commit()


class Certificate(db.Model):
    """Generated certificates and receipts"""
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    certificate_type = db.Column(db.String(30), nullable=False)  # personal_certificate, group_certificate, gift_certificate, tax_receipt
    filename = db.Column(db.String(255), nullable=False)         # Nur Dateiname (ohne Pfad)
    file_path = db.Column(db.String(500), nullable=False)        # Vollständiger absoluter Pfad
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    __table_args__ = (
        Index('idx_certificate_type', 'certificate_type'),
        Index('idx_certificate_generated', 'generated_at'),
        Index('idx_certificate_donation', 'donation_id'),
    )
    
    def __repr__(self):
        return f'<Certificate {self.certificate_type} for Donation {self.donation_id}>'
    
    @property
    def is_sent(self):
        """Check if certificate was sent"""
        return self.sent_at is not None
    
    @property
    def exists_on_disk(self):
        """Check if PDF file actually exists on filesystem"""
        import os
        return os.path.exists(self.file_path)
    
    def mark_sent(self):
        """Mark certificate as sent"""
        self.sent_at = datetime.utcnow()
        db.session.commit()
    
    def delete_file(self):
        """Delete PDF file from filesystem"""
        import os
        if self.exists_on_disk:
            os.remove(self.file_path)
    
    @classmethod
    def get_valid_types(cls):
        """Get list of valid certificate types"""
        return [
            'personal_certificate',
            'group_certificate', 
            'gift_certificate',
            'tax_receipt'
        ]


class DonationCartItem(db.Model):
    """Session-based donation cart items"""
    __tablename__ = 'donation_cart'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    donation_type = db.Column(db.String(20), nullable=False)
    
    # Flexible temporary data storage
    temp_data = db.Column(JSONB)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    __table_args__ = (
        Index('idx_cart_session', 'session_id'),
        Index('idx_cart_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f'<DonationCartItem {self.session_id}: {self.verse.reference}>'
    
    @property
    def is_expired(self):
        """Check if cart item is expired"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired cart items"""
        expired_items = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for item in expired_items:
            db.session.delete(item)
        db.session.commit()
        return len(expired_items)


# Database utility functions
def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()


def import_all_verses():
    """Import all ~11,000 Old Testament verses from verses.json with positivity scores"""
    import json
    import os
    
    # Path to verses.json
    verses_file = os.path.join(os.path.dirname(__file__), 'data', 'verses', 'verses.json')
    
    if not os.path.exists(verses_file):
        print(f"Error: {verses_file} not found!")
        return
    
    print(f"Loading verses from {verses_file}...")
    
    with open(verses_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get verses from JSON (skip metadata)
    verses_data = data.get('verses', [])
    
    print(f"Found {len(verses_data)} verses to import...")
    
    imported_count = 0
    skipped_count = 0
    
    for verse_data in verses_data:
        # Check if verse already exists
        existing = Verse.query.filter_by(
            book=verse_data['book'],
            chapter=verse_data['chapter'],
            verse=verse_data['verse_number']
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Create new verse
        verse = Verse(
            book=verse_data['book'],
            chapter=verse_data['chapter'],
            verse=verse_data['verse_number'],
            text=verse_data['text'],
            positivity_score=verse_data['positivity_score']
        )
        
        db.session.add(verse)
        imported_count += 1
        
        # Commit in batches of 1000 for better performance
        if imported_count % 1000 == 0:
            db.session.commit()
            print(f"Imported {imported_count} verses...")
    
    # Final commit
    db.session.commit()
    
    print(f"Import completed!")
    print(f"- Imported: {imported_count} verses")
    print(f"- Skipped (already existed): {skipped_count} verses")
    print(f"- Total verses in database: {Verse.query.count()}")


