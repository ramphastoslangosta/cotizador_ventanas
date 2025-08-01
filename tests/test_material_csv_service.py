#!/usr/bin/env python3
"""
Comprehensive tests for MaterialCSVService
Tests CSV import/export functionality with secure validation
"""

import pytest
import io
import csv
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

# Import the service and related classes
from services.material_csv_service import MaterialCSVService
from database import AppMaterial as DBAppMaterial, DatabaseMaterialService
from models.product_bom_models import MaterialUnit

class TestMaterialCSVService:
    """Test suite for MaterialCSVService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_material_service(self):
        """Mock DatabaseMaterialService"""
        return Mock(spec=DatabaseMaterialService)
    
    @pytest.fixture
    def csv_service(self, mock_db_session, mock_material_service):
        """MaterialCSVService instance with mocked dependencies"""
        with patch('services.material_csv_service.DatabaseMaterialService', return_value=mock_material_service):
            service = MaterialCSVService(mock_db_session)
            service.material_service = mock_material_service
            return service
    
    @pytest.fixture
    def sample_materials(self):
        """Sample materials for testing"""
        materials = []
        
        # Create mock material objects
        material1 = Mock()
        material1.id = 1
        material1.name = "Perfil Aluminio Serie 3"
        material1.code = "PRF-AL-S3-001"
        material1.unit = "ML"
        material1.category = "Perfiles"
        material1.cost_per_unit = Decimal("45.50")
        material1.selling_unit_length_m = Decimal("6.0")
        material1.description = "Perfil de aluminio serie 3"
        materials.append(material1)
        
        material2 = Mock()
        material2.id = 2
        material2.name = "Vidrio Claro 6mm"
        material2.code = "VID-CLR-6MM"
        material2.unit = "M2"
        material2.category = "Vidrio"
        material2.cost_per_unit = Decimal("280.00")
        material2.selling_unit_length_m = None
        material2.description = "Vidrio claro templado 6mm"
        materials.append(material2)
        
        return materials

class TestCSVExport:
    """Test CSV export functionality"""
    
    def test_export_all_materials(self, csv_service, sample_materials):
        """Test exporting all materials to CSV"""
        csv_service.material_service.get_all_materials.return_value = sample_materials
        
        csv_content = csv_service.export_materials_to_csv()
        
        # Parse the CSV content
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['name'] == "Perfil Aluminio Serie 3"
        assert rows[0]['code'] == "PRF-AL-S3-001"
        assert rows[0]['category'] == "Perfiles"
        assert rows[0]['selling_unit_length_m'] == "6.0"
        
        assert rows[1]['name'] == "Vidrio Claro 6mm"
        assert rows[1]['category'] == "Vidrio"
        assert rows[1]['selling_unit_length_m'] == ""
        
    def test_export_materials_by_category(self, csv_service, sample_materials):
        """Test exporting materials filtered by category"""
        csv_service.material_service.get_all_materials.return_value = sample_materials
        
        csv_content = csv_service.export_materials_to_csv(category="Perfiles")
        
        # Parse the CSV content
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should only include Perfiles category
        assert len(rows) == 1
        assert rows[0]['category'] == "Perfiles"
        
    def test_export_empty_materials(self, csv_service):
        """Test exporting when no materials exist"""
        csv_service.material_service.get_all_materials.return_value = []
        
        csv_content = csv_service.export_materials_to_csv()
        
        # Should have headers but no data rows
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 0
        assert reader.fieldnames == csv_service.CSV_HEADERS

class TestCSVImport:
    """Test CSV import functionality"""
    
    def test_import_create_material_success(self, csv_service):
        """Test successfully creating a new material from CSV"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description"""
        
        # Mock material service responses
        csv_service.material_service.get_material_by_code.return_value = None  # No existing material
        
        # Mock created material
        created_material = Mock()
        created_material.id = 100
        created_material.name = "Test Material"
        csv_service.material_service.create_material.return_value = created_material
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 1
        assert len(results["errors"]) == 0
        assert results["summary"]["created"] == 1
        assert results["success"][0]["action"] == "created"
        assert results["success"][0]["material_name"] == "Test Material"
        
        # Verify create_material was called with correct parameters
        csv_service.material_service.create_material.assert_called_once()
        
    def test_import_update_material_success(self, csv_service):
        """Test successfully updating an existing material from CSV"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
update,1,Updated Material,UPD-001,ML,Perfiles,50.00,6.0,Updated description"""
        
        # Mock existing material
        existing_material = Mock()
        existing_material.id = 1
        existing_material.name = "Old Material"
        existing_material.code = "OLD-001"
        csv_service.material_service.get_material_by_id.return_value = existing_material
        csv_service.material_service.get_material_by_code.return_value = None  # No code conflict
        
        # Mock updated material
        updated_material = Mock()
        updated_material.id = 1
        updated_material.name = "Updated Material"
        csv_service.material_service.update_material.return_value = updated_material
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 1
        assert len(results["errors"]) == 0
        assert results["summary"]["updated"] == 1
        assert results["success"][0]["action"] == "updated"
        
    def test_import_delete_material_success(self, csv_service):
        """Test successfully deleting a material from CSV"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
delete,1,,,,,,,"""
        
        # Mock existing material
        existing_material = Mock()
        existing_material.id = 1
        existing_material.name = "Material to Delete"
        csv_service.material_service.get_material_by_id.return_value = existing_material
        csv_service.material_service.delete_material.return_value = True
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 1
        assert len(results["errors"]) == 0
        assert results["summary"]["deleted"] == 1
        assert results["success"][0]["action"] == "deleted"
        
    def test_import_invalid_action(self, csv_service):
        """Test handling invalid action in CSV"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
invalid,1,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description"""
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 0
        assert len(results["errors"]) == 1
        assert results["summary"]["skipped"] == 1
        assert "Invalid action" in results["errors"][0]["error"]
        
    def test_import_invalid_headers(self, csv_service):
        """Test handling CSV with invalid headers"""
        csv_content = """wrong,headers,here
create,1,Test Material"""
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 0
        assert len(results["errors"]) == 1
        assert "Invalid CSV headers" in results["errors"][0]["error"]
        
    def test_import_duplicate_code_error(self, csv_service):
        """Test handling duplicate material code error"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Test Material,EXISTING-001,ML,Perfiles,45.50,6.0,Test description"""
        
        # Mock existing material with same code
        existing_material = Mock()
        existing_material.id = 99
        existing_material.code = "EXISTING-001"
        csv_service.material_service.get_material_by_code.return_value = existing_material
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 0
        assert len(results["errors"]) == 1
        assert results["summary"]["skipped"] == 1
        assert "already exists" in results["errors"][0]["error"]
        
    def test_import_material_not_found_error(self, csv_service):
        """Test handling material not found for update/delete"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
update,999,Updated Material,UPD-001,ML,Perfiles,50.00,6.0,Updated description"""
        
        # Mock material not found
        csv_service.material_service.get_material_by_id.return_value = None
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        assert len(results["success"]) == 0
        assert len(results["errors"]) == 1
        assert results["summary"]["skipped"] == 1
        assert "not found" in results["errors"][0]["error"]

