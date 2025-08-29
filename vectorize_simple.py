#!/usr/bin/env python3
"""
Vectorization Script - Simplified Version
NGÜ Bibelvers-Sponsoring App

Creates text embeddings for semantic search using OpenAI API.
Simplified for single donation type structure.

Usage:
    python vectorize_simple.py [--limit N] [--batch-size N] [--skip-existing]
"""

import os
import sys
import time
import argparse
from datetime import datetime
import logging
from typing import List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from sqlalchemy import text
from models import db, Verse
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'  # 1536 dimensions
EMBEDDING_DIMENSION = 1536

class VectorizeService:
    """Service for creating and managing verse embeddings"""
    
    def __init__(self):
        """Initialize the service"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.total_processed = 0
        self.total_skipped = 0
        self.total_errors = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            
            # Track usage
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens
                # Pricing: $0.02 per 1M tokens for text-embedding-3-small
                self.estimated_cost += (response.usage.total_tokens / 1_000_000) * 0.02
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return None
    
    def create_batch_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Create embeddings for multiple texts in one API call"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )
            
            # Track usage
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens
                self.estimated_cost += (response.usage.total_tokens / 1_000_000) * 0.02
            
            # Return embeddings in same order as input
            embeddings = [None] * len(texts)
            for i, data in enumerate(response.data):
                embeddings[data.index] = data.embedding
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {e}")
            return [None] * len(texts)
    
    def vectorize_verses(self, limit: Optional[int] = None, 
                        batch_size: int = 100,
                        skip_existing: bool = False):
        """Vectorize verses in the database"""
        
        with app.app_context():
            # Get verses to process
            if skip_existing:
                query = text("""
                    SELECT id, book, chapter, verse, text
                    FROM verses
                    WHERE text_embedding IS NULL
                    ORDER BY id
                    LIMIT :limit
                """ if limit else """
                    SELECT id, book, chapter, verse, text
                    FROM verses
                    WHERE text_embedding IS NULL
                    ORDER BY id
                """)
            else:
                query = text("""
                    SELECT id, book, chapter, verse, text
                    FROM verses
                    ORDER BY id
                    LIMIT :limit
                """ if limit else """
                    SELECT id, book, chapter, verse, text
                    FROM verses
                    ORDER BY id
                """)
            
            params = {'limit': limit} if limit else {}
            verses = db.session.execute(query, params).fetchall()
            
            total_verses = len(verses)
            logger.info(f"Found {total_verses} verses to process")
            
            if total_verses == 0:
                logger.info("No verses to vectorize!")
                return
            
            # Process in batches
            for i in range(0, total_verses, batch_size):
                batch = verses[i:i + batch_size]
                batch_texts = []
                batch_ids = []
                
                # Prepare batch
                for verse in batch:
                    verse_id, book, chapter, verse_num, verse_text = verse
                    
                    # Create contextual text for better embeddings
                    contextual_text = f"{book} {chapter},{verse_num}: {verse_text}"
                    batch_texts.append(contextual_text)
                    batch_ids.append(verse_id)
                
                # Create embeddings
                logger.info(f"Creating embeddings for batch {i//batch_size + 1} "
                          f"({len(batch_texts)} verses)...")
                
                embeddings = self.create_batch_embeddings(batch_texts)
                
                # Update database
                success_count = 0
                for verse_id, embedding in zip(batch_ids, embeddings):
                    if embedding:
                        try:
                            # Convert to PostgreSQL vector format
                            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                            
                            # Use raw SQL with proper casting
                            update_query = text("""
                                UPDATE verses 
                                SET text_embedding = CAST(:embedding_vector AS vector)
                                WHERE id = :verse_id
                            """)
                            
                            db.session.execute(update_query, {
                                'embedding_vector': embedding_str,
                                'verse_id': verse_id
                            })
                            
                            success_count += 1
                            self.total_processed += 1
                            
                        except Exception as e:
                            logger.error(f"Error updating verse {verse_id}: {e}")
                            self.total_errors += 1
                    else:
                        self.total_errors += 1
                
                # Commit batch
                db.session.commit()
                logger.info(f"  ✓ Updated {success_count}/{len(batch)} verses")
                
                # Show progress
                progress = ((i + len(batch)) / total_verses) * 100
                logger.info(f"  Progress: {progress:.1f}% ({self.total_processed}/{total_verses})")
                logger.info(f"  Estimated cost so far: ${self.estimated_cost:.4f}")
                
                # Rate limiting (be nice to API)
                if i + batch_size < total_verses:
                    time.sleep(1)  # 1 second between batches
    
    def verify_embeddings(self):
        """Verify embeddings in database"""
        with app.app_context():
            # Count verses with embeddings
            count_query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(text_embedding) as with_embedding,
                    COUNT(*) - COUNT(text_embedding) as without_embedding
                FROM verses
            """)
            
            result = db.session.execute(count_query).fetchone()
            total, with_embedding, without_embedding = result
            
            logger.info("\n=== Embedding Verification ===")
            logger.info(f"Total verses: {total}")
            logger.info(f"With embeddings: {with_embedding}")
            logger.info(f"Without embeddings: {without_embedding}")
            logger.info(f"Coverage: {(with_embedding/total*100):.1f}%")
            
            # Test semantic search
            if with_embedding > 0:
                self.test_semantic_search()
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        logger.info("\n=== Testing Semantic Search ===")
        
        test_queries = [
            "Gottes Liebe und Barmherzigkeit",
            "Hoffnung in schweren Zeiten",
            "Vergebung der Sünden"
        ]
        
        with app.app_context():
            for query in test_queries:
                logger.info(f"\nQuery: '{query}'")
                
                # Create embedding for query
                query_embedding = self.create_embedding(query)
                if not query_embedding:
                    logger.error("Failed to create query embedding")
                    continue
                
                # Search for similar verses
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                # Use CAST for proper vector type conversion
                search_query = text("""
                    SELECT 
                        id, book, chapter, verse, 
                        SUBSTRING(text, 1, 100) as text_preview,
                        positivity_score,
                        1 - (text_embedding <=> CAST(:embedding_vector AS vector)) as similarity
                    FROM verses
                    WHERE text_embedding IS NOT NULL
                    AND is_sponsored = false
                    ORDER BY text_embedding <=> CAST(:embedding_vector AS vector)
                    LIMIT 3
                """)
                
                results = db.session.execute(search_query, {
                    'embedding_vector': embedding_str
                }).fetchall()
                
                for idx, result in enumerate(results, 1):
                    logger.info(f"  {idx}. {result.book} {result.chapter},{result.verse} "
                              f"(Similarity: {result.similarity:.3f}, "
                              f"Positivity: {result.positivity_score})")
                    logger.info(f"     '{result.text_preview}...'")
    
    def print_summary(self):
        """Print processing summary"""
        logger.info("\n" + "="*50)
        logger.info("VECTORIZATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Verses processed: {self.total_processed}")
        logger.info(f"Verses skipped: {self.total_skipped}")
        logger.info(f"Errors: {self.total_errors}")
        logger.info(f"Total tokens used: {self.total_tokens:,}")
        logger.info(f"Estimated cost: ${self.estimated_cost:.4f}")
        logger.info("="*50)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Vectorize verses for semantic search (simplified)')
    parser.add_argument('--limit', type=int, help='Limit number of verses to process')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Number of verses per batch (default: 100)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip verses that already have embeddings')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify existing embeddings')
    parser.add_argument('--test-search', action='store_true',
                       help='Test semantic search after vectorization')
    
    args = parser.parse_args()
    
    try:
        logger.info("=== NGÜ Verse Vectorization (Simplified) ===\n")
        
        if not OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not found in environment variables!")
            logger.info("\nPlease set it in your .env file:")
            logger.info("OPENAI_API_KEY=sk-...")
            sys.exit(1)
        
        service = VectorizeService()
        
        if args.verify_only:
            service.verify_embeddings()
        else:
            # Estimate cost
            if not args.skip_existing:
                with app.app_context():
                    verse_count = db.session.execute(
                        text("SELECT COUNT(*) FROM verses")
                    ).scalar()
                    
                    if args.limit:
                        verse_count = min(verse_count, args.limit)
                    
                    # Rough estimate: ~50 tokens per verse
                    estimated_tokens = verse_count * 50
                    estimated_cost = (estimated_tokens / 1_000_000) * 0.02
                    
                    logger.info(f"Estimated verses to process: {verse_count}")
                    logger.info(f"Estimated tokens: {estimated_tokens:,}")
                    logger.info(f"Estimated cost: ${estimated_cost:.2f}")
                    
                    response = input("\nContinue? (yes/no): ")
                    if response.lower() != 'yes':
                        logger.info("Vectorization cancelled.")
                        return
            
            # Run vectorization
            service.vectorize_verses(
                limit=args.limit,
                batch_size=args.batch_size,
                skip_existing=args.skip_existing
            )
            
            # Print summary
            service.print_summary()
            
            # Verify results
            service.verify_embeddings()
            
            # Test search if requested
            if args.test_search:
                service.test_semantic_search()
        
        logger.info("\n✅ Vectorization completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Vectorization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()