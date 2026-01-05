-- Migration: Add payment_method_type to payment_transactions
-- Date: 2025-01-25
-- Description: Enables detection of SEPA vs card payments for method-specific handling

BEGIN;

-- Add payment_method_type column
ALTER TABLE payment_transactions
ADD COLUMN payment_method_type VARCHAR(20);

-- Add index for fast lookup
CREATE INDEX idx_payment_transactions_method_type
ON payment_transactions(payment_method_type);

-- Add documentation
COMMENT ON COLUMN payment_transactions.payment_method_type
IS 'Payment method type from Stripe (sepa_debit, card, etc.)';

COMMIT;
