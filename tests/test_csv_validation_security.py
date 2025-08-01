#!/usr/bin/env python3
"""
Security and validation tests for CSV functionality
Focus on edge cases, security vulnerabilities, and data integrity
"""

import pytest
import io
import csv
from decimal import Decimal
from unittest.mock import Mock, patch

from services.material_csv_service import MaterialCSVService
from security.input_validation import InputValidator

class TestCSVSecurityValidation:
    """Test security aspects of CSV processing"""
    
    @pytest.fixture
    def csv_service(self):
        """MaterialCSVService with mocked dependencies"""
        mock_db = Mock()
        mock_material_service = Mock()
        
        with patch('services.material_csv_service.DatabaseMaterialService', return_value=mock_material_service):
            service = MaterialCSVService(mock_db)
            service.material_service = mock_material_service
            return service
    
    def test_csv_injection_prevention(self, csv_service):
        """Test prevention of CSV injection attacks"""
        malicious_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,=cmd|'/c calc'!A0,EVIL-001,ML,Perfiles,45.50,6.0,Malicious formula
create,,@SUM(1+1)*cmd|'/c calc'!A0,EVIL-002,ML,Perfiles,45.50,6.0,Another injection
create,,+cmd|'/c calc'!A0,EVIL-003,ML,Perfiles,45.50,6.0,Third injection
create,,-cmd|'/c calc'!A0,EVIL-004,ML,Perfiles,45.50,6.0,Fourth injection"""
        
        # Mock input validator to catch malicious content
        with patch.object(csv_service.validator, 'validate_text_input') as mock_validate, \
             patch.object(csv_service.validator, 'sanitize_text_input') as mock_sanitize:
            
            # Simulate validator rejecting formula-like content
            def validate_side_effect(text, **kwargs):
                return not any(text.startswith(char) for char in ['=', '@', '+', '-']) or not any(char in text for char in ['|', '!'])
            
            def sanitize_side_effect(text):
                # Remove dangerous characters
                dangerous_chars = ['=', '@', '|', '!']
                for char in dangerous_chars:
                    text = text.replace(char, '')
                return text
            
            mock_validate.side_effect = validate_side_effect
            mock_sanitize.side_effect = sanitize_side_effect
            
            results = csv_service.import_materials_from_csv(malicious_csv)
            
            # All malicious entries should be rejected
            assert len(results["errors"]) == 4
            assert len(results["success"]) == 0
            assert results["summary"]["skipped"] == 4
            
            # Verify validation was called for each material name
            assert mock_validate.call_count >= 4
    
    def test_sql_injection_prevention(self, csv_service):
        """Test prevention of SQL injection through CSV data"""
        sql_injection_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,'; DROP TABLE app_materials; --,SQL-001,ML,Perfiles,45.50,6.0,SQL injection
create,,Material'; UPDATE app_materials SET cost_per_unit=0; --,SQL-002,ML,Perfiles,45.50,6.0,Another SQL injection"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            # Mock material service - the real protection is in the ORM layer
            csv_service.material_service.get_material_by_code.return_value = None
            created_material = Mock()
            created_material.id = 100
            created_material.name = "Safe Name"
            csv_service.material_service.create_material.return_value = created_material
            
            results = csv_service.import_materials_from_csv(sql_injection_csv)
            
            # The service layer should handle this safely
            # Real SQL injection protection comes from SQLAlchemy ORM
            csv_service.material_service.create_material.assert_called()
    
    def test_xss_prevention_in_descriptions(self, csv_service):
        """Test prevention of XSS attacks in material descriptions"""
        xss_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Safe Material,SAFE-001,ML,Perfiles,45.50,6.0,<script>alert('XSS')</script>
create,,Another Material,SAFE-002,ML,Perfiles,45.50,6.0,<img src=x onerror=alert('XSS')>"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input') as mock_sanitize:
            
            # Mock sanitizer to remove HTML tags
            def sanitize_side_effect(text):
                import re
                return re.sub(r'<[^>]+>', '', text)
            
            mock_sanitize.side_effect = sanitize_side_effect
            
            csv_service.material_service.get_material_by_code.return_value = None
            created_material = Mock()
            created_material.id = 100
            created_material.name = "Safe Material"
            csv_service.material_service.create_material.return_value = created_material
            
            results = csv_service.import_materials_from_csv(xss_csv)
            
            # Verify sanitization was called
            assert mock_sanitize.call_count >= 2
            
            # Check that create_material was called with sanitized data
            calls = csv_service.material_service.create_material.call_args_list
            for call in calls:
                description = call[1].get('description', '')
                assert '<script>' not in description
                assert '<img' not in description
    
    def test_path_traversal_prevention(self, csv_service):
        """Test prevention of path traversal attacks in material codes/names"""
        path_traversal_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,../../../etc/passwd,TRAV-001,ML,Perfiles,45.50,6.0,Path traversal
create,,..\\..\\windows\\system32\\calc.exe,TRAV-002,ML,Perfiles,45.50,6.0,Windows path traversal"""
        
        with patch.object(csv_service.validator, 'validate_text_input') as mock_validate, \
             patch.object(csv_service.validator, 'sanitize_text_input') as mock_sanitize:
            
            # Simulate validator rejecting path traversal patterns
            def validate_side_effect(text, **kwargs):
                return not any(pattern in text for pattern in ['../', '..\\', '/etc/', '\\system32\\'])
            
            def sanitize_side_effect(text):
                # Remove path traversal patterns
                patterns = ['../', '..\\', '/etc/', '\\system32\\']
                for pattern in patterns:
                    text = text.replace(pattern, '')
                return text
            
            mock_validate.side_effect = validate_side_effect
            mock_sanitize.side_effect = sanitize_side_effect
            
            results = csv_service.import_materials_from_csv(path_traversal_csv)
            
            # Path traversal attempts should be rejected
            assert len(results["errors"]) == 2
            assert results["summary"]["skipped"] == 2
    
    def test_unicode_normalization_attacks(self, csv_service):
        """Test handling of Unicode normalization attacks"""
        # Unicode characters that might normalize to dangerous characters
        unicode_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Material＜script＞alert()＜/script＞,UNI-001,ML,Perfiles,45.50,6.0,Unicode script
