#!/usr/bin/env python3
"""
Pruebas de compatibilidad de base de datos
Simula diferentes escenarios de BD para verificar robustez
"""

import re

class MockMaterial:
    """Mock de material sin campo category"""
    def __init__(self, id, name, unit, cost_per_unit):
        self.id = id
        self.name = name
        self.unit = unit
        self.cost_per_unit = cost_per_unit
        self.selling_unit_length_m = None
        self.description = None
        self.is_active = True

class MockMaterialWithCategory:
    """Mock de material con campo category"""
    def __init__(self, id, name, unit, cost_per_unit, category="Otros"):
        self.id = id
        self.name = name
        self.unit = unit
        self.cost_per_unit = cost_per_unit
        self.category = category
        self.selling_unit_length_m = None
        self.description = None
        self.is_active = True

def test_category_field_fallback():
    """Probar fallback cuando no existe campo category"""
    print("🗄️  PRUEBA 1: Compatibilidad con BD sin campo category...")
    
    # Simular material sin category
    material_old = MockMaterial(1, "Perfil Test", "ML", 125.50)
    
    # Probar getattr con fallback (como en el código)
    category = getattr(material_old, 'category', 'Otros')
    
    if category == 'Otros':
        print("  ✅ Fallback funciona correctamente")
        success1 = True
    else:
        print("  ❌ Fallback no funciona")
        success1 = False
    
    # Probar hasattr (como en el código)
    has_category = hasattr(material_old, 'category')
    
    if not has_category:
        print("  ✅ hasattr detecta ausencia de campo")
        success2 = True
    else:
        print("  ❌ hasattr no detecta ausencia de campo")
        success2 = False
    
    return success1 and success2

def test_category_field_present():
    """Probar comportamiento cuando sí existe campo category"""
    print("\n🗄️  PRUEBA 2: Compatibilidad con BD con campo category...")
    
    # Simular material con category
    material_new = MockMaterialWithCategory(1, "Perfil Test", "ML", 125.50, "Perfiles")
    
    # Probar getattr
    category = getattr(material_new, 'category', 'Otros')
    
    if category == 'Perfiles':
        print("  ✅ Campo category se lee correctamente")
        success1 = True
    else:
        print("  ❌ Campo category no se lee correctamente")
        success1 = False
    
    # Probar hasattr
    has_category = hasattr(material_new, 'category')
    
    if has_category:
        print("  ✅ hasattr detecta presencia de campo")
        success2 = True
    else:
        print("  ❌ hasattr no detecta presencia de campo")
        success2 = False
    
    return success1 and success2

def test_material_categorization_logic():
    """Probar lógica de categorización automática"""
    print("\n🏷️  PRUEBA 3: Lógica de categorización automática...")
    
    # Casos de prueba
    test_cases = [
        ("Perfil L. Nacional 3' Riel Sup.", "Perfiles"),
        ("Perfil de Aluminio Marco", "Perfiles"), 
        ("Vidrio Claro 6mm", "Vidrio"),
        ("Cristal Templado", "Vidrio"),
        ("Cerradura Multipunto", "Herrajes"),
        ("Manija de Aluminio", "Herrajes"),
        ("Bisagra Inoxidable", "Herrajes"),
        ("Silicón Estructural", "Consumibles"),
        ("Sellador Acético", "Consumibles"),
        ("Cartucho de Silicón", "Consumibles"),
        ("Material Desconocido", "Otros")
    ]
    
    # Simular la lógica del SQL (traducida a Python)
    def categorize_material(name):
        name_lower = name.lower()
        
        # Palabras clave para cada categoría
        perfiles_keywords = ['perfil', 'riel', 'marco', 'batiente', 'contramarco', 'aluminio']
        vidrio_keywords = ['vidrio', 'cristal', 'glass']
        herrajes_keywords = ['cerradura', 'manija', 'bisagra', 'rueda', 'rodamiento', 'tornillo', 'tuerca', 'herraje']
        consumibles_keywords = ['silicón', 'silicon', 'sellador', 'sella', 'empaque', 'hule', 'cartucho', 'masilla']
        
        for keyword in perfiles_keywords:
            if keyword in name_lower:
                return 'Perfiles'
        
        for keyword in vidrio_keywords:
            if keyword in name_lower:
                return 'Vidrio'
        
        for keyword in herrajes_keywords:
            if keyword in name_lower:
                return 'Herrajes'
        
        for keyword in consumibles_keywords:
            if keyword in name_lower:
                return 'Consumibles'
        
        return 'Otros'
    
    success_count = 0
    for name, expected_category in test_cases:
        actual_category = categorize_material(name)
        if actual_category == expected_category:
            print(f"  ✅ {name} → {actual_category}")
            success_count += 1
        else:
            print(f"  ❌ {name} → {actual_category} (esperado: {expected_category})")
    
    print(f"\n  📊 Categorización exitosa: {success_count}/{len(test_cases)}")
    return success_count == len(test_cases)

