# Atomic Execution Plan: ARCH-20251017-001
## Complete Glass Selection Database Migration - Dynamic Dropdown UI

**Task ID**: ARCH-20251017-001
**Created**: 2025-10-17
**Estimated Total Time**: 8-12 hours (1.5-2 work days)
**Risk Level**: LOW (backward compatible)
**Priority**: MEDIUM

---

## Executive Summary

Complete the database-driven migration for glass selection UI by replacing hardcoded GlassType enum dropdown with dynamic database queries. This task completes ARCH-20251007-001 by making glass **selection** (not just pricing) fully database-driven, matching the architecture pattern used for profile colors. Enables users to dynamically add/remove glass types via Materials Catalog UI without code deployment.

**Key Change**: From `selected_glass_type: GlassType (enum)` → `selected_glass_material_id: int (database ID)`

---

## Success Criteria

1. ✅ **Database-Driven Dropdown**: Glass dropdown populated from `app_materials` table query (category='Vidrio')
2. ✅ **Dynamic Catalog**: New glass materials added via Materials Catalog UI immediately appear in quote creation dropdown
3. ✅ **Material ID Selection**: Quote calculations use `glass_material_id` instead of enum value
4. ✅ **Backward Compatibility**: Existing quotes with enum values continue to work (dual-path support)
5. ✅ **All Glass Types Work**: All 7 current glass types (VID-CLARO-4, VID-CLARO-6, etc.) function correctly
6. ✅ **Multi-Tenant Ready**: Dropdown filterable by `tenant_id` (prepared for MTENANT-20251006-012)
7. ✅ **Test Coverage**: Unit + integration tests pass with >90% coverage
8. ✅ **Performance**: No degradation (<5ms overhead, cached lookups)
9. ✅ **Zero Breaking Changes**: Gradual migration, no API contract breakage

---

## Dependency Verification

**Depends on**: ARCH-20251007-001 ✅ COMPLETED (2025-10-14)

**Status**:
- ✅ Glass pricing is database-driven
- ✅ 7 glass materials exist in database with correct codes
- ✅ `GLASS_TYPE_TO_MATERIAL_CODE` mapping established
- ✅ `get_glass_cost_per_m2()` method working
- ✅ Caching mechanism implemented

**Blocks**: MTENANT-20251006-012 (Multi-tenant glass catalogs)

---

## Current State Analysis

### What Works ✅
- Backend pricing queries database for glass costs
- Users can update glass prices via Materials Catalog
- All 7 glass types calculate correctly
- Caching reduces database load

### What's Hardcoded ❌
```python
# app/routes/quotes.py:303-305
glass_types_display = [
    {"value": gt.value, "label": gt.value.replace('_', ' ').title()}
    for gt in GlassType  # ❌ Hardcoded enum iteration
]
```

```html
<!-- templates/new_quote.html:218-225 -->
<select class="form-select selected-glass-type" required>
    {% for glass in glass_types %}  <!-- ❌ Enum values -->
    <option value="{{ glass.value }}">{{ glass.label }}</option>
    {% endfor %}
</select>
```

### Reference Architecture (Profile Colors) ✅
```javascript
// templates/new_quote.html:470-514
async function loadProfileColors(colorSelect, product) {
    const response = await fetch(`/api/materials/by-category`);
    const data = await response.json();
    // ✅ Populates dropdown from database query
    data.categories.Perfiles[0].colors.forEach(color => {
        option.value = color.color_id;  // Database ID
        colorSelect.appendChild(option);
    });
}
```

**Goal**: Apply the same database-driven pattern to glass selection.

---

## Risk Assessment

### Risks and Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking existing quotes | 🔴 HIGH | Keep dual-path support: enum OR material_id |
| Frontend-backend mismatch | 🟡 MEDIUM | Update both simultaneously, test checkpoints |
| Performance degradation | 🟢 LOW | Reuse existing caching mechanism |
| Database migration issues | 🟢 LOW | No schema changes, only code changes |
| Testing complexity | 🟡 MEDIUM | Comprehensive test suite with both paths |

### Rollback Strategy

**Quick Rollback** (if issues discovered):
```bash
git revert <commit-hash>  # Revert specific atomic commit
git checkout main app/routes/quotes.py templates/new_quote.html models/quote_models.py
docker-compose restart app  # Restart application
```

**Complete Rollback** (if major issues):
```bash
git checkout main
git branch -D arch/glass-selection-database-20251017
docker-compose down && docker-compose up -d --build
```

**Database Rollback**: No migrations needed, so no database rollback required.

---

## Docker Development Environment

**IMPORTANT**: All local development and testing should be done inside Docker containers to match production environment exactly.

### Docker Setup for Local Development

#### 1. Start Development Environment
```bash
# Start all services (app, database, redis)
docker-compose up -d

# Verify containers running
docker ps

# Expected containers:
# - cotizador_ventanas-app (FastAPI application)
# - cotizador_ventanas-db (PostgreSQL database)
# - cotizador_ventanas-redis (Redis cache)
```

#### 2. Access Application Container
```bash
# Enter the application container for interactive work
docker exec -it cotizador_ventanas-app bash

# Inside container, you can:
# - Run Python commands
# - Execute tests
# - Check files
# - View logs
```

#### 3. Common Docker Commands for Development

**Execute Python commands:**
```bash
# From host machine
docker exec cotizador_ventanas-app python -c "from database import SessionLocal; print('✓ DB connected')"

# Interactive Python shell
docker exec -it cotizador_ventanas-app python
```

**Run tests:**
```bash
# From host machine
docker exec cotizador_ventanas-app pytest tests/test_glass_pricing_database.py -v

# Inside container
docker exec -it cotizador_ventanas-app bash
pytest tests/test_glass_pricing_database.py -v
```

**View logs:**
```bash
# Application logs
docker logs cotizador_ventanas-app -f

# Database logs
docker logs cotizador_ventanas-db -f
```

**Rebuild after code changes:**
```bash
# Rebuild application container
docker-compose down
docker-compose build --no-cache app
docker-compose up -d

# Or quick restart (for Python code changes only)
docker-compose restart app
```

#### 4. Database Access Inside Docker

**PostgreSQL access:**
```bash
# Access database from host
docker exec -it cotizador_ventanas-db psql -U ventanas_user -d ventanas_db

# Run SQL query from host
docker exec cotizador_ventanas-db psql -U ventanas_user -d ventanas_db -c "SELECT COUNT(*) FROM app_materials WHERE category = 'Vidrio';"
```

**Database shell:**
```bash
# Interactive PostgreSQL shell
docker exec -it cotizador_ventanas-db psql -U ventanas_user -d ventanas_db

# Inside psql:
\dt                           # List tables
\d app_materials              # Describe materials table
SELECT * FROM app_materials WHERE category = 'Vidrio';
```

#### 5. File Editing Workflow

**Recommended workflow:**
1. **Edit files on host** (using your IDE/editor) - changes reflected in container via volume mount
2. **Test in container** - execute tests inside Docker
3. **Restart if needed** - `docker-compose restart app` for Python changes
4. **Commit from host** - use git on host machine

