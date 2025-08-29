#!/usr/bin/env python3
"""
Database Setup Script V2 - Clean Setup with New Structure
NGÜ Bibelvers-Sponsoring App

Usage:
    python setup_db_v2.py [--drop-existing] [--import-verses] [--sample-data]
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
from models import db, Person, Verse, Donation, PaymentTransaction, Certificate, TranslationNotification, VerseReservation
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
    """Create new database structure using SQLAlchemy ORM"""
    logger.info("Creating new database structure...")
    
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
            
            # Create custom indexes (beyond what's defined in models)
            create_indexes_sql = """
            -- Additional performance indexes
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
    
    # Look for verses.json in the root directory (same as setup_db_v2.py)
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
                INSERT INTO verses (book, chapter, verse, text, positivity_score)
                VALUES (:book, :chapter, :verse, :text, :positivity_score)
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
                db.session.execute(verse_sql, batch)
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
    """Create sample data for testing"""
    logger.info("Creating sample data...")
    
    with app.app_context():
        try:
            # Create sample person using SQLAlchemy ORM
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
                    city='Musterstadt'
                )
                db.session.add(sample_person)
                db.session.flush()  # Get the ID
                person_id = sample_person.id
            else:
                person_id = existing_person.id
            
            if person_id:
                logger.info(f"✓ Created sample person (ID: {person_id})")
                
                # Create sample donations using SQLAlchemy ORM
                person_snapshot = {
                    'email': 'demo@example.com',
                    'first_name': 'Max',
                    'last_name': 'Mustermann',
                    'street': 'Musterstraße',
                    'house_number': '42',
                    'postal_code': '12345',
                    'city': 'Musterstadt'
                }
                
                # Check if sample donations already exist
                existing_donations = Donation.query.filter_by(person_id=person_id).count()
                
                if existing_donations == 0:
                    # Create first sample donation (completed)
                    donation1 = Donation(
                        person_id=person_id,
                        verse_id=1,
                        donation_type='einzelperson',
                        donation_details={},
                        person_snapshot=person_snapshot,
                        amount=100.00,
                        payment_status='completed',
                        privacy_consent=True
                    )
                    db.session.add(donation1)
                    
                    # Create second sample donation (pending)
                    donation2 = Donation(
                        person_id=person_id,
                        verse_id=2,
                        donation_type='gruppe',
                        donation_details={
                            'group_article': 'Die',
                            'group_name': 'Familie Mustermann'
                        },
                        person_snapshot=person_snapshot,
                        amount=100.00,
                        payment_status='pending',
                        privacy_consent=True
                    )
                    db.session.add(donation2)
                
                    # Mark first verse as sponsored using ORM
                    verse1 = Verse.query.get(1)
                    if verse1:
                        verse1.is_sponsored = True
                        verse1.sponsored_at = datetime.utcnow()
                    
                    db.session.commit()
                    logger.info("✓ Created sample donations")
                else:
                    logger.info("✓ Sample donations already exist")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            db.session.rollback()

def verify_setup():
    """Verify database setup"""
    logger.info("\n=== Verifying Database Setup ===")
    
    with app.app_context():
        try:
            # Check tables
            tables_sql = text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            
            tables = db.session.execute(tables_sql).fetchall()
            logger.info(f"\n✓ Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
            
            # Check verses count
            verse_count = db.session.execute(
                text("SELECT COUNT(*) FROM verses")
            ).scalar()
            logger.info(f"\n✓ Imported {verse_count} verses")
            
            # Check indexes
            indexes_sql = text("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname NOT LIKE '%_pkey'
                ORDER BY indexname
            """)
            
            indexes = db.session.execute(indexes_sql).fetchall()
            logger.info(f"\n✓ Created {len(indexes)} custom indexes")
            
            # Check extensions
            extensions_sql = text("""
                SELECT extname FROM pg_extension 
                WHERE extname = 'vector'
            """)
            
            extensions = db.session.execute(extensions_sql).fetchall()
            if extensions:
                logger.info("\n✓ pgvector extension installed")
            
        except Exception as e:
            logger.error(f"Verification error: {e}")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup database with new structure')
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
        logger.info("=== NGÜ Database Setup V2 ===\n")
        
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
        
        logger.info("\n✅ Database setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run vectorization: python vectorize_v2.py")
        logger.info("2. Start the app: python app.py")
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()