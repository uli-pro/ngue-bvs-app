# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Database models for NGÜ Bible Verse Sponsoring App - Simplified Version
Single donation type only (Einzelspenden)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, UniqueConstraint, text, func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector


db = SQLAlchemy()

class Person(db.Model):
    """Central person management for donors"""
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
    newsletter_consent = db.Column(db.Boolean, default=False, nullable=False)
    
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
            'country': self.country,
            'newsletter_consent': self.newsletter_consent
        }
    
    @classmethod
    def find_or_create(cls, email, **kwargs):
        """Find or create person based on email"""
        email_lower = email.lower()
        person = cls.query.filter_by(email=email_lower).first()
        
        if not person:
            # Creating new person
            person = cls(email=email_lower, **kwargs)
            db.session.add(person)
        else:
            # Update existing person
            changes = {}
            for key, value in kwargs.items():
                if hasattr(person, key) and (value is not None):
                    old_value = getattr(person, key)
                    if old_value != value:
                        changes[key] = {
                            'old': old_value,
                            'new': value
                        }
                        setattr(person, key, value)
            
            if changes:
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
    positivity_pre_boost = db.Column(db.Integer)  # Original score before any boost
    is_sponsored = db.Column(db.Boolean, default=False, nullable=False)
    is_translated = db.Column(db.Boolean, default=False, nullable=False)
    translation_completed_at = db.Column(db.DateTime)
    translation_book_release = db.Column(db.Date)
    sponsored_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - NEW: Many-to-Many with donations
    donation_associations = db.relationship('DonationVerse', backref='verse_obj')
    donations = association_proxy('donation_associations', 'donation')
    
    # Unique constraint for bible references
    __table_args__ = (
        UniqueConstraint('book', 'chapter', 'verse', name='uq_verse_reference'),
    )
    
    def __repr__(self):
        return f'<Verse {self.book} {self.chapter},{self.verse}>'
    
    @property
    def reference(self):
        """Human-readable verse reference"""
        return f"{self.book} {self.chapter},{self.verse}"
    
    @property
    def german_reference(self):
        """German verse reference with German book names"""
        from book_names import get_german_book_name
        german_book = get_german_book_name(self.book)
        return f"{german_book} {self.chapter},{self.verse}"
    
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
    
    @property
    def current_donation(self):
        """Current donation (if sponsored)"""
        if self.donation_associations:
            return self.donation_associations[0].donation
        return None
    
    def find_similar_verses(self, limit=3, positivity_tolerance=10, 
                           use_semantic=True, use_keywords=True):
        """Find semantically and thematically similar verses."""
        if not self.text:
            return []
        
        # Start with all unsponsored verses in positivity range
        min_score = max(0, self.positivity_score - positivity_tolerance)
        max_score = min(100, self.positivity_score + positivity_tolerance)
        
        base_query = self.__class__.query.filter(
            self.__class__.is_sponsored == False,
            self.__class__.id != self.id,
            self.__class__.positivity_score.between(min_score, max_score)
        )
        
        # Use semantic search if available and requested
        if use_semantic and hasattr(self.__class__, 'search_semantic'):
            # Try semantic search first if embeddings are available
            similar_verses = self.__class__.search_semantic(
                embedding=self.text_embedding,  # Use actual embedding
                limit=limit * 2
            )
            
            # Filter to match our criteria
            filtered = [v for v in similar_verses 
                       if not v.is_sponsored 
                       and v.id != self.id
                       and min_score <= (v.positivity_score or 0) <= max_score]
            
            if filtered:
                return filtered[:limit]
        
        # Fallback to hybrid search if available
        if use_keywords and hasattr(self.__class__, 'search_hybrid'):
            # Extract keywords for hybrid search
            keywords = self.extract_keywords(max_keywords=3) if use_keywords else []
            query_text = ' '.join(keywords) if keywords else self.text[:100]
            
            # Use existing hybrid search method
            similar_verses = self.__class__.search_hybrid(
                query_text, 
                embedding=self.text_embedding,
                limit=limit * 2  # Get more to filter
            )
            
            # Filter to match our criteria
            filtered = [v for v in similar_verses 
                       if not v.is_sponsored 
                       and v.id != self.id
                       and min_score <= (v.positivity_score or 0) <= max_score]
            
            if filtered:
                return filtered[:limit]
        
        # Final fallback: just return verses with similar positivity scores
        return base_query.order_by(
            func.abs(self.__class__.positivity_score - self.positivity_score)
        ).limit(limit).all()
    
    def extract_keywords(self, max_keywords=5):
        """Extract important keywords from verse text with religious term priority."""
        if not self.text:
            return []
        
        import re
        
        # German stopwords (comprehensive list)
        stopwords = {
            'der', 'die', 'das', 'und', 'in', 'zu', 'mit', 'auf', 'für', 
            'von', 'ist', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr',
            'ein', 'eine', 'einen', 'dem', 'den', 'des', 'als', 'aber',
            'so', 'da', 'wenn', 'wie', 'auch', 'noch', 'wird', 'war',
            'hat', 'haben', 'dass', 'sich', 'nicht', 'nur', 'alle',
            'am', 'im', 'um', 'an', 'bei', 'nach', 'vor', 'über',
            'unter', 'durch', 'bis', 'dann', 'schon', 'sein', 'seine',
            'ihm', 'ihn', 'ihre', 'mir', 'mich', 'uns', 'euch', 'aus',
            'oder', 'kann', 'will', 'soll', 'muss', 'doch', 'was', 'wer'
        }
        
        # High-priority religious and positive terms
        high_priority_terms = {
            'gott', 'herr', 'jesus', 'christus', 'geist', 'heilig',
            'liebe', 'hoffnung', 'frieden', 'freude', 'gnade', 'segen',
            'vertrauen', 'glauben', 'treue', 'barmherzigkeit', 'güte',
            'hirte', 'vater', 'sohn', 'erlöser', 'retter', 'heiland',
            'ewigkeit', 'himmel', 'königreich', 'erlösung', 'vergebung'
        }
        
        # Clean text and split into words
        text = re.sub(r'[^\w\s]', ' ', self.text.lower())
        words = text.split()
        
        # Categorize words
        priority_keywords = []
        regular_keywords = []
        
        for word in words:
            if (len(word) >= 3 and 
                word not in stopwords and 
                not word.isdigit()):
                
                if word.lower() in high_priority_terms:
                    priority_keywords.append(word.capitalize())
                else:
                    regular_keywords.append(word.capitalize())
        
        # Remove duplicates while preserving order
        def deduplicate(word_list):
            seen = set()
            unique = []
            for word in word_list:
                if word.lower() not in seen:
                    seen.add(word.lower())
                    unique.append(word)
            return unique
        
        priority_keywords = deduplicate(priority_keywords)
        regular_keywords = deduplicate(regular_keywords)
        
        # Combine with priority terms first
        final_keywords = priority_keywords + regular_keywords
        
        return final_keywords[:max_keywords]