class TestCSVValidation:
    """Test CSV data validation"""
    
    def test_validate_material_data_valid(self, csv_service):
        """Test validation of valid material data"""
        row = {
            "name": "Test Material",
            "code": "TEST-001",
            "unit": "ML",
            "category": "Perfiles",
            "cost_per_unit": "45.50",
            "selling_unit_length_m": "6.0",
            "description": "Test description"
        }
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            result = csv_service._validate_material_data(row, 1, require_id=False)
            
            assert result["valid"] is True
            assert result["data"]["name"] == "Test Material"
            assert result["data"]["cost_per_unit"] == Decimal("45.50")
            
    def test_validate_material_data_invalid_unit(self, csv_service):
        """Test validation with invalid unit"""
        row = {
            "name": "Test Material",
            "unit": "INVALID_UNIT",
            "category": "Perfiles",
            "cost_per_unit": "45.50"
        }
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            result = csv_service._validate_material_data(row, 1, require_id=False)
            
            assert result["valid"] is False
            assert "Invalid unit" in result["error"]
            
    def test_validate_material_data_invalid_category(self, csv_service):
        """Test validation with invalid category"""
        row = {
            "name": "Test Material",
            "unit": "ML",
            "category": "InvalidCategory",
            "cost_per_unit": "45.50"
        }
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            result = csv_service._validate_material_data(row, 1, require_id=False)
            
            assert result["valid"] is False
            assert "Invalid category" in result["error"]
            
    def test_validate_material_data_invalid_cost(self, csv_service):
        """Test validation with invalid cost"""
        row = {
            "name": "Test Material",
            "unit": "ML",
            "category": "Perfiles",
            "cost_per_unit": "invalid_cost"
        }
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            result = csv_service._validate_material_data(row, 1, require_id=False)
            
            assert result["valid"] is False
            assert "Invalid cost per unit format" in result["error"]
            
    def test_validate_material_data_negative_cost(self, csv_service):
        """Test validation with negative cost"""
        row = {
            "name": "Test Material",
            "unit": "ML",
            "category": "Perfiles",
            "cost_per_unit": "-10.00"
        }
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            result = csv_service._validate_material_data(row, 1, require_id=False)
            
            assert result["valid"] is False
            assert "must be greater than 0" in result["error"]

