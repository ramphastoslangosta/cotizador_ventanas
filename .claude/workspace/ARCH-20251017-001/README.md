# Task Workspace: ARCH-20251017-001

**Title**: Complete Glass Selection Database Migration - Dynamic Dropdown UI
**Started**: 2025-10-17
**Status**: Ready for execution
**Branch**: arch/glass-selection-database-20251017

---

## Quick Summary

Complete the database-driven migration for glass selection UI by replacing hardcoded GlassType enum dropdown with dynamic database queries. Enables users to add/remove glass types via Materials Catalog UI without code deployment.

**Key Change**: `selected_glass_type: GlassType (enum)` → `selected_glass_material_id: int (database ID)`

---

## Files

- `atomic-plan-ARCH-20251017-001.md` - Detailed 7-step execution plan (500+ lines)
- `checklist-ARCH-20251017-001.md` - Execution checklist (generated below)
- `notes.md` - Session notes and observations
- `success-criteria.md` - Success criteria checklist
- `errors.log` - Error log (if issues occur)

---

## Quick Start

### 1. Start Work Session
```bash
git checkout main
git pull origin main
git checkout -b arch/glass-selection-database-20251017
```

### 2. Review Plan
```bash
cat .claude/workspace/ARCH-20251017-001/atomic-plan-ARCH-20251017-001.md
```

### 3. Run Baseline Tests
```bash
pytest tests/test_glass_pricing_database.py -v
pytest tests/test_integration_quotes_routes.py::TestGlassPricingIntegration -v
```

### 4. Follow Atomic Steps
Execute steps 1-7 from the atomic plan, committing after each step.

---

## Progress Tracking

### Current Status
- [ ] Preparation phase
- [ ] Implementation phase (Steps 1-7)
- [ ] Integration testing
- [ ] Unit testing
- [ ] Test deployment
- [ ] Production deployment

### Track Progress
```bash
cd .claude/workspace/ARCH-20251017-001
grep "\[x\]" checklist-ARCH-20251017-001.md | wc -l  # Completed items
grep "\[ \]" checklist-ARCH-20251017-001.md | wc -l  # Remaining items
```

---

## Time Estimate

**Total**: 11-16 hours (~2 work days)

**Breakdown**:
- Preparation: 30 minutes
- Implementation (7 steps): 6-8 hours
- Integration: 1-2 hours
- Testing: 2-3 hours
- Deployment: 1-2 hours
- Documentation: 30 minutes

---

## Key Commands

### Development
```bash
# Run application
python main.py

# Run tests
pytest tests/test_glass_selection_database.py -v
pytest --cov=services.product_bom_service_db --cov-report=html

# Manual browser test
# Open http://localhost:8000/quotes/new
```

### Deployment
```bash
# Deploy to test environment (port 8001)
ssh root@159.65.174.94
cd /home/ventanas/app-test
git pull origin arch/glass-selection-database-20251017
docker-compose -f docker-compose.test.yml down && docker-compose -f docker-compose.test.yml up -d --build

# Monitor test environment
docker logs ventanas-test-app -f | grep -i "glass\|error"
```

---

## Success Criteria

1. ✅ Glass dropdown populated from database query
2. ✅ New glass materials added via UI appear in dropdown
3. ✅ Quote calculation uses material ID instead of enum
4. ✅ Backward compatibility: old enum-based quotes still work
5. ✅ All 7 glass types work correctly
6. ✅ Multi-tenant ready: dropdown filterable by tenant_id
7. ✅ Unit + integration tests pass (>90% coverage)
8. ✅ Performance unchanged (<5ms, cached <1ms)
9. ✅ Zero breaking changes

---

## Rollback

**Quick rollback** (if issues):
```bash
git checkout main
docker-compose -f docker-compose.beta.yml restart app
```

**No database rollback needed** - code-only changes.

---

## After Completion

### 1. Update Task Status
```bash
sed -i '' "s/ARCH-20251017-001,\([^,]*\),pending,/ARCH-20251017-001,\1,completed,/" tasks.csv
```

### 2. Document Completion
Add completion notes to `tasks.csv` with:
- Deployment date and time
- Test results (coverage %, performance)
- Issues encountered and resolutions
- Next steps (unblocks MTENANT-20251006-012)

### 3. Archive Workspace
```bash
mv .claude/workspace/ARCH-20251017-001 .claude/workspace/archive/ARCH-20251017-001-completed-$(date +%Y%m%d)
```

---

## Related Tasks

**Depends on**: ARCH-20251007-001 ✅ (Completed 2025-10-14)
**Blocks**: MTENANT-20251006-012 (Multi-tenant glass catalogs)

---

## Reference Documents

- **Architectural Review**: `.claude/workspace/ARCH-20251007-001/post-deployment-review.md`
- **Previous Implementation**: ARCH-20251007-001 (glass pricing)
- **Reference Pattern**: Profile colors dropdown (templates/new_quote.html:470-514)

---

**Created**: 2025-10-17
**Plan Ready**: Yes
**Next Action**: Review atomic plan, then start Phase 1 (Preparation)