**Volume mounts** (already configured in docker-compose.yml):
```yaml
volumes:
  - .:/app  # Current directory mounted to /app in container
```

This means file changes on host are immediately visible in container.

#### 6. Troubleshooting

**Container won't start:**
```bash
# Check logs
docker logs cotizador_ventanas-app

# Remove and rebuild
docker-compose down
docker-compose up -d --build
```

**Database connection issues:**
```bash
# Check database is running
docker ps | grep db

# Test connection
docker exec cotizador_ventanas-app python -c "from database import SessionLocal; db = SessionLocal(); print('✓ Connected'); db.close()"
```

**Permission issues:**
```bash
# Fix file permissions (if needed)
sudo chown -R $USER:$USER .
```

---

## PHASE 1: PREPARATION (30 minutes)

### Pre-Flight Checklist

- [ ] **Environment Setup**
  ```bash
  # Start Docker containers
  docker-compose up -d

  # Verify containers running
  docker ps
  # Expected: cotizador_ventanas-app, cotizador_ventanas-db, cotizador_ventanas-redis

  # Verify Python environment (inside container)
  docker exec cotizador_ventanas-app python --version  # Expected: 3.11+
  docker exec cotizador_ventanas-app pip list | grep -E "fastapi|sqlalchemy|pydantic"

  # Verify database connection (inside container)
  docker exec cotizador_ventanas-app python -c "from database import SessionLocal; db = SessionLocal(); print('✓ DB connected'); db.close()"

  # Verify test framework (inside container)
  docker exec cotizador_ventanas-app pytest --version  # Expected: 7.x+
  ```

- [ ] **Branch Creation**
  ```bash
  git checkout main
  git pull origin main
  git checkout -b arch/glass-selection-database-20251017
  echo "✓ Branch created: arch/glass-selection-database-20251017"
  ```

- [ ] **Baseline Tests**
  ```bash
  # Run existing glass pricing tests (inside Docker container)
  docker exec cotizador_ventanas-app pytest tests/test_glass_pricing_database.py -v
  # Expected: 16 tests pass

  # Run quote integration tests (inside Docker container)
  docker exec cotizador_ventanas-app pytest tests/test_integration_quotes_routes.py::TestGlassPricingIntegration -v
  # Expected: 2 tests pass

  # Baseline performance (inside Docker container)
  docker exec cotizador_ventanas-app python -c "
  from database import SessionLocal
  from services.product_bom_service_db import ProductBOMServiceDB
  from models.quote_models import GlassType
  import time

  db = SessionLocal()
  service = ProductBOMServiceDB(db)

  start = time.time()
  price = service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
  elapsed = (time.time() - start) * 1000

  print(f'Baseline: {elapsed:.2f}ms (cached should be <1ms)')
  db.close()
  "
  ```

- [ ] **Documentation Review**
  ```bash
  # Review architectural analysis
  cat .claude/workspace/ARCH-20251007-001/post-deployment-review.md

  # Review existing glass pricing implementation
  grep -n "get_glass_cost_per_m2" services/product_bom_service_db.py

  # Review profile colors pattern (reference implementation)
  grep -n "loadProfileColors" templates/new_quote.html
  ```

- [ ] **Success Criteria Definition**
  ```bash
  # Create success criteria checklist
  cat > .claude/workspace/ARCH-20251017-001/success-criteria.md << 'EOF'
  # Success Criteria: ARCH-20251017-001

  ## Functional Requirements
  - [ ] Glass dropdown shows database materials (not enum)
  - [ ] New materials added via UI appear in dropdown
  - [ ] Quote calculation uses material_id
  - [ ] Old enum-based quotes still work
  - [ ] All 7 glass types functional

  ## Technical Requirements
  - [ ] No schema migrations needed
  - [ ] Backward compatible API
  - [ ] Multi-tenant ready (tenant_id filter prepared)
  - [ ] Performance <5ms (cached)
  - [ ] Test coverage >90%

  ## User Experience
  - [ ] Dropdown shows: "Glass Name - $Price/m²"
  - [ ] Sorted by name or price
  - [ ] Inactive materials excluded
  - [ ] Error handling for missing materials
  EOF
  ```

---

## PHASE 2: IMPLEMENTATION (6-8 hours)

### Step 1: Add get_glass_cost_by_material_id() Method

**Action**: Create new database-driven method that queries by material ID instead of enum

**Files**:
- Modify: `services/product_bom_service_db.py` (add method after line 270)

**Code**:
```python
def get_glass_cost_by_material_id(self, material_id: int) -> Decimal:
    """
    Get glass cost per m² from database by material ID (not enum).

    This is the NEW database-driven approach. Replaces enum-based lookup.

    Args:
        material_id: Database ID of glass material

    Returns:
        Glass cost per m² from database

    Raises:
        ValueError: If material not found or not a glass material
    """
    # Check cache first (if caching enabled)
    if self._glass_price_cache is not None and material_id in self._glass_price_cache:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Glass price cache HIT for material_id={material_id}")
        return self._glass_price_cache[material_id]

    try:
        # Query database for glass material by ID
        glass_material = (
            self.db.query(DBAppMaterial)
            .filter(DBAppMaterial.id == material_id)
            .filter(DBAppMaterial.category == "Vidrio")
            .filter(DBAppMaterial.is_active == True)
            .first()
        )

        if not glass_material:
            raise ValueError(
                f"Glass material with ID {material_id} not found or not active. "
                "Ensure material exists in database with category='Vidrio'."
            )

        price = glass_material.cost_per_unit

        # Cache the price (if caching enabled)
        if self._glass_price_cache is not None:
            self._glass_price_cache[material_id] = price

        # Audit log: using database price
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(
            f"Glass price retrieved from DATABASE: "
            f"material_id={material_id}, code={glass_material.code}, "
            f"price=${price}/m²"
        )

        return price

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"Failed to retrieve glass price by material_id={material_id}: {e}"
        )
        raise ValueError(
            f"Unable to retrieve glass price for material_id={material_id}. "
            "Database query failed."
        ) from e
```

**Test Checkpoint** (run inside Docker container):
```bash
# Test new method (inside Docker container)
docker exec cotizador_ventanas-app python -c "
from database import SessionLocal
from services.product_bom_service_db import ProductBOMServiceDB, initialize_sample_data

db = SessionLocal()

# Initialize sample data to ensure glass materials exist
initialize_sample_data(db)

service = ProductBOMServiceDB(db)

# Get VID-CLARO-6 material ID
from database import DatabaseMaterialService
material_service = DatabaseMaterialService(db)
glass_material = material_service.get_material_by_code('VID-CLARO-6')

if glass_material:
    material_id = glass_material.id
    price = service.get_glass_cost_by_material_id(material_id)
    print(f'✓ Material ID {material_id}: \${price}/m²')
    assert price == 120.00, f'Expected \$120, got \${price}'
    print('✓ Price correct')
else:
    print('✗ Glass material VID-CLARO-6 not found')

db.close()
"

# Alternative: Run interactively inside container
docker exec -it cotizador_ventanas-app python
# Then paste the code above (without the outer quotes)
```

