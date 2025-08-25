#!/usr/bin/env python3
"""
NGÜ Vectorization Script for Docker Deployment
==============================================

This script automatically creates text embeddings for all verses using OpenAI API.
It runs after setup_db.py and is REQUIRED for the app to function properly.

Features:
- Batch processing for efficiency (100 verses per API call)
- Automatic progress tracking and cost estimation
- Retry logic for API failures
- Resumable process (continues from where it left off)
- Comprehensive error handling

Environment Variables Required:
    - SQLALCHEMY_DATABASE_URI
    - OPENAI_API_KEY

Usage:
    python vectorize.py
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add the parent directory to Python path to import our models
sys.path.insert(0, '/app')

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError, SQLAlchemyError
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Make sure you're running this from the Docker container with required packages")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorizeService:
    """Service for creating and managing verse embeddings for NGÜ deployment"""
    
    def __init__(self):
        """Initialize the vectorization service"""
        self.db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        if not self.db_uri:
            raise ValueError("SQLALCHEMY_DATABASE_URI environment variable required")
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required for vectorization")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.engine = None
        
        # Configuration
        self.embedding_model = 'text-embedding-3-small'  # 1536 dimensions, cost-effective
        self.embedding_dimension = 1536
        self.batch_size = 100  # Optimal batch size for API efficiency
        
        # Tracking
        self.total_processed = 0
        self.total_skipped = 0
        self.total_errors = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0
        
        logger.info(f"Vectorization service initialized")
        logger.info(f"Model: {self.embedding_model} ({self.embedding_dimension}d)")
        logger.info(f"Batch size: {self.batch_size}")
    
    def connect_with_retry(self, max_retries: int = 10, delay: int = 2):
        """Connect to database with retry logic"""
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
    
    def get_verses_needing_embeddings(self) -> List[Dict[str, Any]]:
        """Get all verses that need embeddings"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, book, chapter, verse, text
                FROM verses
                WHERE text_embedding IS NULL
                AND text IS NOT NULL
                AND length(trim(text)) > 0
                ORDER BY id
            """))
            
            verses = []
            for row in result:
                verses.append({
                    'id': row[0],
                    'book': row[1],
                    'chapter': row[2],
                    'verse_number': row[3],
                    'text': row[4]
                })
            
            return verses
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding for a single text with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens += response.usage.total_tokens
                    # Pricing for text-embedding-3-small: $0.02 per 1M tokens
                    self.estimated_cost += (response.usage.total_tokens / 1_000_000) * 0.02
                
                return response.data[0].embedding
                
            except Exception as e:
                logger.warning(f"Embedding creation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to create embedding after {max_retries} attempts")
                    return None
        
        return None
    
    def create_batch_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Create embeddings for multiple texts in one API call"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens += response.usage.total_tokens
                    self.estimated_cost += (response.usage.total_tokens / 1_000_000) * 0.02
                
                # Return embeddings in same order as input
                embeddings = [None] * len(texts)
                for data in response.data:
                    if data.index < len(embeddings):
                        embeddings[data.index] = data.embedding
                
                return embeddings
                
            except Exception as e:
                logger.warning(f"Batch embedding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to create batch embeddings after {max_retries} attempts")
                    return [None] * len(texts)
        
        return [None] * len(texts)
    
    def update_verse_embeddings(self, verse_embeddings: List[tuple]):
        """Update verses with their embeddings in batch"""
        if not verse_embeddings:
            return 0
        
        success_count = 0
        
        with self.engine.connect() as conn:
            for verse_id, embedding in verse_embeddings:
                if embedding:
                    try:
                        # Convert to PostgreSQL vector format
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        conn.execute(text(f"""
                            UPDATE verses 
                            SET text_embedding = '{embedding_str}'::vector
                            WHERE id = {verse_id}
                        """))
                        
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to update verse {verse_id}: {e}")
                        self.total_errors += 1
                else:
                    self.total_errors += 1
            
            conn.commit()
        
        return success_count
    
    def vectorize_all_verses(self):
        """Vectorize all verses that need embeddings"""
        # Get verses needing embeddings
        verses = self.get_verses_needing_embeddings()
        total_verses = len(verses)
        
        if total_verses == 0:
            logger.info("✅ All verses already have embeddings!")
            return True
        
        logger.info(f"📝 Found {total_verses} verses needing embeddings")
        
        # Calculate estimated cost and time
        estimated_tokens = total_verses * 50  # Rough estimate: ~50 tokens per verse
        estimated_cost = (estimated_tokens / 1_000_000) * 0.02
        estimated_batches = (total_verses + self.batch_size - 1) // self.batch_size
        estimated_time_minutes = estimated_batches * 2  # ~2 minutes per batch including delays
        
        logger.info(f"📊 Vectorization Plan:")
        logger.info(f"   Verses to process: {total_verses:,}")
        logger.info(f"   Estimated batches: {estimated_batches}")
        logger.info(f"   Estimated tokens: {estimated_tokens:,}")
        logger.info(f"   Estimated cost: ${estimated_cost:.2f}")
        logger.info(f"   Estimated time: {estimated_time_minutes} minutes")
        logger.info(f"")
        
        # Process in batches
        start_time = datetime.now()
        
        for i in range(0, total_verses, self.batch_size):
            batch = verses[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            logger.info(f"🔄 Processing batch {batch_num}/{estimated_batches} ({len(batch)} verses)")
            
            # Prepare texts for embedding
            batch_texts = []
            batch_ids = []
            
            for verse in batch:
                # Create contextual text for better embeddings
                contextual_text = f"{verse['book']} {verse['chapter']},{verse['verse_number']}: {verse['text']}"
                batch_texts.append(contextual_text)
                batch_ids.append(verse['id'])
            
            # Create embeddings for batch
            logger.info(f"   📡 Creating embeddings via OpenAI API...")
            embeddings = self.create_batch_embeddings(batch_texts)
            
            # Update database
            verse_embeddings = list(zip(batch_ids, embeddings))
            success_count = self.update_verse_embeddings(verse_embeddings)
            
            self.total_processed += success_count
            
            # Progress update
            progress_percent = (i + len(batch)) / total_verses * 100
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            
            logger.info(f"   ✅ Updated {success_count}/{len(batch)} verses successfully")
            logger.info(f"   📈 Progress: {progress_percent:.1f}% ({self.total_processed}/{total_verses})")
            logger.info(f"   💰 Cost so far: ${self.estimated_cost:.4f}")
            logger.info(f"   ⏱️  Elapsed: {elapsed:.1f} minutes")
            
            # Rate limiting (be nice to API)
            if i + self.batch_size < total_verses:
                logger.info(f"   ⏸️  Waiting 2 seconds before next batch...")
                time.sleep(2)
            
            logger.info("")
        
        total_time = (datetime.now() - start_time).total_seconds() / 60
        
        logger.info(f"🎉 Vectorization completed!")
        logger.info(f"   Total verses processed: {self.total_processed}")
        logger.info(f"   Total errors: {self.total_errors}")
        logger.info(f"   Total tokens used: {self.total_tokens:,}")
        logger.info(f"   Total cost: ${self.estimated_cost:.4f}")
        logger.info(f"   Total time: {total_time:.1f} minutes")
        
        return self.total_errors == 0
    
    def verify_embeddings(self):
        """Verify embeddings in database"""
        logger.info("🔍 Verifying embeddings...")
        
        with self.engine.connect() as conn:
            # Count verses with and without embeddings
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(text_embedding) as with_embedding,
                    COUNT(*) - COUNT(text_embedding) as without_embedding
                FROM verses
            """))
            
            row = result.fetchone()
            total, with_embedding, without_embedding = row
            
            logger.info(f"📊 Embedding Statistics:")
            logger.info(f"   Total verses: {total}")
            logger.info(f"   With embeddings: {with_embedding}")
            logger.info(f"   Without embeddings: {without_embedding}")
            logger.info(f"   Coverage: {(with_embedding/total*100) if total > 0 else 0:.1f}%")
            
            # Test semantic search if we have embeddings
            if with_embedding > 0:
                self.test_semantic_search()
            
            return without_embedding == 0
    
    def test_semantic_search(self):
        """Test semantic search functionality with sample queries"""
        logger.info("🧪 Testing semantic search functionality...")
        
        test_queries = [
            "Gottes Liebe und Barmherzigkeit",
            "Hoffnung in schweren Zeiten",
            "Frieden und Trost"
        ]
        
        with self.engine.connect() as conn:
            for query in test_queries[:1]:  # Test only first query to save API costs
                logger.info(f"   Query: '{query}'")
                
                # Create embedding for query
                query_embedding = self.create_embedding(query)
                if not query_embedding:
                    logger.error("   ❌ Failed to create query embedding")
                    continue
                
                # Search for similar verses
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                try:
                    result = conn.execute(text(f"""
                        SELECT 
                            id, book, chapter, verse, 
                            SUBSTRING(text, 1, 80) as text_preview,
                            positivity_score,
                            1 - (text_embedding <=> '{embedding_str}'::vector) as similarity
                        FROM verses
                        WHERE text_embedding IS NOT NULL
                        AND is_sponsored = false
                        ORDER BY text_embedding <=> '{embedding_str}'::vector
                        LIMIT 3
                    """))
                    
                    results = result.fetchall()
                    
                    if results:
                        logger.info(f"   ✅ Found {len(results)} similar verses:")
                        for idx, row in enumerate(results, 1):
                            logger.info(f"      {idx}. {row[1]} {row[2]},{row[3]} (sim: {row[6]:.3f})")
                            logger.info(f"         '{row[4]}...'")
                    else:
                        logger.warning("   ⚠️  No results found")
                        
                except Exception as e:
                    logger.error(f"   ❌ Search test failed: {e}")
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()

def main():
    """Main vectorization function"""
    vectorizer = None
    
    try:
        logger.info("🚀 Starting NGÜ verse vectorization...")
        logger.info("This process creates embeddings for semantic search functionality.")
        logger.info("Embeddings are REQUIRED for the app search features to work properly.")
        logger.info("")
        
        # Initialize vectorizer
        vectorizer = VectorizeService()
        
        # Connect to database
        if not vectorizer.connect_with_retry():
            logger.error("❌ Failed to connect to database")
            return False
        
        # Run vectorization
        if not vectorizer.vectorize_all_verses():
            logger.error("❌ Vectorization process encountered errors")
            return False
        
        # Verify results
        if not vectorizer.verify_embeddings():
            logger.warning("⚠️  Some verses still missing embeddings, but continuing...")
        
        logger.info("🎉 Vectorization completed successfully!")
        logger.info("The NGÜ app is now ready with full search functionality!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vectorization failed: {e}")
        return False
    
    finally:
        if vectorizer:
            vectorizer.close()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)