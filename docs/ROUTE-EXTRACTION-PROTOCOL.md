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
