-- Rollback: Remove payment_method_type
BEGIN;

DROP INDEX IF EXISTS idx_payment_transactions_method_type;
ALTER TABLE payment_transactions DROP COLUMN IF EXISTS payment_method_type;

COMMIT;
