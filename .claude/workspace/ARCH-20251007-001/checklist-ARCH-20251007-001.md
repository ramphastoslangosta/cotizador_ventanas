# Execution Checklist: ARCH-20251007-001

**Task**: Fix Glass Pricing Hardcoded - Database-Driven Architecture
**Branch**: arch/glass-pricing-database-20251007
**Created**: 2025-10-07

---

## PHASE 1: PREPARATION

- [ ] Review current implementation in `services/product_bom_service_db.py:160-174`
- [ ] Check existing glass materials in database
- [ ] Verify no uncommitted changes blocking work
- [ ] Create feature branch: `arch/glass-pricing-database-20251007`
- [ ] Run baseline tests to establish passing state
- [ ] Document current glass prices for validation
- [ ] Verify database connection
- [ ] Create workspace directory

## PHASE 2: IMPLEMENTATION

### Step 1: Material Code Mapping
- [x] Add GLASS_TYPE_TO_MATERIAL_CODE constant
- [x] Add GLASS_FALLBACK_PRICES constant
- [x] Test mapping validation
- [x] Commit: "arch: add glass type to material code mapping"

### Step 2: Refactor get_glass_cost_per_m2()
- [x] Replace hardcoded _GLASS_CATALOG with database query
- [x] Add fallback logic
- [x] Add audit logging
- [x] Test database query path
- [x] Test fallback path
- [x] Commit: "arch: refactor glass pricing to use database"

### Step 3: Update Sample Data
- [x] Update initialize_sample_data() with 7 glass materials
- [x] Assign correct material codes
- [x] Add descriptions
- [x] Test sample data initialization
- [x] Commit: "arch: update sample data with glass material codes"

### Step 4: Database Migration
- [ ] Create Alembic migration file
- [ ] Add upgrade logic for 7 glass types
- [ ] Add downgrade logic (optional)
- [ ] Validate migration syntax
- [ ] Test migration dry run
- [ ] Commit: "arch: add alembic migration for glass material codes"

### Step 5: Unit Tests
- [ ] Create tests/test_glass_pricing_database.py
- [ ] Add test_glass_type_mapping_complete
- [ ] Add test_fallback_prices_complete
- [ ] Add test_database_glass_pricing
- [ ] Add test_fallback_pricing_when_database_empty
- [ ] Add test_price_update_via_ui_takes_effect
- [ ] Add test_all_glass_types_calculate_correctly
- [ ] Add test_invalid_glass_type_raises_error
- [ ] Add test_performance_database_lookup
- [ ] Add test_backward_compatibility_existing_quotes
- [ ] Add parametrized tests for all 7 glass types
- [ ] Run all new tests
- [ ] Check coverage (target: >90%)
- [ ] Commit: "test: add comprehensive glass pricing database tests"

### Step 6: Integration Tests
- [ ] Add test_quote_calculation_with_database_glass_pricing
- [ ] Add test_glass_price_change_affects_new_quotes
- [ ] Run integration tests
- [ ] Run all quote-related tests
- [ ] Commit: "test: add integration tests for glass pricing in quotes"

### Step 7: Performance Optimization
- [ ] Add _glass_price_cache to __init__
- [ ] Update get_glass_cost_per_m2() with caching
- [ ] Add clear_glass_price_cache() method
- [ ] Test caching performance
- [ ] Test cache clearing
- [ ] Commit: "perf: add optional caching for glass pricing"

## PHASE 3: INTEGRATION

- [ ] Verify imports working
- [ ] Test quote calculation flow
- [ ] Check UI materials catalog
- [ ] Test price updates via UI
- [ ] Manual smoke test (local server)

## PHASE 4: TESTING

- [ ] Run all unit tests
- [ ] Run integration tests
- [ ] Run all tests (regression check)
- [ ] Check test coverage (>90%)
- [ ] Run performance benchmarks
- [ ] Test Scenario 1: New quote with database pricing
- [ ] Test Scenario 2: Price update propagation
- [ ] Test Scenario 3: Fallback mechanism

## PHASE 5: DEPLOYMENT

### Test Environment
- [ ] Deploy to test environment (port 8001)
- [ ] Run Alembic migration
- [ ] Initialize sample data (if needed)
- [ ] Verify health check
- [ ] Test glass pricing API
- [ ] Create test quote via UI
- [ ] Verify price updates work
- [ ] Monitor logs (no errors)
- [ ] 24-hour monitoring period

### Production Deployment
- [ ] Create database backup
- [ ] Deploy to production (port 8000)
- [ ] Run Alembic migration
- [ ] Verify migration success
- [ ] Smoke test production
- [ ] Create test quote in production
- [ ] Update glass price, verify propagation
- [ ] Monitor logs (1 hour)
- [ ] Verify no performance degradation
- [ ] Verify no errors

## PHASE 6: DOCUMENTATION

- [ ] Update get_glass_cost_per_m2() docstring
- [ ] Add inline comments (caching, fallback)
- [ ] Update CLAUDE.md with glass pricing architecture
- [ ] Update API docs
- [ ] Mark ARCH-20251007-001 as completed in tasks.csv
- [ ] Create completion summary
- [ ] Update progress dashboard

## POST-DEPLOYMENT VALIDATION

- [ ] All tests passing (24h after deployment)
- [ ] No errors in production logs
- [ ] 7 glass materials exist in database
- [ ] Performance within target (<5ms)
- [ ] Fallback usage minimal (<5%)
- [ ] UI price updates working
- [ ] Quote calculations correct
- [ ] All acceptance criteria met

---

**Progress Tracking**:
```bash
# Check completed items
grep "\[x\]" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md | wc -l

# Check remaining items
grep "\[ \]" .claude/workspace/ARCH-20251007-001/checklist-ARCH-20251007-001.md | wc -l
```
