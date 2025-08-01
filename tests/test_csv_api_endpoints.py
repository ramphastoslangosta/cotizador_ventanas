#!/usr/bin/env python3
"""
Tests for CSV import/export API endpoints
Tests the FastAPI endpoints for material CSV operations
"""

import pytest
import io
import tempfile
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Import the FastAPI app and dependencies
from main import app
from database import get_db, User
from main import get_current_user_flexible

class TestCSVAPIEndpoints:
    """Test suite for CSV API endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.email = "test@example.com"
        user.full_name = "Test User"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def auth_override(self, mock_user):
        """Override authentication dependency"""
        def override_get_current_user():
            return mock_user
        return override_get_current_user
    
    @pytest.fixture
    def db_override(self, mock_db):
        """Override database dependency"""
        def override_get_db():
            yield mock_db
        return override_get_db
    
    def test_export_materials_csv_success(self, client, auth_override, db_override):
        """Test successful CSV export"""
        # Override dependencies
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        sample_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
update,1,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description"""
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.export_materials_to_csv.return_value = sample_csv
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/export")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment; filename=materials.csv" in response.headers["content-disposition"]
            assert "Test Material" in response.text
            
        # Clean up
        app.dependency_overrides.clear()
    
    def test_export_materials_csv_by_category(self, client, auth_override, db_override):
        """Test CSV export filtered by category"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        sample_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
update,1,Perfil Test,PRF-001,ML,Perfiles,45.50,6.0,Test profile"""
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.export_materials_to_csv.return_value = sample_csv
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/export?category=Perfiles")
            
            assert response.status_code == 200
            assert "attachment; filename=materials_Perfiles.csv" in response.headers["content-disposition"]
            mock_service.export_materials_to_csv.assert_called_once_with("Perfiles")
            
        app.dependency_overrides.clear()
    
    def test_export_materials_csv_error(self, client, auth_override, db_override):
        """Test CSV export error handling"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.export_materials_to_csv.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/export")
            
            assert response.status_code == 500
            assert "Error exporting materials" in response.json()["detail"]
            
        app.dependency_overrides.clear()
    
    def test_import_materials_csv_success(self, client, auth_override, db_override):
        """Test successful CSV import"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        # Create a CSV file content
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,New Material,NEW-001,ML,Perfiles,45.50,6.0,New description
update,1,Updated Material,UPD-001,ML,Perfiles,50.00,6.0,Updated description"""
        
        # Mock import results
        import_results = {
            "success": [
                {"action": "created", "row": 2, "material_id": 100, "material_name": "New Material"},
                {"action": "updated", "row": 3, "material_id": 1, "material_name": "Updated Material"}
            ],
            "errors": [],
            "summary": {"created": 1, "updated": 1, "deleted": 0, "skipped": 0}
        }
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.import_materials_from_csv.return_value = import_results
            mock_service_class.return_value = mock_service
            
            # Create a temporary file for upload
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(csv_content)
                tmp_file.flush()
                
                # Upload the file
                with open(tmp_file.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/materials/csv/import",
                        files={"file": ("test.csv", upload_file, "text/csv")}
                    )
        
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "CSV import completed"
        assert result["filename"] == "test.csv"
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert result["summary"]["created"] == 1
        assert result["summary"]["updated"] == 1
        
        app.dependency_overrides.clear()
    
    def test_import_materials_csv_with_errors(self, client, auth_override, db_override):
        """Test CSV import with validation errors"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Invalid Material,INV-001,INVALID_UNIT,Perfiles,45.50,6.0,Invalid unit"""
        
        # Mock import results with errors
        import_results = {
            "success": [],
            "errors": [
                {"row": 2, "error": "Invalid unit. Must be one of: ML, PZA, M2, CARTUCHO, LTS, KG"}
            ],
            "summary": {"created": 0, "updated": 0, "deleted": 0, "skipped": 1}
        }
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.import_materials_from_csv.return_value = import_results
            mock_service_class.return_value = mock_service
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(csv_content)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/materials/csv/import",
                        files={"file": ("test.csv", upload_file, "text/csv")}
                    )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert len(result["errors"]) == 1
        assert "Invalid unit" in result["errors"][0]["error"]
        
        app.dependency_overrides.clear()
    
    def test_import_materials_csv_invalid_file_type(self, client, auth_override, db_override):
        """Test CSV import with invalid file type"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("Not a CSV file")
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as upload_file:
                response = client.post(
                    "/api/materials/csv/import",
                    files={"file": ("test.txt", upload_file, "text/plain")}
                )
        
        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_import_materials_csv_encoding_error(self, client, auth_override, db_override):
        """Test CSV import with encoding error"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        # Create file with invalid UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            # Write invalid UTF-8 bytes
            tmp_file.write(b'\xff\xfe\x00\x00invalid utf-8')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as upload_file:
                response = client.post(
                    "/api/materials/csv/import",
                    files={"file": ("test.csv", upload_file, "text/csv")}
                )
        
        assert response.status_code == 400
        assert "File encoding error" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_import_materials_csv_service_error(self, client, auth_override, db_override):
        """Test CSV import with service error"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        csv_content = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Test Material,TEST-001,ML,Perfiles,45.50,6.0,Test description"""
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.import_materials_from_csv.side_effect = Exception("Database connection error")
            mock_service_class.return_value = mock_service
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(csv_content)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/materials/csv/import",
                        files={"file": ("test.csv", upload_file, "text/csv")}
                    )
        
        assert response.status_code == 500
        assert "Error importing materials" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_csv_template_success(self, client, auth_override, db_override):
        """Test successful CSV template download"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        template_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Perfil Aluminio Serie 3,PRF-AL-S3-001,ML,Perfiles,45.50,6.0,Perfil de aluminio serie 3"""
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_csv_template.return_value = template_csv
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/template")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment; filename=materials_template.csv" in response.headers["content-disposition"]
            assert "Perfil Aluminio Serie 3" in response.text
            mock_service.get_csv_template.assert_called_once_with(None)
            
        app.dependency_overrides.clear()
    
    def test_get_csv_template_by_category(self, client, auth_override, db_override):
        """Test CSV template download for specific category"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        template_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Vidrio Claro 6mm,VID-CLR-6MM,M2,Vidrio,280.00,,Vidrio claro templado 6mm"""
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_csv_template.return_value = template_csv
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/template?category=Vidrio")
            
            assert response.status_code == 200
            assert "attachment; filename=materials_template_Vidrio.csv" in response.headers["content-disposition"]
            mock_service.get_csv_template.assert_called_once_with("Vidrio")
            
        app.dependency_overrides.clear()
    
    def test_get_csv_template_error(self, client, auth_override, db_override):
        """Test CSV template download error handling"""
        app.dependency_overrides[get_current_user_flexible] = auth_override
        app.dependency_overrides[get_db] = db_override
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_csv_template.side_effect = Exception("Template generation error")
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/materials/csv/template")
            
            assert response.status_code == 500
            assert "Error generating template" in response.json()["detail"]
            
        app.dependency_overrides.clear()
    
    def test_unauthorized_access(self, client, db_override):
        """Test that endpoints require authentication"""
        app.dependency_overrides[get_db] = db_override
        
        # Test export endpoint without authentication
        response = client.get("/api/materials/csv/export")
        assert response.status_code == 401
        
        # Test import endpoint without authentication
        csv_content = "action,id,name\ncreate,,Test"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as upload_file:
                response = client.post(
                    "/api/materials/csv/import",
                    files={"file": ("test.csv", upload_file, "text/csv")}
                )
        assert response.status_code == 401
        
        # Test template endpoint without authentication
        response = client.get("/api/materials/csv/template")
        assert response.status_code == 401
        
        app.dependency_overrides.clear()

