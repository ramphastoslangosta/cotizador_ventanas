#!/usr/bin/env python3
"""
Pruebas comprensivas del sistema de materiales con colores
"""

import asyncio
import sys
import json
from typing import Dict, Any

async def test_imports():
    """Probar que todos los imports funcionen correctamente"""
    print("🔍 PRUEBA 1: Verificando imports...")
    
    try:
        # Test core imports
        from fastapi.testclient import TestClient
        print("  ✅ FastAPI TestClient")
        
        from main import app
        print("  ✅ Main app")
        
        from database import AppMaterial, Color, MaterialColor, DatabaseMaterialService, DatabaseColorService
        print("  ✅ Database models and services")
        
        from models.product_bom_models import AppMaterial as PydanticMaterial
        print("  ✅ Pydantic models")
        
        from models.color_models import ColorResponse, MaterialColorResponse
        print("  ✅ Color models")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")
        return False

def test_api_routes():
    """Probar que las rutas estén correctamente definidas"""
    print("\n🛣️  PRUEBA 2: Verificando rutas API...")
    
    try:
        from main import app
        
        # Obtener todas las rutas
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method not in ['HEAD', 'OPTIONS']:
                        routes.append(f"{method} {route.path}")
        
        # Rutas esperadas
        expected_routes = {
            "GET /api/materials": "Listar materiales",
            "POST /api/materials": "Crear material", 
            "PUT /api/materials/{material_id}": "Actualizar material",
            "DELETE /api/materials/{material_id}": "Eliminar material",
            "GET /api/materials/by-category": "Materiales por categoría",
            "GET /api/materials/{material_id}/colors": "Colores de material",
            "POST /api/materials/{material_id}/colors": "Agregar color a material",
            "DELETE /api/materials/colors/{material_color_id}": "Eliminar color de material",
            "GET /api/colors": "Listar colores",
            "POST /api/colors": "Crear color",
            "GET /api/debug/materials": "Debug materiales"
        }
        
        print(f"  📊 Total de rutas encontradas: {len(routes)}")
        
        missing_routes = []
        found_routes = []
        
        for expected_route, description in expected_routes.items():
            if expected_route in routes:
                found_routes.append(expected_route)
                print(f"  ✅ {expected_route} - {description}")
            else:
                missing_routes.append(expected_route)
                print(f"  ❌ {expected_route} - {description} (FALTANTE)")
        
        if missing_routes:
            print(f"\n  ⚠️  Rutas faltantes: {len(missing_routes)}")
            return False
        else:
            print(f"\n  🎉 Todas las rutas están presentes: {len(found_routes)}")
            return True
            
    except Exception as e:
        print(f"  ❌ Error verificando rutas: {e}")
        return False

def test_database_models():
    """Probar los modelos de base de datos"""
    print("\n🗄️  PRUEBA 3: Verificando modelos de base de datos...")
    
    try:
        from database import AppMaterial, Color, MaterialColor
        from sqlalchemy import Column
        
        # Verificar AppMaterial
        print("  📦 Verificando modelo AppMaterial...")
        required_fields = ['id', 'name', 'unit', 'cost_per_unit', 'is_active']
        optional_fields = ['category', 'selling_unit_length_m', 'description']
        
        for field in required_fields:
            if hasattr(AppMaterial, field):
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} (FALTANTE)")
                
        for field in optional_fields:
            if hasattr(AppMaterial, field):
                print(f"    ✅ {field} (opcional)")
            else:
                print(f"    ⚠️  {field} (opcional, no encontrado)")
        
        # Verificar Color
        print("  🎨 Verificando modelo Color...")
        color_fields = ['id', 'name', 'is_active', 'created_at']
        for field in color_fields:
            if hasattr(Color, field):
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} (FALTANTE)")
        
        # Verificar MaterialColor
        print("  🔗 Verificando modelo MaterialColor...")
        mc_fields = ['id', 'material_id', 'color_id', 'price_per_unit', 'is_available']
        for field in mc_fields:
            if hasattr(MaterialColor, field):
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} (FALTANTE)")
                
        return True
        
    except Exception as e:
        print(f"  ❌ Error verificando modelos: {e}")
        return False

def test_pydantic_models():
    """Probar los modelos Pydantic"""
    print("\n📋 PRUEBA 4: Verificando modelos Pydantic...")
    
    try:
        from models.product_bom_models import AppMaterial, MaterialUnit
        from models.color_models import ColorResponse, MaterialColorResponse
        
        # Test AppMaterial creation
        print("  📦 Probando creación de AppMaterial...")
        material_data = {
            "name": "Perfil Test",
            "unit": MaterialUnit.ML,
            "category": "Perfiles",
            "cost_per_unit": 125.50,
            "description": "Material de prueba"
        }
        
        material = AppMaterial(**material_data)
        print(f"    ✅ Material creado: {material.name}")
        
        # Test validation
        print("  🔍 Probando validaciones...")
        try:
            invalid_material = AppMaterial(
                name="",  # Should fail - empty name
                unit=MaterialUnit.ML,
                cost_per_unit=-10  # Should fail - negative cost
            )
            print("    ❌ Validación falló - material inválido fue aceptado")
            return False
        except Exception:
            print("    ✅ Validación funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error probando modelos Pydantic: {e}")
        return False

