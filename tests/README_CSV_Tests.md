# CSV Import/Export Tests

This directory contains comprehensive tests for the CSV import/export functionality of the materials management system.

## Test Files

### 1. `test_material_csv_service.py`
**Unit tests for MaterialCSVService**
- Tests CSV export functionality
- Tests CSV import with validation
- Tests CRUD operations (create, update, delete)
- Tests data validation and sanitization
- Tests CSV template generation
- Tests error handling and edge cases

**Test Classes:**
- `TestMaterialCSVService` - Basic service functionality
- `TestCSVExport` - Export operations
- `TestCSVImport` - Import operations  
- `TestCSVValidation` - Data validation
- `TestCSVTemplate` - Template generation
- `TestCSVHeaders` - Header validation
- `TestCSVIntegration` - End-to-end workflows

### 2. `test_csv_api_endpoints.py`
**Integration tests for FastAPI endpoints**
- Tests `/api/materials/csv/export` endpoint
- Tests `/api/materials/csv/import` endpoint
- Tests `/api/materials/csv/template` endpoint
- Tests authentication and authorization
- Tests file upload handling
- Tests error responses and status codes

**Test Classes:**
- `TestCSVAPIEndpoints` - Main API functionality
- `TestCSVSecurityValidation` - Security aspects

### 3. `test_csv_validation_security.py`
**Security and validation tests**
- Tests CSV injection prevention
- Tests SQL injection prevention
- Tests XSS prevention
- Tests path traversal prevention
- Tests Unicode normalization attacks
- Tests data integrity and boundary conditions
- Tests performance with large files

**Test Classes:**
- `TestCSVSecurityValidation` - Security attack prevention
- `TestCSVDataIntegrity` - Data integrity and edge cases
- `TestCSVConcurrencyAndPerformance` - Performance tests

## Running Tests

### Method 1: Using the test runner script
```bash
python run_csv_tests.py
```

This will run all CSV tests with organized output and summary.

### Method 2: Using pytest directly
```bash
# Run all CSV tests
pytest tests/test_material_csv_service.py tests/test_csv_api_endpoints.py tests/test_csv_validation_security.py -v

# Run specific test file
pytest tests/test_material_csv_service.py -v

# Run tests with specific markers
pytest -m "unit" -v          # Unit tests only
pytest -m "security" -v      # Security tests only
pytest -m "integration" -v   # Integration tests only

# Run with coverage
pytest tests/test_*.py --cov=services.material_csv_service --cov-report=html
```

### Method 3: Run individual test classes
```bash
# Run specific test class
pytest tests/test_material_csv_service.py::TestCSVExport -v

# Run specific test method
pytest tests/test_material_csv_service.py::TestCSVExport::test_export_all_materials -v
```

## Test Coverage

The tests cover the following areas:

### ✅ **Functional Testing**
- CSV export by category
- CSV import with create/update/delete operations
- Template generation
- Data validation
- Error handling

### ✅ **Security Testing**
- CSV injection attacks (=, @, +, - formulas)
- SQL injection prevention
- XSS attack prevention
- Path traversal prevention
- Unicode normalization attacks
- Input sanitization

### ✅ **Data Integrity Testing**
- Boundary value testing
- Invalid data handling
- Missing field validation
- Duplicate detection
- Data type validation

### ✅ **Performance Testing**
- Large file processing (1000+ records)
- Memory usage optimization
- Concurrent operations handling

### ✅ **API Testing**
- HTTP status codes
- Authentication/authorization
- File upload validation
- Content-Type headers
- Error response formats

## Test Data Scenarios

### Valid CSV Examples
```csv
action,id,name,code,unit,category,cost_per_unit,selling_unit_length_m,description
create,,Perfil AL Serie 3,PRF-AL-S3-001,ML,Perfiles,45.50,6.0,Aluminum profile
update,1,Updated Name,PRF-AL-S3-002,ML,Perfiles,47.00,,Updated description
delete,2,,,,,,,
```

### Security Test Cases
- CSV injection: `=cmd|'/c calc'!A0`
- SQL injection: `'; DROP TABLE app_materials; --`
- XSS: `<script>alert('XSS')</script>`
- Path traversal: `../../../etc/passwd`

### Edge Cases
- Empty files
- Files with only headers
- Very large files (1000+ rows)
- Unicode characters
- Special numeric formats
- Missing required fields

## Dependencies

Required packages for testing:
```
pytest>=7.0.0
httpx>=0.24.0  # For FastAPI TestClient
pytest-cov>=4.0.0  # For coverage reports (optional)
```

Install test dependencies:
```bash
pip install pytest httpx pytest-cov
```

## CI/CD Integration

These tests are designed to be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run CSV Tests
  run: |
    pip install pytest httpx
    python run_csv_tests.py
```

## Test Configuration

The `pytest.ini` file contains test configuration:
- Test discovery patterns
- Markers for categorizing tests
- Output formatting options
- Warning filters

## Mocking Strategy

Tests use comprehensive mocking to isolate functionality:
- Database sessions are mocked
- Material service methods are mocked
- Input validation is mocked for security tests
- Authentication is mocked for API tests

This ensures tests are fast, reliable, and don't require actual database connections.

## Expected Test Results

When all tests pass, you should see:
- **Unit Tests**: ~30+ test methods covering core CSV service functionality
- **Integration Tests**: ~15+ test methods covering API endpoints
- **Security Tests**: ~20+ test methods covering security scenarios

Total: **65+ test methods** providing comprehensive coverage of the CSV import/export system.