**Commit Message**:
```
feat: add get_glass_cost_by_material_id() for database-driven glass selection

- Created get_glass_cost_by_material_id(material_id) in ProductBOMServiceDB
- Queries database by material ID instead of enum value
- Includes caching mechanism (reuses _glass_price_cache)
- Comprehensive error handling and audit logging
- Validates category='Vidrio' and is_active=True

Task: ARCH-20251017-001
Step: 1/7
```

**Rollback**: `git checkout HEAD~1 services/product_bom_service_db.py`

**Time**: 30 minutes

---

### Step 2: Update QuoteItemRequest Model (Dual-Path Support)

**Action**: Add `selected_glass_material_id` field while keeping `selected_glass_type` for backward compatibility

**Files**:
- Modify: `models/quote_models.py` (around line 75)

**Code**:
```python
class QuoteItemRequest(BaseModel):
    """Quote item request with product BOM and dimensions."""
    product_bom_id: int = Field(..., description="ID del producto BOM seleccionado")

    # GLASS SELECTION: Dual-path support for gradual migration
    selected_glass_type: Optional[GlassType] = Field(
        None,
        description="[DEPRECATED] Tipo de vidrio (enum). Use selected_glass_material_id instead."
    )
    selected_glass_material_id: Optional[int] = Field(
        None,
        description="[PREFERRED] ID del material de vidrio desde database. "
                    "Si se proporciona, tiene prioridad sobre selected_glass_type."
    )

    selected_profile_color: Optional[int] = Field(None, description="ID del color seleccionado para los perfiles.")

    width_cm: Decimal = Field(..., gt=0, le=1000, description="Ancho en centímetros")
    height_cm: Decimal = Field(..., gt=0, le=1000, description="Alto en centímetros")
    quantity: int = Field(..., gt=0, le=100, description="Cantidad de ventanas")
    description: Optional[str] = None

    @validator('selected_glass_material_id', 'selected_glass_type')
    def validate_glass_selection(cls, v, values):
        """Ensure at least one glass selection method is provided."""
        # If this is selected_glass_material_id validation
        if 'selected_glass_material_id' in values:
            material_id = values.get('selected_glass_material_id')
            glass_type = values.get('selected_glass_type')

            # At least one must be provided
            if material_id is None and glass_type is None:
                raise ValueError(
                    'Either selected_glass_material_id or selected_glass_type must be provided'
                )

        return v

    @validator('width_cm', 'height_cm')
    def validate_dimensions(cls, v):
        """Validar que las dimensiones sean razonables"""
        if v < 30:
            raise ValueError('Las dimensiones mínimas son 30cm')
        if v > 500:
            raise ValueError('Las dimensiones máximas son 500cm')
        return v
```

**Test Checkpoint**:
```bash
# Test model validation
python -c "
from models.quote_models import QuoteItemRequest, GlassType
from decimal import Decimal

# Test 1: Old path (enum) - backward compatibility
try:
    item_old = QuoteItemRequest(
        product_bom_id=1,
        selected_glass_type=GlassType.CLARO_6MM,
        width_cm=Decimal('100'),
        height_cm=Decimal('150'),
        quantity=1
    )
    print('✓ Old path (enum) works')
except Exception as e:
    print(f'✗ Old path failed: {e}')

# Test 2: New path (material_id)
try:
    item_new = QuoteItemRequest(
        product_bom_id=1,
        selected_glass_material_id=123,
        width_cm=Decimal('100'),
        height_cm=Decimal('150'),
        quantity=1
    )
    print('✓ New path (material_id) works')
except Exception as e:
    print(f'✗ New path failed: {e}')

# Test 3: Dual path (both provided - material_id takes precedence)
try:
    item_dual = QuoteItemRequest(
        product_bom_id=1,
        selected_glass_type=GlassType.CLARO_6MM,
        selected_glass_material_id=456,
        width_cm=Decimal('100'),
        height_cm=Decimal('150'),
        quantity=1
    )
    print('✓ Dual path works')
except Exception as e:
    print(f'✗ Dual path failed: {e}')

# Test 4: No glass selection - should fail
try:
    item_none = QuoteItemRequest(
        product_bom_id=1,
        width_cm=Decimal('100'),
        height_cm=Decimal('150'),
        quantity=1
    )
    print('✗ No glass selection should have failed validation')
except ValueError as e:
    print(f'✓ No glass selection correctly rejected: {e}')

print('✓ All model validation tests passed')
"
```

**Commit Message**:
```
feat: add dual-path glass selection to QuoteItemRequest model

- Added selected_glass_material_id field (preferred, database-driven)
- Kept selected_glass_type field (deprecated, enum-based)
- Both fields optional but at least one required (validator)
- Backward compatibility: old quotes with enum still work
- New quotes should use material_id for database selection

Task: ARCH-20251017-001
Step: 2/7
```

**Rollback**: `git checkout HEAD~1 models/quote_models.py`

**Time**: 20 minutes

---

### Step 3: Update Backend Route - Query Glass Materials from Database

**Action**: Modify `new_quote_page()` in routes to query glass materials instead of iterating enum

**Files**:
- Modify: `app/routes/quotes.py` (lines 285-325)

**Code**:
```python
@router.get("/quotes/new", response_class=HTMLResponse)
async def new_quote_page(request: Request, db: Session = Depends(get_db)):
    """Display new quote creation page"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Get products and materials from database
    product_bom_service = ProductBOMServiceDB(db)
    materials_for_frontend = product_bom_service.get_all_materials()
    products_for_frontend = product_bom_service.get_all_products()

    # Map enums for frontend (window types and aluminum lines still use enums)
    window_types_display = [
        {"value": wt.value, "label": wt.value.replace('_', ' ').title()} for wt in WindowType
    ]
    aluminum_lines_display = [
        {"value": al.value, "label": al.value.replace('_', ' ').title()} for al in AluminumLine
    ]

    # GLASS MATERIALS: Query from database (NEW - database-driven) ✅
    material_service = DatabaseMaterialService(db)
    glass_materials_db = material_service.get_materials_by_category("Vidrio")

    # Filter active materials and format for frontend
    glass_materials_display = [
        {
            "id": m.id,
            "code": m.code,
            "name": m.name,
            "cost_per_unit": float(m.cost_per_unit),
            "unit": m.unit.value if hasattr(m.unit, 'value') else str(m.unit),
            "description": m.description or "",
            # Display format: "Vidrio Claro 6mm - $120.00/m²"
            "display_label": f"{m.name} - ${float(m.cost_per_unit):.2f}/{m.unit.value if hasattr(m.unit, 'value') else str(m.unit)}"
        }
        for m in glass_materials_db
        if m.is_active  # Only show active materials
    ]

    # Sort by name for better UX
    glass_materials_display.sort(key=lambda x: x['name'])

    # Convert to JSON-compatible format
    app_materials_json_compatible = [m.model_dump(mode='json') for m in materials_for_frontend]
    app_products_json_compatible = [p.model_dump(mode='json') for p in products_for_frontend]

    return templates.TemplateResponse("new_quote.html", {
        "request": request,
        "title": "Nueva Cotización",
        "user": user,
        "app_materials": app_materials_json_compatible,
        "app_products": app_products_json_compatible,
        "window_types": window_types_display,
        "aluminum_lines": aluminum_lines_display,
        "glass_materials": glass_materials_display,  # NEW: database query ✅
        # Keep old variable for backward compatibility during transition
        "glass_types": glass_materials_display,  # Alias for template compatibility
        "business_overhead": {
            "profit_margin": settings.default_profit_margin,
            "indirect_costs": settings.default_indirect_costs,
            "tax_rate": settings.default_tax_rate
        }
    })
```

