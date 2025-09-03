#!/usr/bin/env python3
"""
Migration script to add email tracking fields to existing donations table
and create magic_link_tokens table
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db
from sqlalchemy import text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_email_fields():
    """Add email tracking fields to existing donations table"""
    logger.info("Adding email tracking fields to donations table...")
    
    with app.app_context():
        try:
            # Check if fields already exist
            check_columns_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'donations' 
                AND table_schema = 'public'
                AND column_name IN ('email_sent', 'email_sent_at')
            """)
            
            existing_columns = db.session.execute(check_columns_sql).fetchall()
            existing_column_names = [col[0] for col in existing_columns]
            
            # Add email_sent field if it doesn't exist
            if 'email_sent' not in existing_column_names:
                logger.info("Adding email_sent column...")
                db.session.execute(text("""
                    ALTER TABLE donations 
                    ADD COLUMN email_sent BOOLEAN NOT NULL DEFAULT FALSE
                """))
                logger.info("✓ email_sent column added")
            else:
                logger.info("✓ email_sent column already exists")
            
            # Add email_sent_at field if it doesn't exist
            if 'email_sent_at' not in existing_column_names:
                logger.info("Adding email_sent_at column...")
                db.session.execute(text("""
                    ALTER TABLE donations 
                    ADD COLUMN email_sent_at TIMESTAMP NULL
                """))
                logger.info("✓ email_sent_at column added")
            else:
                logger.info("✓ email_sent_at column already exists")
            
            # Create index for email_sent if it doesn't exist
            logger.info("Creating email_sent index...")
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_donations_email_sent ON donations(email_sent)
            """))
            logger.info("✓ email_sent index created")
            
            db.session.commit()
            logger.info("✅ Email tracking fields migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            raise

def create_magic_link_table():
    """Create magic_link_tokens table if it doesn't exist"""
    logger.info("Creating magic_link_tokens table...")
    
    with app.app_context():
        try:
            # Check if table already exists
            check_table_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'magic_link_tokens'
                )
            """)
            
            table_exists = db.session.execute(check_table_sql).scalar()
            
            if not table_exists:
                logger.info("Creating magic_link_tokens table...")
                
                create_table_sql = text("""
                    CREATE TABLE magic_link_tokens (
                        id SERIAL PRIMARY KEY,
                        token VARCHAR(64) UNIQUE NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        used BOOLEAN NOT NULL DEFAULT FALSE,
                        ip_address VARCHAR(45),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        used_at TIMESTAMP
                    )
                """)
                
                db.session.execute(create_table_sql)
                
                # Create indexes
                logger.info("Creating magic_link_tokens indexes...")
                indexes_sql = text("""
                    CREATE INDEX idx_magic_token_email ON magic_link_tokens(email);
                    CREATE INDEX idx_magic_token_expires ON magic_link_tokens(expires_at);
                    CREATE INDEX idx_magic_token_used ON magic_link_tokens(used);
                    CREATE UNIQUE INDEX idx_magic_token_unique ON magic_link_tokens(token);
                """)
                
                db.session.execute(indexes_sql)
                db.session.commit()
                logger.info("✓ magic_link_tokens table and indexes created")
            else:
                logger.info("✓ magic_link_tokens table already exists")
                
        except Exception as e:
            logger.error(f"Magic link table creation failed: {e}")
            db.session.rollback()
            raise

def verify_migration():
    """Verify the migration was successful"""
    logger.info("Verifying migration...")
    
    with app.app_context():
        try:
            # Check donations table columns
            check_donations_sql = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'donations' 
                AND table_schema = 'public'
                AND column_name IN ('email_sent', 'email_sent_at')
                ORDER BY column_name
            """)
            
            donations_columns = db.session.execute(check_donations_sql).fetchall()
            
            logger.info("\n✓ Donations table email fields:")
            for col_name, data_type, nullable, default in donations_columns:
                logger.info(f"  - {col_name}: {data_type} (nullable: {nullable}, default: {default})")
            
            # Check magic_link_tokens table
            check_magic_table_sql = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'magic_link_tokens' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            magic_columns = db.session.execute(check_magic_table_sql).fetchall()
            
            if magic_columns:
                logger.info("\n✓ Magic link tokens table structure:")
                for col_name, data_type in magic_columns:
                    logger.info(f"  - {col_name}: {data_type}")
            
            # Test a simple query
            test_query_sql = text("""
                SELECT COUNT(*) as total_donations,
                       SUM(CASE WHEN email_sent THEN 1 ELSE 0 END) as emails_sent
                FROM donations
            """)
            
            result = db.session.execute(test_query_sql).fetchone()
            logger.info(f"\n✓ Migration test successful:")
            logger.info(f"  - Total donations: {result[0]}")
            logger.info(f"  - Emails sent: {result[1]}")
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise

def main():
    """Run the migration"""
    try:
        logger.info("=== Email Service Migration ===\n")
        
        # Run migrations
        migrate_email_fields()
        create_magic_link_table()
        
        # Verify
        verify_migration()
        
        logger.info("\n" + "="*50)
        logger.info("✅ EMAIL SERVICE MIGRATION COMPLETED!")
        logger.info("The checkout process should now work correctly.")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()