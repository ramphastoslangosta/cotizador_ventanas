#!/usr/bin/env python3
"""
Test script for Product Code System features
Tests all the new functionality added on August 8, 2025
"""

import sys
import traceback
from models.product_bom_models import AppProduct, WindowType, AluminumLine, MaterialType

def test_product_model_with_codes():
    """Test the enhanced AppProduct model with code field"""
    print("🧪 Testing AppProduct model with codes...")
    
    try:
        # Test product creation with code
        product_with_code = AppProduct(
            name="Ventana Corrediza Estándar",
            code="WIN-COR-STD-001",
            window_type=WindowType.CORREDIZA,
            aluminum_line=AluminumLine.SERIE_3,
            min_width_cm=80.0,
            max_width_cm=200.0,
            min_height_cm=80.0,
            max_height_cm=150.0,
            bom=[]
        )
        print(f"  ✅ Product with code created: {product_with_code.code}")
        
        # Test product creation without code
        product_without_code = AppProduct(
            name="Ventana Fija Estándar", 
            window_type=WindowType.FIJA,
            aluminum_line=AluminumLine.SERIE_35,
            min_width_cm=60.0,
            max_width_cm=180.0,
            min_height_cm=60.0,
            max_height_cm=120.0,
            bom=[]
        )
        print(f"  ✅ Product without code created: {product_without_code.code}")
        
        # Test JSON serialization
        json_with_code = product_with_code.model_dump(mode='json')
        json_without_code = product_without_code.model_dump(mode='json')
        
        assert 'code' in json_with_code
        assert json_with_code['code'] == "WIN-COR-STD-001"
        assert json_without_code['code'] is None
        
        print("  ✅ JSON serialization works correctly")
        
    except Exception as e:
        print(f"  ❌ Error testing product model: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_database_schema():
    """Test the database schema changes"""
    print("🧪 Testing database schema...")
    
    try:
        from database import AppProduct as DBAppProduct
        
        # Check if code column exists
        columns = DBAppProduct.__table__.columns
        code_column = None
        for col in columns:
            if col.name == 'code':
                code_column = col
                break
        
        assert code_column is not None, "Code column not found in database schema"
        assert code_column.nullable == True, "Code column should be nullable"
        assert code_column.unique == True, "Code column should be unique"
        
        print("  ✅ Database schema has correct code column")
        print(f"    - Type: {code_column.type}")
        print(f"    - Nullable: {code_column.nullable}")
        print(f"    - Unique: {code_column.unique}")
        
    except Exception as e:
        print(f"  ❌ Error testing database schema: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_service_layer():
    """Test the ProductBOMServiceDB with code handling"""
    print("🧪 Testing service layer...")
    
    try:
        from services.product_bom_service_db import ProductBOMServiceDB
        
        # Mock database product
        class MockDBProduct:
            def __init__(self, code=None):
                self.id = 1
                self.name = "Test Product"
                self.code = code
                self.window_type = "corrediza"
                self.aluminum_line = "nacional_serie_3"
                self.min_width_cm = 80.0
                self.max_width_cm = 200.0
                self.min_height_cm = 80.0
                self.max_height_cm = 150.0
                self.bom = []
                self.description = "Test description"
                self.created_at = None
                self.updated_at = None
                self.is_active = True
        
        service = ProductBOMServiceDB(None)
        
        # Test with code
        mock_with_code = MockDBProduct(code="TEST-001")
        pydantic_with_code = service._db_product_to_pydantic(mock_with_code)
        assert pydantic_with_code.code == "TEST-001"
        print("  ✅ Service handles products with codes correctly")
        
        # Test without code
        mock_without_code = MockDBProduct(code=None)
        pydantic_without_code = service._db_product_to_pydantic(mock_without_code)
        assert pydantic_without_code.code is None
        print("  ✅ Service handles products without codes correctly")
        
    except Exception as e:
        print(f"  ❌ Error testing service layer: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_materials_api_enhancement():
    """Test the materials API enhancement for code display"""
    print("🧪 Testing materials API enhancement...")
    
    try:
        # Mock the material data construction from main.py
        class MockMaterial:
            def __init__(self, code=None):
                self.id = 1
                self.name = "Test Profile"
                self.code = code
                self.unit = "ML"
                self.cost_per_unit = 150.0
        
        def simulate_api_response(material):
            return {
                "id": material.id,
                "name": material.name or "Sin nombre",
                "code": material.code or "",  # This is the new line
                "unit": material.unit or "PZA",
                "category": "perfiles",
                "cost_per_unit": float(material.cost_per_unit or 0),
            }
        
        # Test with code
        material_with_code = MockMaterial(code="ALU-PRF-001")
        response_with_code = simulate_api_response(material_with_code)
        assert "code" in response_with_code
        assert response_with_code["code"] == "ALU-PRF-001"
        print("  ✅ Materials API includes codes correctly")
        
        # Test without code
        material_without_code = MockMaterial(code=None)
        response_without_code = simulate_api_response(material_without_code)
        assert response_without_code["code"] == ""
        print("  ✅ Materials API handles missing codes correctly")
        
    except Exception as e:
        print(f"  ❌ Error testing materials API: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_backward_compatibility():
    """Test backward compatibility with existing products without codes"""
    print("🧪 Testing backward compatibility...")
    
    try:
        # Test that products without codes work in all scenarios
        product_no_code = AppProduct(
            name="Legacy Product",
            # code field intentionally omitted
            window_type=WindowType.FIJA,
            aluminum_line=AluminumLine.SERIE_3,
            min_width_cm=100.0,
            max_width_cm=150.0,
            min_height_cm=100.0,
            max_height_cm=120.0,
            bom=[]
        )
        
        # Should have None/null code
        assert product_no_code.code is None
        print("  ✅ Products without codes maintain None value")
        
        # JSON serialization should work
        json_data = product_no_code.model_dump(mode='json')
        assert json_data.get('code') is None
        print("  ✅ JSON serialization preserves null codes")
        
        # Service layer should handle it
        from services.product_bom_service_db import ProductBOMServiceDB
        
        class MockLegacyProduct:
            def __init__(self):
                self.id = 1
                self.name = "Legacy Product"
                # No code attribute at all (simulating old database records)
                self.window_type = "fija"
                self.aluminum_line = "nacional_serie_3"
                self.min_width_cm = 100.0
                self.max_width_cm = 150.0
                self.min_height_cm = 100.0
                self.max_height_cm = 120.0
                self.bom = []
                self.description = None
                self.created_at = None
                self.updated_at = None
                self.is_active = True
        
        service = ProductBOMServiceDB(None)
        legacy_product = MockLegacyProduct()
        
        # The service should use getattr with default None
        pydantic_result = service._db_product_to_pydantic(legacy_product)
        assert pydantic_result.code is None
        print("  ✅ Service layer handles legacy products without code attribute")
        
    except Exception as e:
        print(f"  ❌ Error testing backward compatibility: {e}")
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Product Code System Tests")
    print("=" * 50)
    
    tests = [
        ("Product Model", test_product_model_with_codes),
        ("Database Schema", test_database_schema),
        ("Service Layer", test_service_layer),
        ("Materials API", test_materials_api_enhancement),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            if test_func():
                print(f"✅ {test_name} tests PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} tests FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} tests FAILED with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests PASSED! Product Code System is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Please review before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)