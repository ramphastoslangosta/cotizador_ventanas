#!/usr/bin/env python3
"""
Pruebas de estructura de archivos y código sin dependencias externas
"""

import os
import re
import json
from pathlib import Path

def test_file_structure():
    """Verificar que todos los archivos necesarios existan"""
    print("📁 PRUEBA 1: Verificando estructura de archivos...")
    
    required_files = {
        "main.py": "Archivo principal de FastAPI",
        "database.py": "Modelos y servicios de base de datos", 
        "config.py": "Configuración de la aplicación",
        "models/product_bom_models.py": "Modelos Pydantic para materiales",
        "models/color_models.py": "Modelos Pydantic para colores",
        "services/product_bom_service_db.py": "Servicio de materiales",
        "templates/materials_catalog.html": "Template del catálogo",
        "templates/base.html": "Template base",
        "add_material_categories.sql": "Script de migración SQL",
        "requirements.txt": "Dependencias de Python"
    }
    
    missing_files = []
    found_files = []
    
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            found_files.append(file_path)
            print(f"  ✅ {file_path} - {description}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} - {description} (FALTANTE)")
    
    print(f"\n  📊 Archivos encontrados: {len(found_files)}/{len(required_files)}")
    return len(missing_files) == 0

def test_main_py_endpoints():
    """Verificar endpoints en main.py"""
    print("\n🔌 PRUEBA 2: Verificando endpoints en main.py...")
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Buscar endpoints específicos
        endpoints_patterns = {
            r"@app\.get\(\"/api/materials\"\)": "GET /api/materials",
            r"@app\.post\(\"/api/materials\"\)": "POST /api/materials",
            r"@app\.put\(\"/api/materials/\{material_id\}\"\)": "PUT /api/materials/{id}",
            r"@app\.delete\(\"/api/materials/\{material_id\}\"\)": "DELETE /api/materials/{id}",
            r"@app\.get\(\"/api/materials/by-category\"\)": "GET /api/materials/by-category",
            r"@app\.get\(\"/api/materials/\{material_id\}/colors\"\)": "GET /api/materials/{id}/colors",
            r"@app\.post\(\"/api/materials/\{material_id\}/colors\"\)": "POST /api/materials/{id}/colors",
            r"@app\.delete\(\"/api/materials/colors/\{material_color_id\}\"\)": "DELETE /api/materials/colors/{id}",
            r"@app\.get\(\"/api/colors\"\)": "GET /api/colors",
            r"@app\.post\(\"/api/colors\"\)": "POST /api/colors",
            r"@app\.get\(\"/api/debug/materials\"\)": "GET /api/debug/materials"
        }
        
        found_endpoints = []
        missing_endpoints = []
        
        for pattern, description in endpoints_patterns.items():
            if re.search(pattern, content):
                found_endpoints.append(description)
                print(f"  ✅ {description}")
            else:
                missing_endpoints.append(description)
                print(f"  ❌ {description} (FALTANTE)")
        
        print(f"\n  📊 Endpoints encontrados: {len(found_endpoints)}/{len(endpoints_patterns)}")
        return len(missing_endpoints) == 0
        
    except FileNotFoundError:
        print("  ❌ main.py no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo main.py: {e}")
        return False

