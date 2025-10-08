# Task Workspace: ARCH-20251007-001

**Title**: Fix Glass Pricing Hardcoded - Database-Driven Architecture
**Priority**: HIGH
**Estimated Effort**: 1 day (8 hours)
**Started**: 2025-10-07

---

## Task Summary

Refactor glass pricing from hardcoded values in service layer to database-driven approach, ensuring architectural consistency with other materials (profiles, hardware, consumables). This change enables users to update glass prices via UI and unblocks multi-tenant implementation.

**Current Problem**:
- 7 hardcoded glass types in `services/product_bom_service_db.py:160-174`
- 5 database glass materials exist but are ignored
- Users cannot update glass prices via UI (changes don't affect calculations)
- Requires code deployment to change glass prices

**Solution**:
- Query `app_materials` table using material codes (VID-CLARO-4, VID-CLARO-6, etc.)
- Maintain backward compatibility with hardcoded fallback
- Add comprehensive tests and migration
- Enable UI price updates

---

## Files in Workspace

- `atomic-plan-ARCH-20251007-001.md` - Detailed 7-step execution plan
- `checklist-ARCH-20251007-001.md` - Execution checklist (89 items)
- `README.md` - This file
- `notes.md` - Session notes and observations
- `baseline-tests.log` - Baseline test results
- `baseline-prices.txt` - Current hardcoded glass prices

---

## Quick Commands

### Start Work Session
```bash
# Checkout feature branch
git checkout -b arch/glass-pricing-database-20251007

# Review atomic plan
cat .claude/workspace/ARCH-20251007-001/atomic-plan-ARCH-20251007-001.md

# Start with Step 1
# Follow atomic plan step-by-step
```

### Track Progress
```bash
# Completed items
grep "\[x\]" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md | wc -l

# Remaining items
grep "\[ \]" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md | wc -l

# Progress percentage
TOTAL=$(grep -c "\[" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md)
DONE=$(grep -c "\[x\]" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md)
echo "Progress: $DONE/$TOTAL ($(($DONE * 100 / $TOTAL))%)"
```

### Testing Commands
```bash
# Run new unit tests
pytest tests/test_glass_pricing_database.py -v

# Run integration tests
pytest tests/test_integration_quotes.py -v

# Check coverage
pytest tests/test_glass_pricing_database.py \
  --cov=services.product_bom_service_db \
  --cov-report=term-missing

# Run all tests
pytest tests/ -v --tb=short
```

### Deployment Commands
```bash
# Test environment
bash scripts/deploy-test.sh

# Production
bash scripts/deploy-production.sh

# Run migration
alembic upgrade head

# Verify glass materials
psql -d ventanas_db -c "SELECT code, name, cost_per_unit FROM app_materials WHERE category = 'Vidrio' ORDER BY code"
```

---

## Success Criteria

1. ✅ Glass prices retrieved from database
2. ✅ UI price updates take effect immediately
3. ✅ All 7 glass types work correctly
4. ✅ Existing quotes recalculate correctly
5. ✅ Performance <5ms overhead
6. ✅ Test coverage >90%
7. ✅ Backward compatible fallback

---

## Key Files to Modify

### Implementation
- `services/product_bom_service_db.py` - Main refactoring (lines 160-174)
  - Add GLASS_TYPE_TO_MATERIAL_CODE mapping
  - Add GLASS_FALLBACK_PRICES constant
  - Refactor get_glass_cost_per_m2() method
  - Add caching for performance
  - Update initialize_sample_data()

### Migration
- `alembic/versions/004_update_glass_material_codes.py` - Database migration

### Tests
- `tests/test_glass_pricing_database.py` - Unit tests (16 test cases)
- `tests/test_integration_quotes.py` - Integration tests (2 new cases)

### Documentation
- `CLAUDE.md` - Architecture documentation
- `docs/API.md` - API documentation (if exists)

---

## Implementation Steps

### Step 1: Material Code Mapping (30 min)
Create GLASS_TYPE_TO_MATERIAL_CODE and GLASS_FALLBACK_PRICES constants.

### Step 2: Refactor Pricing Method (45 min)
Replace hardcoded _GLASS_CATALOG with database query + fallback.

### Step 3: Update Sample Data (30 min)
Update initialize_sample_data() with 7 glass materials.

### Step 4: Database Migration (45 min)
Create Alembic migration to update existing glass material codes.

### Step 5: Unit Tests (60 min)
Create comprehensive test suite (16 test cases).

### Step 6: Integration Tests (30 min)
Add end-to-end quote calculation tests.

### Step 7: Performance Optimization (30 min)
Add optional caching for glass prices.

**Total Implementation**: 5 hours

---

## Rollback Strategy

### Code Rollback
```bash
# Delete feature branch
git checkout main
git branch -D arch/glass-pricing-database-20251007

# Or revert commits
git revert <commit-hash>
```

### Database Rollback
```bash
# Downgrade migration
alembic downgrade -1

# Or restore backup
psql -d ventanas_db < backups/db-backup-20251007.sql
```

### Application Rollback
```bash
# Redeploy previous version
git checkout <previous-commit>
bash scripts/deploy-production.sh
```

---

## Monitoring

### During Development
```bash
# Watch test results
watch -n 5 'pytest tests/test_glass_pricing_database.py -v | tail -20'

# Monitor database
watch -n 10 'psql -d ventanas_db -c "SELECT COUNT(*) FROM app_materials WHERE category = \"Vidrio\""'
```

### After Deployment
```bash
# Application logs
docker logs cotizador_app --tail 100 -f | grep -i glass

# Database queries
tail -f /var/log/postgresql/postgresql.log | grep "app_materials.*Vidrio"

# Performance metrics
grep "Glass price loaded from database" logs/application.log | wc -l
grep "Using fallback glass price" logs/application.log | wc -l
```

---

## Troubleshooting

### Issue: Tests Failing
```bash
# Check database connection
python -c "from database import SessionLocal; db = SessionLocal(); print('✓ DB connected')"

# Check glass materials exist
psql -d ventanas_db -c "SELECT * FROM app_materials WHERE category = 'Vidrio'"

# Run single test with verbose output
pytest tests/test_glass_pricing_database.py::test_database_glass_pricing -vv
```

### Issue: Performance Slow
```bash
# Check if caching enabled
python -c "
from services.product_bom_service_db import ProductBOMServiceDB
from database import SessionLocal
db = SessionLocal()
service = ProductBOMServiceDB(db, enable_glass_cache=True)
print(f'Cache enabled: {service._glass_price_cache is not None}')
"

# Measure lookup time
python -c "
import time
from services.product_bom_service_db import ProductBOMServiceDB
from database import SessionLocal
from models.quote_models import GlassType

db = SessionLocal()
service = ProductBOMServiceDB(db, enable_glass_cache=True)

start = time.time()
for _ in range(100):
    service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
avg_ms = ((time.time() - start) / 100) * 1000
print(f'Average: {avg_ms:.2f}ms')
"
```

### Issue: Migration Fails
```bash
# Check migration syntax
python -c "import alembic.versions.004_update_glass_material_codes as m"

# Dry run migration
alembic upgrade head --sql > migration-preview.sql
cat migration-preview.sql

# Check current migration version
alembic current
```

---

## After Completion

### Update Task Status
```bash
# Mark as completed in tasks.csv
sed -i '' "s/ARCH-20251007-001,\([^,]*\),pending,/ARCH-20251007-001,\1,completed,/" tasks.csv

# Add completion note
echo "Completed: $(date)" >> .claude/workspace/ARCH-20251007-001/notes.md
```

### Archive Workspace
```bash
# After verified in production
mv .claude/workspace/ARCH-20251007-001 .claude/workspace/archive/ARCH-20251007-001-completed-$(date +%Y%m%d)
```

### Next Task
```bash
# Move to next high-priority task
NEXT_TASK=$(grep ",high,pending," tasks.csv | head -1 | cut -d',' -f1)
echo "Next task: $NEXT_TASK"

# Create plan for next task
/atomic-plan $NEXT_TASK
```

---

**Workspace Created**: 2025-10-07
**Estimated Completion**: 2025-10-07 (same day, 8 hours)
**Status**: Ready for execution ✅