create,,Normal Material,UNI-002,ML,Perfiles,45.50,6.0,ℋℯ𝓁𝓁ℴ 𝒲ℴ𝓇𝓁𝒹"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input') as mock_sanitize:
            
            # Mock sanitizer to handle Unicode normalization
            def sanitize_side_effect(text):
                import unicodedata
                # Normalize to NFKC form to prevent bypasses
                normalized = unicodedata.normalize('NFKC', text)
                # Remove any remaining dangerous patterns
                import re
                return re.sub(r'[<>]', '', normalized)
            
            mock_sanitize.side_effect = sanitize_side_effect
            
            csv_service.material_service.get_material_by_code.return_value = None
            created_material = Mock()
            created_material.id = 100
            created_material.name = "Safe Material"
            csv_service.material_service.create_material.return_value = created_material
            
            results = csv_service.import_materials_from_csv(unicode_csv)
            
            # Verify sanitization handled Unicode properly
            assert mock_sanitize.call_count >= 2

class TestCSVDataIntegrity:
    """Test data integrity and edge cases in CSV processing"""
    
    @pytest.fixture
    def csv_service(self):
        mock_db = Mock()
        mock_material_service = Mock()
        
        with patch('services.material_csv_service.DatabaseMaterialService', return_value=mock_material_service):
            service = MaterialCSVService(mock_db)
            service.material_service = mock_material_service
            return service
    
    def test_extremely_long_field_values(self, csv_service):
        """Test handling of extremely long field values"""
        long_name = "A" * 10000  # Very long name
        long_description = "B" * 50000  # Very long description
        
        long_csv = f"""action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,{long_name},LONG-001,ML,Perfiles,45.50,6.0,{long_description}"""
        
        with patch.object(csv_service.validator, 'validate_text_input') as mock_validate, \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            # Simulate validator rejecting overly long content
            def validate_side_effect(text, **kwargs):
                max_length = kwargs.get('max_length', 100)
                return len(text) <= max_length
            
            mock_validate.side_effect = validate_side_effect
            
            results = csv_service.import_materials_from_csv(long_csv)
            
            # Should be rejected due to length validation
            assert len(results["errors"]) == 1
            assert "too long" in results["errors"][0]["error"] or "Invalid" in results["errors"][0]["error"]
    
    def test_special_characters_in_numeric_fields(self, csv_service):
        """Test handling of special characters in numeric fields"""
        special_chars_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Test Material,TEST-001,ML,Perfiles,45.50€,6.0m,Normal description
create,,Test Material 2,TEST-002,ML,Perfiles,$45.50,6'0",Another description
create,,Test Material 3,TEST-003,ML,Perfiles,45,50,6.0,Comma decimal separator"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            results = csv_service.import_materials_from_csv(special_chars_csv)
            
            # All entries should fail due to invalid numeric formats
            assert len(results["errors"]) == 3
            for error in results["errors"]:
                assert "Invalid" in error["error"] or "format" in error["error"]
    
    def test_boundary_values_for_numeric_fields(self, csv_service):
        """Test boundary values for numeric fields"""
        boundary_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Zero Cost,ZERO-001,ML,Perfiles,0.00,6.0,Zero cost
create,,Negative Cost,NEG-001,ML,Perfiles,-10.00,6.0,Negative cost
create,,Very Small Cost,SMALL-001,ML,Perfiles,0.0001,6.0,Very small cost
create,,Very Large Cost,LARGE-001,ML,Perfiles,999999999.99,6.0,Very large cost"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            results = csv_service.import_materials_from_csv(boundary_csv)
            
            # Zero and negative costs should be rejected
            errors = [error for error in results["errors"] if "must be greater than 0" in error["error"]]
            assert len(errors) >= 2  # Zero and negative costs
    
    def test_csv_with_missing_required_headers(self, csv_service):
        """Test CSV with missing required headers"""
        missing_headers_csv = """action,name,unit,category,cost_per_unit
create,Test Material,ML,Perfiles,45.50"""
        
        results = csv_service.import_materials_from_csv(missing_headers_csv)
        
        # Should fail header validation
        assert len(results["errors"]) == 1
        assert "Invalid CSV headers" in results["errors"][0]["error"]
    
    def test_csv_with_extra_headers(self, csv_service):
        """Test CSV with extra headers"""
        extra_headers_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description,extra_field
