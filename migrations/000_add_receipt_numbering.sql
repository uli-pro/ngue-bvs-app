-- Migration: Add Receipt Numbering System (§50 EStDV compliant)
-- Date: 2025-11-25
-- Purpose: Add receipt_counters table and receipt tracking fields to donations
-- Legal requirement: §50 Abs. 1 EStDV

-- =============================================================================
-- BACKUP FIRST!
-- Before running this migration, create a backup:
-- pg_dump -h localhost -U ngue_user -d ngue_db > backup_before_receipt_numbering_$(date +%Y%m%d_%H%M%S).sql
-- =============================================================================

BEGIN;

-- Step 1: Create receipt_counters table
-- This table tracks the last used receipt number per year
CREATE TABLE IF NOT EXISTS receipt_counters (
    year INTEGER PRIMARY KEY NOT NULL,
    last_number INTEGER DEFAULT 0 NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_receipt_counters_year ON receipt_counters(year);

-- Initialize counter for current year (if not exists)
INSERT INTO receipt_counters (year, last_number, updated_at)
VALUES (EXTRACT(YEAR FROM CURRENT_TIMESTAMP)::INTEGER, 0, CURRENT_TIMESTAMP)
ON CONFLICT (year) DO NOTHING;

-- Step 2: Add new columns to donations table
-- receipt_number: Unique receipt identifier (format: ngue-bvs-YYYY-NNNN)
-- receipt_issued_at: Timestamp when receipt was officially issued
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(30) UNIQUE,
ADD COLUMN IF NOT EXISTS receipt_issued_at TIMESTAMP;

-- Add index for receipt_number lookups
CREATE INDEX IF NOT EXISTS idx_donations_receipt_number ON donations(receipt_number);

-- Add index for receipt_issued_at (useful for reporting)
CREATE INDEX IF NOT EXISTS idx_donations_receipt_issued_at ON donations(receipt_issued_at);

-- Step 3: Backfill receipt numbers for existing completed donations
-- This generates receipt numbers for all completed donations that don't have one yet
-- Numbers are assigned in order of completion date

DO $$
DECLARE
    donation_record RECORD;
    current_year INTEGER;
    counter INTEGER;
    new_receipt_number VARCHAR(30);
BEGIN
    -- Process donations year by year, ordered by completed_at
    FOR donation_record IN
        SELECT id, completed_at, EXTRACT(YEAR FROM completed_at)::INTEGER as year
        FROM donations
        WHERE payment_status = 'completed'
          AND receipt_number IS NULL
          AND completed_at IS NOT NULL
        ORDER BY completed_at ASC
    LOOP
        current_year := donation_record.year;

        -- Get or initialize counter for this year
        SELECT last_number INTO counter
        FROM receipt_counters
        WHERE year = current_year;

        IF counter IS NULL THEN
            -- Initialize counter for this year
            INSERT INTO receipt_counters (year, last_number)
            VALUES (current_year, 0)
            ON CONFLICT (year) DO NOTHING;
            counter := 0;
        END IF;

        -- Increment counter
        counter := counter + 1;

        -- Update counter in database
        UPDATE receipt_counters
        SET last_number = counter, updated_at = CURRENT_TIMESTAMP
        WHERE year = current_year;

        -- Generate receipt number
        new_receipt_number := 'ngue-bvs-' || current_year || '-' || LPAD(counter::TEXT, 4, '0');

        -- Update donation with receipt number
        UPDATE donations
        SET receipt_number = new_receipt_number,
            receipt_issued_at = donation_record.completed_at
        WHERE id = donation_record.id;

        RAISE NOTICE 'Assigned receipt number % to donation %', new_receipt_number, donation_record.id;
    END LOOP;
END $$;

-- Step 4: Add comment documentation
COMMENT ON TABLE receipt_counters IS 'Tracks receipt number sequences per year for tax compliance (§50 EStDV)';
COMMENT ON COLUMN receipt_counters.year IS 'Calendar year for this counter sequence';
COMMENT ON COLUMN receipt_counters.last_number IS 'Last assigned sequential number for this year';
COMMENT ON COLUMN receipt_counters.updated_at IS 'Last time this counter was incremented';

COMMENT ON COLUMN donations.receipt_number IS 'Unique receipt identifier (format: ngue-bvs-YYYY-NNNN) for tax receipts';
COMMENT ON COLUMN donations.receipt_issued_at IS 'Official issuance timestamp of the tax receipt';

-- Step 5: Add constraint to ensure receipt_number format
ALTER TABLE donations
ADD CONSTRAINT check_receipt_number_format
CHECK (receipt_number IS NULL OR receipt_number ~ '^ngue-bvs-\d{4}-\d{4}$');

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES
-- Run these after migration to verify success:
-- =============================================================================

-- Check receipt_counters table
-- SELECT * FROM receipt_counters ORDER BY year;

-- Check donations with receipt numbers
-- SELECT id, receipt_number, receipt_issued_at, completed_at, payment_status
-- FROM donations
-- WHERE receipt_number IS NOT NULL
-- ORDER BY receipt_issued_at DESC
-- LIMIT 10;

-- Count donations by receipt status
-- SELECT
--     payment_status,
--     COUNT(*) as total,
--     COUNT(receipt_number) as with_receipt_number
-- FROM donations
-- GROUP BY payment_status;

-- Verify no duplicate receipt numbers
-- SELECT receipt_number, COUNT(*)
-- FROM donations
-- WHERE receipt_number IS NOT NULL
-- GROUP BY receipt_number
-- HAVING COUNT(*) > 1;