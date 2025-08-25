#!/usr/bin/env python3
"""
NGÜ Database Initialization Script for Docker Deployment
=======================================================

This script runs after PostgreSQL container startup to:
1. Verify database connection and structure
2. Import verses from verses.json
3. Create sample data if requested
4. Verify everything is working correctly

Usage:
    python initialize_database.py [--sample-data] [--force-reimport]

Environment Variables Required:
    - SQLALCHEMY_DATABASE_URI
    - OPENAI_API_KEY (optional, for embedding generation)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles database initialization for NGÜ app deployment"""
    
    def __init__(self):
        self.db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        if not self.db_uri:
            raise ValueError("SQLALCHEMY_DATABASE_URI environment variable required")
        
        self.engine = None
        self.session = None
        self.verses_file = Path('/app/data/verses/verses.json')
        
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
                    logger.info(f"Connected to PostgreSQL: {version}")
                
                # Create session
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                return True
                
            except OperationalError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
        
        return False
    
    def verify_extensions(self):
        """Verify required PostgreSQL extensions are installed"""
        logger.info("Verifying PostgreSQL extensions...")
        
        required_extensions = ['vector', 'uuid-ossp', 'pg_trgm', 'unaccent']
        
        for ext in required_extensions:
            try:
                result = self.session.execute(
                    text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = :ext)"),
                    {"ext": ext}
                )
                if not result.fetchone()[0]:
                    logger.error(f"Required extension '{ext}' not installed")
                    return False
                logger.info(f"✓ Extension '{ext}' is installed")
            except Exception as e:
                logger.error(f"Error checking extension '{ext}': {e}")
                return False
        
        return True
    
    def verify_tables(self):
        """Verify all required tables exist"""
        logger.info("Verifying database tables...")
        
        required_tables = [
            'persons', 'verses', 'donations', 'donated_verses', 
            'verse_reservations', 'payment_transactions', 'app_config', 'setup_log'
        ]
        
        for table in required_tables:
            try:
                result = self.session.execute(
                    text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = :table)"),
                    {"table": table}
                )
                if not result.fetchone()[0]:
                    logger.error(f"Required table '{table}' not found")
                    return False
                logger.info(f"✓ Table '{table}' exists")
            except Exception as e:
                logger.error(f"Error checking table '{table}': {e}")
                return False
        
        return True
    
    def check_verses_imported(self) -> bool:
        """Check if verses are already imported"""
        try:
            result = self.session.execute(text("SELECT COUNT(*) FROM verses"))
            count = result.fetchone()[0]
            logger.info(f"Found {count} verses in database")
            return count > 0
        except Exception as e:
            logger.error(f"Error checking verses count: {e}")
            return False
    
    def import_verses(self, force_reimport: bool = False):
        """Import verses from JSON file"""
        if self.check_verses_imported() and not force_reimport:
            logger.info("Verses already imported, skipping import")
            return True
        
        if not self.verses_file.exists():
            logger.error(f"Verses file not found: {self.verses_file}")
            return False
        
        logger.info(f"Importing verses from {self.verses_file}")
        
        try:
            with open(self.verses_file, 'r', encoding='utf-8') as f:
                verses_data = json.load(f)
            
            if not isinstance(verses_data, list):
                logger.error("Invalid verses data format - expected list")
                return False
            
            # Clear existing verses if force reimport
            if force_reimport:
                logger.info("Force reimport requested, clearing existing verses...")
                self.session.execute(text("TRUNCATE TABLE verses RESTART IDENTITY CASCADE"))
                self.session.commit()
            
            # Import verses in batches
            batch_size = 1000
            total_verses = len(verses_data)
            logger.info(f"Importing {total_verses} verses in batches of {batch_size}")
            
            for i in range(0, total_verses, batch_size):
                batch = verses_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"Processing batch {batch_num} ({len(batch)} verses)")
                
                # Prepare batch insert
                values = []
                for verse in batch:
                    # Extract embedding if present
                    embedding = None
                    if 'embedding' in verse and verse['embedding']:
                        embedding = verse['embedding']
                        if isinstance(embedding, list):
                            embedding = f"[{','.join(map(str, embedding))}]"
                    
                    values.append({
                        'book': verse.get('book', ''),
                        'chapter': verse.get('chapter', 1),
                        'verse': verse.get('verse', 1),
                        'text': verse.get('text', ''),
                        'text_ngue': verse.get('text_ngue'),
                        'positivity_score': verse.get('positivity_score'),
                        'text_embedding': embedding,
                        'word_count': len(verse.get('text', '').split()),
                        'character_count': len(verse.get('text', '')),
                        'is_translated': bool(verse.get('text_ngue')),
                        'is_featured': verse.get('positivity_score', 0) >= 85  # High positivity for featured
                    })
                
                # Execute batch insert
                insert_query = text("""
                    INSERT INTO verses (
                        book, chapter, verse, text, text_ngue, positivity_score,
                        text_embedding, word_count, character_count, is_translated, is_featured
                    ) VALUES (
                        :book, :chapter, :verse, :text, :text_ngue, :positivity_score,
                        :text_embedding::vector, :word_count, :character_count, :is_translated, :is_featured
                    ) ON CONFLICT (book, chapter, verse) DO NOTHING
                """)
                
                self.session.execute(insert_query, values)
                self.session.commit()
                
                logger.info(f"Batch {batch_num} imported successfully")
            
            # Verify import
            result = self.session.execute(text("SELECT COUNT(*) FROM verses"))
            imported_count = result.fetchone()[0]
            logger.info(f"✓ Successfully imported {imported_count} verses")
            
            # Update statistics
            self.update_verse_statistics()
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing verses: {e}")
            self.session.rollback()
            return False
    
    def update_verse_statistics(self):
        """Update verse statistics and featured verses"""
        logger.info("Updating verse statistics...")
        
        try:
            # Update app configuration with actual verse count
            result = self.session.execute(text("SELECT COUNT(*) FROM verses"))
            total_verses = result.fetchone()[0]
            
            result = self.session.execute(text("SELECT COUNT(DISTINCT book) FROM verses"))
            total_books = result.fetchone()[0]
            
            result = self.session.execute(text("SELECT COUNT(*) FROM verses WHERE is_sponsored = true"))
            sponsored_verses = result.fetchone()[0]
            
            # Update config
            config_updates = [
                ('total_verses', str(total_verses)),
                ('total_books', str(total_books)),
                ('sponsored_verses', str(sponsored_verses)),
                ('sponsorship_progress_percent', str(round((sponsored_verses / total_verses * 100) if total_verses > 0 else 0, 2)))
            ]
            
            for key, value in config_updates:
                self.session.execute(
                    text("INSERT INTO app_config (key, value, description) VALUES (:key, :value, :desc) ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()"),
                    {"key": key, "value": value, "desc": f"Auto-updated: {key}"}
                )
            
            self.session.commit()
            logger.info(f"✓ Statistics updated: {total_verses} verses, {total_books} books, {sponsored_verses} sponsored")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            self.session.rollback()
    
    def create_sample_data(self):
        """Create sample data for testing"""
        logger.info("Creating sample data...")
        
        try:
            # Create sample person
            self.session.execute(text("""
                INSERT INTO persons (email, first_name, last_name, salutation, city, country, gdpr_consent, gdpr_consent_at)
                VALUES ('test@example.com', 'Max', 'Mustermann', 'Herr', 'Berlin', 'DE', true, NOW())
                ON CONFLICT (email) DO NOTHING
            """))
            
            # Create sample donation (pending)
            self.session.execute(text("""
                INSERT INTO donations (donation_number, person_id, amount, verse_count, donation_type, status)
                SELECT 'SAMPLE-' || extract(epoch from now())::text, p.id, 10000, 1, 'individual', 'pending'
                FROM persons p WHERE p.email = 'test@example.com'
                ON CONFLICT (donation_number) DO NOTHING
            """))
            
            self.session.commit()
            logger.info("✓ Sample data created")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            self.session.rollback()
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        logger.info("Running health checks...")
        
        checks = [
            ("Database connection", self.check_database_connection),
            ("Extensions", self.verify_extensions),
            ("Tables", self.verify_tables),
            ("Verses data", self.check_verses_imported),
            ("Indexes", self.check_indexes),
            ("Functions", self.check_functions)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if check_func():
                    logger.info(f"✓ {check_name} - PASSED")
                else:
                    logger.error(f"✗ {check_name} - FAILED")
                    all_passed = False
            except Exception as e:
                logger.error(f"✗ {check_name} - ERROR: {e}")
                all_passed = False
        
        return all_passed
    
    def check_database_connection(self) -> bool:
        """Check database connection"""
        try:
            self.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def check_indexes(self) -> bool:
        """Check critical indexes exist"""
        critical_indexes = [
            'idx_verses_book_chapter_verse',
            'idx_verses_embedding',
            'idx_verses_text_search',
            'idx_donations_person_id'
        ]
        
        for index in critical_indexes:
            result = self.session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = :index)"),
                {"index": index}
            )
            if not result.fetchone()[0]:
                logger.error(f"Missing critical index: {index}")
                return False
        
        return True
    
    def check_functions(self) -> bool:
        """Check custom functions exist"""
        functions = [
            'update_verse_text_search',
            'get_verse_reference',
            'reserve_verses',
            'cleanup_expired_reservations'
        ]
        
        for func in functions:
            result = self.session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = :func)"),
                {"func": func}
            )
            if not result.fetchone()[0]:
                logger.error(f"Missing function: {func}")
                return False
        
        return True
    
    def log_completion(self, success: bool):
        """Log initialization completion"""
        status = 'completed' if success else 'failed'
        message = 'Database initialization completed successfully' if success else 'Database initialization failed'
        
        try:
            self.session.execute(
                text("INSERT INTO setup_log (step, status, message) VALUES ('initialize_database', :status, :message)"),
                {"status": status, "message": message}
            )
            self.session.commit()
        except Exception as e:
            logger.error(f"Error logging completion: {e}")
    
    def close(self):
        """Close database connections"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()


def main():
    """Main initialization function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize NGÜ database')
    parser.add_argument('--sample-data', action='store_true', help='Create sample data for testing')
    parser.add_argument('--force-reimport', action='store_true', help='Force reimport of verses data')
    args = parser.parse_args()
    
    initializer = None
    try:
        logger.info("Starting NGÜ database initialization...")
        
        initializer = DatabaseInitializer()
        
        # Connect to database
        if not initializer.connect_with_retry():
            logger.error("Failed to connect to database")
            return False
        
        # Verify basic structure
        if not initializer.verify_extensions():
            logger.error("Extension verification failed")
            return False
        
        if not initializer.verify_tables():
            logger.error("Table verification failed") 
            return False
        
        # Import verses
        if not initializer.import_verses(force_reimport=args.force_reimport):
            logger.error("Verse import failed")
            return False
        
        # Create sample data if requested
        if args.sample_data:
            initializer.create_sample_data()
        
        # Run health checks
        if not initializer.run_health_checks():
            logger.error("Health checks failed")
            return False
        
        # Log success
        initializer.log_completion(True)
        logger.info("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if initializer:
            initializer.log_completion(False)
        return False
    
    finally:
        if initializer:
            initializer.close()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)