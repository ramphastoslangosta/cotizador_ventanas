#!/usr/bin/env python3
"""
Script de verificación post-migración
Verifica que todos los cambios se aplicaron correctamente
"""

import requests
import json
from datetime import datetime

def print_header(title):
    """Imprimir encabezado decorado"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def verify_api_endpoints():
    """Verificar que los endpoints API estén funcionando"""
    print_header("VERIFICACIÓN DE ENDPOINTS API")
    
    base_url = "http://localhost:8000"
    endpoints_to_test = [
        "/api/materials",
        "/api/materials/by-category", 
        "/api/colors",
        "/api/debug/materials"
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            print(f"🔌 Probando {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "✅ OK",
                    "data_size": len(data) if isinstance(data, list) else "object"
                }
                print(f"   ✅ Status: {response.status_code}")
                
                if endpoint == "/api/materials/by-category":
                    if isinstance(data, dict) and "categories" in data:
                        categories = data["categories"]
                        print(f"   📊 Categorías encontradas: {len(categories)}")
                        for cat_name, materials in categories.items():
                            print(f"      📁 {cat_name}: {len(materials)} materiales")
                    else:
                        print(f"   📊 Datos: {type(data)}")
                        
                elif endpoint == "/api/debug/materials":
                    if isinstance(data, dict):
                        print(f"   📊 Total materiales: {data.get('total_materials', 'N/A')}")
                        print(f"   🏷️  Campo category: {data.get('has_category', 'N/A')}")
                        
            else:
                results[endpoint] = {
                    "status": f"❌ Error {response.status_code}",
                    "data_size": 0
                }
                print(f"   ❌ Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                "status": f"❌ Connection Error: {str(e)}",
                "data_size": 0
            }
            print(f"   ❌ Error de conexión: {e}")
    
    return results

def verify_categorization():
    """Verificar categorización de materiales"""
    print_header("VERIFICACIÓN DE CATEGORIZACIÓN")
    
    try:
        response = requests.get("http://localhost:8000/api/materials/by-category", timeout=10)
        
        if response.status_code != 200:
            print("❌ No se pudo obtener datos de categorización")
            return False
            
        data = response.json()
        
        if "categories" not in data:
            print("❌ Respuesta no tiene estructura de categorías")
            return False
            
        categories = data["categories"]
        expected_categories = ["Perfiles", "Vidrio", "Herrajes", "Consumibles"]
        
        print(f"📊 Total de categorías encontradas: {len(categories)}")
        
        for expected_cat in expected_categories:
            if expected_cat in categories:
                materials_count = len(categories[expected_cat])
                print(f"✅ {expected_cat}: {materials_count} materiales")
                
                # Verificar materiales específicos en Perfiles
                if expected_cat == "Perfiles":
                    profile_materials = categories[expected_cat]
                    materials_with_colors = [m for m in profile_materials if m.get("has_colors", False)]
                    print(f"   🎨 Perfiles con colores: {len(materials_with_colors)}")
                    
                    for material in materials_with_colors:
                        colors_count = len(material.get("colors", []))
                        print(f"      • {material.get('name', 'N/A')}: {colors_count} colores")
                        
            else:
                print(f"⚠️  {expected_cat}: No encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando categorización: {e}")
        return False

def verify_color_configuration():
    """Verificar configuración de colores"""
    print_header("VERIFICACIÓN DE CONFIGURACIÓN DE COLORES")
    
    try:
        # Verificar colores existentes
        response = requests.get("http://localhost:8000/api/colors", timeout=10)
        
        if response.status_code != 200:
            print("❌ No se pudo obtener lista de colores")
            return False
            
        colors = response.json()
        expected_colors = ["Natural", "Blanco", "Bronze", "Champagne", "Negro"]
        
        print(f"🎨 Total de colores encontrados: {len(colors)}")
        
        found_colors = [color.get("name") for color in colors]
        
        for expected_color in expected_colors:
            if expected_color in found_colors:
                print(f"✅ Color '{expected_color}' encontrado")
            else:
                print(f"⚠️  Color '{expected_color}' no encontrado")
        
        # Verificar colores en materiales específicos
        expected_profile_ids = [1, 2, 3, 4]  # IDs de perfiles según análisis
        
        for profile_id in expected_profile_ids:
            try:
                response = requests.get(f"http://localhost:8000/api/materials/{profile_id}/colors", timeout=10)
                
                if response.status_code == 200:
                    material_colors = response.json()
                    print(f"✅ Perfil ID {profile_id}: {len(material_colors)} colores configurados")
                    
                    for color_config in material_colors:
                        color_name = color_config.get("color_name", "N/A")
                        price = color_config.get("price_per_unit", 0)
                        print(f"      • {color_name}: ${price:.2f}")
                        
                else:
                    print(f"⚠️  Perfil ID {profile_id}: No se pudieron obtener colores")
                    
            except Exception as e:
                print(f"❌ Error verificando perfil {profile_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando colores: {e}")
        return False

def verify_ui_accessibility():
    """Verificar que la UI sea accesible"""
    print_header("VERIFICACIÓN DE ACCESIBILIDAD DE UI")
    
    try:
        # Verificar página principal del catálogo
        response = requests.get("http://localhost:8000/materials_catalog", timeout=10)
        
        if response.status_code == 200:
            print("✅ Página de catálogo de materiales accesible")
            
            # Verificar que contiene elementos clave
            content = response.text
            key_elements = [
                "materialsContainer",
                "categoryFilters", 
                "addMaterialModal",
                "colorsModal",
                "fetchMaterialsByCategory"
            ]
            
            for element in key_elements:
                if element in content:
                    print(f"✅ Elemento '{element}' encontrado en UI")
                else:
                    print(f"⚠️  Elemento '{element}' no encontrado en UI")
                    
            return True
            
        else:
            print(f"❌ Página no accesible: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando UI: {e}")
        return False

def generate_migration_report():
    """Generar reporte completo de verificación"""
    print_header("REPORTE DE VERIFICACIÓN POST-MIGRACIÓN")
    
    print(f"📅 Fecha de verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar todas las verificaciones
    api_results = verify_api_endpoints()
    categorization_ok = verify_categorization()
    colors_ok = verify_color_configuration()
    ui_ok = verify_ui_accessibility()
    
    # Resumen de resultados
    print_header("RESUMEN DE RESULTADOS")
    
    total_checks = 4
    passed_checks = 0
    
    if all(result["status"].startswith("✅") for result in api_results.values()):
        print("✅ Endpoints API: FUNCIONANDO")
        passed_checks += 1
    else:
        print("❌ Endpoints API: CON PROBLEMAS")
    
    if categorization_ok:
        print("✅ Categorización: COMPLETADA")
        passed_checks += 1
    else:
        print("❌ Categorización: CON PROBLEMAS")
    
    if colors_ok:
        print("✅ Configuración de Colores: COMPLETADA")
        passed_checks += 1
    else:
        print("❌ Configuración de Colores: CON PROBLEMAS")
    
    if ui_ok:
        print("✅ Interfaz de Usuario: FUNCIONANDO")
        passed_checks += 1
    else:
        print("❌ Interfaz de Usuario: CON PROBLEMAS")
    
    # Resultado final
    success_rate = (passed_checks / total_checks) * 100
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Verificaciones exitosas: {passed_checks}/{total_checks}")
    print(f"   📊 Porcentaje de éxito: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("✨ Todos los sistemas están funcionando correctamente")
        print("🚀 El sistema está listo para usar con las nuevas funcionalidades")
    elif success_rate >= 75:
        print("\n😊 ¡Migración mayormente exitosa!")
        print("🔧 Hay algunos problemas menores que revisar")
    else:
        print("\n⚠️  La migración tiene problemas significativos")
        print("🔧 Revisar los errores arriba y corregir antes de usar")
    
    # Instrucciones adicionales
    print(f"\n📋 PRÓXIMOS PASOS:")
    if success_rate == 100:
        print("   1. ✅ Sistema listo para uso en producción")
        print("   2. 📚 Entrenar usuarios en nuevas funcionalidades")
        print("   3. 📊 Monitorear performance y uso")
    else:
        print("   1. 🔧 Revisar y corregir problemas identificados")
        print("   2. 🔄 Ejecutar verificación nuevamente")
        print("   3. 📞 Consultar documentación de troubleshooting")
    
    return success_rate

def main():
    """Función principal"""
    print("🚀 INICIANDO VERIFICACIÓN POST-MIGRACIÓN")
    print("Verificando que todos los cambios se aplicaron correctamente...")
    
    try:
        success_rate = generate_migration_report()
        
        if success_rate == 100:
            exit(0)  # Éxito total
        elif success_rate >= 75:
            exit(1)  # Éxito parcial
        else:
            exit(2)  # Problemas significativos
            
    except KeyboardInterrupt:
        print("\n⏹️  Verificación interrumpida por el usuario")
        exit(3)
    except Exception as e:
        print(f"\n❌ Error inesperado durante verificación: {e}")
        exit(4)

if __name__ == "__main__":
    main()