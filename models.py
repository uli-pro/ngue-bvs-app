"""
Database models for NGÜ Bible Verse Sponsoring App V2
Using new optimized structure with persons/donations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, UniqueConstraint, text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector

db = SQLAlchemy()

class Person(db.Model):
    """Central person management (replaces User)"""
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    
    # Personal data
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    salutation = db.Column(db.String(20))  # Herr, Frau, Eheleute, Familie, NULL for "Ohne"
    
    # Address data
    street = db.Column(db.String(200))
    house_number = db.Column(db.String(10))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country = db.Column(db.String(2), default='DE')
    
    # Preferences
    # (No preferences currently)
    
    # Metadata
    last_donation_at = db.Column(db.DateTime)
    data_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donations = db.relationship('Donation', backref='person', lazy='dynamic')
    
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
        if self.salutation and self.salutation != 'Ohne':
            name_parts.append(self.salutation)
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
            # Update with new data
            for key, value in kwargs.items():
                if hasattr(person, key) and value:
                    setattr(person, key, value)
            person.data_updated_at = datetime.utcnow()
        
        return person

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
    
    @classmethod
    def search_keyword(cls, query, limit=10):
        """Full-text search using PostgreSQL tsvector"""
        search_query = func.plainto_tsquery('german', query)
        results = cls.query.filter(
            cls.text_search.op('@@')(search_query)
        ).filter(
            cls.is_sponsored == False
        ).order_by(
            func.ts_rank(cls.text_search, search_query).desc()
        ).limit(limit).all()
        return results
    
    @classmethod
    def search_semantic(cls, embedding, limit=10):
        """Semantic search using vector similarity"""
        if embedding is None:
            return []
        
        results = cls.query.filter(
            cls.text_embedding.isnot(None),
            cls.is_sponsored == False
        ).order_by(
            cls.text_embedding.cosine_distance(embedding)
        ).limit(limit).all()
        return results
    
    @classmethod
    def search_hybrid(cls, query, embedding=None, keyword_weight=0.5, limit=10):
        """Hybrid search combining keyword and semantic search"""
        # Dynamic weighting based on query length
        words = query.split()
        if len(words) <= 2:
            keyword_weight = 0.8
        elif len(words) <= 5:
            keyword_weight = 0.5
        else:
            keyword_weight = 0.2
        
        vector_weight = 1 - keyword_weight
        
        # Build the hybrid query
        search_query = func.plainto_tsquery('german', query)
        
        if embedding is not None and vector_weight > 0:
            # Combine keyword and vector scores
            score = (
                keyword_weight * func.ts_rank(cls.text_search, search_query) +
                vector_weight * (1 - cls.text_embedding.cosine_distance(embedding))
            )
        else:
            # Keyword search only
            score = func.ts_rank(cls.text_search, search_query)
        
        results = cls.query.filter(
            cls.text_search.op('@@')(search_query),
            cls.is_sponsored == False
        ).order_by(
            score.desc()
        ).limit(limit).all()
        
        return results

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
    
    def extend_reservation(self, minutes=15):
        """Extend reservation by specified minutes"""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    @classmethod
    def get_active_for_verse(cls, verse_id, exclude_session_id=None):
        """Get active reservations for a verse, optionally excluding a session"""
        query = cls.query.filter(
            cls.verse_id == verse_id,
            cls.expires_at > datetime.utcnow()
        )
        
        if exclude_session_id:
            query = query.filter(cls.session_id != exclude_session_id)
        
        return query.first()
    
    @classmethod
    def create_or_update(cls, verse_id, session_id, minutes=15):
        """Create new reservation or update existing one with race condition protection"""
        try:
            # Check if verse is already sponsored (race condition check)
            verse = Verse.query.filter_by(id=verse_id).with_for_update().first()
            if not verse:
                raise ValueError("Verse not found")
            if verse.is_sponsored:
                raise ValueError("Verse is already sponsored")
            
            # Check if another session has an active reservation
            active_reservation = cls.query.filter(
                cls.verse_id == verse_id,
                cls.session_id != session_id,
                cls.expires_at > datetime.utcnow()
            ).first()
            
            if active_reservation:
                raise ValueError("Verse is currently reserved by another user")
            
            # Check if reservation already exists for this session
            existing = cls.query.filter_by(
                verse_id=verse_id,
                session_id=session_id
            ).first()
            
            if existing:
                # Extend existing reservation
                existing.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
                reservation = existing
            else:
                # Create new reservation
                reservation = cls(
                    verse_id=verse_id,
                    session_id=session_id,
                    expires_at=datetime.utcnow() + timedelta(minutes=minutes)
                )
                db.session.add(reservation)
            
            db.session.commit()
            return reservation
                
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired reservations"""
        expired_count = cls.query.filter(cls.expires_at < datetime.utcnow()).count()
        cls.query.filter(cls.expires_at < datetime.utcnow()).delete()
        db.session.commit()
        return expired_count
    
    @classmethod
    def clear_for_session(cls, session_id):
        """Clear all reservations for a session (e.g., on logout)"""
        count = cls.query.filter_by(session_id=session_id).count()
        cls.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        return count