**Test Checkpoint**:
```bash
# Test route returns glass materials from database
python -c "
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal

client = TestClient(app)

# Login first (adjust credentials as needed)
login_response = client.post('/web/login', data={
    'username': 'admin@test.com',
    'password': 'admin123'
})

if login_response.status_code == 200:
    # Access new quote page
    response = client.get('/quotes/new', follow_redirects=True)

    if response.status_code == 200:
        # Check if glass_materials in context
        if 'glass_materials' in response.text or 'VID-CLARO' in response.text:
            print('✓ Route returns glass materials from database')
        else:
            print('✗ Glass materials not found in response')
    else:
        print(f'✗ Route failed: {response.status_code}')
else:
    print('Note: Manual login required for full test')
    print('Test route manually: http://localhost:8000/quotes/new')
"
```

**Manual Test**:
```bash
# Start application and test manually
python main.py &
sleep 5
curl -s http://localhost:8000/quotes/new | grep -o "glass_materials" | head -1
```

**Commit Message**:
```
feat: query glass materials from database in new_quote_page route

- Modified app/routes/quotes.py new_quote_page()
- Query glass materials from database (category='Vidrio')
- Filter by is_active=True to exclude inactive materials
- Format for frontend: {id, code, name, cost_per_unit, display_label}
- Sort by name for better UX
- Maintain backward compatibility: keep glass_types alias

Task: ARCH-20251017-001
Step: 3/7
```

**Rollback**: `git checkout HEAD~1 app/routes/quotes.py`

**Time**: 25 minutes

---

### Step 4: Update Template Dropdown - Use Database Materials

**Action**: Replace enum-based dropdown with database-driven materials in new_quote.html

**Files**:
- Modify: `templates/new_quote.html` (lines 217-226, 309, 621-622)

**Code Changes**:

**1. Update HTML Dropdown** (lines 217-226):
```html
<div class="col-md-3 mb-3">
    <label class="form-label">Tipo de Vidrio *</label>
    <select class="form-select selected-glass-material-id" required>
        <option value="">Seleccionar...</option>
        {% for glass in glass_materials %}
        <option value="{{ glass.id }}"
                data-code="{{ glass.code }}"
                data-name="{{ glass.name }}"
                data-price="{{ glass.cost_per_unit }}">
            {{ glass.display_label }}
        </option>
        {% endfor %}
    </select>
    <small class="form-text text-muted">Precios desde catálogo de materiales</small>
</div>
```

**2. Update JavaScript Variables** (line 309):
```javascript
// OLD: const glassTypes = {{ glass_types | tojson }};
const glassMaterials = {{ glass_materials | tojson }};  // Database-driven ✅

// Keep for backward compatibility during transition
const glassTypes = glassMaterials;  // Alias
```

**3. Update Item Data Collection** (lines 621-622, 923):
```javascript
// In updateItemLiveCalculation() function (line 621)
const selectedGlassMaterialId = windowItemElement.querySelector('.selected-glass-material-id').value;

// In collectFormData() function (line 923)
const itemData = {
    product_bom_id: productId,
    selected_glass_material_id: parseInt(item.querySelector('.selected-glass-material-id').value),
    // Remove: selected_glass_type: item.querySelector('.selected-glass-type').value,
    selected_profile_color: item.querySelector('.selected-profile-color').value,
    // ... rest of fields
};
```

**4. Update Event Listeners** (line 360):
```javascript
// OLD: selectedGlassTypeSelect.addEventListener('change', ...)
const selectedGlassMaterialIdSelect = clone.querySelector('.selected-glass-material-id');
selectedGlassMaterialIdSelect.addEventListener('change', () =>
    updateItemLiveCalculation(selectedGlassMaterialIdSelect.closest('.window-item'))
);
```

**Test Checkpoint**:
```bash
# Manual test in browser
# 1. Start application
python main.py &
sleep 5

# 2. Open browser
echo "Open http://localhost:8000/quotes/new in browser"
echo "Expected:"
echo "  - Glass dropdown shows: 'Vidrio Claro 6mm - \$120.00/m²'"
echo "  - Dropdown values are material IDs (integers)"
echo "  - No enum values (claro_6mm, etc.)"
echo ""
echo "Test steps:"
echo "  1. Click 'Agregar Ventana' button"
echo "  2. Open glass dropdown"
echo "  3. Verify materials show with prices"
echo "  4. Select a glass type"
echo "  5. Verify live calculation works"
```

**Commit Message**:
```
feat: update new_quote template to use database-driven glass dropdown

- Changed dropdown class: selected-glass-type → selected-glass-material-id
- Dropdown now shows database materials with prices
- Display format: "Material Name - $Price/Unit"
- JavaScript updated: glassTypes → glassMaterials
- Event listeners updated for new selector
- Item data collection uses material_id instead of enum

Task: ARCH-20251017-001
Step: 4/7
```

**Rollback**: `git checkout HEAD~1 templates/new_quote.html`

**Time**: 45 minutes

---

### Step 5: Update Backend Calculation to Support Both Paths

**Action**: Modify quote calculation endpoints to handle both enum (old) and material_id (new)

**Files**:
- Modify: `app/routes/quotes.py` (calculate_quote and calculate_item functions)

**Code** (in calculate_quote function, around line 150):
```python
# Determine glass cost (dual-path support)
if item_request.selected_glass_material_id:
    # NEW PATH: Use material ID (database-driven) ✅
    glass_cost_per_m2 = product_bom_service.get_glass_cost_by_material_id(
        item_request.selected_glass_material_id
    )
    glass_identifier = f"material_id:{item_request.selected_glass_material_id}"
elif item_request.selected_glass_type:
    # OLD PATH: Use enum (backward compatibility) ⚠️
    glass_cost_per_m2 = product_bom_service.get_glass_cost_per_m2(
        item_request.selected_glass_type
    )
    glass_identifier = item_request.selected_glass_type.value
else:
    # Should not happen due to model validation
    raise HTTPException(
        status_code=400,
        detail="Either selected_glass_material_id or selected_glass_type must be provided"
    )

# Log which path was used (for monitoring migration)
import logging
logger = logging.getLogger(__name__)
logger.info(
    f"Glass cost calculation path: {glass_identifier}, "
    f"price=${glass_cost_per_m2}/m²"
)

# Rest of calculation logic remains the same
# ...
```

