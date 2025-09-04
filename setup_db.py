#!/usr/bin/env python3
# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Database Setup Script for Production Deployment
NGÜ Bibelvers-Sponsoring App

Funktioniert sowohl lokal als auch im Docker-Container.
Kann mehrfach ausgeführt werden für Datenbank-Reset.

Usage:
    python setup_db.py [--drop-existing] [--import-verses] [--sample-data] [--docker]
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_database(max_retries=30):
    """Wait for database to be ready (important for Docker)"""
    if os.environ.get('DOCKER_DEPLOYMENT'):
        logger.info("Waiting for database to be ready...")
        
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        
        db_url = os.environ.get('SQLALCHEMY_DATABASE_URI')
        if not db_url:
            logger.error("SQLALCHEMY_DATABASE_URI not set!")
            return False
        
        engine = create_engine(db_url)
        
        for i in range(max_retries):
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✓ Database is ready!")
                return True
            except OperationalError:
                logger.info(f"  Waiting for database... ({i+1}/{max_retries})")
                time.sleep(2)
        
        logger.error("Database not available after maximum retries!")
        return False
    return True

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from app import app
from models import db, Person, Verse, Donation, PaymentTransaction, Certificate, TranslationNotification, VerseReservation, MagicLinkToken, DonationVerse, AdminToken
from sqlalchemy import text

