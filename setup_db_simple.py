#!/usr/bin/env python3
"""
Database Setup Script - Modern Many-to-Many Version with Email Service
NGÜ Bibelvers-Sponsoring App

This modern version includes:
- Many-to-Many donation-verse relationships (multiple verses per donation)
- Email service integration with tracking fields
- Magic Link tokens for future admin authentication
- Optimized indexes for performance

Usage:
    python setup_db_simple.py [--drop-existing] [--import-verses] [--sample-data]
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Person, Verse, Donation, PaymentTransaction, Certificate, TranslationNotification, VerseReservation, MagicLinkToken, DonationVerse
from sqlalchemy import text, Index
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def drop_database():
    """Drop all existing tables and extensions"""
    logger.info("Dropping existing database...")
    
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            # Drop custom types and extensions
            db.session.execute(text("DROP EXTENSION IF EXISTS vector CASCADE"))
            db.session.execute(text("DROP FUNCTION IF EXISTS update_verse_text_search CASCADE"))
            db.session.commit()
            
            logger.info("✓ Database dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            db.session.rollback()

def create_database():
    """Create new simplified database structure"""
    logger.info("Creating new simplified database structure...")
    
    with app.app_context():
        try:
            # Create pgvector extension
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.session.commit()
            logger.info("✓ pgvector extension created")
            
            # Create all tables using SQLAlchemy ORM models
            db.create_all()
            db.session.commit()
            logger.info("✓ Tables created successfully from SQLAlchemy models")
            
            # Create custom indexes (optimized for single donation type)
            create_indexes_sql = """
            -- Person indexes
            CREATE INDEX IF NOT EXISTS idx_persons_email ON persons(email);
            CREATE INDEX IF NOT EXISTS idx_persons_postal ON persons(postal_code);
            
            -- Verse indexes
            CREATE INDEX IF NOT EXISTS idx_verse_book_chapter ON verses(book, chapter);
            CREATE INDEX IF NOT EXISTS idx_verse_positivity ON verses(positivity_score DESC) 
                WHERE positivity_score IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_verse_sponsored ON verses(is_sponsored);
            CREATE INDEX IF NOT EXISTS idx_verse_translated ON verses(is_translated);
            CREATE INDEX IF NOT EXISTS idx_verse_text_search ON verses USING gin(text_search) 
                WHERE text_search IS NOT NULL;
            
            -- Many-to-Many donation indexes (updated for new structure)
            CREATE INDEX IF NOT EXISTS idx_donations_person ON donations(person_id);
            CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(payment_status);
            CREATE INDEX IF NOT EXISTS idx_donations_snapshot ON donations USING gin(person_snapshot);
            CREATE INDEX IF NOT EXISTS idx_donations_email_sent ON donations(email_sent);
            
            -- Donation-Verse junction table indexes
            CREATE INDEX IF NOT EXISTS idx_donation_verses_donation ON donation_verses(donation_id);
            CREATE INDEX IF NOT EXISTS idx_donation_verses_verse ON donation_verses(verse_id);
            CREATE INDEX IF NOT EXISTS idx_donation_verses_unique ON donation_verses(donation_id, verse_id);
            
            -- Payment transaction indexes
            CREATE INDEX IF NOT EXISTS idx_payment_donation ON payment_transactions(donation_id);
            CREATE INDEX IF NOT EXISTS idx_payment_provider ON payment_transactions(provider);
            CREATE INDEX IF NOT EXISTS idx_payment_stripe_intent ON payment_transactions(stripe_payment_intent_id) 
                WHERE stripe_payment_intent_id IS NOT NULL;
            
            -- Certificate indexes
            CREATE INDEX IF NOT EXISTS idx_certificate_donation ON certificates(donation_id);
            CREATE INDEX IF NOT EXISTS idx_certificate_type ON certificates(certificate_type);
            
            -- Translation notification indexes
            CREATE INDEX IF NOT EXISTS idx_notifications_status ON translation_notifications(status);
            CREATE INDEX IF NOT EXISTS idx_notifications_person ON translation_notifications(person_id);
            
            -- Verse reservation indexes
            CREATE INDEX IF NOT EXISTS idx_reservation_verse ON verse_reservations(verse_id);
            CREATE INDEX IF NOT EXISTS idx_reservation_session ON verse_reservations(session_id);
            CREATE INDEX IF NOT EXISTS idx_reservation_expires ON verse_reservations(expires_at);
            
            -- Magic Link Token indexes (for future admin system)
            CREATE INDEX IF NOT EXISTS idx_magic_token_email ON magic_link_tokens(email);
            CREATE INDEX IF NOT EXISTS idx_magic_token_expires ON magic_link_tokens(expires_at);
            CREATE INDEX IF NOT EXISTS idx_magic_token_used ON magic_link_tokens(used);
            """
            
            db.session.execute(text(create_indexes_sql))
            db.session.commit()
            logger.info("✓ Custom indexes created successfully")
            
            # Create trigger for automatic text_search updates
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
    """Import verses from JSON file"""
    logger.info("Importing verses...")
    
    # Look for verses.json in the root directory
    verses_file = Path(__file__).parent / 'verses.json'
    
    if not verses_file.exists():
        # Fallback to old location for compatibility
        verses_file = Path(__file__).parent / 'data' / 'verses' / 'verses.json'
        if not verses_file.exists():
            logger.error(f"Verses file not found in root directory or data/verses/")
            logger.error(f"Expected location: {Path(__file__).parent / 'verses.json'}")
            return
    
    with open(verses_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if 'scored_verses' in data:
        verses_data = data['scored_verses']
    elif 'verses' in data:
        verses_data = data['verses']
    else:
        logger.error("Unknown verses JSON format")
        return
    
    with app.app_context():
        imported = 0
        batch = []
        
        for verse_data in verses_data:
            verse_sql = text("""
                INSERT INTO verses (book, chapter, verse, text, positivity_score, is_sponsored, is_translated)
                VALUES (:book, :chapter, :verse, :text, :positivity_score, FALSE, FALSE)
                ON CONFLICT (book, chapter, verse) DO NOTHING
            """)
            
            batch.append({
                'book': verse_data['book'],
                'chapter': verse_data['chapter'],
                'verse': verse_data.get('verse_number', verse_data.get('verse')),
                'text': verse_data['text'],
                'positivity_score': verse_data.get('positivity_score')
            })
            
            # Execute in batches
            if len(batch) >= 1000:
                for verse_params in batch:
                    db.session.execute(verse_sql, verse_params)
                db.session.commit()
                imported += len(batch)
                logger.info(f"  Imported {imported} verses...")
                batch = []
        
        # Import remaining
        if batch:
            for verse_params in batch:
                db.session.execute(verse_sql, verse_params)
            db.session.commit()
            imported += len(batch)
        
        logger.info(f"✓ Imported {imported} verses successfully")

def create_sample_data():
    """Create simplified sample data for testing (only individual donations)"""
    logger.info("Creating simplified sample data...")
    
    with app.app_context():
        try:
            # Create sample person
            existing_person = Person.query.filter_by(email='demo@example.com').first()
            
            if not existing_person:
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
                person_id = sample_person.id
            else:
                person_id = existing_person.id
            
            if person_id:
                logger.info(f"✓ Created/found sample person (ID: {person_id})")
                
                # Create person snapshot for donations
                person_snapshot = {
                    'email': 'demo@example.com',
                    'first_name': 'Max',
                    'last_name': 'Mustermann',
                    'salutation': 'Herr',
                    'street': 'Musterstraße',
                    'house_number': '42',
                    'postal_code': '12345',
                    'city': 'Musterstadt',
                    'country': 'DE',
                    'newsletter_consent': True
                }
                
                # Check if sample donations already exist
                existing_donations = Donation.query.filter_by(person_id=person_id).count()
                
                if existing_donations == 0:
                    # Create first sample donation (completed) - Many-to-Many structure
                    donation1 = Donation(
                        person_id=person_id,
                        person_snapshot=person_snapshot,
                        amount=100.00,
                        verse_count=1,
                        total_amount=100.00,
                        currency='EUR',
                        wants_receipt=True,
                        privacy_consent=True,
                        payment_status='completed',
                        completed_at=datetime.utcnow(),
                        email_sent=True,  # New email tracking field
                        email_sent_at=datetime.utcnow()
                    )
                    db.session.add(donation1)
                    db.session.flush()  # Get the ID
                    
                    # Create verse association for first donation
                    verse_assoc1 = DonationVerse(
                        donation_id=donation1.id,
                        verse_id=1,
                        amount=100.00
                    )
                    db.session.add(verse_assoc1)
                    
                    # Create second sample donation (pending) - Multiple verses
                    donation2 = Donation(
                        person_id=person_id,
                        person_snapshot=person_snapshot,
                        amount=100.00,  # Per verse
                        verse_count=2,
                        total_amount=200.00,
                        currency='EUR',
                        wants_receipt=True,
                        privacy_consent=True,
                        payment_status='pending',
                        email_sent=False
                    )
                    db.session.add(donation2)
                    db.session.flush()  # Get the ID
                    
                    # Create verse associations for second donation
                    verse_assoc2a = DonationVerse(
                        donation_id=donation2.id,
                        verse_id=2,
                        amount=100.00
                    )
                    verse_assoc2b = DonationVerse(
                        donation_id=donation2.id,
                        verse_id=3,
                        amount=100.00
                    )
                    db.session.add(verse_assoc2a)
                    db.session.add(verse_assoc2b)
                    
                    # Create third sample donation (processing)
                    donation3 = Donation(
                        person_id=person_id,
                        person_snapshot=person_snapshot,
                        amount=100.00,
                        verse_count=1,
                        total_amount=100.00,
                        currency='EUR',
                        wants_receipt=False,
                        privacy_consent=True,
                        payment_status='processing',
                        email_sent=False
                    )
                    db.session.add(donation3)
                    db.session.flush()  # Get the ID
                    
                    # Create verse association for third donation
                    verse_assoc3 = DonationVerse(
                        donation_id=donation3.id,
                        verse_id=4,
                        amount=100.00
                    )
                    db.session.add(verse_assoc3)
                
                    # Mark first verse as sponsored
                    verse1 = Verse.query.get(1)
                    if verse1:
                        verse1.is_sponsored = True
                        verse1.sponsored_at = datetime.utcnow()
                    
                    db.session.commit()
                    logger.info("✓ Created 3 sample donations with Many-to-Many verse associations")
                else:
                    logger.info("✓ Sample donations already exist")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            db.session.rollback()

def verify_setup():
    """Verify simplified database setup"""
    logger.info("\n=== Verifying Simplified Database Setup ===")
    
    with app.app_context():
        try:
            # Check tables (should be fewer without user-related tables)
            tables_sql = text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            tables = db.session.execute(tables_sql).fetchall()
            logger.info(f"\n✓ Created {len(tables)} tables:")
            expected_tables = [
                'certificates',
                'donation_verses',  # New Many-to-Many junction table
                'donations', 
                'magic_link_tokens',  # New email service table
                'payment_transactions',
                'persons',
                'sessions',
                'translation_notifications', 
                'verse_reservations',
                'verses'
            ]
            for table in tables:
                table_name = table[0]
                if table_name in expected_tables:
                    logger.info(f"  - {table_name} ✓")
                else:
                    logger.info(f"  - {table_name} (unexpected)")
            
            # Check verses count
            verse_count = db.session.execute(
                text("SELECT COUNT(*) FROM verses")
            ).scalar()
            logger.info(f"\n✓ Imported {verse_count} verses")
            
            # Check donations structure (simplified)
            donations_columns = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'donations' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)).fetchall()
            
            logger.info("\n✓ Donations table structure (simplified):")
            for col_name, col_type in donations_columns:
                # Highlight that donation_type and donation_details are removed
                if col_name in ['donation_type', 'donation_details']:
                    logger.warning(f"  ⚠️  {col_name} should be removed!")
                else:
                    logger.info(f"  - {col_name}: {col_type}")
            
            # Check indexes
            indexes_sql = text("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname NOT LIKE '%_pkey'
                ORDER BY indexname
            """)
            
            indexes = db.session.execute(indexes_sql).fetchall()
            logger.info(f"\n✓ Created {len(indexes)} custom indexes")
            
            # Check pgvector extension
            extensions_sql = text("""
                SELECT extname FROM pg_extension 
                WHERE extname = 'vector'
            """)
            
            extensions = db.session.execute(extensions_sql).fetchall()
            if extensions:
                logger.info("\n✓ pgvector extension installed")
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("MODERN DATABASE READY")
            logger.info("- Many-to-Many donation-verse relationships")
            logger.info("- Email service integration with tracking")
            logger.info("- Magic Link tokens for future admin system")
            logger.info("- No user accounts or login tables")
            logger.info("- Optimized for multiple verses per donation")
            logger.info("="*50)
            
        except Exception as e:
            logger.error(f"Verification error: {e}")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup simplified database (single donation type)')
    parser.add_argument('--drop-existing', action='store_true', 
                       help='Drop existing database before creating')
    parser.add_argument('--import-verses', action='store_true',
                       help='Import verses from JSON file')
    parser.add_argument('--sample-data', action='store_true',
                       help='Create sample data for testing')
    parser.add_argument('--skip-verification', action='store_true',
                       help='Skip verification step')
    
    args = parser.parse_args()
    
    try:
        logger.info("=== NGÜ Modern Database Setup ===")
        logger.info("=== Many-to-Many + Email Service ===\n")
        
        if args.drop_existing:
            response = input("⚠️  WARNING: This will DELETE all existing data! Continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Setup cancelled.")
                return
            drop_database()
        
        create_database()
        
        if args.import_verses:
            import_verses()
        
        if args.sample_data:
            create_sample_data()
        
        if not args.skip_verification:
            verify_setup()
        
        logger.info("\n✅ Modern database setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run vectorization: python vectorize_simple.py")
        logger.info("2. Install Flask-Mail: pip install Flask-Mail")
        logger.info("3. Test email service: python test_email_service.py")
        logger.info("4. Start the app: python app.py")
        logger.info("5. Test email endpoints: curl localhost:5000/api/email/test")
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()