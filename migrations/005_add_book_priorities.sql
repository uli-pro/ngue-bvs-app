-- Migration: Add positivity_pre_boost and book_priorities table
-- Created: 2026-01-06
-- Purpose: Enable database-based book prioritization

-- 1. Add positivity_pre_boost column to verses
ALTER TABLE verses
ADD COLUMN positivity_pre_boost INTEGER;

-- 2. Copy current scores as baseline
UPDATE verses
SET positivity_pre_boost = positivity_score
WHERE positivity_pre_boost IS NULL;

-- 3. Create index for performance
CREATE INDEX idx_verse_positivity_pre_boost
ON verses(positivity_pre_boost);

-- 4. Create book_priorities table
CREATE TABLE book_priorities (
    id SERIAL PRIMARY KEY,
    book_code VARCHAR(10) UNIQUE NOT NULL,
    boost_value INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- 5. Create indexes for book_priorities
CREATE INDEX idx_book_priorities_code ON book_priorities(book_code);
CREATE INDEX idx_book_priorities_active ON book_priorities(is_active);

-- 6. Verify migration
SELECT COUNT(*) as verses_with_pre_boost
FROM verses
WHERE positivity_pre_boost IS NOT NULL;

-- Should return same count as total verses