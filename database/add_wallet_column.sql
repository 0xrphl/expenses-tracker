-- Add wallet/payment_source column to expenses table
ALTER TABLE expenses 
ADD COLUMN IF NOT EXISTS payment_source VARCHAR(50);

-- Add payment_source to income table
ALTER TABLE income 
ADD COLUMN IF NOT EXISTS payment_source VARCHAR(50);

