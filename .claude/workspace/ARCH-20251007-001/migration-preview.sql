-- Migration Preview: 004_update_glass_material_codes
-- This SQL shows what the Alembic migration will execute
-- Generated: 2025-10-07

-- Update existing glass materials with standardized codes
-- Pattern: Update materials that match old names to use new standardized codes

BEGIN;

-- 1. Vidrio Flotado 6mm → VID-CLARO-6
UPDATE app_materials
SET code = 'VID-CLARO-6',
    name = 'Vidrio Claro 6mm',
    cost_per_unit = 120.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Flotado 6mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 2. Vidrio Claro 4mm → VID-CLARO-4
UPDATE app_materials
SET code = 'VID-CLARO-4',
    name = 'Vidrio Claro 4mm',
    cost_per_unit = 85.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Claro 4mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 3. Vidrio Claro 6mm → VID-CLARO-6 (already updated above, skip duplicates)

-- 4. Vidrio Bronce 4mm → VID-BRONCE-4
UPDATE app_materials
SET code = 'VID-BRONCE-4',
    name = 'Vidrio Bronce 4mm',
    cost_per_unit = 95.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Bronce 4mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 5. Vidrio Bronce 6mm → VID-BRONCE-6
UPDATE app_materials
SET code = 'VID-BRONCE-6',
    name = 'Vidrio Bronce 6mm',
    cost_per_unit = 135.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Bronce 6mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 6. Vidrio Templado 6mm → VID-TEMP-6
UPDATE app_materials
SET code = 'VID-TEMP-6',
    name = 'Vidrio Templado 6mm',
    cost_per_unit = 195.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Templado 6mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 7. Vidrio Laminado 6mm → VID-LAMINADO-6
UPDATE app_materials
SET code = 'VID-LAMINADO-6',
    name = 'Vidrio Laminado 6mm',
    cost_per_unit = 220.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Laminado 6mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- 8. Vidrio Reflectivo Bronze 6mm → VID-REFLECTIVO-6
UPDATE app_materials
SET code = 'VID-REFLECTIVO-6',
    name = 'Vidrio Reflectivo 6mm',
    cost_per_unit = 180.00,
    category = 'Vidrio',
    updated_at = NOW()
WHERE name LIKE '%Vidrio Reflectivo%6mm%'
  AND (category = 'Vidrio' OR category IS NULL);

-- Verify results
SELECT
    id,
    code,
    name,
    cost_per_unit,
    category,
    updated_at
FROM app_materials
WHERE category = 'Vidrio'
ORDER BY code;

COMMIT;

-- Expected result: 7 glass materials with standardized codes
-- VID-BRONCE-4, VID-BRONCE-6, VID-CLARO-4, VID-CLARO-6,
-- VID-LAMINADO-6, VID-REFLECTIVO-6, VID-TEMP-6
