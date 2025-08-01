#!/usr/bin/env python3
"""
Verificación del estado actual antes de la migración
"""

import requests
from datetime import datetime

def check_system_status():
    """Verificar estado actual del sistema"""
    print("🔍 VERIFICANDO ESTADO ACTUAL DEL SISTEMA")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    try:
        # Verificar endpoint básico de materiales
        print("\n1️⃣ Verificando endpoint básico /api/materials...")
        response = requests.get(f"{base_url}/api/materials", timeout=10)
        
        if response.status_code == 200:
            materials = response.json()
            print(f"   ✅ Endpoint funcionando")
            print(f"   📊 Materiales encontrados: {len(materials)}")
            
            # Verificar si ya tienen campo category
            if materials and isinstance(materials[0], dict):
                first_material = materials[0]
                has_category = 'category' in first_material
                print(f"   🏷️  Campo 'category' existe: {has_category}")
                
                if has_category:
                    print("   ⚠️  ATENCIÓN: El campo 'category' ya existe")
                    print("   💡 La migración de categorización puede ya estar aplicada")
                else:
                    print("   ✅ Campo 'category' no existe - migración necesaria")
                    
                # Mostrar algunos materiales de ejemplo
                print("\n   📋 Primeros 5 materiales:")
                for i, material in enumerate(materials[:5]):
                    name = material.get('name', 'N/A')
                    price = material.get('cost_per_unit', 0)
                    unit = material.get('unit', 'N/A')
                    category = material.get('category', 'NO CATEGORY')
                    print(f"      {i+1}. {name} - ${price}/{unit} [{category}]")
                    
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: No se puede conectar al servidor")
        print("   💡 Asegúrate de que el servidor esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False
    
    try:
        # Verificar endpoint de categorías
        print("\n2️⃣ Verificando endpoint /api/materials/by-category...")
        response = requests.get(f"{base_url}/api/materials/by-category", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Endpoint funcionando")
            
            if 'categories' in data:
                categories = data['categories']
                print(f"   📊 Categorías encontradas: {len(categories)}")
                for cat_name, materials in categories.items():
                    print(f"      📁 {cat_name}: {len(materials)} materiales")
            else:
                print("   ⚠️  Estructura de respuesta inesperada")
                
        elif response.status_code == 405:
            print("   ⚠️  Error 405 - Usar fallback automático")
        elif response.status_code == 500:
            print("   ⚠️  Error 500 - Campo category probablemente no existe")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Error con endpoint categorías: {e}")
    
    try:
        # Verificar colores
        print("\n3️⃣ Verificando colores existentes...")
        response = requests.get(f"{base_url}/api/colors", timeout=10)
        
        if response.status_code == 200:
            colors = response.json()
            print(f"   ✅ Endpoint de colores funcionando")
            print(f"   🎨 Colores encontrados: {len(colors)}")
            
            if colors:
                print("   🎨 Colores existentes:")
                for color in colors:
                    name = color.get('name', 'N/A')
                    code = color.get('code', 'N/A')
                    print(f"      • {name} ({code})")
            else:
                print("   📝 No hay colores configurados - migración necesaria")
                
        else:
            print(f"   ❌ Error en colores: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Error con endpoint colores: {e}")
    
    # Verificar UI
    try:
        print("\n4️⃣ Verificando acceso a UI...")
        response = requests.get(f"{base_url}/materials_catalog", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ UI del catálogo accesible")
        else:
            print(f"   ⚠️  UI status: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Error accediendo UI: {e}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN PRE-MIGRACIÓN COMPLETADA")
    print("\n💡 RECOMENDACIÓN:")
    print("   Si todo se ve bien, podemos proceder con la migración")
    print("   Los errores 405/500 en categorías son normales antes de migrar")
    
    return True

if __name__ == "__main__":
    check_system_status()