class TestCSVTemplate:
    """Test CSV template generation"""
    
    def test_get_csv_template_all_categories(self, csv_service):
        """Test generating template for all categories"""
        template = csv_service.get_csv_template()
        
        # Parse the template
        reader = csv.DictReader(io.StringIO(template))
        rows = list(reader)
        
        # Should have headers and sample rows for each category
        assert reader.fieldnames == csv_service.CSV_HEADERS
        assert len(rows) == 4  # One for each category
        
        categories = [row['category'] for row in rows]
        assert "Perfiles" in categories
        assert "Vidrio" in categories
        assert "Herrajes" in categories
        assert "Consumibles" in categories
        
    def test_get_csv_template_specific_category(self, csv_service):
        """Test generating template for specific category"""
        template = csv_service.get_csv_template(category="Perfiles")
        
        # Parse the template
        reader = csv.DictReader(io.StringIO(template))
        rows = list(reader)
        
        # Should have only one row for Perfiles
        assert len(rows) == 1
        assert rows[0]['category'] == "Perfiles"
        assert rows[0]['selling_unit_length_m'] == "6.0"  # Perfiles should have length
        
    def test_get_csv_template_vidrio_category(self, csv_service):
        """Test generating template for Vidrio category"""
        template = csv_service.get_csv_template(category="Vidrio")
        
        # Parse the template
        reader = csv.DictReader(io.StringIO(template))
        rows = list(reader)
        
        # Should have only one row for Vidrio
        assert len(rows) == 1
        assert rows[0]['category'] == "Vidrio"
        assert rows[0]['unit'] == "M2"
        assert rows[0]['selling_unit_length_m'] == ""  # Vidrio shouldn't have length

class TestCSVHeaders:
    """Test CSV header validation"""
    
    def test_validate_csv_headers_valid(self, csv_service):
        """Test validation of correct CSV headers"""
        valid_headers = csv_service.CSV_HEADERS
        result = csv_service._validate_csv_headers(valid_headers)
        assert result is True
        
    def test_validate_csv_headers_invalid(self, csv_service):
        """Test validation of incorrect CSV headers"""
        invalid_headers = ["wrong", "headers", "here"]
        result = csv_service._validate_csv_headers(invalid_headers)
        assert result is False
        
    def test_validate_csv_headers_missing(self, csv_service):
        """Test validation when headers are missing"""
        result = csv_service._validate_csv_headers(None)
        assert result is False
        
        result = csv_service._validate_csv_headers([])
        assert result is False

class TestCSVIntegration:
    """Integration tests for complete CSV workflows"""
    
    def test_export_import_roundtrip(self, csv_service, sample_materials):
        """Test complete export-import roundtrip"""
        # Setup export
        csv_service.material_service.get_all_materials.return_value = sample_materials
        
        # Export materials
        csv_content = csv_service.export_materials_to_csv()
        
        # Modify CSV for import (change action to update)
        modified_csv = csv_content.replace("update,1,", "update,1,Modified ")
        
        # Setup import mocks
        existing_material = Mock()
        existing_material.id = 1
        existing_material.name = "Old Name"
        existing_material.code = "PRF-AL-S3-001"
        csv_service.material_service.get_material_by_id.return_value = existing_material
        csv_service.material_service.get_material_by_code.return_value = None
        
        updated_material = Mock()
        updated_material.id = 1
        updated_material.name = "Modified Perfil Aluminio Serie 3"
        csv_service.material_service.update_material.return_value = updated_material
        
        # Import modified CSV
        results = csv_service.import_materials_from_csv(modified_csv)
        
        # Verify import results
        assert len(results["success"]) >= 1
        assert results["summary"]["updated"] >= 1
        
    def test_mixed_operations_csv(self, csv_service):
        """Test CSV with mixed create, update, delete operations"""
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,New Material,NEW-001,ML,Perfiles,45.50,6.0,New description
update,1,Updated Material,UPD-001,ML,Perfiles,50.00,6.0,Updated description
delete,2,,,,,,,"""
        
        # Mock responses for each operation
        # Create operation
        csv_service.material_service.get_material_by_code.return_value = None
        created_material = Mock()
        created_material.id = 100
        created_material.name = "New Material"
        csv_service.material_service.create_material.return_value = created_material
        
        # Update operation
        existing_material1 = Mock()
        existing_material1.id = 1
        existing_material1.name = "Old Material"
        existing_material1.code = "OLD-001"
        updated_material = Mock()
        updated_material.id = 1
        updated_material.name = "Updated Material"
        csv_service.material_service.update_material.return_value = updated_material
        
        # Delete operation
        existing_material2 = Mock()
        existing_material2.id = 2
        existing_material2.name = "Material to Delete"
        csv_service.material_service.delete_material.return_value = True
        
        # Configure get_material_by_id to return different materials based on ID
        def get_material_by_id_side_effect(material_id):
            if material_id == 1:
                return existing_material1
            elif material_id == 2:
                return existing_material2
            return None
            
        csv_service.material_service.get_material_by_id.side_effect = get_material_by_id_side_effect
        
        results = csv_service.import_materials_from_csv(csv_content)
        
        # Verify all operations succeeded
        assert len(results["success"]) == 3
        assert len(results["errors"]) == 0
        assert results["summary"]["created"] == 1
        assert results["summary"]["updated"] == 1
        assert results["summary"]["deleted"] == 1

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])