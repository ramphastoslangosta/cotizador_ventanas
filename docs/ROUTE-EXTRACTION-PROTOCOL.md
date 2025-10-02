# Route Extraction Protocol
## Safe Process for Moving Routes from main.py to Modular Routers

**Version:** 1.0
**Created:** October 2, 2025
**Last Updated:** October 2, 2025
**Status:** 🔴 DRAFT

---

## Table of Contents

1. [Overview](#overview)
2. [When to Use This Protocol](#when-to-use)
3. [Pre-Extraction Checklist](#pre-extraction)
4. [Extraction Steps](#extraction-steps)
5. [Testing Requirements](#testing-requirements)
6. [Deployment Protocol](#deployment-protocol)
7. [Rollback Plan](#rollback-plan)
8. [Case Studies](#case-studies)
9. [Quick Reference](#quick-reference)

---

## 1. Overview

### Purpose

This protocol provides a **step-by-step, battle-tested process** for safely extracting routes from `main.py` into modular routers under `app/routes/`. It was created in response to **HOTFIX-20251001-001**, a production incident caused by incomplete route extraction.

**Key Principle:** **Gradual transition with parallel operation** until verified.

### Background

The FastAPI Window Quotation System originally had all routes in a 2,273-line `main.py`. During refactoring (TASK-001, TASK-002, TASK-003), routes were extracted to:
- `app/routes/auth.py` ✅ Successful
- `app/routes/quotes.py` ⚠️ Caused production incident
- `app/routes/materials.py` ✅ Successful
- `app/routes/work_orders.py` ✅ Successful

**The quotes router incident revealed critical gaps in our extraction process.**

### Core Philosophy

```
KEEP OLD → ADD NEW → TEST BOTH → VERIFY NEW → REMOVE OLD
     ↓          ↓          ↓           ↓            ↓
  Safe      Parallel   Redundancy  Confidence   Clean
```

**NOT:** ~~Remove old → Add new → Hope it works~~ ❌

---

## 2. When to Use This Protocol

### Required Situations

Use this protocol for:

✅ **Any route extraction from main.py to modular routers**
✅ **Refactoring routes that involve data processing**
✅ **Routes with template dependencies**
✅ **Routes with complex business logic**
✅ **High-traffic production endpoints**

### Optional Situations (Still Recommended)

Consider using for:
- New route creation (follow structure, skip extraction steps)
- Internal API endpoints (lower risk)
- Development-only routes

### When NOT to Use

Skip this protocol for:
- ❌ Static file routes
- ❌ Health check endpoints
- ❌ OpenAPI documentation routes

---

## 3. Pre-Extraction Checklist

**STOP!** Before writing any code, complete this checklist. This prevents 90% of extraction bugs.

### 3.1 Route Identification

- [ ] **Route path identified** (e.g., `@app.get("/quotes")`)
- [ ] **HTTP methods documented** (GET, POST, PUT, DELETE)
- [ ] **Authentication requirements** (cookie, bearer, flexible, none)
- [ ] **Response type** (HTMLResponse, JSONResponse, RedirectResponse)

**Example:**
```python
# Route: /quotes
@app.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")
    # ... processing logic ...
```

**Document:** Route path, methods, auth, response type

---

### 3.2 Dependency Analysis

- [ ] **Database services used** (list all: `DatabaseQuoteService`, etc.)
- [ ] **External services** (PDF service, CSV service, etc.)
- [ ] **Helper functions** (calculation functions, formatters)
- [ ] **Imports required** (models, enums, types)

**How to Find:**
```bash
# Find all imports in route function
grep -A 50 "def your_route_function" main.py | grep -E "(Service|from|import)"

# Find database calls
grep -A 50 "def your_route_function" main.py | grep "\.db\."
```

**Document:** Complete dependency tree

---

### 3.3 Data Processing Logic

- [ ] **Raw data extraction** (from database, request params)
- [ ] **Data transformation** (calculations, formatting, aggregation)
- [ ] **Presentation logic** (prepare for templates)
- [ ] **Pagination/filtering** (query modifications)

**Critical:** If your route does ANY data processing before passing to templates, you MUST extract it.

**HOTFIX-20251001-001 Lesson:**
```python
# ❌ WRONG: Router returns raw database objects
quotes = quote_service.get_quotes_by_user(user.id)
return templates.TemplateResponse("quotes_list.html", {"quotes": quotes})

# ✅ RIGHT: Router returns processed data via presenter
quotes = quote_service.get_quotes_by_user(user.id)
processed_quotes = QuoteListPresenter.present(quotes)
return templates.TemplateResponse("quotes_list.html", {"quotes": processed_quotes})
```

**Tool to identify processing logic:**
```bash
# Find calculations/transformations in route
grep -A 100 "def your_route" main.py | grep -E "(for .* in|\.append\(|calculate|format|transform)"
```

**Document:** All processing steps in route

---

### 3.4 Template Requirements

- [ ] **Template file identified** (e.g., `templates/quotes_list.html`)
- [ ] **Template variables documented** (all `{{ variable }}` references)
- [ ] **Required data shape** (dict keys, object attributes)
- [ ] **Optional data** (fields that can be null)

**How to find template requirements:**
```bash
# List all template variables
grep -oE '\{\{[^}]+\}\}' templates/your_template.html | sort -u

# Find loops and conditionals
grep -E '{% (for|if)' templates/your_template.html
```

**Example template analysis:**
```html
<!-- templates/quotes_list.html expects: -->
{% for quote in quotes %}
  {{ quote.id }}                 <!-- REQUIRED: integer -->
  {{ quote.client_name }}        <!-- REQUIRED: string -->
  {{ quote.total_area }}         <!-- REQUIRED: calculated field ⚠️ -->
  {{ quote.price_per_m2 }}       <!-- REQUIRED: calculated field ⚠️ -->
  {{ quote.sample_items }}       <!-- REQUIRED: transformed list ⚠️ -->
{% endfor %}
```

**Document:** Template contract (input/output specification)

---

### 3.5 Test Coverage Analysis

- [ ] **Existing tests found** (unit, integration, e2e)
- [ ] **Test coverage measured** (pytest --cov)
- [ ] **Missing tests identified** (template rendering, data processing)
- [ ] **Test strategy documented** (what new tests needed)

**Commands:**
```bash
# Find existing tests for route
grep -r "test.*quotes" tests/

# Measure coverage
pytest tests/ --cov=app.routes --cov-report=term-missing

# Identify gaps
grep -L "test_.*_template" tests/test_*.py
```

**Document:** Current coverage % and gaps

---

### 3.6 Deployment Risk Assessment

**Answer these questions:**

1. **Traffic volume:** How many requests/day does this route handle?
   - Low (<100) = Lower risk
   - Medium (100-1000) = Medium risk
   - High (>1000) = High risk

2. **Business criticality:** What breaks if this route fails?
   - Minor inconvenience = Lower risk
   - Feature unavailable = Medium risk
   - Revenue impact = High risk

3. **User visibility:** Who uses this route?
   - Developers only = Lower risk
   - Internal team = Medium risk
   - End users = High risk

4. **Data sensitivity:** Does route handle sensitive data?
   - Public data = Lower risk
   - User data = Medium risk
   - Financial/PII = High risk

**Risk Matrix:**

| Risk Level | Protocol Adjustments |
|------------|---------------------|
| **LOW** | Standard protocol, can skip some verification |
| **MEDIUM** | Full protocol, 24-hour monitoring period |
| **HIGH** | Full protocol + staged rollout + feature flag |

---

### 3.7 Rollback Plan

- [ ] **Backup created** (git tag or branch)
- [ ] **Rollback steps documented** (exact commands)
- [ ] **Rollback testing** (verify rollback works)
- [ ] **Communication plan** (who to notify if rollback needed)

**Template:**
```bash
# Rollback Plan for [ROUTE_NAME] Extraction

## Quick Rollback (if router fails)
git revert [COMMIT_HASH]
git push origin main
docker-compose restart app

## Full Rollback (if issues discovered later)
git checkout [BACKUP_TAG]
git push origin main --force  # USE WITH CAUTION
docker-compose down && docker-compose up -d

## Verification after rollback
curl http://localhost:8000/your-route  # Should return 200
grep "ERROR" logs/app.log  # Should be empty
```

---

### Pre-Extraction Checklist Summary

**Before proceeding to extraction, you must have:**

1. ✅ Route fully documented (path, methods, auth, response)
2. ✅ All dependencies identified (services, functions, imports)
3. ✅ Data processing logic mapped (calculations, transformations)
4. ✅ Template requirements specified (variables, data shape)
5. ✅ Test coverage analyzed (existing tests, gaps)
6. ✅ Risk assessed (traffic, criticality, visibility)
7. ✅ Rollback plan created (backup, commands, communication)

**Estimated time:** 30-60 minutes (pays off in prevention)

---

## 4. Extraction Steps

**Critical Rule:** **NEVER remove the original route until the new router is verified in production.**

### 4.1 Create Router File

**Action:** Create new router file in `app/routes/`

**File structure:**
```
app/
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── quotes.py        # Quote management routes
│   ├── work_orders.py   # Work order routes
│   └── [your_new_router].py  ← Create this
```

**Template:**
```python
# app/routes/[your_feature].py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List

# Import database and dependencies
from database import get_db, [YourModels]
from app.dependencies.auth import get_current_user_from_cookie
from config import templates

# Import services
from database import [YourDatabaseServices]

# Import models
from models.[your_models] import [YourPydanticModels]

# Create router
router = APIRouter(
    prefix="",  # Keep empty for backward compatibility
    tags=["your-feature"]
)

# Routes will be added in next steps
```

**Commands:**
```bash
# Create router file
touch app/routes/your_feature.py

# Verify imports work
python -c "from app.routes import your_feature; print('✓ Import successful')"
```

**Commit after this step:**
```
refactor: create [feature] router skeleton

- Created app/routes/your_feature.py
- Added router imports and structure
- No routes implemented yet

Task: PROCESS-20251001-001
```

---

### 4.2 Extract Route Handler Function

**Action:** Copy route function to new router file

**Steps:**

1. **Copy the entire route function** from `main.py`
2. **Paste into router file**
3. **Replace `@app.get/post/put/delete` with `@router.get/post/put/delete`**
4. **Keep original in main.py commented out**

**Example:**

```python
# In app/routes/quotes.py

@router.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Quote list page with pagination"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # ... rest of function (copied verbatim from main.py) ...
```

**In main.py:**
```python
# TASK-XXX: Route moved to app/routes/quotes.py (keep for rollback)
# @app.get("/quotes", response_class=HTMLResponse)
# async def quotes_list_page(request: Request, ...):
#     ... (keep original code commented) ...
```

**Test immediately:**
```bash
# Verify syntax
python -c "from app.routes.quotes import router; print(f'✓ Router has {len(router.routes)} routes')"
```

**Commit after this step:**
```
refactor: extract [route_name] to router

- Copied route handler to app/routes/your_feature.py
- Converted @app decorator to @router decorator
- Original route commented in main.py for rollback

Task: PROCESS-20251001-001
```

---

### 4.3 Extract Data Processing Logic

**⚠️ CRITICAL STEP - This is where HOTFIX-20251001-001 went wrong**

**Action:** Identify and extract ALL data processing before template rendering

**How to identify data processing:**

```python
# Look for these patterns in your route:

# 1. List comprehensions
processed_items = [transform(item) for item in raw_items]

# 2. Dictionary building
data = {"key": calculation(value), "total": sum(items)}

# 3. Calculations
total_area = sum(item.width * item.height for item in items)

# 4. Formatting
formatted_date = date.strftime("%Y-%m-%d")

# 5. Filtering/sorting
filtered = [x for x in items if x.status == "active"]
```

**Decision tree:**

```
Is there ANY code between database query and template rendering?
    YES → Extract to Presenter class
    NO → Route can return raw data directly
```

**Presenter Pattern (Recommended):**

```python
# app/presenters/quote_presenter.py

class QuoteListPresenter:
    """Processes raw Quote objects for template rendering"""

    @staticmethod
    def present(quotes: List[Quote]) -> List[dict]:
        """
        Convert raw Quote objects to template-ready dictionaries

        Args:
            quotes: Raw Quote objects from database

        Returns:
            List of dicts with calculated fields for template
        """
        processed_quotes = []

        for quote in quotes:
            # Extract quote_data
            quote_data = quote.quote_data if quote.quote_data else {}
            items = quote_data.get('items', [])

            # Calculate derived fields
            total_area = sum(
                float(item.get('area_m2', 0)) * item.get('quantity', 1)
                for item in items
            )

            price_per_m2 = (
                float(quote.total_final) / total_area
                if total_area > 0 else 0
            )

            # Get sample items for preview
            sample_items = [
                f"{item.get('window_type', 'N/A')} "
                f"{item.get('width_cm')}x{item.get('height_cm')}cm"
                for item in items[:3]
            ]

            # Build template-ready dict
            processed_quotes.append({
                'id': quote.id,
                'client_name': quote.client_name,
                'created_at': quote.created_at,
                'total_final': quote.total_final,
                'items_count': len(items),
                'total_area': round(total_area, 2),
                'price_per_m2': round(price_per_m2, 2),
                'sample_items': sample_items
            })

        return processed_quotes
```

**Update router to use presenter:**

```python
# app/routes/quotes.py

from app.presenters.quote_presenter import QuoteListPresenter

@router.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Get raw data from database
    quote_service = DatabaseQuoteService(db)
    quotes = quote_service.get_quotes_by_user(user.id, limit=50)

    # ✅ PROCESS DATA via presenter
    processed_quotes = QuoteListPresenter.present(quotes)

    # Pass processed data to template
    return templates.TemplateResponse("quotes_list.html", {
        "request": request,
        "title": "Mis Cotizaciones",
        "user": user,
        "quotes": processed_quotes  # ← Processed, not raw
    })
```

**Test checkpoint:**
```bash
# Test presenter in isolation
python -c "
from app.presenters.quote_presenter import QuoteListPresenter
print('✓ QuoteListPresenter imported')

# Test with mock data
mock_quote = type('Quote', (), {
    'id': 1,
    'client_name': 'Test',
    'created_at': '2025-01-01',
    'total_final': 1000,
    'quote_data': {'items': [{'area_m2': 2.5, 'quantity': 2}]}
})

result = QuoteListPresenter.present([mock_quote])
assert 'total_area' in result[0], 'Missing calculated field'
print('✓ Presenter processes data correctly')
"
```

**Commit after this step:**
```
refactor: extract data processing to presenter

- Created app/presenters/quote_presenter.py
- Moved 85 lines of processing logic from route
- Router now returns processed data to template
- Fixes pattern that caused HOTFIX-20251001-001

Task: PROCESS-20251001-001
```

---

### 4.4 Update Database Service (If Needed)

**Action:** Check if database service needs pagination, filtering, or sorting

**HOTFIX-20251001-001 Lesson:** Database service lacked `offset` parameter

**Before:**
```python
# database.py (WRONG - missing offset)
def get_quotes_by_user(self, user_id: uuid.UUID, limit: int = 50):
    return (self.db.query(Quote)
            .filter(Quote.user_id == user_id)
            .order_by(Quote.created_at.desc())
            .limit(limit)  # ← Missing .offset()
            .all())
```

**After:**
```python
# database.py (CORRECT - with offset)
def get_quotes_by_user(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0):
    """
    Get quotes by user with pagination support

    Args:
        user_id: User UUID
        limit: Maximum results to return
        offset: Number of results to skip (for pagination)
    """
    return (self.db.query(Quote)
            .filter(Quote.user_id == user_id)
            .order_by(Quote.created_at.desc())
            .offset(offset)  # ← Added for pagination
            .limit(limit)
            .all())
```

**Test database service:**
```bash
python -c "
from database import SessionLocal, DatabaseQuoteService
import uuid

db = SessionLocal()
service = DatabaseQuoteService(db)

# Test with offset
user_id = uuid.uuid4()
page_1 = service.get_quotes_by_user(user_id, limit=10, offset=0)
page_2 = service.get_quotes_by_user(user_id, limit=10, offset=10)

print(f'✓ Pagination works: Page 1={len(page_1)}, Page 2={len(page_2)}')
db.close()
"
```

**Commit after this step:**
```
fix(database): add offset parameter for pagination

- Added offset parameter to get_quotes_by_user()
- Enables proper pagination in quote routes
- Prevents pagination bug from HOTFIX-20251001-001

Task: PROCESS-20251001-001
```

---

### 4.5 Register Router in main.py

**Action:** Add router to main.py using `app.include_router()`

**Steps:**

1. Import router at top of main.py
2. Call `app.include_router()` after middleware setup
3. **Keep original route commented** (DO NOT DELETE YET)

**Code:**

```python
# main.py (add at top with other imports)
from app.routes import quotes as quote_routes

# main.py (add after middleware, before route definitions)
# === TASK-XXX: Add Quotes Router ===
from app.routes import quotes as quote_routes
app.include_router(quote_routes.router)
# NOTE: Original route kept below for rollback (remove after verification)
```

**Test router registration:**
```bash
# Check app routes
python -c "
import main
routes = [r for r in main.app.routes if hasattr(r, 'path')]
quote_routes = [r for r in routes if '/quotes' in r.path]
print(f'✓ Found {len(quote_routes)} quote routes')
for route in quote_routes:
    print(f'  - {list(route.methods)} {route.path}')
"
```

**Expected output:**
```
✓ Found 2 quote routes
  - ['GET'] /quotes  ← From router
  - ['GET'] /quotes  ← From main.py (commented but still registered if not properly commented)
```

**⚠️ If you see duplicate routes, verify original is properly commented in main.py**

**Commit after this step:**
```
refactor: register quotes router in main.py

- Imported app.routes.quotes
- Registered router with app.include_router()
- Original route kept commented for rollback
- Verified router registration with route count

Task: PROCESS-20251001-001
```

---

### 4.6 Verify Both Routes Work (Parallel Operation)

**Action:** Test that BOTH the router route and original route work identically

**Why:** This catches integration issues before deployment

**Test checklist:**

- [ ] **Start app:** `python main.py` or `docker-compose up`
- [ ] **Test router route:** Should work via `app.include_router()`
- [ ] **Test original route:** Should work if uncommented temporarily
- [ ] **Compare responses:** Identical HTML/JSON output
- [ ] **Test error cases:** 401, 404, 500 scenarios

**Test script:**
```bash
# test_both_routes.sh

echo "🔄 Testing parallel operation..."

# Start app in background
python main.py &
APP_PID=$!
sleep 5  # Wait for startup

# Test router route
echo "Testing router route..."
ROUTER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/quotes)
echo "  Router: $ROUTER_RESPONSE"

# Temporarily uncomment original route (manual step)
echo "⚠️  Manually uncomment original route in main.py, then press Enter"
read

# Restart app
kill $APP_PID
python main.py &
APP_PID=$!
sleep 5

# Test original route
ORIGINAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/quotes)
echo "  Original: $ORIGINAL_RESPONSE"

# Stop app
kill $APP_PID

# Compare
if [ "$ROUTER_RESPONSE" = "$ORIGINAL_RESPONSE" ]; then
    echo "✅ Both routes return same status code"
else
    echo "❌ Routes return different status codes!"
    echo "   Router: $ROUTER_RESPONSE"
    echo "   Original: $ORIGINAL_RESPONSE"
    exit 1
fi
```

**Manual verification:**
1. Access http://localhost:8000/quotes in browser
2. Verify page renders correctly
3. Check browser console for errors
4. Test pagination, filters, sorting
5. Verify all links work

**Commit after this step:**
```
test: verify router and original routes work identically

- Tested router route returns correct status codes
- Verified HTML rendering matches original
- Confirmed no JavaScript errors in console
- Both routes operate in parallel successfully

Task: PROCESS-20251001-001
```

---

### 4.7 Keep Original Route for Rollback

**Action:** Leave original route commented in main.py

**Format:**

```python
# ============================================================================
# TASK-XXX: ROUTE EXTRACTION - DO NOT REMOVE UNTIL PRODUCTION VERIFIED
# ============================================================================
# This route was extracted to app/routes/quotes.py
# Kept here for emergency rollback if router fails in production
#
# To rollback:
# 1. Uncomment this route
# 2. Comment out app.include_router(quote_routes.router)
# 3. Restart app
#
# REMOVAL TIMELINE:
# - Test environment: After 24 hours of successful operation
# - Production: After 1 week of successful operation with no errors
#
# @app.get("/quotes", response_class=HTMLResponse)
# async def quotes_list_page(request: Request, db: Session = Depends(get_db)):
#     user = await get_current_user_from_cookie(request, db)
#     if not user:
#         return RedirectResponse(url="/login")
#
#     quote_service = DatabaseQuoteService(db)
#     quotes = quote_service.get_quotes_by_user(user.id, limit=50)
#
#     # [Original processing logic kept here...]
#     processed_quotes = []
#     for quote in quotes:
#         # ... all processing ...
#         processed_quotes.append({...})
#
#     return templates.TemplateResponse("quotes_list.html", {
#         "request": request,
#         "quotes": processed_quotes,
#         ...
#     })
#
# ============================================================================
```

**Benefits:**
- Easy emergency rollback (uncomment + restart)
- Code reference for debugging
- Prevents "what did the old code do?" questions

**Timeline for removal:**
- **Test environment:** 24-48 hours after successful deployment
- **Production:** 1 week after successful deployment with zero errors

**Commit after this step:**
```
docs: document rollback process for extracted route

- Added detailed rollback instructions
- Kept original route commented with timeline
- Specified removal criteria (1 week zero errors)

Task: PROCESS-20251001-001
```

---

### Extraction Steps Summary

**Completed when:**
1. ✅ Router file created (`app/routes/your_feature.py`)
2. ✅ Route handler extracted to router
3. ✅ Data processing extracted to presenter (if needed)
4. ✅ Database service updated (pagination, filtering)
5. ✅ Router registered in main.py
6. ✅ Both routes verified working
7. ✅ Original route kept for rollback

**Total commits:** 7 atomic commits

**Next:** Proceed to Testing Requirements (Section 5)

---

## 5. Testing Requirements

**Critical:** Integration tests are MANDATORY. Unit tests alone won't catch template compatibility issues.

### 5.1 Unit Tests

**Purpose:** Test individual components in isolation

**Required tests:**

- [ ] **Presenter classes** - Test data transformation logic
- [ ] **Helper functions** - Test calculation functions
- [ ] **Database service methods** - Test pagination, filtering, sorting
- [ ] **Route parameter validation** - Test query params, path params

**Example:**
```python
# tests/unit/test_quote_presenter.py

def test_quote_list_presenter_processes_single_quote():
    """Test presenter converts Quote to template dict"""
    from app.presenters.quote_presenter import QuoteListPresenter

    # Create mock quote
    quote = Mock(
        id=1,
        client_name="Test Client",
        created_at=datetime.now(),
        total_final=1000.0,
        quote_data={'items': [{'area_m2': 2.5, 'quantity': 2}]}
    )

    # Process with presenter
    result = QuoteListPresenter.present([quote])

    # Verify calculated fields present
    assert len(result) == 1
    assert result[0]['id'] == 1
    assert result[0]['client_name'] == "Test Client"
    assert 'total_area' in result[0]
    assert 'price_per_m2' in result[0]
    assert result[0]['total_area'] == 5.0  # 2.5 * 2


def test_database_service_pagination():
    """Test offset parameter works correctly"""
    from database import DatabaseQuoteService

    service = DatabaseQuoteService(db_session)

    # Get first page
    page_1 = service.get_quotes_by_user(user_id, limit=10, offset=0)

    # Get second page
    page_2 = service.get_quotes_by_user(user_id, limit=10, offset=10)

    # Verify no overlap
    page_1_ids = {q.id for q in page_1}
    page_2_ids = {q.id for q in page_2}
    assert page_1_ids.isdisjoint(page_2_ids)
```

**Run unit tests:**
```bash
pytest tests/unit/ -v
```

---

### 5.2 Integration Tests

**Purpose:** Test full request → response flow including database and templates

**Required tests:**

- [ ] **Route renders successfully** - 200 OK with valid HTML
- [ ] **Authentication works** - Redirects when not logged in
- [ ] **Template receives correct data** - All required fields present
- [ ] **Pagination works** - Multiple pages accessible
- [ ] **Error handling** - 404, 500 errors handled gracefully

**Example:**
```python
# tests/integration/test_quotes_routes.py

def test_quotes_list_page_renders_successfully(authenticated_client, sample_quotes):
    """Test quotes list page renders without errors"""
    response = authenticated_client.get("/quotes")

    assert response.status_code == 200
    assert b"Cotizaciones" in response.content
    assert b"Cliente" in response.content


def test_quotes_list_pagination(authenticated_client, create_quotes):
    """Test pagination works correctly"""
    # Create 25 quotes
    quotes = create_quotes(count=25)

    # Test page 1
    response = authenticated_client.get("/quotes?page=1&page_size=10")
    assert response.status_code == 200
    assert b"1 de 3" in response.content  # Page 1 of 3

    # Test page 2
    response = authenticated_client.get("/quotes?page=2&page_size=10")
    assert response.status_code == 200
    assert b"2 de 3" in response.content  # Page 2 of 3


def test_quotes_list_template_data_compatibility(authenticated_client, sample_quote):
    """Verify all template fields are present in quote data"""
    response = authenticated_client.get("/quotes")

    # Parse HTML to verify data structure
    html = response.content.decode()

    # Verify calculated fields present
    assert "total_area" in html or "m²" in html
    assert "price_per_m2" in html or "$" in html
    assert "items_count" in html or "ventanas" in html
```

**Run integration tests:**
```bash
pytest tests/integration/ -v --cov=app.routes
```

---

### 5.3 Template Compatibility Tests

**Purpose:** Verify template receives data in expected format

**Required tests:**

- [ ] **All template variables present** - No missing keys
- [ ] **Data types correct** - Strings are strings, numbers are numbers
- [ ] **Calculated fields available** - Derived values computed
- [ ] **Optional fields handled** - Null values don't break rendering

**Example:**
```python
# tests/integration/test_template_compatibility.py

def test_quotes_template_receives_required_fields(authenticated_client, db_session):
    """Test template gets all required data fields"""
    # Create quote with known data
    quote = create_test_quote(
        client_name="Test Client",
        total_final=1000.0,
        items=[
            {'width_cm': 100, 'height_cm': 150, 'area_m2': 1.5, 'quantity': 2}
        ]
    )

    response = authenticated_client.get("/quotes")
    html = response.content.decode()

    # Verify all required fields rendered
    assert "Test Client" in html
    assert "1000" in html or "1,000" in html
    assert "3.0" in html or "3" in html  # total_area = 1.5 * 2
    assert "333" in html  # price_per_m2 = 1000 / 3


def test_quotes_template_handles_empty_list(authenticated_client):
    """Test template renders correctly with no quotes"""
    response = authenticated_client.get("/quotes")

    assert response.status_code == 200
    assert b"No hay cotizaciones" in response.content or b"0 cotizaciones" in response.content
```

**Run template tests:**
```bash
pytest tests/integration/test_template_compatibility.py -v
```

---

### 5.4 Error Handling Tests

**Purpose:** Verify routes handle errors gracefully

**Required tests:**

- [ ] **404 for invalid IDs** - Non-existent resources
- [ ] **401 for unauthenticated** - Redirect to login
- [ ] **403 for unauthorized** - User accessing other's data
- [ ] **500 handled gracefully** - Database errors don't expose internals

**Example:**
```python
# tests/integration/test_error_handling.py

def test_quotes_list_requires_authentication(client):
    """Test unauthenticated users redirected to login"""
    response = client.get("/quotes", follow_redirects=False)

    assert response.status_code == 307  # Redirect
    assert "/login" in response.headers["Location"]


def test_quote_detail_not_found(authenticated_client):
    """Test 404 for non-existent quote"""
    response = authenticated_client.get("/quotes/99999")

    assert response.status_code == 404


def test_database_error_returns_500(authenticated_client, monkeypatch):
    """Test database errors handled gracefully"""
    def mock_get_quotes(*args, **kwargs):
        raise Exception("Database connection failed")

    monkeypatch.setattr(
        "database.DatabaseQuoteService.get_quotes_by_user",
        mock_get_quotes
    )

    response = authenticated_client.get("/quotes")

    assert response.status_code == 500
    assert b"Database connection failed" not in response.content  # No exposure
```

---

### 5.5 Performance Tests

**Purpose:** Verify routes perform acceptably under load

**Required tests:**

- [ ] **Response time** - Under 500ms for list pages
- [ ] **Database queries** - N+1 query detection
- [ ] **Memory usage** - No memory leaks with pagination
- [ ] **Large datasets** - 1000+ records render correctly

**Example:**
```python
# tests/performance/test_quotes_performance.py

def test_quotes_list_response_time(authenticated_client, create_quotes):
    """Test quotes list responds in under 500ms"""
    # Create 100 quotes
    create_quotes(count=100)

    import time
    start = time.time()
    response = authenticated_client.get("/quotes")
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5  # 500ms


def test_quotes_list_no_n_plus_one_queries(authenticated_client, create_quotes, query_counter):
    """Test no N+1 query problem"""
    create_quotes(count=50)

    with query_counter() as counter:
        response = authenticated_client.get("/quotes")

    # Should be constant queries regardless of quote count
    assert counter.count <= 5  # Fixed number of queries
```

---

### 5.6 Test Coverage Requirements

**Minimum coverage:**
- **Routes:** 80% line coverage
- **Presenters:** 90% line coverage
- **Database services:** 85% line coverage

**Commands:**
```bash
# Run all tests with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# View coverage report
open htmlcov/index.html

# Check coverage threshold
pytest tests/ --cov=app --cov-fail-under=80
```

**Example coverage report:**
```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
app/routes/quotes.py                   45      3    93%   12, 45-46
app/presenters/quote_presenter.py      38      2    95%   67-68
database.py                           120     15    88%   Various
-----------------------------------------------------------------
TOTAL                                 203     20    90%
```

---

### Testing Checklist Summary

**Before merging, verify:**

1. ✅ Unit tests pass (isolated components)
2. ✅ Integration tests pass (full request flow)
3. ✅ Template compatibility verified (all fields present)
4. ✅ Error handling tested (404, 401, 500)
5. ✅ Coverage meets minimum thresholds (80%+)
6. ✅ No N+1 query problems detected
7. ✅ Performance acceptable (<500ms response)

**Estimated testing time:** 2-4 hours for comprehensive test suite

---

## 6. Deployment Protocol

**Critical:** Deploy to test environment first. Never deploy directly to production.

### 6.1 Pre-Deployment Checklist

**Before deploying, verify:**

- [ ] All tests pass (unit + integration + template)
- [ ] Coverage meets thresholds (80%+)
- [ ] Code review completed and approved
- [ ] Database migrations ready (if applicable)
- [ ] Rollback plan documented and tested
- [ ] Monitoring alerts configured

**Commands:**
```bash
# Run full test suite
pytest tests/ -v --cov=app --cov-fail-under=80

# Verify no uncommitted changes
git status

# Verify branch is up to date
git fetch origin
git log --oneline origin/main..HEAD
```

---

### 6.2 Test Environment Deployment

**Purpose:** Verify router works in production-like environment

**Steps:**

1. **Deploy to test environment**
```bash
# SSH into test server
ssh user@test-server

# Navigate to application directory
cd /app

# Pull latest code
git fetch origin
git checkout feature/route-extraction-branch
git pull origin feature/route-extraction-branch

# Rebuild with no cache
docker-compose -f docker-compose.test.yml build --no-cache app

# Restart application
docker-compose -f docker-compose.test.yml up -d app

# Wait for startup
sleep 10
```

2. **Verify deployment**
```bash
# Check container is running
docker ps | grep app

# Check application logs
docker logs test-app --tail 50

# Verify no errors in startup
docker logs test-app 2>&1 | grep -i error
```

3. **Smoke test critical endpoints**
```bash
# Test quotes list (unauthenticated - should redirect)
curl -I http://test-server:8000/quotes

# Test quotes list (authenticated)
curl -b "session_cookie=..." http://test-server:8000/quotes

# Verify 200 OK response
```

4. **Monitor for 24 hours**
- Check error logs every 4 hours
- Verify user activity is normal
- Test pagination, filtering, sorting
- Monitor response times

**Success criteria:**
- ✅ Application starts without errors
- ✅ Route responds with 200 OK
- ✅ No 500 errors in logs for 24 hours
- ✅ User-facing functionality works correctly

---

### 6.3 Production Deployment

**Purpose:** Deploy verified router to production

**Prerequisites:**
- [ ] Test environment stable for 24+ hours
- [ ] No critical issues found in testing
- [ ] Rollback plan ready
- [ ] Team notified of deployment window

**Steps:**

1. **Create deployment tag**
```bash
# Tag release for rollback
git tag -a v1.2.3 -m "Deploy: Route extraction for quotes"
git push origin v1.2.3
```

2. **Deploy to production**
```bash
# SSH into production server
ssh user@production-server

# Navigate to application directory
cd /app

# Pull latest code
git fetch origin
git checkout feature/route-extraction-branch
git pull origin feature/route-extraction-branch

# Backup current deployment
docker commit production-app production-app-backup-$(date +%Y%m%d-%H%M%S)

# Rebuild with no cache
docker-compose -f docker-compose.prod.yml build --no-cache app

# Restart application
docker-compose -f docker-compose.prod.yml up -d app

# Wait for startup
sleep 15
```

3. **Immediate verification (within 5 minutes)**
```bash
# Check container is running
docker ps | grep app

# Check application logs
docker logs production-app --tail 100

# Test critical endpoints
curl -I https://production-domain.com/quotes

# Verify 200 OK or 307 redirect (auth required)
```

4. **Monitor closely (first 1 hour)**
```bash
# Watch logs in real-time
docker logs production-app -f

# Monitor error rate
docker logs production-app | grep -i error | wc -l

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://production-domain.com/quotes
```

**Success criteria:**
- ✅ Application starts without errors
- ✅ Route responds correctly (200 or 307)
- ✅ No 500 errors in first hour
- ✅ Response times < 500ms
- ✅ No user complaints

---

### 6.4 Post-Deployment Monitoring

**Timeline:** Monitor for 1 week before removing duplicate routes

**Day 1 (Deployment Day):**
- [ ] Check logs every hour for first 4 hours
- [ ] Monitor error rate and response times
- [ ] Test all route functionality manually
- [ ] Verify pagination, filtering, sorting work
- [ ] Check database query performance

**Day 2-3:**
- [ ] Check logs twice daily (morning, evening)
- [ ] Monitor error rate trends
- [ ] Verify no user complaints
- [ ] Test edge cases (empty lists, large datasets)

**Day 4-7:**
- [ ] Check logs daily
- [ ] Monitor weekly error rate
- [ ] Collect user feedback
- [ ] Document any issues found

**Monitoring commands:**
```bash
# Check error count in last 24 hours
docker logs production-app --since 24h | grep -i error | wc -l

# Check response time stats
docker logs production-app --since 24h | grep "GET /quotes" | awk '{print $NF}' | sort -n | tail -10

# Check database query count
docker logs production-app --since 1h | grep "SQL:" | wc -l
```

---

### 6.5 Duplicate Route Removal

**When:** After 1 week of successful production operation with zero errors

**Steps:**

1. **Final verification**
```bash
# Verify zero errors in last week
docker logs production-app --since 168h | grep -i error | grep quotes | wc -l

# Should return 0
```

2. **Remove duplicate route from main.py**
```python
# Before (main.py):
# ============================================================================
# TASK-XXX: ROUTE EXTRACTION - DO NOT REMOVE UNTIL PRODUCTION VERIFIED
# ============================================================================
# This route was extracted to app/routes/quotes.py
# ... (all commented code) ...
# ============================================================================

# After (main.py):
# [Completely removed - router now handles all /quotes requests]
```

3. **Deploy duplicate removal**
```bash
# Create new branch
git checkout -b cleanup/remove-duplicate-quotes-route

# Commit removal
git add main.py
git commit -m "cleanup: remove duplicate quotes route

- Router verified stable for 1 week
- Zero errors in production logs
- All functionality working correctly

Task: PROCESS-20251001-001 (Cleanup)"

# Deploy using same process as 6.3
```

4. **Final verification**
```bash
# Verify route still works
curl -I https://production-domain.com/quotes

# Check logs for issues
docker logs production-app --tail 50 | grep quotes
```

---

### 6.6 Rollback Procedures

**Scenario 1: Router fails immediately (within 1 hour)**

```bash
# Quick rollback - restore backup container
docker stop production-app
docker rm production-app
docker run --name production-app production-app-backup-TIMESTAMP
docker start production-app

# Verify rollback
curl -I https://production-domain.com/quotes

# Should return 200 or 307
```

**Scenario 2: Issues discovered later (1-7 days)**

```bash
# Git rollback to previous version
git revert [COMMIT_HASH]

# Or restore from tag
git checkout v1.2.2  # Previous stable version

# Rebuild and deploy
docker-compose -f docker-compose.prod.yml build --no-cache app
docker-compose -f docker-compose.prod.yml up -d app

# Verify rollback
curl -I https://production-domain.com/quotes
```

**Scenario 3: Emergency - disable router registration**

```python
# main.py - Quick fix
# Comment out router registration
# from app.routes import quotes as quote_routes
# app.include_router(quote_routes.router)

# Uncomment original route
@app.get("/quotes", response_class=HTMLResponse)
async def quotes_list_page(request: Request, db: Session = Depends(get_db)):
    # ... (original implementation) ...
```

```bash
# Deploy emergency fix
docker-compose -f docker-compose.prod.yml build --no-cache app
docker-compose -f docker-compose.prod.yml restart app
```

---

### Deployment Checklist Summary

**Test Environment:**
1. ✅ All tests pass
2. ✅ Deploy to test environment
3. ✅ Smoke test critical endpoints
4. ✅ Monitor for 24 hours
5. ✅ No errors or issues found

**Production Environment:**
1. ✅ Test environment stable for 24+ hours
2. ✅ Create deployment tag
3. ✅ Backup current deployment
4. ✅ Deploy to production
5. ✅ Immediate verification (5 minutes)
6. ✅ Close monitoring (1 hour)
7. ✅ Extended monitoring (1 week)
8. ✅ Remove duplicate routes

**Rollback Ready:**
1. ✅ Backup container created
2. ✅ Git tag created for rollback
3. ✅ Rollback commands documented
4. ✅ Emergency procedures tested

**Timeline:**
- Test deployment: Day 0
- Test monitoring: 24 hours
- Production deployment: Day 1
- Production monitoring: 7 days
- Duplicate removal: Day 8+

---
