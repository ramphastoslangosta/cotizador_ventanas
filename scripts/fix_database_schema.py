#!/usr/bin/env python3
"""
Script para agregar la columna category si no existe
"""

import os
from config import settings

def add_category_column_sql():
    """Generar SQL para agregar la columna category"""
    sql_commands = [
        # Agregar columna category si no existe
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'app_materials' 
                AND column_name = 'category'
            ) THEN
                ALTER TABLE app_materials 
                ADD COLUMN category TEXT NOT NULL DEFAULT 'Otros';
            END IF;
        END $$;
        """,
        
        # Actualizar materiales existentes con categorías basadas en nombre
        """
        UPDATE app_materials 
        SET category = CASE
            WHEN LOWER(name) LIKE '%perfil%' OR LOWER(name) LIKE '%riel%' OR LOWER(name) LIKE '%marco%' THEN 'Perfiles'
            WHEN LOWER(name) LIKE '%vidrio%' OR LOWER(name) LIKE '%cristal%' THEN 'Vidrio'
            WHEN LOWER(name) LIKE '%cerradura%' OR LOWER(name) LIKE '%manija%' OR LOWER(name) LIKE '%bisagra%' 
                 OR LOWER(name) LIKE '%rueda%' OR LOWER(name) LIKE '%tornillo%' OR LOWER(name) LIKE '%herraje%' THEN 'Herrajes'
            WHEN LOWER(name) LIKE '%silicón%' OR LOWER(name) LIKE '%silicon%' OR LOWER(name) LIKE '%sellador%' 
                 OR LOWER(name) LIKE '%empaque%' OR LOWER(name) LIKE '%cartucho%' THEN 'Consumibles'
            ELSE 'Otros'
        END
        WHERE category = 'Otros';
        """
    ]
    
    return sql_commands

def main():
    print("🔧 Generando script SQL para agregar columna category...")
    
    sql_commands = add_category_column_sql()
    
    sql_script = """
-- Script para agregar categorización a materiales
-- Ejecutar este script en la base de datos PostgreSQL

""" + "\n\n".join(sql_commands) + """

-- Verificar resultado
SELECT category, COUNT(*) as count 
FROM app_materials 
WHERE is_active = true 
GROUP BY category 
ORDER BY count DESC;
"""
    
    # Guardar script SQL
    with open('add_material_categories.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("✅ Script SQL generado: add_material_categories.sql")
    print("\n📋 Para ejecutar:")
    print("1. Conectarse a la base de datos PostgreSQL")
    print("2. Ejecutar: \\i add_material_categories.sql")
    print("\n💡 O usar herramientas como pgAdmin o DBeaver")
    
    # Mostrar también el database URL (sin password)
    db_url = settings.database_url
    if '@' in db_url:
        parts = db_url.split('@')
        host_part = parts[1]
        print(f"\n🔗 Database host: {host_part}")

if __name__ == "__main__":
    main()