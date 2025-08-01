#!/usr/bin/env python3
"""
Script para verificar que la selección de colores funciona en nueva cotización
"""
import requests
from datetime import datetime

def test_color_selection():
    """Verificar funcionalidad de selección de colores"""
    print("🎯 VERIFICANDO SELECCIÓN DE COLORES EN NUEVA COTIZACIÓN")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    # 1. Verificar que la página de nueva cotización se carga
    print("\n1️⃣ Verificando acceso a página de nueva cotización...")
    try:
        response = requests.get(f"{base_url}/quotes/new", timeout=10)
        if response.status_code == 200:
            print("   ✅ Página de nueva cotización accesible")
            content = response.text
            
            # Verificar elementos de color
            if "selected-profile-color" in content:
                print("   ✅ Selector de color de perfiles encontrado")
            else:
                print("   ❌ Selector de color de perfiles NO encontrado")
                
            if "Color de Perfiles" in content:
                print("   ✅ Etiqueta 'Color de Perfiles' encontrada")
            else:
                print("   ❌ Etiqueta 'Color de Perfiles' NO encontrada")
                
            if "loadProfileColors" in content:
                print("   ✅ Función loadProfileColors encontrada")
            else:
                print("   ❌ Función loadProfileColors NO encontrada")
                
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Verificar API de materiales por categoría (necesaria para colores)
    print("\n2️⃣ Verificando API de materiales por categoría...")
    try:
        response = requests.get(f"{base_url}/api/materials/by-category", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API de categorías funcionando")
            
            if 'categories' in data and 'Perfiles' in data['categories']:
                profiles = data['categories']['Perfiles']
                profiles_with_colors = [p for p in profiles if p.get('has_colors', False)]
                print(f"   📊 Perfiles totales: {len(profiles)}")
                print(f"   🎨 Perfiles con colores: {len(profiles_with_colors)}")
                
                if profiles_with_colors:
                    example_profile = profiles_with_colors[0]
                    print(f"   💡 Ejemplo: {example_profile['name']} tiene {len(example_profile.get('colors', []))} colores")
                    
                    # Mostrar colores disponibles
                    if example_profile.get('colors'):
                        print("   🎨 Colores disponibles:")
                        for color in example_profile['colors'][:3]:  # Solo mostrar primeros 3
                            print(f"      • {color['color_name']}: ${color['price_per_unit']}")
                
        else:
            print(f"   ❌ Error API: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error API: {e}")
    
    # 3. Verificar API de colores
    print("\n3️⃣ Verificando API de colores...")
    try:
        response = requests.get(f"{base_url}/api/colors", timeout=10)
        if response.status_code == 200:
            colors = response.json()
            print(f"   ✅ API de colores funcionando - {len(colors)} colores disponibles")
            
            for color in colors[:5]:  # Mostrar primeros 5
                print(f"      🎨 {color['name']} ({color['code']})")
                
        else:
            print(f"   ❌ Error API colores: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error API colores: {e}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("\n💡 Para probar la funcionalidad completa:")
    print("   🌐 Visita: http://localhost:8000/quotes/new")
    print("   🔧 Pasos a seguir:")
    print("      1. Llena los datos del cliente")
    print("      2. Haz clic en 'Agregar Ventana'")
    print("      3. Selecciona tipo de ventana y línea de aluminio")
    print("      4. Selecciona un producto")
    print("      5. ✨ NUEVO: Observa que aparecen colores disponibles")
    print("      6. Selecciona un color de perfil")
    print("      7. Completa dimensiones y tipo de vidrio")
    print("      8. Observa que la descripción incluye el color")
    print("      9. Calcula la cotización")
    
    return True

if __name__ == "__main__":
    test_color_selection()