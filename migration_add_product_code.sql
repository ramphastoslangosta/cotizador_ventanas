-- Migration: Add code column to app_products table
-- Date: August 8, 2025
-- Description: Add optional product code field with unique constraint

-- Add the code column to app_products table
ALTER TABLE app_products 
ADD COLUMN code TEXT;

-- Add unique constraint to the code column
ALTER TABLE app_products 
ADD CONSTRAINT app_products_code_unique UNIQUE (code);

-- Verify the migration
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'app_products' AND column_name = 'code';

-- Show current products (should all have NULL codes initially)
SELECT id, name, code FROM app_products LIMIT 5;