**Test Checkpoint**:
```bash
# Test both paths work
python -c "
from fastapi.testclient import TestClient
from main import app
from models.quote_models import GlassType
from decimal import Decimal
import json

client = TestClient(app)

# Test data
quote_data_old_path = {
    'client': {'name': 'Test Client'},
    'items': [{
        'product_bom_id': 1,
        'selected_glass_type': 'claro_6mm',  # OLD: enum value
        'width_cm': 100,
        'height_cm': 150,
        'quantity': 1
    }],
    'profit_margin': 0.25,
    'indirect_costs_rate': 0.15,
    'tax_rate': 0.16
}

quote_data_new_path = {
    'client': {'name': 'Test Client'},
    'items': [{
        'product_bom_id': 1,
        'selected_glass_material_id': 2,  # NEW: material ID
        'width_cm': 100,
        'height_cm': 150,
        'quantity': 1
    }],
    'profit_margin': 0.25,
    'indirect_costs_rate': 0.15,
    'tax_rate': 0.16
}

# Test old path (enum)
try:
    response_old = client.post('/quotes/calculate', json=quote_data_old_path)
    if response_old.status_code == 200:
        print('✓ Old path (enum) works')
    else:
        print(f'✗ Old path failed: {response_old.status_code}')
except Exception as e:
    print(f'Note: Full test requires running app: {e}')

# Test new path (material_id)
try:
    response_new = client.post('/quotes/calculate', json=quote_data_new_path)
    if response_new.status_code == 200:
        print('✓ New path (material_id) works')
    else:
        print(f'✗ New path failed: {response_new.status_code}')
except Exception as e:
    print(f'Note: Full test requires running app: {e}')

print('Manual test recommended: Start app and test via browser')
"
```

**Commit Message**:
```
feat: add dual-path support to quote calculation endpoints

- Modified calculate_quote() to handle both paths:
  - selected_glass_material_id (preferred, database ID)
  - selected_glass_type (deprecated, enum value)
- Material ID takes precedence if both provided
- Added logging to track which path is used
- Backward compatibility: existing quotes still work
- Forward compatibility: new quotes use material_id

Task: ARCH-20251017-001
Step: 5/7
```

**Rollback**: `git checkout HEAD~1 app/routes/quotes.py`

**Time**: 40 minutes

---

### Step 6: Update Edit Quote Page (Optional but Recommended)

**Action**: Apply same changes to edit_quote.html for consistency

**Files**:
- Modify: `templates/edit_quote.html` (similar changes to new_quote.html)
- Modify: `app/routes/quotes.py` (edit_quote_page function, around line 430)

**Code** (edit_quote_page route):
```python
@router.get("/quotes/{quote_id}/edit", response_class=HTMLResponse)
async def edit_quote_page(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Display quote editing page"""
    user = await get_current_user_from_cookie(request, db)
    # ... existing code ...

    # Query glass materials from database (same as new_quote_page)
    material_service = DatabaseMaterialService(db)
    glass_materials_db = material_service.get_materials_by_category("Vidrio")

    glass_materials_display = [
        {
            "id": m.id,
            "code": m.code,
            "name": m.name,
            "cost_per_unit": float(m.cost_per_unit),
            "display_label": f"{m.name} - ${float(m.cost_per_unit):.2f}/m²"
        }
        for m in glass_materials_db
        if m.is_active
    ]
    glass_materials_display.sort(key=lambda x: x['name'])

    return templates.TemplateResponse("edit_quote.html", {
        # ... existing context ...
        "glass_materials": glass_materials_display,  # NEW
        "glass_types": glass_materials_display,  # Alias for compatibility
    })
```

**Template Changes** (edit_quote.html - similar to new_quote.html):
- Update dropdown to use glass_materials
- Change class from `selected-glass-type` to `selected-glass-material-id`
- Update JavaScript to use glassMaterials

**Test Checkpoint**:
```bash
# Manual test
echo "Test edit quote page:"
echo "1. Create a quote via new quote page"
echo "2. Navigate to quotes list"
echo "3. Click 'Edit' on a quote"
echo "4. Verify glass dropdown shows database materials"
echo "5. Change glass type and save"
echo "6. Verify quote recalculates correctly"
```

**Commit Message**:
```
feat: update edit_quote page to use database-driven glass dropdown

- Modified edit_quote_page route to query glass materials
- Updated edit_quote.html template (same pattern as new_quote)
- Consistent UX: both create and edit use database materials
- Existing quotes can be edited with new glass types

Task: ARCH-20251017-001
Step: 6/7
```

**Rollback**: `git checkout HEAD~1 app/routes/quotes.py templates/edit_quote.html`

**Time**: 30 minutes

---

### Step 7: Add Deprecation Warnings and Documentation

**Action**: Add deprecation notices to guide future developers

**Files**:
- Modify: `models/quote_models.py` (add deprecation comments)
- Modify: `services/product_bom_service_db.py` (add deprecation warning)
- Modify: `CLAUDE.md` (update documentation)

**Code** (service deprecation warning):
```python
def get_glass_cost_per_m2(self, glass_type: GlassType) -> Decimal:
    """
    Get glass cost per m² from DATABASE (not hardcoded).

    **DEPRECATED**: This method uses enum-based selection.
    Use get_glass_cost_by_material_id(material_id) instead for database-driven selection.

    This method is kept for backward compatibility with existing quotes.
    Will be removed in future version after full migration.

    Args:
        glass_type: GlassType enum value

    Returns:
        Glass cost per m² from database
    """
    import warnings
    warnings.warn(
        "get_glass_cost_per_m2() is deprecated. "
        "Use get_glass_cost_by_material_id() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Existing implementation...
```

**Documentation** (CLAUDE.md update):
```markdown
## Glass Material Selection Architecture

### Current Implementation (2025-10-17)

Glass materials are now **fully database-driven** for both pricing and selection:

**Pricing**: Database query via `get_glass_cost_by_material_id(material_id)`
**Selection**: Database query populates dropdown in quote UI

### Migration Status

- ✅ **ARCH-20251007-001**: Glass pricing database-driven (2025-10-14)
- ✅ **ARCH-20251017-001**: Glass selection database-driven (2025-10-17)

### Backward Compatibility

**Dual-path support** maintains compatibility with existing quotes:

1. **New Path** (Preferred): `selected_glass_material_id: int`
   - Database ID from app_materials table
   - Enables dynamic catalog management
   - Multi-tenant ready (filterable by tenant_id)

2. **Old Path** (Deprecated): `selected_glass_type: GlassType`
   - Enum-based selection
   - Kept for backward compatibility
   - Will be removed in future version

**Usage in code**:
```python
# NEW: Use material ID (database-driven)
glass_cost = service.get_glass_cost_by_material_id(material_id=123)

