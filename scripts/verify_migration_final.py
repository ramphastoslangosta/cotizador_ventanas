#!/usr/bin/env python3
"""
Verificación final de migración sin autenticación
"""
import requests
import json
from datetime import datetime

def verify_final_migration():
    """Verificar migración final sin autenticación"""
    print("🎯 VERIFICACIÓN FINAL DE MIGRACIÓN")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    success_count = 0
    total_tests = 0
    
    # 1. Verificar colores disponibles
    print("\n1️⃣ Verificando colores disponibles...")
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/api/colors", timeout=10)
        if response.status_code == 200:
            colors = response.json()
            print(f"   ✅ Colores disponibles: {len(colors)}")
            for color in colors:
                name = color.get('name', 'N/A')
                code = color.get('code', 'N/A')
                print(f"      🎨 {name} ({code})")
            success_count += 1
        else:
            print(f"   ❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Verificar categorías de materiales
    print("\n2️⃣ Verificando categorías de materiales...")
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/api/materials/by-category", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Endpoint de categorías funcionando")
            if 'categories' in data:
                categories = data['categories']
                print(f"   📊 Categorías encontradas: {len(categories)}")
                for cat_name, materials in categories.items():
                    print(f"      📁 {cat_name}: {len(materials)} materiales")
            success_count += 1
        else:
            print(f"   ❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Verificar colores de material específico (perfil)
    print("\n3️⃣ Verificando colores de perfiles...")
    total_tests += 1
    try:
        # Probar algunos IDs de perfiles que sabemos existen
        profile_ids = [1, 2, 3, 4]  # IDs de perfiles de la migración
        found_colors = False
        
        for profile_id in profile_ids:
            try:
                response = requests.get(f"{base_url}/api/materials/{profile_id}/colors", timeout=10)
                if response.status_code == 200:
                    material_colors = response.json()
                    if material_colors:
                        print(f"   ✅ Perfil ID {profile_id}: {len(material_colors)} colores configurados")
                        for mc in material_colors[:2]:  # Solo mostrar primeros 2
                            color_name = mc.get('color_name', 'N/A')
                            price = mc.get('price_per_unit', 0)
                            print(f"      💰 {color_name}: ${price}")
                        found_colors = True
                        break
                else:
                    print(f"      ⚠️  Perfil ID {profile_id}: Status {response.status_code}")
            except:
                continue
                
        if found_colors:
            success_count += 1
        else:
            print("   ❌ No se encontraron colores configurados")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Verificar UI accesible
    print("\n4️⃣ Verificando acceso a UI...")
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/materials_catalog", timeout=10)
        if response.status_code == 200:
            print("   ✅ UI del catálogo accesible")
            success_count += 1
        else:
            print(f"   ❌ UI Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accediendo UI: {e}")
    
    # 5. Verificar debug endpoint
    print("\n5️⃣ Verificando debug de materiales...")
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/api/debug/materials", timeout=10)
        if response.status_code == 200:
            debug_data = response.json()
            print(f"   ✅ Debug endpoint funcionando")
            print(f"   📊 Total materiales: {debug_data.get('total_materials', 'N/A')}")
            print(f"   📊 Perfiles: {debug_data.get('profiles_count', 'N/A')}")
            print(f"   📊 Colores: {debug_data.get('colors_count', 'N/A')}")
            print(f"   📊 Combinaciones: {debug_data.get('material_colors_count', 'N/A')}")
            success_count += 1
        else:
            print(f"   ❌ Debug Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print(f"✅ Pruebas exitosas: {success_count}/{total_tests}")
    print(f"📈 Porcentaje de éxito: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 ¡MIGRACIÓN COMPLETAMENTE EXITOSA!")
        print("✅ Todas las funcionalidades están operativas")
        print("🚀 El sistema está listo para usar")
    elif success_count >= total_tests * 0.8:
        print("\n✅ ¡MIGRACIÓN MAYORMENTE EXITOSA!")
        print("⚠️  Algunas funcionalidades menores pueden necesitar ajustes")
        print("🚀 El sistema está listo para usar")
    else:
        print("\n⚠️  MIGRACIÓN PARCIALMENTE EXITOSA")
        print("🔧 Requiere revisión de algunas funcionalidades")
    
    return success_count == total_tests

if __name__ == "__main__":
    verify_final_migration()