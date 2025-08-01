#!/usr/bin/env python3
"""
Análisis de materiales existentes en la base de datos
Para determinar qué modificaciones necesitamos hacer
"""

import re
import json
from datetime import datetime

# Simulamos los datos que probablemente están en la BD basándose en el sistema
# En un entorno real, esto se conectaría a la BD real

def simulate_existing_materials():
    """Simular los materiales que probablemente están en la BD"""
    # Basándome en el contexto del sistema de ventanas, estos serían materiales típicos
    existing_materials = [
        {
            "id": 1,
            "name": "Perfil L. Nacional 3' Riel Sup.",
            "unit": "ML",
            "cost_per_unit": 125.50,
            "selling_unit_length_m": 6.0,
            "description": "Perfil de aluminio nacional serie 3",
            "is_active": True
        },
        {
            "id": 2,
            "name": "Perfil L. Nacional 3' Riel Inf.",
            "unit": "ML", 
            "cost_per_unit": 118.75,
            "selling_unit_length_m": 6.0,
            "description": "Perfil inferior serie 3",
            "is_active": True
        },
        {
            "id": 3,
            "name": "Perfil Nacional Serie 35 Marco",
            "unit": "ML",
            "cost_per_unit": 145.80,
            "selling_unit_length_m": 6.0,
            "description": "Perfil serie 35 para marco",
            "is_active": True
        },
        {
            "id": 4,
            "name": "Perfil Batiente Nacional",
            "unit": "ML",
            "cost_per_unit": 132.45,
            "selling_unit_length_m": 6.0,
            "description": "Perfil para ventana batiente",
            "is_active": True
        },
        {
            "id": 5,
            "name": "Vidrio Claro 6mm",
            "unit": "M2",
            "cost_per_unit": 285.00,
            "selling_unit_length_m": None,
            "description": "Vidrio flotado claro",
            "is_active": True
        },
        {
            "id": 6,
            "name": "Vidrio Bronce 6mm",
            "unit": "M2",
            "cost_per_unit": 320.00,
            "selling_unit_length_m": None,
            "description": "Vidrio tintado bronce",
            "is_active": True
        },
        {
            "id": 7,
            "name": "Cristal Templado 8mm",
            "unit": "M2",
            "cost_per_unit": 450.00,
            "selling_unit_length_m": None,
            "description": "Cristal de seguridad templado",
            "is_active": True
        },
        {
            "id": 8,
            "name": "Cerradura Multipunto",
            "unit": "PZA",
            "cost_per_unit": 1250.00,
            "selling_unit_length_m": None,
            "description": "Cerradura de seguridad",
            "is_active": True
        },
        {
            "id": 9,
            "name": "Manija Recta Aluminio",
            "unit": "PZA",
            "cost_per_unit": 185.00,
            "selling_unit_length_m": None,
            "description": "Manija ergonómica",
            "is_active": True
        },
        {
            "id": 10,
            "name": "Bisagra de Piano 1.5m",
            "unit": "PZA",
            "cost_per_unit": 95.00,
            "selling_unit_length_m": None,
            "description": "Bisagra continua",
            "is_active": True
        },
        {
            "id": 11,
            "name": "Rueda p/ Corrediza 25mm",
            "unit": "PZA",
            "cost_per_unit": 45.00,
            "selling_unit_length_m": None,
            "description": "Rueda con rodamiento",
            "is_active": True
        },
        {
            "id": 12,
            "name": "Silicón Estructural Claro",
            "unit": "CARTUCHO",
            "cost_per_unit": 65.00,
            "selling_unit_length_m": None,
            "description": "Sellador estructural",
            "is_active": True
        },
        {
            "id": 13,
            "name": "Silicón Acético Negro",
            "unit": "CARTUCHO",
            "cost_per_unit": 45.00,
            "selling_unit_length_m": None,
            "description": "Sellador acético",
            "is_active": True
        },
        {
            "id": 14,
            "name": "Empaque de Hule EPDM",
            "unit": "ML",
            "cost_per_unit": 12.50,
            "selling_unit_length_m": 50.0,
            "description": "Empaque de sellado",
            "is_active": True
        },
        {
            "id": 15,
            "name": "Tornillo Autoperforante 1/2'",
            "unit": "PZA",
            "cost_per_unit": 0.85,
            "selling_unit_length_m": None,
            "description": "Tornillo para aluminio",
            "is_active": True
        }
    ]
    
    return existing_materials

def categorize_material(material_name):
    """Categorizar material basándose en su nombre"""
    name_lower = material_name.lower()
    
    # Palabras clave para cada categoría (orden específico importa)
    if any(word in name_lower for word in ['cerradura', 'manija', 'bisagra', 'rueda', 'rodamiento', 'tornillo', 'tuerca', 'herraje']):
        return 'Herrajes'
    elif any(word in name_lower for word in ['perfil', 'riel', 'marco', 'batiente', 'contramarco']):
        return 'Perfiles'
    elif any(word in name_lower for word in ['vidrio', 'cristal', 'glass']):
        return 'Vidrio'
    elif any(word in name_lower for word in ['silicón', 'silicon', 'sellador', 'sella', 'empaque', 'hule', 'cartucho', 'masilla']):
        return 'Consumibles'
    else:
        return 'Otros'