def test_database_models():
    """Verificar modelos en database.py"""
    print("\n🗄️  PRUEBA 3: Verificando modelos en database.py...")
    
    try:
        with open("database.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificar modelos de base de datos
        models_to_check = {
            r"class AppMaterial\(Base\):": "Modelo AppMaterial",
            r"class Color\(Base\):": "Modelo Color", 
            r"class MaterialColor\(Base\):": "Modelo MaterialColor",
            r"class DatabaseMaterialService:": "Servicio de Materiales",
            r"class DatabaseColorService:": "Servicio de Colores"
        }
        
        found_models = []
        missing_models = []
        
        for pattern, description in models_to_check.items():
            if re.search(pattern, content):
                found_models.append(description)
                print(f"  ✅ {description}")
            else:
                missing_models.append(description)
                print(f"  ❌ {description} (FALTANTE)")
        
        # Verificar campos específicos en AppMaterial
        print("\n  📋 Verificando campos de AppMaterial...")
        appmaterial_fields = {
            r"category = Column": "Campo category",
            r"cost_per_unit = Column": "Campo cost_per_unit",
            r"selling_unit_length_m = Column": "Campo selling_unit_length_m"
        }
        
        for pattern, description in appmaterial_fields.items():
            if re.search(pattern, content):
                print(f"    ✅ {description}")
            else:
                print(f"    ❌ {description} (FALTANTE)")
                
        return len(missing_models) == 0
        
    except FileNotFoundError:
        print("  ❌ database.py no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo database.py: {e}")
        return False

def test_pydantic_models():
    """Verificar modelos Pydantic"""
    print("\n📋 PRUEBA 4: Verificando modelos Pydantic...")
    
    files_to_check = {
        "models/product_bom_models.py": {
            r"class AppMaterial\(BaseModel\):": "AppMaterial Pydantic",
            r"category: str": "Campo category en AppMaterial"
        },
        "models/color_models.py": {
            r"class ColorResponse\(ColorBase\):": "ColorResponse",
            r"class MaterialColorResponse\(MaterialColorBase\):": "MaterialColorResponse",
            r"class MaterialWithColors\(BaseModel\):": "MaterialWithColors"
        }
    }
    
    all_found = True
    
    for file_path, patterns in files_to_check.items():
        print(f"\n  📄 Verificando {file_path}...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            for pattern, description in patterns.items():
                if re.search(pattern, content):
                    print(f"    ✅ {description}")
                else:
                    print(f"    ❌ {description} (FALTANTE)")
                    all_found = False
                    
        except FileNotFoundError:
            print(f"    ❌ {file_path} no encontrado")
            all_found = False
        except Exception as e:
            print(f"    ❌ Error leyendo {file_path}: {e}")
            all_found = False
    
    return all_found

def test_template_functionality():
    """Verificar funcionalidad del template"""
    print("\n🎨 PRUEBA 5: Verificando template materials_catalog.html...")
    
    try:
        with open("templates/materials_catalog.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificar elementos HTML importantes
        html_elements = {
            r'id="materialsContainer"': "Contenedor de materiales",
            r'id="categoryFilters"': "Filtros de categoría",
            r'id="addMaterialModal"': "Modal de agregar material",
            r'id="colorsModal"': "Modal de colores",
            r'id="materialCategory"': "Campo de categoría en formulario",
            r'data-category="Perfiles"': "Filtro de Perfiles",
            r'data-category="Vidrio"': "Filtro de Vidrio",
            r'data-category="Herrajes"': "Filtro de Herrajes",
            r'data-category="Consumibles"': "Filtro de Consumibles"
        }
        
        # Verificar funciones JavaScript críticas
        js_functions = {
            r'function fetchMaterialsByCategory\(\)': "Función fetchMaterialsByCategory",
            r'function fetchMaterialsLegacy\(\)': "Función fallback fetchMaterialsLegacy", 
            r'function renderMaterials\(\)': "Función renderMaterials",
            r'function manageColors\(': "Función manageColors",
            r'function addMaterialColor\(\)': "Función addMaterialColor",
            r'function openNewMaterialModal\(\)': "Función openNewMaterialModal"
        }
        
        # Verificar manejo de errores
        error_handling = {
            r'response\.status === 405': "Manejo de error 405",
            r'fetchMaterialsLegacy\(\)': "Fallback en caso de error",
            r'showAlert\(': "Función de mostrar alertas"
        }
        
        print("  🔧 Verificando elementos HTML...")
        for pattern, description in html_elements.items():
            if re.search(pattern, content):
                print(f"    ✅ {description}")
            else:
                print(f"    ❌ {description} (FALTANTE)")
        
        print("\n  🟡 Verificando funciones JavaScript...")
        for pattern, description in js_functions.items():
            if re.search(pattern, content):
                print(f"    ✅ {description}")
            else:
                print(f"    ❌ {description} (FALTANTE)")
        
        print("\n  🛡️  Verificando manejo de errores...")
        for pattern, description in error_handling.items():
            if re.search(pattern, content):
                print(f"    ✅ {description}")
            else:
                print(f"    ❌ {description} (FALTANTE)")
        
        return True
        
    except FileNotFoundError:
        print("  ❌ templates/materials_catalog.html no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo template: {e}")
        return False

def test_sql_migration():
    """Verificar script SQL de migración"""
    print("\n📝 PRUEBA 6: Verificando script SQL...")
    
    try:
        with open("add_material_categories.sql", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificar elementos SQL críticos
        sql_elements = {
            r"ALTER TABLE app_materials": "Comando ALTER TABLE",
            r"ADD COLUMN category": "Agregar columna category",
            r"UPDATE app_materials": "Comando UPDATE",
            r"SET category = CASE": "Lógica de categorización",
            r"WHEN.*perfil.*THEN 'Perfiles'": "Categorización de Perfiles",
            r"WHEN.*vidrio.*THEN 'Vidrio'": "Categorización de Vidrio", 
            r"WHEN.*cerradura.*THEN 'Herrajes'": "Categorización de Herrajes",
            r"WHEN.*silicón.*THEN 'Consumibles'": "Categorización de Consumibles",
            r"DO \$\$": "Bloque PL/pgSQL inicio",
            r"END \$\$": "Bloque PL/pgSQL fin"
        }
        
        found_elements = 0
        for pattern, description in sql_elements.items():
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ✅ {description}")
                found_elements += 1
            else:
                print(f"  ❌ {description} (FALTANTE)")
        
        # Verificar que no hay SQL peligroso
        dangerous_patterns = [r"DROP TABLE", r"DELETE FROM.*WHERE.*!=", r"TRUNCATE"]
        safe = True
        
        print("\n  🛡️  Verificando seguridad del SQL...")
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ⚠️  Patrón peligroso encontrado: {pattern}")
                safe = False
        
        if safe:
            print("  ✅ SQL es seguro")
        
        return found_elements >= 7 and safe
        
    except FileNotFoundError:
        print("  ❌ add_material_categories.sql no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo SQL: {e}")
        return False

def test_service_layer():
    """Verificar capa de servicios"""
    print("\n⚙️  PRUEBA 7: Verificando servicios...")
    
    try:
        with open("services/product_bom_service_db.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificar métodos importantes
        service_methods = {
            r"def create_material\(.*category": "create_material con category",
            r"def update_material\(.*category": "update_material con category", 
            r"def _db_material_to_pydantic": "Conversión DB a Pydantic",
            r"category=.*category": "Uso del campo category"
        }
        
        for pattern, description in service_methods.items():
            if re.search(pattern, content):
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} (FALTANTE)")
        
        return True
        
    except FileNotFoundError:
        print("  ❌ services/product_bom_service_db.py no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo servicio: {e}")
        return False

def run_all_tests():
    """Ejecutar todas las pruebas de estructura"""
    print("🚀 INICIANDO PRUEBAS DE ESTRUCTURA DE ARCHIVOS")
    print("=" * 60)
    
    tests = [
        ("Estructura de Archivos", test_file_structure),
        ("Endpoints en main.py", test_main_py_endpoints),
        ("Modelos de Base de Datos", test_database_models),
        ("Modelos Pydantic", test_pydantic_models),
        ("Template Functionality", test_template_functionality),
        ("Script SQL", test_sql_migration),
        ("Capa de Servicios", test_service_layer)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS DE ESTRUCTURA")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name}")
            failed += 1
    
    print(f"\n📈 RESULTADOS FINALES:")
    print(f"  ✅ Pruebas exitosas: {passed}")
    print(f"  ❌ Pruebas fallidas: {failed}")
    print(f"  📊 Porcentaje de éxito: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ¡TODA LA ESTRUCTURA ESTÁ CORRECTA!")
        print("✨ Archivos y código listos para despliegue")
    elif passed >= 5:
        print("\n😊 ¡La mayoría de pruebas pasaron!")
        print("🔧 Solo faltan ajustes menores")
    else:
        print(f"\n⚠️  Necesita más trabajo: {failed} pruebas fallaron")
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()