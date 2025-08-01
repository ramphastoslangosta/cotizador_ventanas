#!/usr/bin/env python3
"""
Script para probar los nuevos endpoints de materiales y colores
"""

import sys
import json

def test_api_endpoints_structure():
    """Verificar que la estructura de endpoints sea correcta"""
    print("🔍 Verificando estructura de endpoints...")
    
    # Verificar que los imports están correctos
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        print("✅ FastAPI app cargada correctamente")
        
        # Verificar rutas disponibles
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method != 'HEAD':  # Ignorar HEAD methods
                        routes.append(f"{method} {route.path}")
        
        print(f"\n📋 Rutas disponibles ({len(routes)}):")
        materials_routes = [r for r in routes if '/materials' in r]
        colors_routes = [r for r in routes if '/colors' in r]
        
        print("\n🎨 Rutas de Colores:")
        for route in colors_routes:
            print(f"  {route}")
            
        print("\n📦 Rutas de Materiales:")
        for route in materials_routes:
            print(f"  {route}")
        
        # Verificar endpoints específicos
        expected_endpoints = [
            "GET /api/materials",
            "POST /api/materials", 
            "PUT /api/materials/{material_id}",
            "DELETE /api/materials/{material_id}",
            "GET /api/materials/by-category",
            "GET /api/materials/{material_id}/colors",
            "POST /api/materials/{material_id}/colors",
            "DELETE /api/materials/colors/{material_color_id}",
            "GET /api/colors",
            "POST /api/colors"
        ]
        
        print(f"\n✅ Endpoints esperados:")
        for endpoint in expected_endpoints:
            if endpoint in routes:
                print(f"  ✅ {endpoint}")
            else:
                print(f"  ❌ {endpoint} - FALTANTE")
        
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando endpoints: {e}")
        return False
    
    return True

def check_database_models():
    """Verificar que los modelos de base de datos estén correctos"""
    print("\n🗄️ Verificando modelos de base de datos...")
    
    try:
        from database import AppMaterial, Color, MaterialColor
        
        # Verificar campos del modelo AppMaterial
        material_fields = []
        for field_name in dir(AppMaterial):
            if not field_name.startswith('_') and hasattr(getattr(AppMaterial, field_name), 'type'):
                material_fields.append(field_name)
        
        print(f"📦 Campos de AppMaterial: {material_fields}")
        
        # Verificar que existe el campo category
        if hasattr(AppMaterial, 'category'):
            print("✅ Campo 'category' encontrado en AppMaterial")
        else:
            print("❌ Campo 'category' NO encontrado en AppMaterial")
        
        # Verificar Color model
        color_fields = []
        for field_name in dir(Color):
            if not field_name.startswith('_') and hasattr(getattr(Color, field_name), 'type'):
                color_fields.append(field_name)
        
        print(f"🎨 Campos de Color: {color_fields}")
        
        # Verificar MaterialColor model
        material_color_fields = []
        for field_name in dir(MaterialColor):
            if not field_name.startswith('_') and hasattr(getattr(MaterialColor, field_name), 'type'):
                material_color_fields.append(field_name)
        
        print(f"🔗 Campos de MaterialColor: {material_color_fields}")
        
        print("✅ Modelos de base de datos verificados")
        
    except ImportError as e:
        print(f"❌ Error importando modelos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False
    
    return True

def main():
    print("🚀 Iniciando verificación del sistema de materiales con colores...")
    
    # Verificar endpoints
    if not test_api_endpoints_structure():
        print("❌ Falló la verificación de endpoints")
        sys.exit(1)
    
    # Verificar modelos
    if not check_database_models():
        print("❌ Falló la verificación de modelos")
        sys.exit(1)
    
    print("\n🎉 ¡Verificación completada exitosamente!")
    print("\n💡 Próximos pasos:")
    print("  1. Ejecutar el servidor: python main.py")
    print("  2. Ir a: http://localhost:8000/materials_catalog")
    print("  3. Probar la funcionalidad de categorías y colores")

if __name__ == "__main__":
    main()