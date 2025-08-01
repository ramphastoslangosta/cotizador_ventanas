-- Script para agregar categorización a materiales
-- Ejecutar este script en la base de datos PostgreSQL

-- 1. Agregar columna category si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'app_materials' 
        AND column_name = 'category'
    ) THEN
        ALTER TABLE app_materials 
        ADD COLUMN category TEXT NOT NULL DEFAULT 'Otros';
        RAISE NOTICE 'Columna category agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna category ya existe';
    END IF;
END $$;

-- 2. Actualizar materiales existentes con categorías basadas en nombre
UPDATE app_materials 
SET category = CASE
    -- Herrajes primero (más específico)
    WHEN LOWER(name) LIKE '%cerradura%' OR LOWER(name) LIKE '%manija%' OR LOWER(name) LIKE '%bisagra%' 
         OR LOWER(name) LIKE '%rueda%' OR LOWER(name) LIKE '%rodamiento%' OR LOWER(name) LIKE '%tornillo%' 
         OR LOWER(name) LIKE '%tuerca%' OR LOWER(name) LIKE '%herraje%' THEN 'Herrajes'
    -- Perfiles (excluyendo los que ya son herrajes)
    WHEN LOWER(name) LIKE '%perfil%' OR LOWER(name) LIKE '%riel%' OR LOWER(name) LIKE '%marco%' 
         OR LOWER(name) LIKE '%batiente%' OR LOWER(name) LIKE '%contramarco%' 
         OR (LOWER(name) LIKE '%aluminio%' AND LOWER(name) NOT LIKE '%manija%' AND LOWER(name) NOT LIKE '%cerradura%') THEN 'Perfiles'
    -- Vidrio
    WHEN LOWER(name) LIKE '%vidrio%' OR LOWER(name) LIKE '%cristal%' OR LOWER(name) LIKE '%glass%' THEN 'Vidrio'
    -- Consumibles
    WHEN LOWER(name) LIKE '%silicón%' OR LOWER(name) LIKE '%silicon%' OR LOWER(name) LIKE '%sellador%' 
         OR LOWER(name) LIKE '%sella%' OR LOWER(name) LIKE '%empaque%' OR LOWER(name) LIKE '%hule%' 
         OR LOWER(name) LIKE '%cartucho%' OR LOWER(name) LIKE '%masilla%' THEN 'Consumibles'
    ELSE 'Otros'
END
WHERE category = 'Otros';

-- 3. Verificar resultado
SELECT 
    category, 
    COUNT(*) as cantidad,
    STRING_AGG(name, ', ') as ejemplos
FROM app_materials 
WHERE is_active = true 
GROUP BY category 
ORDER BY cantidad DESC;

-- Mostrar mensaje de éxito
DO $$
BEGIN
    RAISE NOTICE '✅ Categorización completada exitosamente';
END $$;