# OLD: Use enum (deprecated, backward compatibility only)
glass_cost = service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
```

### Future Deprecation Timeline

1. **Now → 6 months**: Dual-path support (both work)
2. **6 months → 1 year**: Deprecation warnings in logs
3. **1 year+**: Remove enum-based path entirely
```

**Test Checkpoint**:
```bash
# Verify deprecation warning triggers
python -c "
import warnings
warnings.simplefilter('always', DeprecationWarning)

from database import SessionLocal
from services.product_bom_service_db import ProductBOMServiceDB
from models.quote_models import GlassType

db = SessionLocal()
service = ProductBOMServiceDB(db)

# This should trigger deprecation warning
price = service.get_glass_cost_per_m2(GlassType.CLARO_6MM)

print('✓ Deprecation warning test complete')
db.close()
"
```

**Commit Message**:
```
docs: add deprecation warnings for enum-based glass selection

- Added deprecation warning to get_glass_cost_per_m2()
- Updated CLAUDE.md with migration status and timeline
- Documented dual-path architecture
- Added backward compatibility notes
- Established deprecation timeline (1 year)

Task: ARCH-20251017-001
Step: 7/7
```

**Rollback**: `git checkout HEAD~1 models/quote_models.py services/product_bom_service_db.py CLAUDE.md`

**Time**: 25 minutes

---

## PHASE 3: INTEGRATION (1-2 hours)

### Integration Testing

- [ ] **End-to-End Quote Creation** (New Path)
  ```bash
  # Manual test in browser
  # 1. Navigate to /quotes/new
  # 2. Add window item
  # 3. Select product
  # 4. Select glass from dropdown (database-driven)
  # 5. Enter dimensions
  # 6. Calculate quote
  # 7. Verify glass cost correct
  # 8. Save quote
  # 9. View saved quote
  # 10. Verify glass displayed correctly
  ```

- [ ] **Edit Existing Quote** (Old Path - Backward Compatibility)
  ```bash
  # Test backward compatibility
  # 1. Find quote created before this change (has enum value)
  # 2. Click "Edit"
  # 3. Verify quote loads correctly
  # 4. Change glass type (now uses dropdown)
  # 5. Save changes
  # 6. Verify quote recalculates correctly
  ```

- [ ] **Add New Glass Material**
  ```bash
  # Test dynamic catalog
  # 1. Navigate to /materials_catalog
  # 2. Click "Add Material"
  # 3. Create new glass: "Vidrio Acústico 8mm"
  #    - Code: VID-ACUSTICO-8
  #    - Category: Vidrio
  #    - Cost: $250.00
  #    - Unit: M2
  # 4. Save material
  # 5. Navigate to /quotes/new
  # 6. Add window item
  # 7. Open glass dropdown
  # 8. VERIFY: New material appears in dropdown ✅
  # 9. Select new material
  # 10. Create quote
  # 11. VERIFY: Quote uses new material price ✅
  ```

- [ ] **Performance Testing**
  ```bash
  # Test caching works
  python -c "
  from database import SessionLocal
  from services.product_bom_service_db import ProductBOMServiceDB
  import time

  db = SessionLocal()
  service = ProductBOMServiceDB(db)

  # First call (uncached)
  start = time.time()
  price1 = service.get_glass_cost_by_material_id(2)
  time1 = (time.time() - start) * 1000

  # Second call (should be cached)
  start = time.time()
  price2 = service.get_glass_cost_by_material_id(2)
  time2 = (time.time() - start) * 1000

  print(f'First call: {time1:.2f}ms (database query)')
  print(f'Second call: {time2:.2f}ms (cached)')
  print(f'Cache speedup: {time1/time2:.1f}x')

  assert time2 < time1, 'Cache should be faster'
  assert time2 < 1.0, 'Cached call should be <1ms'
  print('✓ Performance test passed')

  db.close()
  "
  ```

---

## PHASE 4: TESTING (2-3 hours)

### Unit Tests

- [ ] **Create Test Suite for Material ID Path**

  **File**: `tests/test_glass_selection_database.py` (new file)

  ```python
  import pytest
  from decimal import Decimal
  from database import SessionLocal, DatabaseMaterialService, initialize_sample_data
  from services.product_bom_service_db import ProductBOMServiceDB
  from models.quote_models import QuoteItemRequest, GlassType

  @pytest.fixture
  def db_session():
      db = SessionLocal()
      initialize_sample_data(db)
      yield db
      db.close()

  @pytest.fixture
  def material_service(db_session):
      return DatabaseMaterialService(db_session)

  @pytest.fixture
  def bom_service(db_session):
      return ProductBOMServiceDB(db_session)

  class TestGlassSelectionDatabaseDriven:
      """Test database-driven glass selection (ARCH-20251017-001)"""

      def test_get_glass_cost_by_material_id(self, bom_service, material_service):
          """Test new material ID-based glass cost retrieval"""
          glass = material_service.get_material_by_code("VID-CLARO-6")
          assert glass is not None, "Glass material VID-CLARO-6 should exist"

          price = bom_service.get_glass_cost_by_material_id(glass.id)
          assert price == Decimal("120.00"), f"Expected $120, got ${price}"

      def test_get_glass_cost_by_invalid_material_id(self, bom_service):
          """Test error handling for invalid material ID"""
          with pytest.raises(ValueError, match="not found"):
              bom_service.get_glass_cost_by_material_id(99999)

      def test_quote_item_with_material_id(self):
          """Test QuoteItemRequest accepts material_id"""
          item = QuoteItemRequest(
              product_bom_id=1,
              selected_glass_material_id=123,
              width_cm=Decimal("100"),
              height_cm=Decimal("150"),
              quantity=1
          )
          assert item.selected_glass_material_id == 123

      def test_quote_item_dual_path_material_id_priority(self):
          """Test material_id takes precedence over enum"""
          item = QuoteItemRequest(
              product_bom_id=1,
              selected_glass_type=GlassType.CLARO_4MM,
              selected_glass_material_id=456,
              width_cm=Decimal("100"),
              height_cm=Decimal("150"),
              quantity=1
          )
          # Both provided, material_id should be preferred
          assert item.selected_glass_material_id == 456
          assert item.selected_glass_type == GlassType.CLARO_4MM

      def test_quote_item_requires_glass_selection(self):
          """Test validation requires glass selection"""
          with pytest.raises(ValueError, match="must be provided"):
              QuoteItemRequest(
                  product_bom_id=1,
                  width_cm=Decimal("100"),
                  height_cm=Decimal("150"),
                  quantity=1
              )

      def test_backward_compatibility_enum_still_works(self, bom_service):
          """Test old enum-based path still works (backward compatibility)"""
          price = bom_service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
          assert price == Decimal("120.00")

      def test_all_glass_materials_have_valid_ids(self, material_service):
          """Test all glass materials in database are accessible"""
          glass_materials = material_service.get_materials_by_category("Vidrio")
          assert len(glass_materials) >= 7, "Should have at least 7 glass types"

          for material in glass_materials:
              assert material.id > 0
              assert material.code.startswith("VID-")
              assert material.cost_per_unit > 0

  # Run tests
  if __name__ == "__main__":
      pytest.main([__file__, "-v"])
  ```

