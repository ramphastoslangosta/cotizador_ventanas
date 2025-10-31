-- Migration SQL Preview: 005_add_product_categories
-- ARCH-20251029-002: Add ProductCategory system to app_products table
-- Generated: 2025-10-30
-- Apply with: psql -U ventanas_user -d ventanas_db -f 005_add_product_categories.sql

BEGIN;

-- Step 1: Add product_category column with default 'window' (backward compatible)
ALTER TABLE app_products
ADD COLUMN product_category VARCHAR(50) NOT NULL DEFAULT 'window';

-- Step 2: Make window_type nullable (non-window products don't need it)
ALTER TABLE app_products
ALTER COLUMN window_type DROP NOT NULL;

-- Step 3: Add door_type column (nullable, only for doors)
ALTER TABLE app_products
ADD COLUMN door_type VARCHAR(50);

-- Step 4: Add check constraint for valid product categories
ALTER TABLE app_products
ADD CONSTRAINT check_product_category
CHECK (product_category IN ('window', 'door', 'louver_door', 'railing', 'curtain_wall', 'skylight', 'canopy', 'standalone_material'));

-- Step 5: Add conditional constraint: windows must have window_type
ALTER TABLE app_products
ADD CONSTRAINT check_window_type_for_windows
CHECK ((product_category = 'window' AND window_type IS NOT NULL) OR (product_category != 'window'));

-- Step 6: Add conditional constraint: doors must have door_type
ALTER TABLE app_products
ADD CONSTRAINT check_door_type_for_doors
CHECK ((product_category IN ('door', 'louver_door') AND door_type IS NOT NULL) OR (product_category NOT IN ('door', 'louver_door')));

-- Step 7: Add index for category filtering (performance)
CREATE INDEX idx_app_products_category ON app_products(product_category);

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'app_products'
  AND column_name IN ('product_category', 'window_type', 'door_type')
ORDER BY column_name;

-- Verify existing products have category='window'
SELECT COUNT(*), product_category
FROM app_products
GROUP BY product_category;

COMMIT;

-- Rollback commands (if needed):
/*
BEGIN;
DROP INDEX IF EXISTS idx_app_products_category;
ALTER TABLE app_products DROP CONSTRAINT IF EXISTS check_door_type_for_doors;
ALTER TABLE app_products DROP CONSTRAINT IF EXISTS check_window_type_for_windows;
ALTER TABLE app_products DROP CONSTRAINT IF EXISTS check_product_category;
ALTER TABLE app_products DROP COLUMN IF EXISTS door_type;
ALTER TABLE app_products ALTER COLUMN window_type SET NOT NULL;
ALTER TABLE app_products DROP COLUMN IF EXISTS product_category;
COMMIT;
*/