create,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description,Extra data"""
        
        results = csv_service.import_materials_from_csv(extra_headers_csv)
        
        # Should fail header validation (strict header matching)
        assert len(results["errors"]) == 1
        assert "Invalid CSV headers" in results["errors"][0]["error"]
    
    def test_empty_csv_file(self, csv_service):
        """Test processing of empty CSV file"""
        empty_csv = ""
        
        results = csv_service.import_materials_from_csv(empty_csv)
        
        # Should handle empty file gracefully
        assert len(results["errors"]) >= 1
        assert results["summary"]["created"] == 0
        assert results["summary"]["updated"] == 0
        assert results["summary"]["deleted"] == 0
    
    def test_csv_with_only_headers(self, csv_service):
        """Test CSV with only headers, no data rows"""
        headers_only_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description"""
        
        results = csv_service.import_materials_from_csv(headers_only_csv)
        
        # Should process successfully but with no operations
        assert len(results["errors"]) == 0
        assert len(results["success"]) == 0
        assert results["summary"]["created"] == 0
    
    def test_csv_with_bom_character(self, csv_service):
        """Test CSV with BOM (Byte Order Mark) character"""
        # CSV with UTF-8 BOM
        bom_csv = "\ufeffaction,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description\ncreate,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description"
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            csv_service.material_service.get_material_by_code.return_value = None
            created_material = Mock()
            created_material.id = 100
            created_material.name = "Test Material"
            csv_service.material_service.create_material.return_value = created_material
            
            results = csv_service.import_materials_from_csv(bom_csv)
            
            # Should handle BOM gracefully
            assert len(results["success"]) == 1 or len(results["errors"]) == 1  # Depending on CSV parser behavior

class TestCSVConcurrencyAndPerformance:
    """Test concurrency and performance aspects"""
    
    @pytest.fixture
    def csv_service(self):
        mock_db = Mock()
        mock_material_service = Mock()
        
        with patch('services.material_csv_service.DatabaseMaterialService', return_value=mock_material_service):
            service = MaterialCSVService(mock_db)
            service.material_service = mock_material_service
            return service
    
    def test_large_batch_processing(self, csv_service):
        """Test processing of large CSV files"""
        # Generate a large CSV with 1000 materials
        csv_lines = ["action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description"]
        for i in range(1000):
            csv_lines.append(f"create,,Material {i},MAT-{i:04d},ML,Perfiles,45.50,6.0,Description for material {i}")
        
        large_csv = "\n".join(csv_lines)
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            csv_service.material_service.get_material_by_code.return_value = None
            
            # Mock material creation to return different materials
            def create_material_side_effect(**kwargs):
                material = Mock()
                material.id = hash(kwargs['name']) % 100000  # Generate pseudo-unique ID
                material.name = kwargs['name']
                return material
            
            csv_service.material_service.create_material.side_effect = create_material_side_effect
            
            results = csv_service.import_materials_from_csv(large_csv)
            
            # Should process all materials
            assert len(results["success"]) == 1000
            assert results["summary"]["created"] == 1000
            assert len(results["errors"]) == 0
    
    def test_duplicate_operations_in_same_csv(self, csv_service):
        """Test handling of duplicate operations in the same CSV"""
        duplicate_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,First creation
create,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Duplicate creation
update,1,Updated Material,TEST-001,ML,Perfiles,50.00,6.0,Update after create"""
        
        with patch.object(csv_service.validator, 'validate_text_input', return_value=True), \
             patch.object(csv_service.validator, 'sanitize_text_input', side_effect=lambda x: x):
            
            # First create should succeed, second should fail due to duplicate code
            csv_service.material_service.get_material_by_code.side_effect = [
                None,  # First call - no existing material
                Mock(),  # Second call - material exists (from first create)
                None   # Third call - for the update operation
            ]
            
            created_material = Mock()
            created_material.id = 100
            created_material.name = "Test Material"
            csv_service.material_service.create_material.return_value = created_material
            
            # Mock for update operation
            existing_material = Mock()
            existing_material.id = 1
            existing_material.code = "OLD-001"
            csv_service.material_service.get_material_by_id.return_value = existing_material
            
            updated_material = Mock()
            updated_material.id = 1
            updated_material.name = "Updated Material"
            csv_service.material_service.update_material.return_value = updated_material
            
            results = csv_service.import_materials_from_csv(duplicate_csv)
            
            # First create should succeed, second should fail, update should succeed
            assert len(results["success"]) == 2  # Create and update
            assert len(results["errors"]) == 1   # Duplicate create
            assert results["summary"]["created"] == 1
            assert results["summary"]["updated"] == 1
            assert results["summary"]["skipped"] == 1

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])