class TestCSVSecurityValidation:
    """Test security aspects of CSV endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.email = "test@example.com"
        return user
    
    def test_csv_injection_protection(self, client, mock_user):
        """Test protection against CSV injection attacks"""
        app.dependency_overrides[get_current_user_flexible] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()
        
        # CSV with potential injection payload
        malicious_csv = """action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,=cmd|'/c calc'!A0,EVIL-001,ML,Perfiles,45.50,6.0,Malicious formula"""
        
        import_results = {
            "success": [],
            "errors": [{"row": 2, "error": "Invalid material name"}],
            "summary": {"created": 0, "updated": 0, "deleted": 0, "skipped": 1}
        }
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            mock_service.import_materials_from_csv.return_value = import_results
            mock_service_class.return_value = mock_service
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(malicious_csv)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/materials/csv/import",
                        files={"file": ("evil.csv", upload_file, "text/csv")}
                    )
        
        assert response.status_code == 200
        # The service should have been called with the malicious content
        # but validation should catch and reject it
        mock_service.import_materials_from_csv.assert_called_once()
        
        app.dependency_overrides.clear()
    
    def test_large_file_handling(self, client, mock_user):
        """Test handling of large CSV files"""
        app.dependency_overrides[get_current_user_flexible] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock()
        
        # Create a large CSV content (simulate large file)
        large_csv_lines = ["action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description"]
        for i in range(1000):  # 1000 rows
            large_csv_lines.append(f"create,,Material {i},MAT-{i:04d},ML,Perfiles,45.50,6.0,Description {i}")
        
        large_csv = "\n".join(large_csv_lines)
        
        with patch('services.material_csv_service.MaterialCSVService') as mock_service_class:
            mock_service = Mock()
            # Simulate successful processing of large file
            mock_service.import_materials_from_csv.return_value = {
                "success": [{"action": "created", "row": i, "material_id": i} for i in range(1, 1001)],
                "errors": [],
                "summary": {"created": 1000, "updated": 0, "deleted": 0, "skipped": 0}
            }
            mock_service_class.return_value = mock_service
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                tmp_file.write(large_csv)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/materials/csv/import",
                        files={"file": ("large.csv", upload_file, "text/csv")}
                    )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1000
        
        app.dependency_overrides.clear()

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])