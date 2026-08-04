-- Migration: Mark books of the volume "Die Geschichtsbücher Josua bis Ester" as translated
-- Created: 2026-08-03
-- Purpose: The volume was published in 06/2026. Its books are no longer available
--          for sponsoring, but their verses must stay in the table because
--          donation_verses references them.
--
-- Affected books (4152 verses):
--   1KI 1. Könige (816)   2KI 2. Könige (719)   1CH 1. Chronik (942)
--   2CH 2. Chronik (822)  EZR Esra (280)        NEH Nehemia (406)
--   EST Ester (167)
--
-- Note: The books Josua, Richter, Rut, 1./2. Samuel are part of the same volume
--       but were never in this table, so nothing to do for them.
--
-- The book boosts (+7 each) for these seven books were already removed through
-- the admin panel before this migration. This migration does NOT touch
-- book_priorities.

BEGIN;

-- 1. Mark verses as translated and record the volume's release date
UPDATE verses
SET is_translated = TRUE,
    translation_book_release = DATE '2026-06-01',   -- exact day unknown, 06/2026
    translation_completed_at = TIMESTAMP '2026-06-01 00:00:00'
WHERE book IN ('1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST');

-- 2. Drop reservations on these verses — they can no longer be bought
DELETE FROM verse_reservations
WHERE verse_id IN (
    SELECT id FROM verses
    WHERE book IN ('1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST')
);

-- No index is added on is_translated. Measured on the local database before
-- writing this migration: the statistics query runs in 3.3 ms and the
-- featured-verse query in 0.5 ms, both as sequential scans — at 11003 rows an
-- index earns nothing. It would also require table-owner rights, which the
-- application user does not have.

COMMIT;

-- 3. Verify
--    Expected: translated = 4152, of which sponsored = 74 (local) / 49 (production)
SELECT
    COUNT(*) FILTER (WHERE is_translated)                          AS translated,
    COUNT(*) FILTER (WHERE is_translated AND is_sponsored)         AS translated_sponsored,
    COUNT(*) FILTER (WHERE NOT is_sponsored AND NOT is_translated) AS sponsorable,
    COUNT(*) FILTER (WHERE NOT is_translated)                      AS still_to_translate
FROM verses;

--    Expected: 0 — no verse outside the seven books may be flagged
SELECT COUNT(*) AS wrongly_flagged
FROM verses
WHERE is_translated
  AND book NOT IN ('1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST');
