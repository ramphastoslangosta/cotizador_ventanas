-- Migración para agregar códigos de producto estándar
-- Ejecutar en PostgreSQL

-- 1. Agregar columna code si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'app_materials' 
        AND column_name = 'code'
    ) THEN
        ALTER TABLE app_materials 
        ADD COLUMN code TEXT UNIQUE;
        RAISE NOTICE 'Columna code agregada exitosamente a app_materials';
    ELSE
        RAISE NOTICE 'Columna code ya existe en app_materials';
    END IF;
END $$;

-- 2. Generar códigos estándar para materiales existentes basados en patrones de la industria
-- Formato: [CATEGORIA]-[TIPO]-[SERIE]-[NUMERO]

-- PERFILES - Códigos estándar de aluminio
UPDATE app_materials 
SET code = CASE
    -- Perfiles Nacional Serie 3"
    WHEN LOWER(name) LIKE '%perfil%nac%3%riel sup%' THEN 'ALU-PER-NAC3-001'
    WHEN LOWER(name) LIKE '%perfil%nac%3%jamba%' THEN 'ALU-PER-NAC3-002'  
    WHEN LOWER(name) LIKE '%perfil%nac%3%traslape%' THEN 'ALU-PER-NAC3-003'
    WHEN LOWER(name) LIKE '%perfil%nac%3%zoclo%' THEN 'ALU-PER-NAC3-004'
    
    -- Perfiles Serie 35
    WHEN LOWER(name) LIKE '%perfil%serie 35%contramarco%' THEN 'ALU-PER-S35-001'
    WHEN LOWER(name) LIKE '%perfil%serie 35%marco%móvil%' THEN 'ALU-PER-S35-002'
    WHEN LOWER(name) LIKE '%perfil%serie 35%marco%movil%' THEN 'ALU-PER-S35-002'
    
    -- Perfiles Fijos
    WHEN LOWER(name) LIKE '%perfil fijo%escalonado%' THEN 'ALU-PER-FIJ-001'
    
    -- Perfiles Batientes
    WHEN LOWER(name) LIKE '%perfil batiente%' THEN 'ALU-PER-BAT-001'
    
    ELSE NULL
END
WHERE category = 'Perfiles' AND code IS NULL;

-- HERRAJES - Códigos estándar de herrajes
UPDATE app_materials 
SET code = CASE
    -- Rodamientos
    WHEN LOWER(name) LIKE '%rodamiento%doble%línea%3%' THEN 'HER-ROD-DL3-001'
    WHEN LOWER(name) LIKE '%rodamiento%doble%linea%3%' THEN 'HER-ROD-DL3-001'
    
    -- Cerraduras
    WHEN LOWER(name) LIKE '%cerradura%multipunto%' THEN 'HER-CER-MUL-001'
    
    -- Manijas
    WHEN LOWER(name) LIKE '%manija%recta%' THEN 'HER-MAN-REC-001'
    
    -- Brazos y mecanismos
    WHEN LOWER(name) LIKE '%brazo%proyectante%10%' THEN 'HER-BRA-PRO-010'
    
    -- Cremona
    WHEN LOWER(name) LIKE '%cremona%serie 35%' THEN 'HER-CRE-S35-001'
    
    -- Junquillos
    WHEN LOWER(name) LIKE '%junquillo%fijo%3%' THEN 'HER-JUN-FIJ-003'
    
    ELSE NULL
END
WHERE category = 'Herrajes' AND code IS NULL;

