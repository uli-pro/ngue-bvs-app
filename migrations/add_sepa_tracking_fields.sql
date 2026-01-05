-- Migration: Add SEPA/Webhook tracking fields to donations
-- Date: 2025-11-26
-- Description: Enables idempotent webhook handling and storno tracking for SEPA Direct Debit

BEGIN;

-- Add certificate_sent_at column (for idempotency - prevents duplicate certificate emails)
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS certificate_sent_at TIMESTAMP;

-- Add storno_generated flag (tracks if storno PDF was created)
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS storno_generated BOOLEAN DEFAULT FALSE NOT NULL;

-- Add storno_sent_at column (when storno email was sent)
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS storno_sent_at TIMESTAMP;

-- Add failure_reason column (stores Stripe error message)
ALTER TABLE donations
ADD COLUMN IF NOT EXISTS failure_reason VARCHAR(255);

-- Create partial index for idempotency checks (only index non-null values)
CREATE INDEX IF NOT EXISTS idx_donations_certificate_sent
ON donations(certificate_sent_at)
WHERE certificate_sent_at IS NOT NULL;

-- Create partial index for storno queries (only index storno cases)
CREATE INDEX IF NOT EXISTS idx_donations_storno
ON donations(storno_generated)
WHERE storno_generated = true;

-- Add documentation comments
COMMENT ON COLUMN donations.certificate_sent_at
IS 'Timestamp when certificate email was sent (used for idempotency in webhook handlers)';

COMMENT ON COLUMN donations.storno_generated
IS 'Flag indicating if a storno/cancellation PDF has been generated';

COMMENT ON COLUMN donations.storno_sent_at
IS 'Timestamp when storno notification email was sent to donor';

COMMENT ON COLUMN donations.failure_reason
IS 'Error message from Stripe when payment fails or is disputed';

COMMIT;