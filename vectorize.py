#!/usr/bin/env python3
# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Vectorization Script for Production Deployment
NGÜ Bibelvers-Sponsoring App

Creates text embeddings for semantic search.
Can be run multiple times, will skip existing vectors by default.

Usage:
    python vectorize.py [--limit N] [--force] [--docker]
"""

import os
import sys
import time
import argparse
import logging
from typing import List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def wait_for_database():
    """Wait for database to be ready"""
    if os.environ.get('DOCKER_DEPLOYMENT'):
        logger.info("Waiting for database...")
        time.sleep(5)
    return True

# Import after path setup
from app import app
from models import db, Verse
from sqlalchemy import text

# Check for OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSION = 1536

class VectorizeService:
    """Service for creating verse embeddings"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.total_processed = 0
        self.total_skipped = 0
        self.total_errors = 0
        self.estimated_cost = 0.0
    
    def create_batch_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Create embeddings for multiple texts"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )
            
            # Track costs
            if hasattr(response, 'usage'):
                tokens = response.usage.total_tokens
                self.estimated_cost += (tokens / 1_000_000) * 0.02
            
            # Return in order
            embeddings = [None] * len(texts)
            for i, data in enumerate(response.data):
                embeddings[data.index] = data.embedding
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return [None] * len(texts)
    
    def vectorize_verses(self, limit: Optional[int] = None, 
                        force: bool = False,
                        batch_size: int = 100):
        """Vectorize verses in database"""
        
        with app.app_context():
            # Build query
            if force:
                query = Verse.query.order_by(Verse.id)
            else:
                query = Verse.query.filter(Verse.text_embedding.is_(None)).order_by(Verse.id)
            
            if limit:
                query = query.limit(limit)
            
            verses = query.all()
            total = len(verses)
            
            if total == 0:
                logger.info("No verses to vectorize!")
                return
            
            logger.info(f"Found {total} verses to process")
            
            # Process in batches
            for i in range(0, total, batch_size):
                batch = verses[i:i + batch_size]
                batch_texts = []
                
                # Prepare texts with context
                for verse in batch:
                    context = f"{verse.book} {verse.chapter},{verse.verse}: {verse.text}"
                    batch_texts.append(context)
                
                # Create embeddings
                logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} verses)...")
                embeddings = self.create_batch_embeddings(batch_texts)
                
                # Update database
                success = 0
                for verse, embedding in zip(batch, embeddings):
                    if embedding:
                        try:
                            # Convert to vector format
                            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                            
                            # Update with raw SQL for reliability
                            db.session.execute(text("""
                                UPDATE verses 
                                SET text_embedding = CAST(:embedding AS vector)
                                WHERE id = :id
                            """), {
                                'embedding': embedding_str,
                                'id': verse.id
                            })
                            
                            success += 1
                            self.total_processed += 1
                            
                        except Exception as e:
                            logger.error(f"Error updating verse {verse.id}: {e}")
                            self.total_errors += 1
                    else:
                        self.total_errors += 1
                
                # Commit batch
                db.session.commit()
                
                # Progress
                progress = ((i + len(batch)) / total) * 100
                logger.info(f"  ✓ Processed {success}/{len(batch)} verses")
                logger.info(f"  Progress: {progress:.1f}% | Cost: ${self.estimated_cost:.4f}")
                
                # Rate limit
                if i + batch_size < total:
                    time.sleep(1)
    
    def verify_embeddings(self):
        """Verify embeddings in database"""
        with app.app_context():
            total = Verse.query.count()
            with_embedding = Verse.query.filter(Verse.text_embedding.isnot(None)).count()
            
            logger.info("\n=== Embedding Status ===")
            logger.info(f"Total verses: {total}")
            logger.info(f"With embeddings: {with_embedding}")
            logger.info(f"Coverage: {(with_embedding/total*100):.1f}%")
            
            return with_embedding > 0
    
    def test_search(self):
        """Test semantic search"""
        logger.info("\n=== Testing Semantic Search ===")
        
        test_query = "Gottes Liebe und Barmherzigkeit"
        logger.info(f"Test query: '{test_query}'")
        
        with app.app_context():
            # Create query embedding
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=test_query
            )
            
            query_embedding = response.data[0].embedding
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Search
            results = db.session.execute(text("""
                SELECT book, chapter, verse, 
                       SUBSTRING(text, 1, 80) as preview,
                       1 - (text_embedding <=> CAST(:embedding AS vector)) as similarity
                FROM verses
                WHERE text_embedding IS NOT NULL
                ORDER BY text_embedding <=> CAST(:embedding AS vector)
                LIMIT 3
            """), {'embedding': embedding_str}).fetchall()
            
            for i, r in enumerate(results, 1):
                logger.info(f"{i}. {r.book} {r.chapter},{r.verse} (Score: {r.similarity:.3f})")
                logger.info(f"   '{r.preview}...'")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Vectorize verses for semantic search')
    parser.add_argument('--limit', type=int, help='Limit number of verses')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--force', action='store_true', help='Re-vectorize all verses')
    parser.add_argument('--test', action='store_true', help='Test search after vectorization')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing')
    parser.add_argument('--docker', action='store_true', help='Running in Docker')
    
    args = parser.parse_args()
    
    if args.docker:
        os.environ['DOCKER_DEPLOYMENT'] = '1'
    
    try:
        logger.info("=== NGÜ Verse Vectorization ===\n")
        
        if not OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not set!")
            logger.info("Vectorization is optional but enables semantic search.")
            logger.info("Set OPENAI_API_KEY in .env to enable.")
            sys.exit(0)  # Exit gracefully - vectorization is optional
        
        wait_for_database()
        
        service = VectorizeService()
        
        if args.verify_only:
            service.verify_embeddings()
        else:
            # Estimate cost
            with app.app_context():
                if args.force:
                    count = Verse.query.count()
                else:
                    count = Verse.query.filter(Verse.text_embedding.is_(None)).count()
                
                if args.limit:
                    count = min(count, args.limit)
                
                if count > 0:
                    estimated_cost = (count * 50 / 1_000_000) * 0.02
                    logger.info(f"Verses to process: {count}")
                    logger.info(f"Estimated cost: ${estimated_cost:.2f}")
                    
                    if not args.docker:
                        response = input("\nContinue? (yes/no): ")
                        if response.lower() != 'yes':
                            logger.info("Cancelled.")
                            return
            
            # Run vectorization
            service.vectorize_verses(
                limit=args.limit,
                force=args.force,
                batch_size=args.batch_size
            )
            
            # Verify
            service.verify_embeddings()
            
            # Test if requested
            if args.test:
                service.test_search()
            
            logger.info(f"\n✅ Vectorization complete!")
            logger.info(f"Total cost: ${service.estimated_cost:.4f}")
        
    except Exception as e:
        logger.error(f"\n❌ Vectorization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()