def test_service_layer():
    """Probar la capa de servicios"""
    print("\n⚙️  PRUEBA 5: Verificando capa de servicios...")
    
    try:
        from services.product_bom_service_db import ProductBOMServiceDB
        
        # Verificar métodos del servicio
        service_methods = [
            'get_all_materials',
            'get_material', 
            'create_material',
            'update_material',
            'delete_material'
        ]
        
        print("  🔧 Verificando métodos de ProductBOMServiceDB...")
        for method in service_methods:
            if hasattr(ProductBOMServiceDB, method):
                print(f"    ✅ {method}")
            else:
                print(f"    ❌ {method} (FALTANTE)")
        
        # Verificar servicios de base de datos
        from database import DatabaseMaterialService, DatabaseColorService
        
        print("  🗄️  Verificando DatabaseMaterialService...")
        db_methods = ['get_all_materials', 'get_material_by_id', 'create_material']
        for method in db_methods:
            if hasattr(DatabaseMaterialService, method):
                print(f"    ✅ {method}")
            else:
                print(f"    ❌ {method} (FALTANTE)")
        
        print("  🎨 Verificando DatabaseColorService...")
        color_methods = ['get_all_colors', 'create_color', 'get_material_colors']
        for method in color_methods:
            if hasattr(DatabaseColorService, method):
                print(f"    ✅ {method}")
            else:
                print(f"    ❌ {method} (FALTANTE)")
                
        return True
        
    except Exception as e:
        print(f"  ❌ Error verificando servicios: {e}")
        return False

def test_template_structure():
    """Probar la estructura del template"""
    print("\n🎨 PRUEBA 6: Verificando template materials_catalog.html...")
    
    try:
        template_path = "templates/materials_catalog.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar elementos clave
        required_elements = [
            'materialsContainer',
            'categoryFilters', 
            'addMaterialModal',
            'colorsModal',
            'fetchMaterialsByCategory',
            'fetchMaterialsLegacy',
            'manageColors',
            'addMaterialColor'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element in content:
                print(f"  ✅ {element}")
            else:
                missing_elements.append(element)
                print(f"  ❌ {element} (FALTANTE)")
        
        # Verificar funciones JavaScript críticas
        js_functions = [
            'function fetchMaterialsByCategory',
            'function fetchMaterialsLegacy', 
            'function renderMaterials',
            'function manageColors',
            'function addMaterialColor'
        ]
        
        print("\n  🟡 Verificando funciones JavaScript...")
        for func in js_functions:
            if func in content:
                print(f"    ✅ {func}")
            else:
                print(f"    ❌ {func} (FALTANTE)")
        
        return len(missing_elements) == 0
        
    except FileNotFoundError:
        print(f"  ❌ Archivo template no encontrado: {template_path}")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo template: {e}")
        return False

def test_sql_migration():
    """Probar el script de migración SQL"""
    print("\n📝 PRUEBA 7: Verificando script de migración SQL...")
    
    try:
        sql_path = "add_material_categories.sql"
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Verificar elementos clave del SQL
        required_sql_elements = [
            'ALTER TABLE app_materials',
            'ADD COLUMN category',
            'UPDATE app_materials',
            'SET category = CASE',
            'Perfiles',
            'Vidrio', 
            'Herrajes',
            'Consumibles'
        ]
        
        missing_sql = []
        for element in required_sql_elements:
            if element in sql_content:
                print(f"  ✅ {element}")
            else:
                missing_sql.append(element)
                print(f"  ❌ {element} (FALTANTE)")
        
        # Verificar que sea SQL válido básico
        if 'DO $$' in sql_content and 'END $$' in sql_content:
            print("  ✅ Estructura PL/pgSQL válida")
        else:
            print("  ⚠️  Estructura PL/pgSQL no detectada")
            
        return len(missing_sql) == 0
        
    except FileNotFoundError:
        print(f"  ❌ Archivo SQL no encontrado: {sql_path}")
        return False
    except Exception as e:
        print(f"  ❌ Error leyendo SQL: {e}")
        return False

async def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS COMPRENSIVAS DEL SISTEMA DE MATERIALES")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("API Routes", test_api_routes), 
        ("Database Models", test_database_models),
        ("Pydantic Models", test_pydantic_models),
        ("Service Layer", test_service_layer),
        ("Template Structure", test_template_structure),
        ("SQL Migration", test_sql_migration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
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
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✨ El sistema está listo para usar")
    else:
        print(f"\n⚠️  {failed} pruebas fallaron")
        print("🔧 Revisar los errores arriba para corregir")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_all_tests())