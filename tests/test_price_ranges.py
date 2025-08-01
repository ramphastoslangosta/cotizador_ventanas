#!/usr/bin/env python3
"""
Script para verificar que los rangos de precios se muestran correctamente
"""
import requests
from datetime import datetime

def test_price_ranges():
    """Verificar rangos de precios en la UI"""
    print("🎯 VERIFICANDO RANGOS DE PRECIOS EN TARJETAS")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    # 1. Verificar que la página se carga
    print("\n1️⃣ Verificando acceso a página de materiales...")
    try:
        response = requests.get(f"{base_url}/materials_catalog", timeout=10)
        if response.status_code == 200:
            print("   ✅ Página de materiales accesible")
            content = response.text
            
            # Verificar que contiene los nuevos elementos
            if "Colores y precios:" in content:
                print("   ✅ Nueva etiqueta 'Colores y precios:' encontrada")
            else:
                print("   ⚠️  Etiqueta 'Colores y precios:' no encontrada")
                
            if "text-success fw-bold" in content:
                print("   ✅ Estilos de precios individuales encontrados")
            else:
                print("   ⚠️  Estilos de precios individuales no encontrados")
                
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Verificar datos de API por categorías
    print("\n2️⃣ Verificando datos de API...")
    try:
        response = requests.get(f"{base_url}/api/materials/by-category", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API de categorías funcionando")
            
            if 'categories' in data and 'Perfiles' in data['categories']:
                profiles = data['categories']['Perfiles']
                print(f"   📊 Perfiles encontrados: {len(profiles)}")
                
                # Verificar que tienen colores y precios
                profiles_with_colors = [p for p in profiles if p.get('has_colors', False)]
                print(f"   🎨 Perfiles con colores: {len(profiles_with_colors)}")
                
                # Mostrar ejemplo de rango de precios
                if profiles_with_colors:
                    profile = profiles_with_colors[0]
                    print(f"\n   💰 Ejemplo - {profile['name']}:")
                    if profile.get('colors'):
                        prices = [float(c['price_per_unit']) for c in profile['colors']]
                        min_price = min(prices)
                        max_price = max(prices)
                        print(f"      • Precio mínimo: ${min_price:.2f}")
                        print(f"      • Precio máximo: ${max_price:.2f}")
                        print(f"      • Rango: ${min_price:.2f} - ${max_price:.2f}")
                        print(f"      • Colores: {len(profile['colors'])}")
                
        else:
            print(f"   ❌ Error API: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error API: {e}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("\n💡 Para ver los cambios:")
    print("   🌐 Visita: http://localhost:8000/materials_catalog")
    print("   🔍 Busca la sección 'Perfiles' y observa:")
    print("      • Rangos de precios en el encabezado de cada tarjeta")
    print("      • Lista detallada de 'Colores y precios'")
    
    return True

if __name__ == "__main__":
    test_price_ranges()