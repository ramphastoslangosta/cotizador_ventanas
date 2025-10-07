"""
Unit tests for database-driven glass pricing

Tests the refactored get_glass_cost_per_m2() method to ensure:
1. Database prices are retrieved correctly
2. Fallback prices work when database fails
3. All 7 glass types are supported
4. Price updates via UI take effect
5. Backward compatibility maintained
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from database import SessionLocal, DatabaseMaterialService, AppMaterial as DBAppMaterial
from services.product_bom_service_db import (
    ProductBOMServiceDB,
    GLASS_TYPE_TO_MATERIAL_CODE,
    GLASS_FALLBACK_PRICES
)
from models.quote_models import GlassType
from models.product_bom_models import MaterialUnit


class TestGlassPricingDatabase:
    """Test suite for database-driven glass pricing"""

    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def material_service(self, db_session):
        """Create material service"""
        return DatabaseMaterialService(db_session)

    @pytest.fixture
    def bom_service(self, db_session):
        """Create BOM service"""
        return ProductBOMServiceDB(db_session)

    @pytest.fixture
    def sample_glass_materials(self, material_service, db_session):
        """Create sample glass materials in database"""
        glass_materials = []

        for glass_type, material_code in GLASS_TYPE_TO_MATERIAL_CODE.items():
            # Check if material already exists
            existing = material_service.get_material_by_code(material_code)
            if existing:
                glass_materials.append(existing)
                continue

            # Create glass material with code
            material = material_service.create_material(
                name=f"Test {glass_type.value}",
                code=material_code,
                unit=MaterialUnit.M2.value,
                category="Vidrio",
                cost_per_unit=Decimal("100.00"),  # Test price
                description=f"Test glass material for {glass_type.value}"
            )
            glass_materials.append(material)

        return glass_materials

    def test_glass_type_mapping_complete(self):
        """Test that all 7 glass types have material code mappings"""
        assert len(GLASS_TYPE_TO_MATERIAL_CODE) == 7, "Missing glass type mappings"

        for glass_type in GlassType:
            assert glass_type in GLASS_TYPE_TO_MATERIAL_CODE, \
                f"Glass type {glass_type} not in mapping"

            material_code = GLASS_TYPE_TO_MATERIAL_CODE[glass_type]
            assert material_code.startswith("VID-"), \
                f"Material code {material_code} doesn't follow VID- pattern"

    def test_fallback_prices_complete(self):
        """Test that all 7 glass types have fallback prices"""
        assert len(GLASS_FALLBACK_PRICES) == 7, "Missing fallback prices"

        for glass_type in GlassType:
            assert glass_type in GLASS_FALLBACK_PRICES, \
                f"Glass type {glass_type} has no fallback price"

            price = GLASS_FALLBACK_PRICES[glass_type]
            assert price > 0, f"Invalid fallback price for {glass_type}"
            assert isinstance(price, Decimal), "Fallback price should be Decimal"

    def test_database_glass_pricing(self, bom_service, sample_glass_materials):
        """Test glass pricing retrieval from database"""
        for glass_type in GlassType:
            price = bom_service.get_glass_cost_per_m2(glass_type)

            # Should return the test price (100.00)
            assert price == Decimal("100.00"), \
                f"Glass type {glass_type} returned wrong price: {price}"

    def test_fallback_pricing_when_database_empty(self, db_session):
        """Test fallback to hardcoded prices when database has no materials"""
        # Create fresh service (without sample materials)
        bom_service_no_data = ProductBOMServiceDB(db_session)

        # Delete any existing glass materials
        db_session.query(DBAppMaterial).filter(
            DBAppMaterial.category == "Vidrio"
        ).delete()
        db_session.commit()

        for glass_type in GlassType:
            price = bom_service_no_data.get_glass_cost_per_m2(glass_type)
            expected_price = GLASS_FALLBACK_PRICES[glass_type]

            assert price == expected_price, \
                f"Fallback price mismatch for {glass_type}: {price} != {expected_price}"

    def test_price_update_via_ui_takes_effect(self, bom_service, material_service, sample_glass_materials):
        """Test that price updates in UI (database) immediately affect calculations"""
        glass_type = GlassType.CLARO_6MM
        material_code = GLASS_TYPE_TO_MATERIAL_CODE[glass_type]

        # Get initial price
        initial_price = bom_service.get_glass_cost_per_m2(glass_type)
        assert initial_price == Decimal("100.00")

        # Update price in database (simulating UI update)
        material = material_service.get_material_by_code(material_code)
        material_service.update_material(
            material.id,
            cost_per_unit=Decimal("250.00")
        )

        # Clear cache to force database query
        if hasattr(bom_service, '_glass_price_cache') and bom_service._glass_price_cache is not None:
            bom_service.clear_glass_price_cache()

        # Get updated price - should reflect database change
        updated_price = bom_service.get_glass_cost_per_m2(glass_type)
        assert updated_price == Decimal("250.00"), \
            "Price update via UI did not take effect"

    def test_all_glass_types_calculate_correctly(self, bom_service, sample_glass_materials):
        """Test that all 7 glass types can be retrieved without errors"""
        for glass_type in GlassType:
            try:
                price = bom_service.get_glass_cost_per_m2(glass_type)
                assert price > 0, f"Invalid price for {glass_type}"
                assert isinstance(price, Decimal), f"Price should be Decimal for {glass_type}"
            except Exception as e:
                pytest.fail(f"Failed to get price for {glass_type}: {e}")

    def test_invalid_glass_type_raises_error(self, bom_service):
        """Test that invalid glass type raises appropriate error"""
        with pytest.raises(ValueError, match="Código de material no encontrado"):
            # Create fake glass type
            class FakeGlassType:
                value = "fake_glass"

            bom_service.get_glass_cost_per_m2(FakeGlassType())

    def test_performance_database_lookup(self, bom_service, sample_glass_materials):
        """Test that database lookup is fast (<5ms)"""
        import time

        glass_type = GlassType.CLARO_6MM

        # Warm up (first query might be slower)
        bom_service.get_glass_cost_per_m2(glass_type)

        # Measure 100 lookups
        start = time.time()
        for _ in range(100):
            bom_service.get_glass_cost_per_m2(glass_type)
        end = time.time()

        avg_time_ms = ((end - start) / 100) * 1000
        assert avg_time_ms < 5, \
            f"Database lookup too slow: {avg_time_ms:.2f}ms (target: <5ms)"

    def test_backward_compatibility_existing_quotes(self, bom_service, sample_glass_materials):
        """Test that existing quotes can recalculate with new pricing"""
        # Simulate existing quote data
        from models.quote_models import WindowItem

        window_item = WindowItem(
            product_bom_id=1,
            selected_glass_type=GlassType.TEMPLADO_6MM,
            width_cm=Decimal("100"),
            height_cm=Decimal("150"),
            quantity=2
        )

        # Should calculate without errors
        glass_price = bom_service.get_glass_cost_per_m2(window_item.selected_glass_type)
        assert glass_price > 0

    @pytest.mark.parametrize("glass_type,expected_code", [
        (GlassType.CLARO_4MM, "VID-CLARO-4"),
        (GlassType.CLARO_6MM, "VID-CLARO-6"),
        (GlassType.BRONCE_4MM, "VID-BRONCE-4"),
        (GlassType.BRONCE_6MM, "VID-BRONCE-6"),
        (GlassType.REFLECTIVO_6MM, "VID-REFLECTIVO-6"),
        (GlassType.LAMINADO_6MM, "VID-LAMINADO-6"),
        (GlassType.TEMPLADO_6MM, "VID-TEMP-6"),
    ])
    def test_material_code_mapping(self, glass_type, expected_code):
        """Test material code mapping for each glass type"""
        actual_code = GLASS_TYPE_TO_MATERIAL_CODE[glass_type]
        assert actual_code == expected_code, \
            f"Material code mismatch for {glass_type}: {actual_code} != {expected_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
