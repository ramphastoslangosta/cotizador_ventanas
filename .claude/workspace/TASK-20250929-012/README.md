# Task Workspace: TASK-20250929-012

**Title**: Remove duplicate auth and quote routes from main.py
**Started**: 2025-10-01
**Priority**: Medium
**Estimated Effort**: 0.5 days (4 hours)

## Overview

Clean up main.py by removing ~670 lines of duplicate route definitions that now exist in dedicated routers. This is a safe cleanup operation with zero functional changes.

## Files

- `atomic-plan-TASK-20250929-012.md` - Detailed execution plan with 6 phases
- `checklist-TASK-20250929-012.md` - Execution checklist (33 items)
- `notes.md` - Session notes and observations
- `success-criteria.md` - Acceptance criteria verification

## Quick Commands

### Start Work Session
```bash
# Create and checkout task branch
git checkout -b refactor/cleanup-duplicate-routes-20250929

# Review the atomic plan
cat .claude/workspace/TASK-20250929-012/atomic-plan-TASK-20250929-012.md
```

### Investigation Phase
```bash
# Check for duplicate routes
grep -E "^@app\.(get|post|put|delete)" main.py | wc -l

# Verify router registration
python -c "import main; print(f'Routes: {len(main.app.routes)}')"

# Expected: 104 routes via routers + main.py core routes
```

### Track Progress
```bash
# Count completed items
grep "\[x\]" .claude/workspace/TASK-20250929-012/checklist-TASK-20250929-012.md | wc -l

# Count remaining items
grep "\[ \]" .claude/workspace/TASK-20250929-012/checklist-TASK-20250929-012.md | wc -l

# View progress percentage
TOTAL=$(grep -c "\[ \]" .claude/workspace/TASK-20250929-012/checklist-TASK-20250929-012.md)
DONE=$(grep -c "\[x\]" .claude/workspace/TASK-20250929-012/checklist-TASK-20250929-012.md)
echo "Progress: $DONE/$TOTAL items ($(( DONE * 100 / TOTAL ))%)"
```

### Testing Commands
```bash
# Run all tests
pytest tests/ -v

# Test application startup
timeout 10s python main.py &
sleep 3
pkill -f "python.*main.py"

# Test critical pages
python main.py &
sleep 3
curl -s http://localhost:8000/login | grep -q "login" && echo "✅ Login OK"
curl -s http://localhost:8000/quotes | grep -q "Cotizaciones" && echo "✅ Quotes OK"
pkill -f "python.*main.py"
```

### After Completion
```bash
# Update task status
sed -i '' "s/TASK-20250929-012,\\([^,]*\\),\\([^,]*\\),medium,pending/TASK-20250929-012,\\1,\\2,medium,completed/" tasks.csv

# Verify update
grep "TASK-20250929-012" tasks.csv

# Add completion timestamp
echo "Completed: $(date)" >> .claude/workspace/TASK-20250929-012/notes.md

# Create completion summary
cat .claude/workspace/TASK-20250929-012/COMPLETION_SUMMARY.md
```

## Success Criteria

1. ✅ All duplicate auth routes removed
2. ✅ All duplicate quote routes removed
3. ✅ All tests passing (13/13)
4. ✅ Application starts successfully
5. ✅ 104 routes registered via routers
6. ✅ No broken imports or dependencies

## Key Findings

### Investigation Results
The task description mentions duplicates at:
- Lines 724-901 (auth routes)
- Lines 903-1400 (quote routes)

**Reality Check**: Need to verify if duplicates actually exist or were already cleaned up in:
- TASK-20250929-001 (auth routes - completed Sept 30)
- HOTFIX-20251001-001 (quote routes - completed Oct 1)

### Important Notes
- Comments at line 739 and 933 suggest cleanup already occurred
- Router registration confirmed working (104 routes)
- This may be a documentation task rather than code cleanup

## Execution Strategy

### Scenario A: Duplicates Found
1. Remove duplicate auth routes (lines 724-901)
2. Remove duplicate quote routes (lines 903-1400)
3. Test and verify no regressions
4. Commit atomically and deploy

### Scenario B: No Duplicates (Already Clean)
1. Document investigation findings
2. Mark task as completed
3. Update tasks.csv with retroactive completion
4. Create completion report for team

## Rollback Strategy

### Quick Rollback
```bash
# Restore all changes
git checkout main.py tasks.csv TASK_STATUS.md

# Verify restoration
python -c "import main; print(len(main.app.routes))"
pytest tests/ -q
```

### Emergency Production Rollback
```bash
# On production server
ssh user@159.65.174.94
cd /path/to/app
git log --oneline -5
git checkout <previous-working-commit>
systemctl restart quotation-app
curl http://159.65.174.94:8000/quotes  # Verify
```

## Dependencies

- ✅ **TASK-20250929-002**: Quote routes extraction (completed)
- ✅ **TASK-20250929-001**: Auth routes extraction (completed - implied)
- ✅ **HOTFIX-20251001-001**: Quote presenter fix (completed)

All dependencies satisfied - ready to proceed.

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Preparation | 35 min | 35 min |
| Investigation | 15 min | 50 min |
| Implementation | 30 min | 80 min |
| Testing | 20 min | 100 min |
| Deployment | 20 min | 120 min |
| Documentation | 15 min | 135 min |
| **Total** | **2.25 hrs** | **Buffer: 15 min** |

**Target Completion**: 2.5 hours

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Accidentally remove active routes | 🟢 Low | Verify router registration first |
| Break template rendering | 🟢 Low | Test all HTML pages |
| Import errors | 🟢 Low | Keep imports intact |
| Production issues | 🟢 Low | Test env first, atomic commits |

**Overall Risk**: 🟢 **LOW** - Safe cleanup operation

## Next Task

After TASK-012 completion, proceed to:
- **TASK-20250929-004**: Fix CSV test complexity (31 → <10)
  - Can run in parallel with other Phase 1 tasks
  - Estimated: 1 day

---

**Workspace Status**: ✅ Ready for execution
**Plan Generated**: 2025-10-01
**Last Updated**: 2025-10-01