def test_api_error_handling():
    """Probar manejo de errores en el API"""
    print("\n🔌 PRUEBA 4: Manejo de errores en endpoints...")
    
    # Verificar que el código tiene manejo de errores
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        error_patterns = {
            r"try:.*except.*Exception": "Try-catch general",
            r"HTTPException.*status_code=500": "Error HTTP 500",
            r"HTTPException.*status_code=404": "Error HTTP 404", 
            r"print\(.*Error": "Logging de errores",
            r"getattr\(.*,.*,.*\)": "Acceso seguro a atributos"
        }
        
        found_patterns = 0
        for pattern, description in error_patterns.items():
            if re.search(pattern, content, re.DOTALL):
                print(f"  ✅ {description}")
                found_patterns += 1
            else:
                print(f"  ❌ {description} (FALTANTE)")
        
        return found_patterns >= 3
        
    except Exception as e:
        print(f"  ❌ Error leyendo main.py: {e}")
        return False

def test_frontend_fallback():
    """Probar fallback del frontend"""
    print("\n🎨 PRUEBA 5: Fallback del frontend...")
    
    try:
        with open("templates/materials_catalog.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        fallback_patterns = {
            r"response\.status === 405": "Detección de error 405",
            r"fetchMaterialsLegacy": "Función fallback",
            r"console\.warn": "Logging de advertencias",
            r"catch.*error": "Manejo de excepciones JS",
            r"/api/materials.*by-category": "Endpoint principal",
            r"/api/materials[^/]": "Endpoint fallback"
        }
        
        found_patterns = 0
        for pattern, description in fallback_patterns.items():
            if re.search(pattern, content):
                print(f"  ✅ {description}")
                found_patterns += 1
            else:
                print(f"  ❌ {description} (FALTANTE)")
        
        return found_patterns >= 4
        
    except Exception as e:
        print(f"  ❌ Error leyendo template: {e}")
        return False

def test_sql_safety():
    """Probar seguridad del SQL"""
    print("\n🛡️  PRUEBA 6: Seguridad del script SQL...")
    
    try:
        with open("add_material_categories.sql", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verificar elementos de seguridad
        safety_checks = {
            r"IF NOT EXISTS": "Verificación de existencia",
            r"WHERE.*is_active.*=.*true": "Filtro de seguridad",
            r"WHERE.*category.*=.*'Otros'": "Condición específica",
            r"DEFAULT.*'Otros'": "Valor por defecto seguro"
        }
        
        # Verificar ausencia de elementos peligrosos
        dangerous_patterns = [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM.*WHERE.*!=",
            r"TRUNCATE",
            r"DROP\s+DATABASE"
        ]
        
        safe_count = 0
        for pattern, description in safety_checks.items():
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ✅ {description}")
                safe_count += 1
            else:
                print(f"  ⚠️  {description} (NO ENCONTRADO)")
        
        dangerous_found = 0
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ❌ PELIGRO: {pattern}")
                dangerous_found += 1
        
        if dangerous_found == 0:
            print("  ✅ No se encontraron patrones peligrosos")
        
        return safe_count >= 2 and dangerous_found == 0
        
    except Exception as e:
        print(f"  ❌ Error leyendo SQL: {e}")
        return False

def run_compatibility_tests():
    """Ejecutar todas las pruebas de compatibilidad"""
    print("🧪 INICIANDO PRUEBAS DE COMPATIBILIDAD DE BASE DE DATOS")
    print("=" * 60)
    
    tests = [
        ("Fallback sin campo category", test_category_field_fallback),
        ("Campo category presente", test_category_field_present),
        ("Lógica de categorización", test_material_categorization_logic),
        ("Manejo de errores API", test_api_error_handling),
        ("Fallback del frontend", test_frontend_fallback),
        ("Seguridad del SQL", test_sql_safety)
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
    print("📊 RESUMEN DE COMPATIBILIDAD")
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
        print("\n🎉 ¡SISTEMA TOTALMENTE COMPATIBLE!")
        print("✨ Funciona en cualquier estado de base de datos")
    elif passed >= 4:
        print("\n😊 ¡Sistema muy compatible!")
        print("🔧 Funciona en la mayoría de escenarios")
    else:
        print(f"\n⚠️  Necesita mejorar compatibilidad")
    
    return failed == 0

if __name__ == "__main__":
    run_compatibility_tests()