-- VIDRIOS - Códigos estándar de vidrios
UPDATE app_materials 
SET code = CASE
    -- Vidrios Claros
    WHEN LOWER(name) LIKE '%vidrio%claro%6mm%' THEN 'VID-CLA-6MM-001'
    WHEN LOWER(name) LIKE '%vidrio%claro%4mm%' THEN 'VID-CLA-4MM-001'
    
    -- Vidrios Bronce
    WHEN LOWER(name) LIKE '%vidrio%bronce%6mm%' THEN 'VID-BRO-6MM-001'
    WHEN LOWER(name) LIKE '%vidrio%bronce%4mm%' THEN 'VID-BRO-4MM-001'
    
    -- Vidrios Reflectivo
    WHEN LOWER(name) LIKE '%vidrio%reflectivo%6mm%' THEN 'VID-REF-6MM-001'
    
    ELSE NULL
END
WHERE category = 'Vidrio' AND code IS NULL;

-- CONSUMIBLES - Códigos estándar de consumibles
UPDATE app_materials 
SET code = CASE
    -- Siliconas
    WHEN LOWER(name) LIKE '%silicón%neutra%' THEN 'CON-SIL-NEU-001'
    WHEN LOWER(name) LIKE '%silicon%neutra%' THEN 'CON-SIL-NEU-001'
    WHEN LOWER(name) LIKE '%silicón%estructural%claro%' THEN 'CON-SIL-EST-001'
    WHEN LOWER(name) LIKE '%silicon%estructural%claro%' THEN 'CON-SIL-EST-001'
    
    -- Cuñas y empaques
    WHEN LOWER(name) LIKE '%cuñas%hule%' THEN 'CON-CUN-HUL-001'
    
    -- Felpas
    WHEN LOWER(name) LIKE '%felpa%1/2%' THEN 'CON-FEL-05I-001'
    
    -- Pijas y tornillería
    WHEN LOWER(name) LIKE '%pijas%#8%x%1%' THEN 'CON-PIJ-8X1-001'
    
    ELSE NULL
END
WHERE category = 'Consumibles' AND code IS NULL;

-- OTROS - Códigos genéricos para materiales sin categoría específica
UPDATE app_materials 
SET code = CONCAT('GEN-OTR-', LPAD(id::text, 3, '0'))
WHERE category = 'Otros' AND code IS NULL;

-- 3. Verificar resultados
SELECT 
    category,
    COUNT(*) as total_materiales,
    COUNT(code) as con_codigo,
    COUNT(*) - COUNT(code) as sin_codigo
FROM app_materials 
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- 4. Mostrar códigos generados
SELECT 
    id,
    name,
    code,
    category
FROM app_materials 
WHERE is_active = true 
AND code IS NOT NULL
ORDER BY category, code;

-- Mostrar mensaje de éxito
DO $$
DECLARE
    total_con_codigo INTEGER;
    total_materiales INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_materiales FROM app_materials WHERE is_active = true;
    SELECT COUNT(code) INTO total_con_codigo FROM app_materials WHERE is_active = true AND code IS NOT NULL;
    
    RAISE NOTICE '';
    RAISE NOTICE '✅ CÓDIGOS DE PRODUCTO GENERADOS EXITOSAMENTE!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Estadísticas:';
    RAISE NOTICE '   • Total de materiales activos: %', total_materiales;
    RAISE NOTICE '   • Materiales con código: %', total_con_codigo;
    RAISE NOTICE '   • Materiales sin código: %', total_materiales - total_con_codigo;
    RAISE NOTICE '';
    RAISE NOTICE '🏷️  Formato de códigos implementado:';
    RAISE NOTICE '   • Perfiles: ALU-PER-[SERIE]-[NUM] (ej: ALU-PER-NAC3-001)';
    RAISE NOTICE '   • Herrajes: HER-[TIPO]-[SERIE]-[NUM] (ej: HER-ROD-DL3-001)';
    RAISE NOTICE '   • Vidrios: VID-[TIPO]-[ESP]-[NUM] (ej: VID-CLA-6MM-001)';
    RAISE NOTICE '   • Consumibles: CON-[TIPO]-[VAR]-[NUM] (ej: CON-SIL-NEU-001)';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Sistema listo para usar códigos estándar de la industria!';
END $$;