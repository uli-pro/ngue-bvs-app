#!/usr/bin/env python3
"""
Vectorization script for NGÜ Bible Verse Sponsoring App
Generates text embeddings for all verses using OpenAI's API
"""

import os
import sys
import json
import time
from datetime import datetime
import openai
from tqdm import tqdm
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 100  # Process verses in batches
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI model (1536 dimensions)
RATE_LIMIT_DELAY = 0.1  # Seconds between API calls to avoid rate limiting

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv('DATABASE_URL', 'postgresql://localhost/ngue_bvs_db')

def get_openai_client():
    """Initialize OpenAI client"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please add it to your .env file")
        sys.exit(1)
    
    openai.api_key = api_key
    return openai

def create_embedding(text, client):
    """Generate embedding for a single text"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def batch_create_embeddings(texts, client):
    """Generate embeddings for multiple texts in a batch"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"Error generating batch embeddings: {e}")
        return [None] * len(texts)

def init_pgvector(engine):
    """Initialize pgvector extension in PostgreSQL"""
    with engine.connect() as conn:
        try:
            # Create pgvector extension if not exists
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✓ pgvector extension initialized")
        except Exception as e:
            print(f"Error initializing pgvector: {e}")
            return False
    return True

def update_text_search_vectors(engine):
    """Update text search vectors for all verses"""
    print("\nUpdating text search vectors...")
    with engine.connect() as conn:
        try:
            # Update all text_search columns with German language configuration
            result = conn.execute(text("""
                UPDATE verses 
                SET text_search = to_tsvector('german', text)
                WHERE text IS NOT NULL
            """))
            conn.commit()
            print(f"✓ Updated text search vectors for {result.rowcount} verses")
        except Exception as e:
            print(f"Error updating text search vectors: {e}")
            return False
    return True

def vectorize_verses(engine, client, resume_from_id=None):
    """Vectorize all verses in the database"""
    with engine.connect() as conn:
        # Get total count
        total_query = "SELECT COUNT(*) FROM verses WHERE text IS NOT NULL"
        if resume_from_id:
            total_query += f" AND id > {resume_from_id}"
        
        total_count = conn.execute(text(total_query)).scalar()
        print(f"\nFound {total_count} verses to vectorize")
        
        if total_count == 0:
            print("No verses to process")
            return
        
        # Process in batches
        offset = 0
        processed = 0
        failed = 0
        
        with tqdm(total=total_count, desc="Vectorizing verses") as pbar:
            while offset < total_count:
                # Fetch batch of verses
                query = """
                    SELECT id, text 
                    FROM verses 
                    WHERE text IS NOT NULL
                """
                if resume_from_id:
                    query += f" AND id > {resume_from_id}"
                query += f" ORDER BY id LIMIT {BATCH_SIZE} OFFSET {offset}"
                
                verses = conn.execute(text(query)).fetchall()
                
                if not verses:
                    break
                
                # Extract texts for batch processing
                texts = [verse.text for verse in verses]
                verse_ids = [verse.id for verse in verses]
                
                # Generate embeddings
                embeddings = batch_create_embeddings(texts, client)
                
                # Update database
                for verse_id, embedding in zip(verse_ids, embeddings):
                    if embedding:
                        try:
                            # Convert embedding to string format for pgvector
                            embedding_str = str(embedding)
                            
                            conn.execute(text("""
                                UPDATE verses 
                                SET text_embedding = :embedding
                                WHERE id = :id
                            """), {"embedding": embedding_str, "id": verse_id})
                            
                            processed += 1
                        except Exception as e:
                            print(f"\nError updating verse {verse_id}: {e}")
                            failed += 1
                    else:
                        failed += 1
                
                # Commit batch
                conn.commit()
                
                # Update progress
                pbar.update(len(verses))
                
                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
                offset += BATCH_SIZE
        
        print(f"\n✓ Vectorization complete!")
        print(f"  - Processed: {processed} verses")
        print(f"  - Failed: {failed} verses")
        print(f"  - Success rate: {(processed/(processed+failed)*100):.1f}%")

def verify_vectorization(engine):
    """Verify the vectorization results"""
    with engine.connect() as conn:
        # Count verses with embeddings
        count_with_embeddings = conn.execute(text("""
            SELECT COUNT(*) FROM verses 
            WHERE text_embedding IS NOT NULL
        """)).scalar()
        
        # Count verses with text search
        count_with_search = conn.execute(text("""
            SELECT COUNT(*) FROM verses 
            WHERE text_search IS NOT NULL
        """)).scalar()
        
        # Total verses
        total_verses = conn.execute(text("SELECT COUNT(*) FROM verses")).scalar()
        
        print("\n📊 Verification Results:")
        print(f"  - Total verses: {total_verses}")
        print(f"  - With embeddings: {count_with_embeddings} ({count_with_embeddings/total_verses*100:.1f}%)")
        print(f"  - With text search: {count_with_search} ({count_with_search/total_verses*100:.1f}%)")
        
        # Test semantic search
        if count_with_embeddings > 0:
            print("\n🔍 Testing semantic search...")
            test_query = "Liebe und Hoffnung"
            
            # Get embedding for test query
            client = get_openai_client()
            test_embedding = create_embedding(test_query, client)
            
            if test_embedding:
                embedding_str = str(test_embedding)
                
                results = conn.execute(text("""
                    SELECT book, chapter, verse, text,
                           text_embedding <=> :embedding as distance
                    FROM verses
                    WHERE text_embedding IS NOT NULL
                    ORDER BY text_embedding <=> :embedding
                    LIMIT 3
                """), {"embedding": embedding_str}).fetchall()
                
                print(f"  Top 3 results for '{test_query}':")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.book} {result.chapter}:{result.verse} (distance: {result.distance:.4f})")
                    print(f"     {result.text[:100]}...")

def main():
    """Main execution function"""
    print("="*60)
    print("NGÜ Bible Verse Vectorization Script")
    print("="*60)
    
    # Initialize database connection
    print("\n1. Connecting to database...")
    engine = create_engine(get_database_url())
    
    # Initialize pgvector
    print("\n2. Initializing pgvector extension...")
    if not init_pgvector(engine):
        print("Failed to initialize pgvector. Exiting.")
        sys.exit(1)
    
    # Update text search vectors
    print("\n3. Updating text search vectors...")
    if not update_text_search_vectors(engine):
        print("Warning: Text search vector update failed")
    
    # Check for OpenAI API key
    print("\n4. Checking OpenAI API configuration...")
    client = get_openai_client()
    print("✓ OpenAI API configured")
    
    # Ask user if they want to proceed with vectorization
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Vectorization will use OpenAI API credits")
    print(f"   Estimated cost: ~$0.02 per 1000 verses")
    print(f"   Total verses to process: ~11,000")
    print(f"   Estimated total cost: ~$0.22")
    print(f"   Estimated time: 30-60 minutes")
    print("="*60)
    
    response = input("\nDo you want to proceed with vectorization? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Vectorization cancelled.")
        # Still verify what we have
        verify_vectorization(engine)
        return
    
    # Check if we should resume
    with engine.connect() as conn:
        last_id = conn.execute(text("""
            SELECT MAX(id) FROM verses 
            WHERE text_embedding IS NOT NULL
        """)).scalar()
        
        if last_id:
            print(f"\n⚠️  Found existing embeddings up to verse ID {last_id}")
            response = input("Resume from this point? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                resume_from_id = last_id
            else:
                resume_from_id = None
        else:
            resume_from_id = None
    
    # Start vectorization
    print("\n5. Starting vectorization...")
    start_time = time.time()
    
    vectorize_verses(engine, client, resume_from_id)
    
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed_time/60:.1f} minutes")
    
    # Verify results
    print("\n6. Verifying results...")
    verify_vectorization(engine)
    
    print("\n✅ Vectorization script completed!")

if __name__ == "__main__":
    main()