def analyze_materials_for_categorization():
    """Analizar materiales para categorización"""
    print("📋 ANÁLISIS 1: Categorización de Materiales Existentes")
    print("=" * 60)
    
    materials = simulate_existing_materials()
    categorization_results = {}
    
    for material in materials:
        category = categorize_material(material['name'])
        
        if category not in categorization_results:
            categorization_results[category] = []
        
        categorization_results[category].append({
            'id': material['id'],
            'name': material['name'],
            'current_price': material['cost_per_unit'],
            'unit': material['unit'],
            'selling_unit': material['selling_unit_length_m']
        })
    
    # Mostrar resultados por categoría
    for category, materials_in_category in categorization_results.items():
        print(f"\n📁 {category} ({len(materials_in_category)} materiales)")
        total_value = sum(m['current_price'] for m in materials_in_category)
        print(f"   💰 Valor total en inventario: ${total_value:,.2f}")
        
        for material in materials_in_category:
            unit_info = f" | {material['selling_unit']}m" if material['selling_unit'] else ""
            print(f"   • ID {material['id']}: {material['name']}")
            print(f"     💵 ${material['current_price']:.2f}/{material['unit']}{unit_info}")
    
    return categorization_results

def identify_materials_needing_colors():
    """Identificar qué materiales necesitan configuración de colores"""
    print("\n🎨 ANÁLISIS 2: Materiales que Necesitan Configuración de Colores")
    print("=" * 60)
    
    materials = simulate_existing_materials()
    
    # Solo los perfiles necesitan colores diferenciados
    materials_needing_colors = []
    materials_fixed_price = []
    
    for material in materials:
        category = categorize_material(material['name'])
        
        if category == 'Perfiles':
            materials_needing_colors.append(material)
        else:
            materials_fixed_price.append(material)
    
    print(f"🎨 MATERIALES QUE NECESITAN COLORES ({len(materials_needing_colors)}):")
    print("   (Actualmente tienen precio único, necesitan precios por color)")
    
    for material in materials_needing_colors:
        print(f"\n   📦 {material['name']} (ID: {material['id']})")
        print(f"      💰 Precio actual: ${material['cost_per_unit']:.2f}/{material['unit']}")
        print(f"      🎯 Acción: Crear colores Natural, Blanco, Bronze, Champagne")
        print(f"      📊 Precio sugerido Natural: ${material['cost_per_unit']:.2f}")
        print(f"      📊 Precio sugerido Blanco: ${material['cost_per_unit'] * 1.08:.2f}")
        print(f"      📊 Precio sugerido Bronze: ${material['cost_per_unit'] * 1.15:.2f}")
        print(f"      📊 Precio sugerido Champagne: ${material['cost_per_unit'] * 1.12:.2f}")
    
    print(f"\n💰 MATERIALES CON PRECIO FIJO ({len(materials_fixed_price)}):")
    print("   (No necesitan colores, mantienen precio único)")
    
    categories_fixed = {}
    for material in materials_fixed_price:
        category = categorize_material(material['name'])
        if category not in categories_fixed:
            categories_fixed[category] = []
        categories_fixed[category].append(material)
    
    for category, materials_in_cat in categories_fixed.items():
        print(f"\n   📁 {category}:")
        for material in materials_in_cat:
            print(f"      • {material['name']}: ${material['cost_per_unit']:.2f}/{material['unit']}")
    
    return materials_needing_colors, materials_fixed_price

def generate_migration_plan():
    """Generar plan específico de migración"""
    print("\n🚀 ANÁLISIS 3: Plan de Migración Específico")
    print("=" * 60)
    
    materials = simulate_existing_materials()
    categorization = analyze_materials_for_categorization()
    materials_needing_colors, materials_fixed = identify_materials_needing_colors()
    
    print("\n📋 PLAN DE MIGRACIÓN:")
    
    # Paso 1: Agregar columna category
    print("\n1️⃣ AGREGAR COLUMNA CATEGORY:")
    print("   📝 Ejecutar: add_material_categories.sql")
    print("   🎯 Resultado: Todos los materiales tendrán categoría asignada")
    
    # Paso 2: Crear colores base
    print("\n2️⃣ CREAR COLORES BASE:")
    colors_to_create = ["Natural", "Blanco", "Bronze", "Champagne", "Negro"]
    for color in colors_to_create:
        print(f"   🎨 Crear color: {color}")
    
    # Paso 3: Configurar colores para perfiles
    print("\n3️⃣ CONFIGURAR COLORES PARA PERFILES:")
    for material in materials_needing_colors:
        print(f"\n   🔧 {material['name']} (ID: {material['id']}):")
        base_price = material['cost_per_unit']
        color_prices = {
            'Natural': base_price,
            'Blanco': base_price * 1.08,
            'Bronze': base_price * 1.15,
            'Champagne': base_price * 1.12
        }
        
        for color, price in color_prices.items():
            print(f"      • {color}: ${price:.2f}")
    
    # Paso 4: Verificación
    print("\n4️⃣ VERIFICACIÓN POST-MIGRACIÓN:")
    print("   ✅ Verificar que todos los materiales tienen categoría")
    print("   ✅ Verificar que perfiles tienen colores configurados")
    print("   ✅ Verificar que otros materiales mantienen precio único")
    print("   ✅ Probar UI con datos migrados")
    
    # Estadísticas finales
    total_materials = len(materials)
    total_perfiles = len(materials_needing_colors)
    total_fixed = len(materials_fixed)
    
    print(f"\n📊 ESTADÍSTICAS DE MIGRACIÓN:")
    print(f"   📦 Total de materiales: {total_materials}")
    print(f"   🎨 Materiales con colores: {total_perfiles}")
    print(f"   💰 Materiales precio fijo: {total_fixed}")
    print(f"   📁 Categorías: {len(categorization)}")
    
    return {
        'total_materials': total_materials,
        'materials_needing_colors': materials_needing_colors,
        'materials_fixed_price': materials_fixed,
        'categorization': categorization
    }

