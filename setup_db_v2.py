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
from models import db
from sqlalchemy import text
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
    """Create new database structure"""
    logger.info("Creating new database structure...")
    
    with app.app_context():
        try:
            # Create pgvector extension
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.session.commit()
            logger.info("✓ pgvector extension created")
            
            # Create new tables with updated structure
            create_tables_sql = """
            -- 1. Persons table (replaces users)
            CREATE TABLE IF NOT EXISTS persons (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                salutation VARCHAR(20),
                title VARCHAR(50),
                street VARCHAR(200),
                house_number VARCHAR(10),
                postal_code VARCHAR(10),
                city VARCHAR(100),
                country VARCHAR(2) DEFAULT 'DE',
                newsletter_opt_in BOOLEAN DEFAULT FALSE,
                save_data_consent BOOLEAN DEFAULT TRUE,
                last_donation_at TIMESTAMP,
                data_updated_at TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- 2. Optional person logins
            CREATE TABLE IF NOT EXISTS person_logins (
                person_id INTEGER PRIMARY KEY REFERENCES persons(id),
                password_hash VARCHAR(255) NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- 3. Verses table with NGÜ support
            CREATE TABLE IF NOT EXISTS verses (
                id SERIAL PRIMARY KEY,
                book VARCHAR(50) NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                text_ngue TEXT,
                text_search TSVECTOR,
                text_embedding vector(1536),
                positivity_score INTEGER,
                is_sponsored BOOLEAN DEFAULT FALSE,
                is_translated BOOLEAN DEFAULT FALSE,
                translation_completed_at TIMESTAMP,
                translation_book_release DATE,
                sponsored_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_verse_reference UNIQUE(book, chapter, verse)
            );
            
            -- 4. Donations table (simplified)
            CREATE TABLE IF NOT EXISTS donations (
                id SERIAL PRIMARY KEY,
                person_id INTEGER REFERENCES persons(id) NOT NULL,
                verse_id INTEGER REFERENCES verses(id) NOT NULL,
                donation_type VARCHAR(20) NOT NULL CHECK (
                    donation_type IN ('einzelperson', 'gruppe', 'geschenk')
                ),
                donation_details JSONB,
                person_snapshot JSONB NOT NULL,
                amount NUMERIC(6,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'EUR',
                wants_receipt BOOLEAN DEFAULT TRUE,
                privacy_consent BOOLEAN NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending' CHECK (
                    payment_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded')
                ),
                certificate_generated BOOLEAN DEFAULT FALSE,
                receipt_generated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            );
            
            -- 5. Payment transactions
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id SERIAL PRIMARY KEY,
                donation_id INTEGER REFERENCES donations(id) NOT NULL,
                provider VARCHAR(20) DEFAULT 'stripe' NOT NULL,
                provider_transaction_id VARCHAR(100),
                stripe_payment_intent_id VARCHAR(100),
                stripe_client_secret VARCHAR(200),
                stripe_status VARCHAR(20),
                stripe_payment_method_id VARCHAR(100),
                stripe_payment_method_type VARCHAR(20),
                stripe_customer_id VARCHAR(100),
                stripe_receipt_url VARCHAR(500),
                provider_fee_amount NUMERIC(6,2),
                net_amount NUMERIC(6,2),
                refund_status VARCHAR(20) DEFAULT 'none',
                refund_amount NUMERIC(6,2),
                refunded_at TIMESTAMP,
                last_error TEXT,
                retry_count INTEGER DEFAULT 0,
                provider_metadata JSON,
                created_at TIMESTAMP DEFAULT NOW(),
                confirmed_at TIMESTAMP,
                failed_at TIMESTAMP
            );
            
            -- 6. Certificates
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                donation_id INTEGER REFERENCES donations(id) NOT NULL,
                certificate_type VARCHAR(30) NOT NULL,
                version INTEGER DEFAULT 1,
                includes_ngue_text BOOLEAN DEFAULT FALSE,
                parent_certificate_id INTEGER REFERENCES certificates(id),
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                generated_at TIMESTAMP DEFAULT NOW(),
                sent_at TIMESTAMP
            );
            
            -- 7. Translation notifications
            CREATE TABLE IF NOT EXISTS translation_notifications (
                id SERIAL PRIMARY KEY,
                donation_id INTEGER REFERENCES donations(id) NOT NULL,
                verse_id INTEGER REFERENCES verses(id) NOT NULL,
                person_id INTEGER REFERENCES persons(id) NOT NULL,
                notification_type VARCHAR(30) NOT NULL CHECK (
                    notification_type IN ('verse_translated', 'book_completed', 'testament_completed')
                ),
                status VARCHAR(20) DEFAULT 'pending' CHECK (
                    status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')
                ),
                sent_at TIMESTAMP,
                email_sent_to VARCHAR(255),
                certificate_url VARCHAR(500),
                retry_count INTEGER DEFAULT 0,
                last_error TEXT,
                next_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT unique_donation_notification UNIQUE(donation_id, notification_type)
            );
            
            -- 8. Verse reservations (for checkout)
            CREATE TABLE IF NOT EXISTS verse_reservations (
                id SERIAL PRIMARY KEY,
                verse_id INTEGER REFERENCES verses(id) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                reserved_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '15 minutes')
            );
            
            -- 9. Sessions (Flask sessions)
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE,
                data BYTEA,
                expiry TIMESTAMP
            );
            
            -- 10. Email verification tokens
            CREATE TABLE IF NOT EXISTS verification_tokens (
                id SERIAL PRIMARY KEY,
                person_id INTEGER REFERENCES persons(id) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                token_type VARCHAR(20) DEFAULT 'email_verification',
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours'),
                used BOOLEAN DEFAULT FALSE
            );
            """
            
            db.session.execute(text(create_tables_sql))
            db.session.commit()
            logger.info("✓ Tables created successfully")
            
            # Create indexes
            create_indexes_sql = """
            -- Persons indexes
            CREATE INDEX idx_persons_email ON persons(email);
            CREATE INDEX idx_persons_postal ON persons(postal_code);
            
            -- Verses indexes
            CREATE INDEX idx_verse_book_chapter ON verses(book, chapter);
            CREATE INDEX idx_verse_positivity ON verses(positivity_score DESC);
            CREATE INDEX idx_verse_sponsored ON verses(is_sponsored);
            CREATE INDEX idx_verse_translated ON verses(is_translated);
            CREATE INDEX idx_verse_text_search ON verses USING gin(text_search);
            
            -- Donations indexes
            CREATE INDEX idx_donations_person ON donations(person_id);
            CREATE INDEX idx_donations_verse ON donations(verse_id);
            CREATE INDEX idx_donations_status ON donations(payment_status);
            CREATE INDEX idx_donations_type ON donations(donation_type);
            CREATE INDEX idx_donations_details ON donations USING gin(donation_details);
            CREATE INDEX idx_donations_snapshot ON donations USING gin(person_snapshot);
            
            -- Payment indexes
            CREATE INDEX idx_payment_donation ON payment_transactions(donation_id);
            CREATE INDEX idx_payment_provider ON payment_transactions(provider);
            CREATE INDEX idx_payment_stripe_intent ON payment_transactions(stripe_payment_intent_id);
            
            -- Certificate indexes
            CREATE INDEX idx_certificate_donation ON certificates(donation_id);
            CREATE INDEX idx_certificate_type ON certificates(certificate_type);
            
            -- Notification indexes
            CREATE INDEX idx_notifications_status ON translation_notifications(status, next_retry_at);
            CREATE INDEX idx_notifications_person ON translation_notifications(person_id);
            
            -- Reservation indexes
            CREATE INDEX idx_reservation_verse ON verse_reservations(verse_id);
            CREATE INDEX idx_reservation_session ON verse_reservations(session_id);
            CREATE INDEX idx_reservation_expires ON verse_reservations(expires_at);
            
            -- Token indexes
            CREATE INDEX idx_verification_token ON verification_tokens(token);
            CREATE INDEX idx_verification_expires ON verification_tokens(expires_at);
            """
            
            db.session.execute(text(create_indexes_sql))
            db.session.commit()
            logger.info("✓ Indexes created successfully")
            
            # Create trigger for automatic text_search updates
            create_trigger_sql = """
            CREATE OR REPLACE FUNCTION update_verse_text_search()
            RETURNS trigger AS $$
            BEGIN
                NEW.text_search := to_tsvector('german', NEW.text);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
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
    
    verses_file = Path(__file__).parent / 'data' / 'verses' / 'verses.json'
    
    if not verses_file.exists():
        logger.error(f"Verses file not found: {verses_file}")
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
            # Create sample person
            sample_person_sql = text("""
                INSERT INTO persons (email, first_name, last_name, salutation, 
                                    street, house_number, postal_code, city, 
                                    newsletter_opt_in, save_data_consent)
                VALUES ('demo@example.com', 'Max', 'Mustermann', 'Herr',
                        'Musterstraße', '42', '12345', 'Musterstadt',
                        true, true)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
            """)
            
            result = db.session.execute(sample_person_sql)
            person_id = result.fetchone()
            
            if person_id:
                logger.info(f"✓ Created sample person (ID: {person_id[0]})")
                
                # Create sample donations
                sample_donations = [
                    {
                        'person_id': person_id[0],
                        'verse_id': 1,
                        'donation_type': 'einzelperson',
                        'donation_details': '{}',
                        'person_snapshot': json.dumps({
                            'email': 'demo@example.com',
                            'first_name': 'Max',
                            'last_name': 'Mustermann',
                            'street': 'Musterstraße',
                            'house_number': '42',
                            'postal_code': '12345',
                            'city': 'Musterstadt'
                        }),
                        'amount': 100.00,
                        'payment_status': 'completed'
                    },
                    {
                        'person_id': person_id[0],
                        'verse_id': 2,
                        'donation_type': 'gruppe',
                        'donation_details': json.dumps({
                            'group_article': 'Die',
                            'group_name': 'Familie Mustermann'
                        }),
                        'person_snapshot': json.dumps({
                            'email': 'demo@example.com',
                            'first_name': 'Max',
                            'last_name': 'Mustermann'
                        }),
                        'amount': 100.00,
                        'payment_status': 'pending'
                    }
                ]
                
                for donation in sample_donations:
                    donation_sql = text("""
                        INSERT INTO donations (person_id, verse_id, donation_type, 
                                             donation_details, person_snapshot, 
                                             amount, payment_status, privacy_consent)
                        VALUES (:person_id, :verse_id, :donation_type, 
                                :donation_details::jsonb, :person_snapshot::jsonb, 
                                :amount, :payment_status, true)
                    """)
                    db.session.execute(donation_sql, donation)
                
                # Mark first verse as sponsored
                db.session.execute(text("""
                    UPDATE verses SET is_sponsored = true, sponsored_at = NOW() 
                    WHERE id = 1
                """))
                
                db.session.commit()
                logger.info("✓ Created sample donations")
            
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