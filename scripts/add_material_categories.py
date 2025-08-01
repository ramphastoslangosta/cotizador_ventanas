#!/usr/bin/env python3
"""
Script para agregar categorización a materiales existentes.
Agrega la columna 'category' y categoriza los materiales existentes.
"""

import sys
from sqlalchemy import text
from database import engine, get_db

def add_category_column():
    """Agregar columna category a la tabla app_materials"""
    print("🔧 Agregando columna 'category' a la tabla app_materials...")
    
    try:
        with engine.connect() as conn:
            # Agregar columna category con valor por defecto
            conn.execute(text("""
                ALTER TABLE app_materials 
                ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'Otros'
            """))
            conn.commit()
            print("✅ Columna 'category' agregada exitosamente")
    except Exception as e:
        print(f"❌ Error agregando columna: {e}")
        return False
    
    return True

def categorize_existing_materials():
    """Categorizar materiales existentes basándose en sus nombres"""
    print("\n🏷️ Categorizando materiales existentes...")
    
    categories = {
        'Perfiles': ['perfil', 'riel', 'marco', 'batiente', 'contramarco', 'aluminio'],
        'Vidrio': ['vidrio', 'cristal', 'glass'],
        'Herrajes': ['cerradura', 'manija', 'bisagra', 'rueda', 'rodamiento', 'tornillo', 'tuerca', 'herraje'],
        'Consumibles': ['silicón', 'silicon', 'sellador', 'sella', 'empaque', 'hule', 'cartucho', 'masilla']
    }
    
    try:
        with engine.connect() as conn:
            # Obtener todos los materiales
            result = conn.execute(text("SELECT id, name FROM app_materials WHERE category = 'Otros'"))
            materials = result.fetchall()
            
            categorized_count = 0
            
            for material in materials:
                material_id, material_name = material
                material_name_lower = material_name.lower()
                
                assigned_category = 'Otros'
                
                # Buscar categoria basándose en palabras clave
                for category, keywords in categories.items():
                    if any(keyword in material_name_lower for keyword in keywords):
                        assigned_category = category
                        break
                
                # Actualizar categoria
                if assigned_category != 'Otros':
                    conn.execute(text("""
                        UPDATE app_materials 
                        SET category = :category 
                        WHERE id = :material_id
                    """), {'category': assigned_category, 'material_id': material_id})
                    categorized_count += 1
                    print(f"   📋 {material_name} → {assigned_category}")
            
            conn.commit()
            print(f"\n✅ {categorized_count} materiales categorizados exitosamente")
            
    except Exception as e:
        print(f"❌ Error categorizando materiales: {e}")
        return False
    
    return True

def show_categorization_summary():
    """Mostrar resumen de categorización"""
    print("\n📊 Resumen de categorización:")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM app_materials 
                WHERE is_active = true 
                GROUP BY category 
                ORDER BY count DESC
            """))
            
            categories = result.fetchall()
            
            for category, count in categories:
                print(f"   📂 {category}: {count} materiales")
            
    except Exception as e:
        print(f"❌ Error mostrando resumen: {e}")

def main():
    print("🚀 Iniciando categorización de materiales...")
    
    # 1. Agregar columna category
    if not add_category_column():
        sys.exit(1)
    
    # 2. Categorizar materiales existentes
    if not categorize_existing_materials():
        sys.exit(1)
    
    # 3. Mostrar resumen
    show_categorization_summary()
    
    print("\n🎉 ¡Categorización completada exitosamente!")

if __name__ == "__main__":
    main()