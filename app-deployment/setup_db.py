#!/usr/bin/env python3
"""
NGÜ Database Setup Script for Docker Deployment
===============================================

This script sets up the NGÜ app database with the current model structure.
It runs automatically during Docker deployment and:
1. Creates all tables using SQLAlchemy ORM
2. Sets up pgvector extension
3. Creates necessary indexes and triggers
4. Imports verses from verses.json
5. Creates sample data if requested

Environment Variables Required:
    - SQLALCHEMY_DATABASE_URI

Usage:
    python setup_db.py [--sample-data]
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to Python path to import our models
sys.path.insert(0, '/app')

try:
    from models import db, Person, Verse, Donation, PaymentTransaction, Certificate, TranslationNotification, VerseReservation
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError, SQLAlchemyError
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Make sure you're running this from the Docker container with the app mounted")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Handles database setup for NGÜ app deployment"""
    
    def __init__(self):
        self.db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        if not self.db_uri:
            raise ValueError("SQLALCHEMY_DATABASE_URI environment variable required")
        
        self.engine = None
        # Look for verses.json in app-deployment directory
        self.verses_file = Path('/app/app-deployment/verses.json')
        
        if not self.verses_file.exists():
            # Fallback locations
            fallback_paths = [
                Path('/app/verses.json'),
                Path('/app-deployment/verses.json'),
                Path('./verses.json')
            ]
            
            for path in fallback_paths:
                if path.exists():
                    self.verses_file = path
                    break
            else:
                raise FileNotFoundError(f"verses.json not found in expected locations: {[str(p) for p in [self.verses_file] + fallback_paths]}")
        
        logger.info(f"Using verses file: {self.verses_file}")
        
    def connect_with_retry(self, max_retries: int = 30, delay: int = 2):
        """Connect to database with retry logic for container startup"""
        logger.info("Connecting to PostgreSQL database...")
        
        for attempt in range(max_retries):
            try:
                self.engine = create_engine(self.db_uri, pool_pre_ping=True)
                # Test connection
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()[0]
                    logger.info(f"✓ Connected to PostgreSQL: {version}")
                return True
                
            except OperationalError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
        
        return False
    
    def setup_extensions(self):
        """Setup required PostgreSQL extensions"""
        logger.info("Setting up PostgreSQL extensions...")
        
        extensions = [
            ('vector', True),  # Required for embeddings
            ('uuid-ossp', False),  # Optional
            ('pg_trgm', False),  # Optional for text search
            ('unaccent', False)  # Optional for text search
        ]
        
        for ext_name, required in extensions:
            try:
                with self.engine.connect() as conn:
                    if ext_name == 'uuid-ossp':
                        # Handle hyphenated extension name
                        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                    else:
                        conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext_name}"))
                    conn.commit()
                    logger.info(f"✓ Extension '{ext_name}' ready")
            except Exception as e:
                if required:
                    logger.error(f"❌ Required extension '{ext_name}' failed: {e}")
                    raise
                else:
                    logger.warning(f"⚠️  Optional extension '{ext_name}' not available: {e}")
        
        logger.info("✓ Extensions setup completed")
    
    def create_tables(self):
        """Create all database tables using SQLAlchemy ORM"""
        logger.info("Creating database tables...")
        
        # Create a Flask app context to use SQLAlchemy
        from flask import Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = self.db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        with app.app_context():
            db.init_app(app)
            db.create_all()
            logger.info("✓ All tables created via SQLAlchemy ORM")
            
            # Ensure unique constraint exists (SQLAlchemy sometimes misses this)
            with self.engine.connect() as conn:
                try:
                    conn.execute(text("""
                        ALTER TABLE verses 
                        ADD CONSTRAINT uq_verse_reference 
                        UNIQUE (book, chapter, verse)
                    """))
                    conn.commit()
                    logger.info("✓ Unique constraint added to verses table")
                except Exception as e:
                    # Constraint might already exist
                    logger.info("Unique constraint already exists or not needed")
    
    def create_indexes(self):
        """Create additional performance indexes"""
        logger.info("Creating additional indexes...")
        
        indexes_sql = """
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_persons_email ON persons(email);
        CREATE INDEX IF NOT EXISTS idx_persons_postal ON persons(postal_code);
        
        CREATE INDEX IF NOT EXISTS idx_verse_book_chapter ON verses(book, chapter);
        CREATE INDEX IF NOT EXISTS idx_verse_positivity ON verses(positivity_score DESC) WHERE positivity_score IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_verse_sponsored ON verses(is_sponsored);
        CREATE INDEX IF NOT EXISTS idx_verse_translated ON verses(is_translated);
        CREATE INDEX IF NOT EXISTS idx_verse_text_search ON verses USING gin(text_search) WHERE text_search IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_donations_person ON donations(person_id);
        CREATE INDEX IF NOT EXISTS idx_donations_verse ON donations(verse_id);
        CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(payment_status);
        CREATE INDEX IF NOT EXISTS idx_donations_type ON donations(donation_type);
        CREATE INDEX IF NOT EXISTS idx_donations_details ON donations USING gin(donation_details) WHERE donation_details IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_donations_snapshot ON donations USING gin(person_snapshot);
        
        CREATE INDEX IF NOT EXISTS idx_payment_donation ON payment_transactions(donation_id);
        CREATE INDEX IF NOT EXISTS idx_payment_provider ON payment_transactions(provider);
        CREATE INDEX IF NOT EXISTS idx_payment_stripe_intent ON payment_transactions(stripe_payment_intent_id) WHERE stripe_payment_intent_id IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_certificate_donation ON certificates(donation_id);
        CREATE INDEX IF NOT EXISTS idx_certificate_type ON certificates(certificate_type);
        
        CREATE INDEX IF NOT EXISTS idx_notifications_status ON translation_notifications(status);
        CREATE INDEX IF NOT EXISTS idx_notifications_person ON translation_notifications(person_id);
        
        CREATE INDEX IF NOT EXISTS idx_reservation_verse ON verse_reservations(verse_id);
        CREATE INDEX IF NOT EXISTS idx_reservation_session ON verse_reservations(session_id);
        CREATE INDEX IF NOT EXISTS idx_reservation_expires ON verse_reservations(expires_at);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(indexes_sql))
            conn.commit()
            
        logger.info("✓ Additional indexes created")
    
    def create_triggers(self):
        """Create database triggers"""
        logger.info("Creating database triggers...")
        
        trigger_sql = """
        -- Function for automatic text_search updates
        CREATE OR REPLACE FUNCTION update_verse_text_search()
        RETURNS trigger AS $$
        BEGIN
            NEW.text_search := to_tsvector('german', NEW.text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Drop trigger if exists and recreate
        DROP TRIGGER IF EXISTS verse_text_search_trigger ON verses;
        CREATE TRIGGER verse_text_search_trigger
        BEFORE INSERT OR UPDATE OF text ON verses
        FOR EACH ROW
        EXECUTE FUNCTION update_verse_text_search();
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            
        logger.info("✓ Database triggers created")
    
    def check_verses_imported(self) -> int:
        """Check how many verses are already imported"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM verses"))
            count = result.fetchone()[0]
            logger.info(f"Found {count} verses in database")
            return count
    
    def import_verses(self, force_reimport: bool = False):
        """Import verses from JSON file"""
        existing_count = self.check_verses_imported()
        
        if existing_count > 0 and not force_reimport:
            logger.info("Verses already imported, skipping import")
            return True
        
        logger.info(f"Importing verses from {self.verses_file}")
        
        try:
            with open(self.verses_file, 'r', encoding='utf-8') as f:
                verses_data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(verses_data, dict):
                if 'scored_verses' in verses_data:
                    verses_list = verses_data['scored_verses']
                elif 'verses' in verses_data:
                    verses_list = verses_data['verses']
                else:
                    logger.error("Unknown verses JSON format")
                    return False
            else:
                verses_list = verses_data
            
            if not isinstance(verses_list, list):
                logger.error("Invalid verses data format - expected list")
                return False
            
            # Clear existing verses if force reimport
            if force_reimport and existing_count > 0:
                logger.info("Force reimport requested, clearing existing verses...")
                with self.engine.connect() as conn:
                    conn.execute(text("TRUNCATE TABLE verses RESTART IDENTITY CASCADE"))
                    conn.commit()
            
            # Import verses in batches
            batch_size = 1000
            total_verses = len(verses_list)
            logger.info(f"Importing {total_verses} verses in batches of {batch_size}")
            
            with self.engine.connect() as conn:
                for i in range(0, total_verses, batch_size):
                    batch = verses_list[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logger.info(f"Processing batch {batch_num}/{(total_verses + batch_size - 1) // batch_size} ({len(batch)} verses)")
                    
                    # Prepare batch data
                    batch_values = []
                    for verse in batch:
                        batch_values.append({
                            'book': verse.get('book', '').upper(),
                            'chapter': int(verse.get('chapter', 1)),
                            'verse': int(verse.get('verse_number', verse.get('verse', 1))),
                            'text': verse.get('text', ''),
                            'text_ngue': verse.get('text_ngue'),
                            'positivity_score': verse.get('positivity_score'),
                            'is_sponsored': False,
                            'is_translated': bool(verse.get('text_ngue'))
                        })
                    
                    # Execute batch insert
                    insert_query = text("""
                        INSERT INTO verses (
                            book, chapter, verse, text, text_ngue, positivity_score,
                            is_sponsored, is_translated, created_at
                        ) VALUES (
                            :book, :chapter, :verse, :text, :text_ngue, :positivity_score,
                            :is_sponsored, :is_translated, NOW()
                        ) ON CONFLICT (book, chapter, verse) DO NOTHING
                    """)
                    
                    conn.execute(insert_query, batch_values)
                    conn.commit()
                
                # Verify import
                result = conn.execute(text("SELECT COUNT(*) FROM verses"))
                imported_count = result.fetchone()[0]
                logger.info(f"✓ Successfully imported {imported_count} verses")
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing verses: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample data for testing"""
        logger.info("Creating sample data...")
        
        try:
            with self.engine.connect() as conn:
                # Check if sample person exists
                result = conn.execute(
                    text("SELECT id FROM persons WHERE email = 'demo@example.com'")
                )
                existing_person = result.fetchone()
                
                if not existing_person:
                    # Create sample person
                    conn.execute(text("""
                        INSERT INTO persons (
                            email, first_name, last_name, salutation,
                            street, house_number, postal_code, city, country,
                            created_at
                        ) VALUES (
                            'demo@example.com', 'Max', 'Mustermann', 'Herr',
                            'Musterstraße', '42', '12345', 'Musterstadt', 'DE',
                            NOW()
                        )
                    """))
                    
                    # Get the person ID
                    result = conn.execute(
                        text("SELECT id FROM persons WHERE email = 'demo@example.com'")
                    )
                    person_id = result.fetchone()[0]
                else:
                    person_id = existing_person[0]
                
                # Check if sample donations exist
                result = conn.execute(
                    text("SELECT COUNT(*) FROM donations WHERE person_id = :person_id"),
                    {"person_id": person_id}
                )
                existing_donations = result.fetchone()[0]
                
                if existing_donations == 0:
                    # Create sample donations
                    person_snapshot = {
                        'email': 'demo@example.com',
                        'first_name': 'Max',
                        'last_name': 'Mustermann',
                        'street': 'Musterstraße',
                        'house_number': '42',
                        'postal_code': '12345',
                        'city': 'Musterstadt',
                        'country': 'DE'
                    }
                    
                    # First donation (completed)
                    conn.execute(text("""
                        INSERT INTO donations (
                            person_id, verse_id, donation_type, donation_details,
                            person_snapshot, amount, currency, wants_receipt,
                            privacy_consent, payment_status, created_at
                        ) VALUES (
                            :person_id, 1, 'einzelperson', '{}',
                            :person_snapshot::jsonb, 100.00, 'EUR', true,
                            true, 'completed', NOW()
                        )
                    """), {
                        "person_id": person_id,
                        "person_snapshot": json.dumps(person_snapshot)
                    })
                    
                    # Mark first verse as sponsored
                    conn.execute(text("""
                        UPDATE verses 
                        SET is_sponsored = true, sponsored_at = NOW() 
                        WHERE id = 1
                    """))
                    
                conn.commit()
                logger.info("✓ Sample data created")
                
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
    
    def verify_setup(self):
        """Verify the database setup"""
        logger.info("Verifying database setup...")
        
        checks_passed = 0
        total_checks = 5
        
        with self.engine.connect() as conn:
            # Check 1: Tables exist
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('persons', 'verses', 'donations', 'payment_transactions')
                """))
                table_count = result.fetchone()[0]
                if table_count >= 4:
                    logger.info("✓ Required tables exist")
                    checks_passed += 1
                else:
                    logger.error("✗ Missing required tables")
            except Exception as e:
                logger.error(f"✗ Table check failed: {e}")
            
            # Check 2: Verses imported
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM verses"))
                verse_count = result.fetchone()[0]
                if verse_count > 0:
                    logger.info(f"✓ {verse_count} verses imported")
                    checks_passed += 1
                else:
                    logger.error("✗ No verses found")
            except Exception as e:
                logger.error(f"✗ Verse check failed: {e}")
            
            # Check 3: Extensions
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_extension 
                    WHERE extname IN ('vector', 'pg_trgm')
                """))
                ext_count = result.fetchone()[0]
                if ext_count >= 2:
                    logger.info("✓ Required extensions installed")
                    checks_passed += 1
                else:
                    logger.error("✗ Missing required extensions")
            except Exception as e:
                logger.error(f"✗ Extension check failed: {e}")
            
            # Check 4: Indexes
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE schemaname = 'public' 
                    AND indexname LIKE 'idx_%'
                """))
                index_count = result.fetchone()[0]
                if index_count > 10:
                    logger.info(f"✓ {index_count} custom indexes created")
                    checks_passed += 1
                else:
                    logger.error(f"✗ Only {index_count} indexes found")
            except Exception as e:
                logger.error(f"✗ Index check failed: {e}")
            
            # Check 5: Triggers
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.triggers 
                    WHERE trigger_name = 'verse_text_search_trigger'
                """))
                trigger_count = result.fetchone()[0]
                if trigger_count > 0:
                    logger.info("✓ Text search trigger active")
                    checks_passed += 1
                else:
                    logger.error("✗ Text search trigger missing")
            except Exception as e:
                logger.error(f"✗ Trigger check failed: {e}")
        
        logger.info(f"Database setup verification: {checks_passed}/{total_checks} checks passed")
        return checks_passed == total_checks
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup NGÜ database for deployment')
    parser.add_argument('--sample-data', action='store_true', help='Create sample data for testing')
    parser.add_argument('--force-reimport', action='store_true', help='Force reimport of verses data')
    args = parser.parse_args()
    
    setup = None
    try:
        logger.info("🚀 Starting NGÜ database setup...")
        
        setup = DatabaseSetup()
        
        # Connect to database
        if not setup.connect_with_retry():
            logger.error("Failed to connect to database")
            return False
        
        # Setup extensions
        setup.setup_extensions()
        
        # Create tables
        setup.create_tables()
        
        # Create indexes
        setup.create_indexes()
        
        # Create triggers
        setup.create_triggers()
        
        # Import verses
        if not setup.import_verses(force_reimport=args.force_reimport):
            logger.error("Verse import failed")
            return False
        
        # Create sample data if requested
        if args.sample_data:
            setup.create_sample_data()
        
        # Verify setup
        if not setup.verify_setup():
            logger.warning("Some verification checks failed, but continuing...")
        
        logger.info("🎉 Database setup completed successfully!")
        logger.info("Ready for vectorization process...")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    
    finally:
        if setup:
            setup.close()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)