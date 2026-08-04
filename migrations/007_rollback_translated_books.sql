-- Rollback for 007_mark_translated_books.sql
-- Created: 2026-08-03
--
-- Makes the seven books of the volume "Die Geschichtsbücher Josua bis Ester"
-- available for sponsoring again.
--
-- CANNOT be undone by this script:
--   - The verse_reservations deleted by step 2 of the migration. They were
--     short-lived (15 minutes) session locks, so this is harmless.
--   - The book boosts (+7) removed through the admin panel before the
--     migration. Re-apply them there if needed.

BEGIN;

-- 1. Clear the translation flags
UPDATE verses
SET is_translated = FALSE,
    translation_book_release = NULL,
    translation_completed_at = NULL
WHERE book IN ('1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST');

COMMIT;

-- 2. Verify — expected: 0
SELECT COUNT(*) AS still_translated FROM verses WHERE is_translated;