- [ ] **Run Unit Tests**
  ```bash
  pytest tests/test_glass_selection_database.py -v
  # Expected: 7 tests pass
  ```

### Integration Tests

- [ ] **Update Existing Integration Tests**

  **File**: `tests/test_integration_quotes_routes.py` (modify existing)

  Add new test class:
  ```python
  class TestGlassSelectionIntegration:
      """Integration tests for database-driven glass selection"""

      def test_new_quote_page_has_glass_materials(self):
          """Test /quotes/new page provides glass_materials from database"""
          # Test implementation
          pass

      def test_quote_creation_with_material_id(self):
          """Test end-to-end quote creation using material_id"""
          # Test implementation
          pass

      def test_quote_edit_with_material_id(self):
          """Test editing existing quote with new material_id path"""
          # Test implementation
          pass

      def test_new_material_appears_in_dropdown(self):
          """Test dynamically added material appears in quote UI"""
          # Test implementation
          pass
  ```

- [ ] **Run Integration Tests**
  ```bash
  pytest tests/test_integration_quotes_routes.py::TestGlassSelectionIntegration -v
  # Expected: 4 tests pass
  ```

### Test Coverage Report

- [ ] **Generate Coverage Report**
  ```bash
  pytest --cov=services.product_bom_service_db \
         --cov=app.routes.quotes \
         --cov=models.quote_models \
         --cov-report=html

  # Open htmlcov/index.html to view report
  # Target: >90% coverage
  ```

---

## PHASE 5: DEPLOYMENT (1-2 hours)

### Test Environment Deployment

- [ ] **Deploy to Test Environment** (port 8001)
  ```bash
  # SSH to droplet
  ssh root@159.65.174.94

  # Navigate to test environment
  cd /home/ventanas/app-test

  # Pull latest changes
  git fetch origin
  git checkout arch/glass-selection-database-20251017
  git pull origin arch/glass-selection-database-20251017

  # Rebuild container
  docker-compose -f docker-compose.test.yml down
  docker-compose -f docker-compose.test.yml build --no-cache app
  docker-compose -f docker-compose.test.yml up -d

  # Verify container running
  docker ps | grep test

  # Check logs
  docker logs ventanas-test-app --tail 50
  ```

- [ ] **Test Environment Verification**
  ```bash
  # Test database connectivity
  docker exec ventanas-test-app python -c "from database import SessionLocal; db = SessionLocal(); print('✓ DB connected'); db.close()"

  # Verify glass materials exist
  docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "SELECT COUNT(*) FROM app_materials WHERE category = 'Vidrio';"
  # Expected: 7 or more

  # Test external access
  curl -s http://159.65.174.94:8001/login | head -20
  # Expected: HTTP 200, login page HTML
  ```

- [ ] **Test Environment Smoke Test**
  - [ ] Login to test environment: http://159.65.174.94:8001/login
  - [ ] Navigate to /quotes/new
  - [ ] Verify glass dropdown shows database materials with prices
  - [ ] Create test quote with glass selection
  - [ ] Verify quote calculates correctly
  - [ ] Add new glass material via /materials_catalog
  - [ ] Verify new material appears in /quotes/new dropdown immediately

### Production Deployment

⚠️ **HOLD**: Do not deploy to production until test environment monitoring complete (24 hours minimum)

- [ ] **24-Hour Test Monitoring** (manual check)
  ```bash
  # Monitor test environment logs
  docker logs ventanas-test-app -f | grep -i "glass\|error"

  # Check for errors
  docker logs ventanas-test-app --since 24h | grep -i error | wc -l
  # Expected: 0 errors

  # Performance check
  docker exec ventanas-test-app python -c "
  from database import SessionLocal
  from services.product_bom_service_db import ProductBOMServiceDB
  import time

  db = SessionLocal()
  service = ProductBOMServiceDB(db)

  start = time.time()
  price = service.get_glass_cost_by_material_id(2)
  elapsed = (time.time() - start) * 1000

  print(f'Performance: {elapsed:.2f}ms')
  assert elapsed < 10, f'Too slow: {elapsed}ms'
  db.close()
  "
  ```

- [ ] **Production Deployment** (after 24h test monitoring)
  ```bash
  # Create database backup first
  ssh root@159.65.174.94
  docker exec ventanas-beta-db pg_dump -U ventanas_user ventanas_beta_db > /root/db-backup-glass-selection-$(date +%Y%m%d-%H%M%S).sql

  # Navigate to production
  cd /home/ventanas/app

  # Pull changes
  git fetch origin
  git checkout arch/glass-selection-database-20251017
  git pull origin arch/glass-selection-database-20251017

  # Deploy
  bash scripts/deploy-production.sh

  # Or manual deployment:
  docker-compose -f docker-compose.beta.yml down
  docker-compose -f docker-compose.beta.yml build --no-cache app
  docker-compose -f docker-compose.beta.yml up -d

  # Verify
  docker ps | grep beta
  docker logs ventanas-beta-app --tail 50
  curl -s http://159.65.174.94:8000/login | head -20
  ```

- [ ] **Production Smoke Test**
  - [ ] Login: http://159.65.174.94:8000/login
  - [ ] Test /quotes/new - glass dropdown works
  - [ ] Test /materials_catalog - add new glass material
  - [ ] Test /quotes/new - new material appears
  - [ ] Create real quote
  - [ ] Test /quotes/{id}/edit - edit existing quote
  - [ ] Verify all calculations correct

### Post-Deployment Monitoring

- [ ] **Monitor Production Logs** (first 48 hours)
  ```bash
  # Real-time monitoring
  docker logs ventanas-beta-app -f | grep -i "glass\|error\|warning"

  # Check error count
  docker logs ventanas-beta-app --since 1h | grep -i error | wc -l

  # Check which path is being used
  docker logs ventanas-beta-app --since 1h | grep "Glass cost calculation path"
  # Should show mix of material_id and enum (during transition)
  ```

- [ ] **Performance Monitoring**
  ```bash
  # Check glass price lookup performance
  docker exec ventanas-beta-app python -c "
  from database import SessionLocal
  from services.product_bom_service_db import ProductBOMServiceDB
  import time

  db = SessionLocal()
  service = ProductBOMServiceDB(db)

  # Test 10 lookups
  times = []
  for _ in range(10):
      start = time.time()
      price = service.get_glass_cost_by_material_id(2)
      times.append((time.time() - start) * 1000)

  avg = sum(times) / len(times)
  print(f'Average: {avg:.2f}ms')
  print(f'Min: {min(times):.2f}ms')
  print(f'Max: {max(times):.2f}ms')

  db.close()
  "
  ```

---

## PHASE 6: DOCUMENTATION (30 minutes)

### Update Documentation

- [ ] **Update CLAUDE.md** (already done in Step 7)