class DonationVerse(db.Model):
    """Junction table for Many-to-Many relationship between donations and verses"""
    __tablename__ = 'donation_verses'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id', ondelete='CASCADE'), nullable=False)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    amount = db.Column(db.Numeric(6, 2), default=100.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    verse = db.relationship('Verse', overlaps="donation_associations,verse_obj")
    
    __table_args__ = (
        db.UniqueConstraint('donation_id', 'verse_id'),
    )


class Donation(db.Model):
    """Many-to-Many donations supporting multiple verses"""
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    
    # Person snapshot for historical record
    person_snapshot = db.Column(JSONB, nullable=False)
    
    # Financial - NEW: support for multiple verses
    amount = db.Column(db.Numeric(6, 2), nullable=False, default=100.00)  # For backward compatibility
    verse_count = db.Column(db.Integer, default=1, nullable=False)
    total_amount = db.Column(db.Numeric(8, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR', nullable=False)
    
    # Preferences
    wants_receipt = db.Column(db.Boolean, default=True, nullable=False)
    privacy_consent = db.Column(db.Boolean, nullable=False)
    
    # Status
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    certificate_generated = db.Column(db.Boolean, default=False, nullable=False)
    receipt_generated = db.Column(db.Boolean, default=False, nullable=False)

    # Receipt numbering (legally required per §50 Abs. 1 EStDV)
    receipt_number = db.Column(db.String(30), unique=True, nullable=True, index=True)
    receipt_issued_at = db.Column(db.DateTime, nullable=True)
    
    # Email tracking
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)

    # SEPA/Webhook tracking (for idempotency and storno handling)
    certificate_sent_at = db.Column(db.DateTime, nullable=True)  # When certificate email was sent (idempotency)
    storno_generated = db.Column(db.Boolean, default=False, nullable=False)  # Storno PDF generated
    storno_sent_at = db.Column(db.DateTime, nullable=True)  # When storno email was sent
    failure_reason = db.Column(db.String(255), nullable=True)  # Stripe error message

    # Bulk sponsoring flag (for externally acquired book/chapter sponsorings)
    # These have different pricing (e.g., €2000 for 21 verses instead of €2100)
    # and are excluded from daily report totals
    is_bulk_sponsoring = db.Column(db.Boolean, default=False, nullable=False)

    # Admin comment field for internal notes
    admin_comment = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships - NEW: Many-to-Many with verses
    verse_associations = db.relationship('DonationVerse', backref='donation', cascade='all, delete-orphan')
    verses = association_proxy('verse_associations', 'verse')
    certificates = db.relationship('Certificate', backref='donation', lazy='dynamic')
    payment = db.relationship('PaymentTransaction', uselist=False, backref='donation')
    
    def __repr__(self):
        verse_count = self.verse_count or 0
        return f'<Donation {self.id}: {verse_count} verse{"s" if verse_count != 1 else ""}>'
    
    @property
    def display_name(self):
        """Name for certificate display (simplified - always individual)"""
        snapshot = self.person_snapshot or {}
        first_name = snapshot.get('first_name', '')
        last_name = snapshot.get('last_name', '')
        return f"{first_name} {last_name}".strip() or snapshot.get('email', '')
    
    @property
    def is_completed(self):
        """Check if donation is completed"""
        return self.payment_status == 'completed'
    
    def mark_completed(self):
        """Mark donation as completed"""
        # Check if already completed to avoid duplicate processing
        if self.payment_status == 'completed':
            return

        self.payment_status = 'completed'
        self.completed_at = datetime.utcnow()

        # Mark all verses as sponsored and collect verse IDs
        verse_ids = []
        for verse_assoc in self.verse_associations:
            verse_assoc.verse.is_sponsored = True
            verse_assoc.verse.sponsored_at = datetime.utcnow()
            verse_ids.append(verse_assoc.verse_id)

        # Clean up reservations for sponsored verses
        if verse_ids:
            VerseReservation.query.filter(
                VerseReservation.verse_id.in_(verse_ids)
            ).delete(synchronize_session=False)

        # Update person's last donation date
        if self.person:
            self.person.last_donation_at = datetime.utcnow()
        if self.payment:
            self.payment.mark_confirmed()
        db.session.commit()

    def mark_verses_sponsored(self):
        """Mark verses as sponsored without changing payment status.

        Used for SEPA "Optimistic Completion" pattern where we want to
        sponsor verses immediately at 'processing' status, before the
        payment is fully confirmed (which happens 5-6 days later).

        Unlike mark_completed(), this does NOT:
        - Change payment_status to 'completed'
        - Set completed_at timestamp
        - Call payment.mark_confirmed()
        """
        now = datetime.utcnow()
        verse_ids = []
        for verse_assoc in self.verse_associations:
            if not verse_assoc.verse.is_sponsored:
                verse_assoc.verse.is_sponsored = True
                verse_assoc.verse.sponsored_at = now
            verse_ids.append(verse_assoc.verse_id)

        # Clean up reservations for sponsored verses
        if verse_ids:
            VerseReservation.query.filter(
                VerseReservation.verse_id.in_(verse_ids)
            ).delete(synchronize_session=False)

        # Update person's last donation date
        if self.person:
            self.person.last_donation_at = now

    def mark_failed(self, error_message=None):
        """Mark donation as failed and release verses"""
        # Check if already failed to avoid duplicate processing
        if self.payment_status == 'failed':
            return

        self.payment_status = 'failed'

        # Mark all verses as available again and collect verse IDs
        verse_ids = []
        for verse_assoc in self.verse_associations:
            verse_assoc.verse.is_sponsored = False
            verse_assoc.verse.sponsored_at = None
            verse_ids.append(verse_assoc.verse_id)

        # Clean up any lingering reservations (verses are now free)
        if verse_ids:
            VerseReservation.query.filter(
                VerseReservation.verse_id.in_(verse_ids)
            ).delete(synchronize_session=False)

        # Store error message in dedicated field
        if error_message:
            self.failure_reason = error_message[:255]  # Truncate to field length

        db.session.commit()

    def mark_disputed(self, reason=None):
        """Mark donation as disputed (chargeback) and release verses"""
        # Check if already disputed to avoid duplicate processing
        if self.payment_status == 'disputed':
            return

        self.payment_status = 'disputed'

        # Mark all verses as available again and collect verse IDs
        verse_ids = []
        for verse_assoc in self.verse_associations:
            verse_assoc.verse.is_sponsored = False
            verse_assoc.verse.sponsored_at = None
            verse_ids.append(verse_assoc.verse_id)

        # Clean up any lingering reservations (verses are now free)
        if verse_ids:
            VerseReservation.query.filter(
                VerseReservation.verse_id.in_(verse_ids)
            ).delete(synchronize_session=False)

        # Store dispute reason
        if reason:
            self.failure_reason = f"Dispute: {reason}"[:255]

        db.session.commit()
    
    # Helper Methods for Many-to-Many verses
    def add_verse(self, verse, amount=100.00):
        """Add a verse to this donation"""
        from decimal import Decimal
        dv = DonationVerse(donation=self, verse=verse, amount=Decimal(str(amount)))
        self.verse_associations.append(dv)
        # Note: verse_count is set during donation creation and should not be recalculated here
        # to avoid double-counting issues
        # Don't recalculate total_amount here - it's already set correctly in stripe_service.py
        return dv
        
    def get_verses_sorted(self):
        """Get verses sorted by biblical order (book, chapter, verse)"""
        # Über verse_associations gehen für zuverlässigen Zugriff
        verses = [assoc.verse for assoc in self.verse_associations]
        return sorted(verses, key=lambda v: (v.book, v.chapter, v.verse))
    
    @property
    def has_multiple_verses(self):
        """Check if this donation has multiple verses"""
        return self.verse_count > 1

    @classmethod
    def cleanup_orphaned_pending(cls, max_age_hours=24):
        """Delete orphaned pending donations older than max_age_hours.

        Orphaned donations occur when:
        - User starts checkout but abandons it
        - User starts checkout but payment fails without webhook
        - Session expires before payment completion

        Args:
            max_age_hours: Maximum age in hours for pending donations (default: 24)

        Returns:
            int: Number of deleted donations
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        # Find old pending donations with row-level locking (skip locked rows)
        old_pending = cls.query.filter(
            cls.payment_status == 'pending',
            cls.created_at < cutoff
        ).with_for_update(skip_locked=True).all()

        if not old_pending:
            return 0

        count = len(old_pending)
        for donation in old_pending:
            # Collect verse IDs for reservation cleanup
            verse_ids = [dv.verse_id for dv in donation.verse_associations]

            # Clean up any lingering reservations for these verses
            if verse_ids:
                VerseReservation.query.filter(
                    VerseReservation.verse_id.in_(verse_ids)
                ).delete(synchronize_session=False)

            # Delete associated PaymentTransaction first (NOT NULL constraint)
            if donation.payment:
                db.session.delete(donation.payment)

            # Delete donation (CASCADE will delete DonationVerse records)
            db.session.delete(donation)

        db.session.commit()
        return count


class MagicLinkToken(db.Model):
    """Magic Link Tokens für Admin-Authentication (vorbereitet)"""
    __tablename__ = 'magic_link_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def is_valid(self):
        """Check if token is still valid"""
        return (not self.used and 
                datetime.utcnow() < self.expires_at)
    
    def mark_used(self, ip_address=None):
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address
        db.session.commit()

    def __repr__(self):
        return f'<MagicLinkToken {self.token[:8]}... for {self.email}>'


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
    
    def update_stripe_data(self, payment_intent):
        """Update transaction with Stripe PaymentIntent data"""
        # Handle both Stripe objects and webhook dictionaries
        if isinstance(payment_intent, dict):
            self.stripe_payment_intent_id = payment_intent.get('id')
            self.stripe_status = payment_intent.get('status')
            self.provider_transaction_id = payment_intent.get('id')
        else:
            self.stripe_payment_intent_id = payment_intent.id
            self.stripe_status = payment_intent.status
            self.provider_transaction_id = payment_intent.id
    
    def mark_failed(self, error_message=None):
        """Mark payment transaction as failed"""
        self.stripe_status = 'failed'

class Certificate(db.Model):
    """Generated certificates and receipts"""
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    certificate_type = db.Column(db.String(30), nullable=False)  # 'sponsorship' or 'receipt'
    version = db.Column(db.Integer, default=1)
    includes_ngue_text = db.Column(db.Boolean, default=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    @property
    def exists_on_disk(self):
        """Check if PDF file actually exists"""
        import os
        return os.path.exists(self.file_path) if self.file_path else False
    
    @property
    def file_size(self):
        """File size in bytes"""
        import os
        if self.exists_on_disk:
            return os.path.getsize(self.file_path)
        return 0
    
    def delete_file(self):
        """Delete PDF file from filesystem"""
        import os
        if self.exists_on_disk:
            try:
                os.remove(self.file_path)
                return True
            except OSError:
                return False
        return True
    
    def get_download_url(self):
        """Generate secure download URL"""
        return f"/download/certificate/{self.id}"
    
    def validate_file_path(self):
        """Validate file_path for security"""
        import os
        if not self.file_path:
            return False
        
        # Only allowed characters
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./\\')
        if not all(c in allowed_chars for c in self.file_path):
            return False
            
        # No path traversal
        normalized = os.path.normpath(self.file_path)
        if '..' in normalized:
            return False
            
        return True
    
    @classmethod
    def find_by_donation_and_type(cls, donation_id: int, certificate_type: str):
        """Find Certificate by Donation and Type"""
        return cls.query.filter_by(
            donation_id=donation_id,
            certificate_type=certificate_type
        ).first()
    
    @classmethod
    def cleanup_orphaned_files(cls):
        """Delete PDF files without corresponding DB record"""
        import os
        from flask import current_app
        
        base_path = current_app.config.get('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')
        if not os.path.exists(base_path):
            return 0
            
        deleted_count = 0
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    
                    # Check if Certificate record exists
                    certificate = cls.query.filter_by(file_path=file_path).first()
                    if not certificate:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except OSError:
                            pass
        
        return deleted_count
    
    def __repr__(self):
        return f'<Certificate {self.id}: {self.certificate_type} for Donation {self.donation_id}>'


class ReceiptCounter(db.Model):
    """
    Tracks receipt numbers per year for tax receipts (Spendenbescheinigungen).

    Format: ngue-bvs-{year}-{number:04d}
    Example: ngue-bvs-2025-0001

    Counter resets to 1 at the beginning of each year.
    """
    __tablename__ = 'receipt_counters'

    year = db.Column(db.Integer, primary_key=True, nullable=False)
    last_number = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ReceiptCounter year={self.year} last_number={self.last_number}>'

    @staticmethod
    def get_next_receipt_number(auto_commit=True):
        """
        Generates the next receipt number in format: ngue-bvs-YYYY-NNNN

        Thread-safe implementation using database-level locking.

        Args:
            auto_commit: If True, commits the transaction. If False, only flushes
                        (for use within atomic operations).

        Returns:
            str: Receipt number (e.g., 'ngue-bvs-2025-0001')

        Raises:
            Exception: If database transaction fails
        """
        import logging
        logger = logging.getLogger(__name__)

        current_year = datetime.utcnow().year

        try:
            # Use SELECT FOR UPDATE to prevent race conditions
            counter = db.session.query(ReceiptCounter).filter_by(
                year=current_year
            ).with_for_update().first()

            if not counter:
                # Create new counter for this year
                counter = ReceiptCounter(year=current_year, last_number=1)
                db.session.add(counter)
                db.session.flush()  # Get the ID before commit
                next_number = 1
            else:
                # Increment existing counter
                counter.last_number += 1
                counter.updated_at = datetime.utcnow()
                next_number = counter.last_number

            # Commit or flush depending on context
            if auto_commit:
                db.session.commit()
            else:
                db.session.flush()

            # Format: ngue-bvs-YYYY-NNNN
            receipt_number = f"ngue-bvs-{current_year}-{next_number:04d}"

            logger.info(f"Generated receipt number: {receipt_number}")
            return receipt_number

        except Exception as e:
            if auto_commit:
                db.session.rollback()
            logger.error(f"Error generating receipt number: {e}")
            raise


class TranslationNotification(db.Model):
    """Notifications for translated verses - granular per verse"""
    __tablename__ = 'translation_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_verse_id = db.Column(db.Integer, db.ForeignKey('donation_verses.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    notification_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donation_verse = db.relationship('DonationVerse', backref='notifications')
    
    # Helper properties for easy access
    @property
    def donation(self):
        """Get the donation this notification belongs to"""
        return self.donation_verse.donation
    
    @property
    def verse(self):
        """Get the specific verse this notification is for"""
        return self.donation_verse.verse
    
    @property
    def amount(self):
        """Get the amount donated for this specific verse"""
        return self.donation_verse.amount

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
        """Clear all reservations for a session"""
        count = cls.query.filter_by(session_id=session_id).count()
        cls.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        return count


class AdminToken(db.Model):
    """Magic Link Tokens für Admin-Login"""
    __tablename__ = 'admin_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    
    @classmethod
    def create_token(cls, email, ip_address=None):
        """Create new magic link token"""
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        admin_token = cls(
            token=token,
            email=email,
            expires_at=expires_at,
            ip_address=ip_address
        )
        db.session.add(admin_token)
        db.session.commit()
        return admin_token
    
    @classmethod
    def verify_token(cls, token):
        """Verify and invalidate token"""
        admin_token = cls.query.filter_by(
            token=token,
            used=False
        ).first()
        
        if not admin_token:
            return None
            
        if admin_token.expires_at < datetime.utcnow():
            return None
        
        # Mark as used
        admin_token.used = True
        admin_token.used_at = datetime.utcnow()
        db.session.commit()
        
        return admin_token
    
    @classmethod
    def cleanup_expired(cls):
        """Delete expired tokens"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        cls.query.filter(cls.created_at < cutoff).delete()
        db.session.commit()


class BookPriority(db.Model):
    """
    Manages book prioritization boosts for verse selection.

    Stores boost configuration and applies transformations to verses table.
    One active boost per book (enforced by UNIQUE constraint on book_code).
    """
    __tablename__ = 'book_priorities'

    id = db.Column(db.Integer, primary_key=True)
    book_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    boost_value = db.Column(db.Integer, nullable=False)  # -25 to +25
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, index=True)

    @classmethod
    def apply_boost(cls, book_code, boost_value, reason=None, admin_email=None):
        """
        Applies boost to all verses of a book by updating positivity_score in DB.

        Process:
        1. Ensure positivity_pre_boost is set for all verses (if NULL)
        2. Calculate new scores: pre_boost + boost_value (capped 0-100)
        3. Update positivity_score in verses table
        4. Insert/update BookPriority record

        Args:
            book_code: Book code (e.g., '1KI', '2CH')
            boost_value: Integer from -25 to +25
            reason: Optional explanation
            admin_email: Email of admin making change

        Raises:
            ValueError: If book_code doesn't exist or boost_value out of range
        """

        # Validation
        if not book_code:
            raise ValueError("book_code is required")

        if boost_value < -25 or boost_value > 25:
            raise ValueError("boost_value must be between -25 and +25")

        # Check if book exists
        verse_count = db.session.query(Verse).filter_by(book=book_code).count()
        if verse_count == 0:
            raise ValueError(f"Book code '{book_code}' not found in verses table")

        # 1. Ensure pre_boost is set (only if NULL)
        db.session.execute(
            text("""
            UPDATE verses
            SET positivity_pre_boost = positivity_score
            WHERE book = :book AND positivity_pre_boost IS NULL
            """),
            {"book": book_code}
        )

        # 2. Apply boost (capped at 0 and 100)
        db.session.execute(
            text("""
            UPDATE verses
            SET positivity_score = GREATEST(0, LEAST(positivity_pre_boost + :boost, 100))
            WHERE book = :book
            """),
            {"book": book_code, "boost": boost_value}
        )

        # 3. Insert or update BookPriority record
        existing = cls.query.filter_by(book_code=book_code).first()

        if existing:
            # Update existing record
            existing.boost_value = boost_value
            existing.reason = reason
            existing.created_by = admin_email
            existing.is_active = True
        else:
            # Create new record
            priority = cls(
                book_code=book_code,
                boost_value=boost_value,
                reason=reason,
                created_by=admin_email,
                is_active=True
            )
            db.session.add(priority)

        db.session.commit()

    @classmethod
    def remove_boost(cls, book_code):
        """
        Removes boost by restoring original scores from positivity_pre_boost.

        Process:
        1. Restore positivity_score from positivity_pre_boost
        2. Mark BookPriority record as inactive (soft delete)

        Args:
            book_code: Book code to remove boost from
        """

        # 1. Restore original scores
        db.session.execute(
            text("""
            UPDATE verses
            SET positivity_score = positivity_pre_boost
            WHERE book = :book
            """),
            {"book": book_code}
        )

        # 2. Mark BookPriority as inactive
        priority = cls.query.filter_by(book_code=book_code).first()
        if priority:
            priority.is_active = False

        db.session.commit()

    @classmethod
    def get_active_boosts(cls):
        """
        Returns all active book boosts.

        Returns:
            List of BookPriority objects with is_active=True
        """
        return cls.query.filter_by(is_active=True).order_by(cls.book_code).all()

    @classmethod
    def get_boost_statistics(cls):
        """
        Returns statistics for each boosted book.

        Returns:
            dict: {
                'book_code': {
                    'total_verses': int,
                    'original_avg_score': float,
                    'boosted_avg_score': float,
                    'verses_promoted_to_90': int (how many reached 90+ with boost)
                }
            }
        """

        active_boosts = cls.get_active_boosts()
        stats = {}

        for boost in active_boosts:
            # Query verses for this book
            verses = db.session.query(
                func.count(Verse.id).label('total'),
                func.avg(Verse.positivity_pre_boost).label('orig_avg'),
                func.avg(Verse.positivity_score).label('boost_avg'),
                func.count(
                    db.case(
                        (Verse.positivity_score >= 90, 1),
                        else_=None
                    )
                ).label('promoted')
            ).filter(
                Verse.book == boost.book_code,
                Verse.is_sponsored == False
            ).first()

            stats[boost.book_code] = {
                'total_verses': verses.total,
                'original_avg_score': round(verses.orig_avg, 1) if verses.orig_avg else 0,
                'boosted_avg_score': round(verses.boost_avg, 1) if verses.boost_avg else 0,
                'verses_promoted_to_90': verses.promoted
            }

        return stats

    def __repr__(self):
        active = "active" if self.is_active else "inactive"
        return f'<BookPriority {self.book_code} {self.boost_value:+d} ({active})>'