def drop_database():
    """Drop all existing tables and extensions"""
    logger.info("Dropping existing database...")
    
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            # Drop custom types and extensions (keep pgvector for reinstall)
            db.session.execute(text("DROP FUNCTION IF EXISTS update_verse_text_search CASCADE"))
            db.session.commit()
            
            logger.info("✓ Database dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            db.session.rollback()

def create_database():
    """Create database structure optimized for production"""
    logger.info("Creating database structure...")
    
    with app.app_context():
        try:
            # Create pgvector extension
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.session.commit()
            logger.info("✓ pgvector extension created")
            
            # Create all tables
            db.create_all()
            db.session.commit()
            logger.info("✓ Tables created successfully")
            
            # Create indexes for performance
            create_indexes_sql = """
            -- Person indexes
            CREATE INDEX IF NOT EXISTS idx_persons_email ON persons(email);
            CREATE INDEX IF NOT EXISTS idx_persons_postal ON persons(postal_code);
            
            -- Verse indexes  
            CREATE INDEX IF NOT EXISTS idx_verse_book_chapter ON verses(book, chapter);
            CREATE INDEX IF NOT EXISTS idx_verse_positivity ON verses(positivity_score DESC) 
                WHERE positivity_score IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_verse_sponsored ON verses(is_sponsored);
            CREATE INDEX IF NOT EXISTS idx_verse_text_search ON verses USING gin(text_search) 
                WHERE text_search IS NOT NULL;
            
            -- Donation indexes
            CREATE INDEX IF NOT EXISTS idx_donations_person ON donations(person_id);
            CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(payment_status);
            CREATE INDEX IF NOT EXISTS idx_donations_email_sent ON donations(email_sent);
            
            -- Donation-Verse junction indexes
            CREATE INDEX IF NOT EXISTS idx_donation_verses_donation ON donation_verses(donation_id);
            CREATE INDEX IF NOT EXISTS idx_donation_verses_verse ON donation_verses(verse_id);
            
            -- Payment indexes
            CREATE INDEX IF NOT EXISTS idx_payment_donation ON payment_transactions(donation_id);
            CREATE INDEX IF NOT EXISTS idx_payment_stripe_intent ON payment_transactions(stripe_payment_intent_id);
            
            -- Certificate indexes
            CREATE INDEX IF NOT EXISTS idx_certificate_donation ON certificates(donation_id);
            
            -- Reservation indexes
            CREATE INDEX IF NOT EXISTS idx_reservation_verse ON verse_reservations(verse_id);
            CREATE INDEX IF NOT EXISTS idx_reservation_expires ON verse_reservations(expires_at);
            
            -- Admin token indexes
            CREATE INDEX IF NOT EXISTS idx_admin_token ON admin_tokens(token);
            CREATE INDEX IF NOT EXISTS idx_admin_token_expires ON admin_tokens(expires_at);
            """
            
            for statement in create_indexes_sql.split(';'):
                if statement.strip():
                    db.session.execute(text(statement))
            db.session.commit()
            logger.info("✓ Indexes created successfully")
            
            # Create text search trigger
            create_trigger_sql = """
            CREATE OR REPLACE FUNCTION update_verse_text_search()
            RETURNS trigger AS $$
            BEGIN
                NEW.text_search := to_tsvector('german', NEW.text);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS verse_text_search_trigger ON verses;
            CREATE TRIGGER verse_text_search_trigger
            BEFORE INSERT OR UPDATE OF text ON verses
            FOR EACH ROW
            EXECUTE FUNCTION update_verse_text_search();
            """
            
            db.session.execute(text(create_trigger_sql))
            db.session.commit()
            logger.info("✓ Triggers created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            db.session.rollback()
            raise

def import_verses():
    """Import verses from verses.json"""
    logger.info("Importing verses from verses.json...")
    
    # Look for verses.json in root directory
    verses_file = Path(__file__).parent / 'verses.json'
    
    if not verses_file.exists():
        logger.error(f"verses.json not found at {verses_file}")
        return False
    
    with open(verses_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if 'scored_verses' in data:
        verses_data = data['scored_verses']
    elif 'verses' in data:
        verses_data = data['verses']
    else:
        logger.error("Unknown verses.json format")
        return False
    
    with app.app_context():
        imported = 0
        batch = []
        batch_size = 1000
        
        for verse_data in verses_data:
            verse = Verse(
                book=verse_data['book'],
                chapter=verse_data['chapter'],
                verse=verse_data.get('verse_number', verse_data.get('verse')),
                text=verse_data['text'],
                positivity_score=verse_data.get('positivity_score'),
                is_sponsored=False,
                is_translated=False
            )
            batch.append(verse)
            
            # Batch insert for performance
            if len(batch) >= batch_size:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                imported += len(batch)
                logger.info(f"  Imported {imported} verses...")
                batch = []
        
        # Import remaining
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            imported += len(batch)
        
        # Update text search vectors
        logger.info("Updating text search vectors...")
        db.session.execute(text("""
            UPDATE verses 
            SET text_search = to_tsvector('german', text)
            WHERE text_search IS NULL
        """))
        db.session.commit()
        
        logger.info(f"✓ Successfully imported {imported} verses")
        return True

def create_sample_data():
    """Create minimal sample data for testing"""
    logger.info("Creating sample data...")
    
    with app.app_context():
        try:
            # Check if sample data already exists
            existing = Person.query.filter_by(email='demo@example.com').first()
            if existing:
                logger.info("Sample data already exists")
                return
            
            # Create sample person
            sample_person = Person(
                email='demo@example.com',
                first_name='Max',
                last_name='Mustermann',
                salutation='Herr',
                street='Musterstraße',
                house_number='42',
                postal_code='12345',
                city='Musterstadt',
                country='DE',
                newsletter_consent=True
            )
            db.session.add(sample_person)
            db.session.flush()
            
            # Create sample completed donation
            donation = Donation(
                person_id=sample_person.id,
                person_snapshot=sample_person.to_snapshot(),
                verse_count=1,
                total_amount=100.00,
                currency='EUR',
                wants_receipt=True,
                privacy_consent=True,
                payment_status='completed',
                completed_at=datetime.utcnow()
            )
            db.session.add(donation)
            db.session.flush()
            
            # Add verse to donation
            verse = Verse.query.first()
            if verse:
                donation_verse = DonationVerse(
                    donation_id=donation.id,
                    verse_id=verse.id,
                    amount=100.00
                )
                db.session.add(donation_verse)
                verse.is_sponsored = True
                verse.sponsored_at = datetime.utcnow()
            
            db.session.commit()
            logger.info("✓ Sample data created successfully")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            db.session.rollback()

def verify_setup():
    """Verify database setup"""
    logger.info("\n=== Verifying Database Setup ===")
    
    with app.app_context():
        try:
            # Check verses
            verse_count = Verse.query.count()
            logger.info(f"✓ Verses in database: {verse_count}")
            
            # Check if text search is working
            test_verse = Verse.query.filter(Verse.text_search.isnot(None)).first()
            if test_verse:
                logger.info("✓ Text search vectors created")
            
            # Check pgvector
            has_vector = db.session.execute(text("""
                SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'
            """)).scalar()
            if has_vector:
                logger.info("✓ pgvector extension installed")
            
            # Check indexes
            index_count = db.session.execute(text("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname NOT LIKE '%_pkey'
            """)).scalar()
            logger.info(f"✓ Custom indexes created: {index_count}")
            
            logger.info("\n=== Database Ready for Production ===")
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Production database setup')
    parser.add_argument('--drop-existing', action='store_true',
                       help='Drop existing database before creating')
    parser.add_argument('--import-verses', action='store_true',
                       help='Import verses from verses.json')
    parser.add_argument('--sample-data', action='store_true',
                       help='Create sample data')
    parser.add_argument('--docker', action='store_true',
                       help='Running in Docker container')
    parser.add_argument('--skip-verification', action='store_true',
                       help='Skip verification step')
    
    args = parser.parse_args()
    
    # Set Docker environment flag
    if args.docker:
        os.environ['DOCKER_DEPLOYMENT'] = '1'
    
    try:
        logger.info("=== NGÜ Production Database Setup ===\n")
        
        # Wait for database if in Docker
        if not wait_for_database():
            sys.exit(1)
        
        if args.drop_existing:
            if not args.docker:  # Only ask for confirmation if not in Docker
                response = input("⚠️  WARNING: This will DELETE all data! Continue? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Setup cancelled.")
                    return
            drop_database()
        
        create_database()
        
        if args.import_verses:
            if not import_verses():
                logger.error("Verse import failed!")
                sys.exit(1)
        
        if args.sample_data:
            create_sample_data()
        
        if not args.skip_verification:
            verify_setup()
        
        logger.info("\n✅ Database setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run vectorization: python vectorize.py")
        logger.info("2. Start the application")
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()