- [ ] **Create Deployment Summary**

  **File**: `.claude/workspace/ARCH-20251017-001/deployment-summary.md`

  ```markdown
  # Deployment Summary: ARCH-20251017-001

  **Date**: [Deployment Date]
  **Environment**: Test (port 8001) → Production (port 8000)
  **Duration**: [Total Time]

  ## Changes Deployed

  - ✅ Database-driven glass selection dropdown
  - ✅ Material ID-based quote calculations
  - ✅ Dual-path support (enum + material_id)
  - ✅ Edit quote page updated
  - ✅ Deprecation warnings added

  ## Files Modified

  1. `services/product_bom_service_db.py` - Added get_glass_cost_by_material_id()
  2. `models/quote_models.py` - Added selected_glass_material_id field
  3. `app/routes/quotes.py` - Database query for glass materials
  4. `templates/new_quote.html` - Database-driven dropdown
  5. `templates/edit_quote.html` - Database-driven dropdown
  6. `CLAUDE.md` - Architecture documentation

  ## Test Results

  - Unit tests: [X]/[Y] passed
  - Integration tests: [X]/[Y] passed
  - Coverage: [XX]%
  - Performance: [X]ms average (cached: [Y]ms)

  ## Verification

  - ✅ New materials added via UI appear in dropdown
  - ✅ Quote calculations correct
  - ✅ Backward compatibility maintained
  - ✅ Performance acceptable

  ## Monitoring

  - Test environment: [Date] - [Date] (24h)
  - Production: [Date] - ongoing
  - Errors: 0
  - Performance degradation: None

  ## Next Steps

  - Monitor production for 1 week
  - Track dual-path usage (material_id vs enum)
  - Plan enum deprecation timeline
  - Update MTENANT-20251006-012 (now unblocked)
  ```

- [ ] **Update Task Status**
  ```bash
  # Update tasks.csv
  sed -i '' "s/ARCH-20251017-001,\([^,]*\),pending,/ARCH-20251017-001,\1,completed,/" tasks.csv

  # Add completion notes
  # (Manually edit tasks.csv to add deployment notes)
  ```

- [ ] **Create Session Notes**

  **File**: `.claude/workspace/ARCH-20251017-001/notes.md`

  Document:
  - Issues encountered and resolutions
  - Time spent on each phase
  - Lessons learned
  - Recommendations for future tasks

---

## Time Estimates Summary

| Phase | Estimated Time | Tasks |
|-------|----------------|-------|
| 1. Preparation | 30 minutes | Setup, baseline tests, review |
| 2. Implementation | 6-8 hours | 7 atomic steps |
| 3. Integration | 1-2 hours | End-to-end testing |
| 4. Testing | 2-3 hours | Unit + integration tests |
| 5. Deployment | 1-2 hours | Test + production |
| 6. Documentation | 30 minutes | Docs and summaries |
| **TOTAL** | **11-16 hours** | **~2 work days** |

### Realistic Schedule

**Day 1** (6-8 hours):
- Morning: Preparation + Steps 1-3 (3 hours)
- Afternoon: Steps 4-7 (4 hours)
- Evening: Integration testing (1 hour)

**Day 2** (5-8 hours):
- Morning: Testing + test deployment (3 hours)
- Afternoon: 24-hour wait for test monitoring
- Evening: Production deployment + verification (2 hours)
- Documentation (30 minutes)

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

**If issues discovered in production:**

```bash
# SSH to droplet
ssh root@159.65.174.94

# Navigate to production
cd /home/ventanas/app

# Checkout previous commit
git log --oneline | head -10  # Find commit before changes
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose -f docker-compose.beta.yml down
docker-compose -f docker-compose.beta.yml build --no-cache app
docker-compose -f docker-compose.beta.yml up -d

# Verify
curl http://159.65.174.94:8000/login
docker logs ventanas-beta-app --tail 50
```

### Selective Rollback (Revert Specific Commit)

**If only one commit causes issues:**

```bash
# Identify problematic commit
git log --oneline arch/glass-selection-database-20251017

# Revert specific commit
git revert <commit-hash>

# Deploy revert
docker-compose -f docker-compose.beta.yml down
docker-compose -f docker-compose.beta.yml up -d --build
```

### Database Rollback

**Not needed** - this task makes no schema changes. All changes are code-only.

---

## Success Metrics

### Quantitative Metrics

- [ ] **Test Coverage**: >90% (target: 95%)
- [ ] **Performance**: <5ms glass lookup (cached: <1ms)
- [ ] **Error Rate**: 0 errors in 48h post-deployment
- [ ] **Backward Compatibility**: 100% of old quotes work
- [ ] **Migration Adoption**: >50% new quotes use material_id within 1 week

### Qualitative Metrics

- [ ] **User Experience**: Users can add glass types via UI without code deployment
- [ ] **Architectural Consistency**: Glass matches profiles/colors architecture
- [ ] **Multi-Tenant Ready**: Dropdown supports tenant_id filtering
- [ ] **Developer Experience**: Clear deprecation path, good documentation

---

## Lessons Learned (Post-Implementation)

### What Went Well
- [ ] Document successes here after completion

### What Could Be Improved
- [ ] Document improvements here after completion

### Future Recommendations
- [ ] Apply same pattern to WindowType enum?
- [ ] Apply same pattern to AluminumLine enum?
- [ ] Create admin UI for bulk catalog management?
- [ ] Add catalog export/import feature?

---

## Workspace Structure

```
.claude/workspace/ARCH-20251017-001/
├── atomic-plan-ARCH-20251017-001.md     # This file
├── checklist-ARCH-20251017-001.md       # Execution checklist
├── notes.md                              # Session notes
├── success-criteria.md                   # Success criteria checklist
├── deployment-summary.md                 # Deployment report (post-deploy)
└── errors.log                            # Error log (if needed)
```

---

## Quick Reference Commands

### Start Work Session
```bash
git checkout -b arch/glass-selection-database-20251017
cat .claude/workspace/ARCH-20251017-001/atomic-plan-ARCH-20251017-001.md
```

### Track Progress
```bash
cd .claude/workspace/ARCH-20251017-001
grep "\[x\]" checklist-ARCH-20251017-001.md | wc -l  # Completed
grep "\[ \]" checklist-ARCH-20251017-001.md | wc -l  # Remaining
```

### Run Tests
```bash
pytest tests/test_glass_selection_database.py -v
pytest tests/test_integration_quotes_routes.py::TestGlassSelectionIntegration -v
pytest --cov=services.product_bom_service_db --cov-report=html
```

### Deploy to Test
```bash
ssh root@159.65.174.94
cd /home/ventanas/app-test
git pull origin arch/glass-selection-database-20251017
docker-compose -f docker-compose.test.yml down && docker-compose -f docker-compose.test.yml up -d --build
```

### Monitor Production
```bash
docker logs ventanas-beta-app -f | grep -i "glass\|error"
```

---

**Plan Created**: 2025-10-17
**Status**: Ready for execution
**Next Action**: Review plan, then start Phase 1 (Preparation)
