"""Add search fields to verses table

Revision ID: add_search_fields
Revises: 
Create Date: 2025-08-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'add_search_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add text_search column for full-text search
    op.add_column('verses', sa.Column('text_search', postgresql.TSVECTOR(), nullable=True))
    
    # Add text_embedding column for semantic search
    op.add_column('verses', sa.Column('text_embedding', Vector(1536), nullable=True))
    
    # Create indexes
    op.create_index('idx_verse_text_search', 'verses', ['text_search'], postgresql_using='gin')
    op.create_index('idx_verse_embedding', 'verses', ['text_embedding'], 
                    postgresql_using='ivfflat', 
                    postgresql_ops={'text_embedding': 'vector_cosine_ops'})
    
    # Update existing rows with text search vectors
    op.execute("""
        UPDATE verses 
        SET text_search = to_tsvector('german', text)
        WHERE text IS NOT NULL
    """)
    
    # Create trigger to automatically update text_search on insert/update
    op.execute("""
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
    """)


def downgrade():
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS verse_text_search_trigger ON verses')
    op.execute('DROP FUNCTION IF EXISTS update_verse_text_search()')
    
    # Drop indexes
    op.drop_index('idx_verse_embedding', table_name='verses')
    op.drop_index('idx_verse_text_search', table_name='verses')
    
    # Drop columns
    op.drop_column('verses', 'text_embedding')
    op.drop_column('verses', 'text_search')
    
    # Note: We don't drop the vector extension as other tables might use it