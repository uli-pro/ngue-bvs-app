-- Rollback for migration 005
-- Removes book_priorities feature and restores original state

-- 1. Drop book_priorities table
DROP TABLE IF EXISTS book_priorities;

-- 2. Drop index
DROP INDEX IF EXISTS idx_verse_positivity_pre_boost;

-- 3. Drop column
ALTER TABLE verses DROP COLUMN IF EXISTS positivity_pre_boost;

-- Verify rollback
\d verses
\d book_priorities  -- Should error "does not exist"
