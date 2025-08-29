#!/usr/bin/env python3
"""
Newsletter Consent Migration Script
Adds newsletter_consent column to persons table
"""

import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db

def migrate_newsletter_consent():
    """Add newsletter_consent column to persons table"""
    
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='persons' AND column_name='newsletter_consent'
            """)).fetchone()
            
            if result:
                print("✓ newsletter_consent column already exists")
                return True
            
            # Add the column with default FALSE
            print("Adding newsletter_consent column to persons table...")
            db.session.execute(text("""
                ALTER TABLE persons 
                ADD COLUMN newsletter_consent BOOLEAN DEFAULT FALSE NOT NULL
            """))
            
            # Add comment for documentation
            db.session.execute(text("""
                COMMENT ON COLUMN persons.newsletter_consent 
                IS 'Newsletter subscription consent - TRUE if user opted in, FALSE by default (GDPR compliant)'
            """))
            
            db.session.commit()
            print("✓ Successfully added newsletter_consent column")
            
            # Verify the addition
            result = db.session.execute(text("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name='persons' AND column_name='newsletter_consent'
            """)).fetchone()
            
            if result:
                print(f"✓ Verification: {result.column_name} ({result.data_type}, default: {result.column_default})")
                return True
            else:
                print("✗ Verification failed: Column not found after creation")
                return False
                
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("NGÜ Newsletter Consent Migration")
    print("=" * 40)
    
    success = migrate_newsletter_consent()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)