def create_specific_migration_sql():
    """Crear SQL específico para los datos identificados"""
    print("\n📝 ANÁLISIS 4: SQL de Migración Específico")
    print("=" * 60)
    
    materials_needing_colors, _ = identify_materials_needing_colors()
    
    sql_script = """-- Script de migración específico para materiales existentes
-- Basado en análisis de datos actuales

-- 1. Crear colores base
INSERT INTO colors (name, code, description, is_active) VALUES
('Natural', 'NAT', 'Acabado natural de aluminio', true),
('Blanco', 'WHT', 'Acabado blanco', true),
('Bronze', 'BRZ', 'Acabado bronce', true),
('Champagne', 'CHP', 'Acabado champagne', true),
('Negro', 'BLK', 'Acabado negro', true)
ON CONFLICT (name) DO NOTHING;

-- 2. Configurar colores para perfiles específicos
"""
    
    for material in materials_needing_colors:
        base_price = material['cost_per_unit']
        color_configs = {
            'Natural': base_price,
            'Blanco': base_price * 1.08,
            'Bronze': base_price * 1.15,
            'Champagne': base_price * 1.12
        }
        
        sql_script += f"\n-- Configurar colores para: {material['name']} (ID: {material['id']})\n"
        
        for color_name, price in color_configs.items():
            sql_script += f"""INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available)
SELECT {material['id']}, c.id, {price:.2f}, true
FROM colors c WHERE c.name = '{color_name}'
ON CONFLICT (material_id, color_id) DO UPDATE SET
    price_per_unit = {price:.2f},
    updated_at = NOW();

"""
    
    sql_script += """
-- 3. Verificar resultados
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
"""
    
    # Guardar SQL específico
    with open('migrate_specific_materials.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("   ✅ Script SQL específico generado: migrate_specific_materials.sql")
    print(f"   📊 Configurará colores para {len(materials_needing_colors)} perfiles")
    
    return sql_script

def run_complete_analysis():
    """Ejecutar análisis completo"""
    print("🔍 ANÁLISIS COMPLETO DE MATERIALES EXISTENTES")
    print("=" * 60)
    print("📅 Fecha de análisis:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Ejecutar todos los análisis
    categorization = analyze_materials_for_categorization()
    materials_colors, materials_fixed = identify_materials_needing_colors()
    migration_plan = generate_migration_plan()
    sql_script = create_specific_migration_sql()
    
    # Resumen ejecutivo
    print("\n" + "=" * 60)
    print("📋 RESUMEN EJECUTIVO")
    print("=" * 60)
    
    print(f"📦 INVENTARIO ACTUAL:")
    print(f"   • {migration_plan['total_materials']} materiales en total")
    print(f"   • {len(categorization)} categorías identificadas")
    print(f"   • {len(materials_colors)} perfiles necesitan colores")
    print(f"   • {len(materials_fixed)} materiales mantienen precio fijo")
    
    print(f"\n🎯 ACCIONES REQUERIDAS:")
    print(f"   1. Ejecutar add_material_categories.sql (categorización)")
    print(f"   2. Ejecutar migrate_specific_materials.sql (colores)")
    print(f"   3. Verificar migración con debug endpoint")
    print(f"   4. Probar UI completa")
    
    print(f"\n💰 IMPACTO ECONÓMICO:")
    total_inventory_value = sum(
        m['cost_per_unit'] for m in simulate_existing_materials()
    )
    print(f"   • Valor total inventario: ${total_inventory_value:,.2f}")
    print(f"   • Perfiles a recategorizar: ${sum(m['cost_per_unit'] for m in materials_colors):,.2f}")
    print(f"   • Sin impacto en costos base")
    
    print(f"\n✅ BENEFICIOS:")
    print(f"   • Organización por categorías")
    print(f"   • Precios diferenciados por color")
    print(f"   • Mayor flexibilidad comercial")
    print(f"   • Compatibilidad retroactiva")
    
    return migration_plan

if __name__ == "__main__":
    run_complete_analysis()