-- Script de migración específico para materiales existentes
-- Basado en análisis de datos actuales
-- EJECUTAR DESPUÉS de add_material_categories.sql

-- 1. Crear colores base
DO $$
BEGIN
    RAISE NOTICE 'Iniciando creación de colores base...';
END $$;

INSERT INTO colors (name, code, description, is_active) VALUES
('Natural', 'NAT', 'Acabado natural de aluminio', true),
('Blanco', 'WHT', 'Acabado blanco', true),
('Bronze', 'BRZ', 'Acabado bronce', true),
('Champagne', 'CHP', 'Acabado champagne', true),
('Negro', 'BLK', 'Acabado negro', true)
ON CONFLICT (name) DO NOTHING;

-- Verificar colores creados
DO $$
DECLARE
    color_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO color_count FROM colors WHERE is_active = true;
    RAISE NOTICE 'Colores disponibles: %', color_count;
END $$;

-- 2. Configurar colores para perfiles específicos

-- Configurar colores para: Perfil L. Nacional 3' Riel Sup. (ID: 1)
INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 1, c.id, 125.50, true
FROM colors c WHERE c.name = 'Natural'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 125.50,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 1, c.id, 135.54, true
FROM colors c WHERE c.name = 'Blanco'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 135.54,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 1, c.id, 144.32, true
FROM colors c WHERE c.name = 'Bronze'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 144.32,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 1, c.id, 140.56, true
FROM colors c WHERE c.name = 'Champagne'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 140.56,
    updated_at = NOW();


-- Configurar colores para: Perfil L. Nacional 3' Riel Inf. (ID: 2)
INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 2, c.id, 118.75, true
FROM colors c WHERE c.name = 'Natural'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 118.75,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 2, c.id, 128.25, true
FROM colors c WHERE c.name = 'Blanco'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 128.25,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 2, c.id, 136.56, true
FROM colors c WHERE c.name = 'Bronze'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 136.56,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 2, c.id, 133.00, true
FROM colors c WHERE c.name = 'Champagne'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 133.00,
    updated_at = NOW();


-- Configurar colores para: Perfil Nacional Serie 35 Marco (ID: 3)
INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 3, c.id, 145.80, true
FROM colors c WHERE c.name = 'Natural'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 145.80,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 3, c.id, 157.46, true
FROM colors c WHERE c.name = 'Blanco'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 157.46,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 3, c.id, 167.67, true
FROM colors c WHERE c.name = 'Bronze'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 167.67,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 3, c.id, 163.30, true
FROM colors c WHERE c.name = 'Champagne'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 163.30,
    updated_at = NOW();


-- Configurar colores para: Perfil Batiente Nacional (ID: 4)
INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 4, c.id, 132.45, true
FROM colors c WHERE c.name = 'Natural'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 132.45,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 4, c.id, 143.05, true
FROM colors c WHERE c.name = 'Blanco'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 143.05,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 4, c.id, 152.32, true
FROM colors c WHERE c.name = 'Bronze'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 152.32,
    updated_at = NOW();

INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT 4, c.id, 148.34, true
FROM colors c WHERE c.name = 'Champagne'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = 148.34,
    updated_at = NOW();


-- 3. Verificar resultados
DO $$
BEGIN
    RAISE NOTICE 'Verificando configuración de colores...';
END $$;

SELECT 
    m.name as material_name,
    m.category,
    c.name as color_name,
    mc.price_per_unit
FROM app_materials m
LEFT JOIN material_colors mc ON m.id = mc.material_id
LEFT JOIN colors c ON mc.color_id = c.id
WHERE m.category = 'Perfiles'
ORDER BY m.name, c.name;

-- 4. Resumen final
DO $$
DECLARE
    total_materials INTEGER;
    total_profiles INTEGER;
    total_colors INTEGER;
    total_material_colors INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_materials FROM app_materials WHERE is_active = true;
    SELECT COUNT(*) INTO total_profiles FROM app_materials WHERE category = 'Perfiles' AND is_active = true;
    SELECT COUNT(*) INTO total_colors FROM colors WHERE is_active = true;
    SELECT COUNT(*) INTO total_material_colors FROM material_colors WHERE is_available = true;
    
    RAISE NOTICE '';
    RAISE NOTICE '🎉 MIGRACIÓN DE COLORES COMPLETADA EXITOSAMENTE!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Estadísticas finales:';
    RAISE NOTICE '   • Total de materiales: %', total_materials;
    RAISE NOTICE '   • Perfiles configurados: %', total_profiles;
    RAISE NOTICE '   • Colores disponibles: %', total_colors;
    RAISE NOTICE '   • Combinaciones material-color: %', total_material_colors;
    RAISE NOTICE '';
    RAISE NOTICE '✅ Sistema listo para usar con nuevas funcionalidades!';
END $$;
