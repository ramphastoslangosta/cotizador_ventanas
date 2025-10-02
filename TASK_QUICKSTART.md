# Task Package Quickstart Guide

**Generated**: 2025-09-29 | **Updated**: 2025-10-01 (After Hotfix)
**Project**: FastAPI Window Quotation System Refactoring
**Total Tasks**: 19 tasks (12 original + 7 hotfix) | **Estimated Effort**: 16-20 days

---

## ✅ HOTFIX-20251001-001 COMPLETE (Oct 1, 2025 21:30 UTC)

**Emergency hotfix completed** - Production quotes list page was broken for 4-6 hours. QuoteListPresenter pattern implemented and deployed to production.

**TASK-012 UNBLOCKED** - Ready to proceed with duplicate route cleanup

---

## Quick Overview

This task package provides a complete workflow for executing the refactoring roadmap identified in the code review, **now updated with 7 critical hotfix tasks** from production incident.

### What You Get
- 19 actionable tasks (12 original + 7 hotfix prevention)
- **7 new high-priority tasks** from hotfix RCA
- Branch creation scripts for all tasks
- PR templates for each phase type
- Test scaffolds ready to implement
- Interactive progress dashboard
- Comprehensive execution guide
- **Root cause analysis** (797 lines)

---

## 5-Minute Setup

### 1. Review Task List

```bash
# View all tasks
cat tasks.csv

# Or open interactive dashboard
open docs/task-dashboards/refactoring-progress-20250929.html
```

### 2. Create Branches for Phase 1

```bash
# Create all Phase 1 branches at once
bash scripts/branches/create-phase-1-branches.sh

# Branches created:
# - refactor/auth-routes-20250929
# - refactor/quote-routes-20250929
# - refactor/workorder-material-routes-20250929
# - refactor/csv-tests-complexity-20250929
# - refactor/service-interfaces-20250929
```

### 3. Start First Task

```bash
# Checkout first task branch
git checkout refactor/auth-routes-20250929

# Read task details
grep "TASK-20250929-001" tasks.csv

# View test scaffold
cat tests/test_routes_refactor_scaffold.py

# Start implementing!
```

---

## Task Phases (UPDATED)

### Phase 0: HOTFIX Tasks (4 tasks, 5-6 days) **NEW**
**Focus**: Fix router bugs and prevent future incidents

| Task | Description | Effort | Priority | Status |
|------|-------------|--------|----------|--------|
| HOTFIX-20251001-001 | Fix router data processing | 1 day | 🔴 CRITICAL | ✅ **COMPLETE** (Oct 1, 21:30 UTC) |
| HOTFIX-20251001-002 | Add integration tests | 1-2 days | HIGH | Pending |
| DEVOPS-20251001-001 | Docker build improvements | 1 week | HIGH | Pending |
| PROCESS-20251001-001 | Route extraction protocol | 1 day | HIGH | ✅ Complete |

### Phase 1: Critical Architecture (6 tasks, 9 days)
**Focus**: Decompose 2,273-line main.py monolith

| Task | Description | Effort | Priority | Status |
|------|-------------|--------|----------|--------|
| TASK-20250929-001 | Extract authentication routes | 2 days | CRITICAL | ✅ **DEPLOYED** |
| TASK-20250929-002 | Extract quote routes | 2 days | CRITICAL | ✅ **DEPLOYED** (with QuoteListPresenter) |
| TASK-20250929-003 | Extract work order & material routes | 2 days | CRITICAL | ✅ **DEPLOYED** |
| TASK-20250929-012 | Remove duplicate routes | 0.5 days | MEDIUM | 🔲 **READY** (Unblocked) |
| TASK-20250929-004 | Fix CSV test complexity (31 → <10) | 1 day | HIGH | Pending |
| TASK-20250929-005 | Implement service interfaces (DIP) | 2 days | HIGH | Pending |

### Phase 2: Performance Optimization (3 tasks, 5 days)
**Focus**: Improve response times and eliminate bottlenecks

| Task | Description | Effort | Target |
|------|-------------|--------|--------|
| TASK-20250929-006 | Optimize BOM database queries | 2 days | 200ms → 50ms |
| TASK-20250929-007 | Implement formula caching | 1 day | 60% faster |
| TASK-20250929-008 | Implement CSV streaming | 2 days | Support 100MB files |

### Phase 3: Architecture Improvements (3 tasks, 4 days)
**Focus**: Implement design patterns and improve code quality

| Task | Description | Effort | Pattern |
|------|-------------|--------|---------|
| TASK-20250929-009 | Implement command pattern | 2 days | Command Pattern |
| TASK-20250929-010 | Extract template business logic | 1 day | Service Layer |
| TASK-20250929-011 | Implement factory pattern | 1 day | Factory Pattern |

---

## Quick Commands

### Branch Management

```bash
# Create all Phase 1 branches
bash scripts/branches/create-phase-1-branches.sh

# Create all Phase 2 branches (after Phase 1 complete)
bash scripts/branches/create-phase-2-branches.sh

# Create all Phase 3 branches (after Phase 2 complete)
bash scripts/branches/create-phase-3-branches.sh

# Checkout specific task
git checkout refactor/auth-routes-20250929
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run route refactor tests
pytest tests/test_routes_refactor_scaffold.py -v

# Run performance tests
pytest tests/test_performance_optimization_scaffold.py --benchmark-only

# Run architecture tests
pytest tests/test_architecture_patterns_scaffold.py -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html
```

### Code Quality

```bash
# Check complexity
radon cc main.py -a

# Check maintainability
radon mi main.py -s

# Format code
black .

# Sort imports
isort .

# Security scan
bandit -r . -f json
```

### Progress Tracking

```bash
# View task list
cat tasks.csv | column -t -s','

# View interactive dashboard
open docs/task-dashboards/refactoring-progress-20250929.html

# Check task dependencies
awk -F',' 'NR>1 {print $1 ": depends on " $8}' tasks.csv
```

---

## File Structure

### Generated Files

```
/Users/rafaellang/cotizador/cotizador_ventanas/
├── tasks.csv                                           # Task tracker
├── TASK_QUICKSTART.md                                  # This file
├── scripts/branches/
│   ├── create-phase-1-branches.sh                     # Phase 1 branch script
│   ├── create-phase-2-branches.sh                     # Phase 2 branch script
│   └── create-phase-3-branches.sh                     # Phase 3 branch script
├── .github/pull_request_template/
│   ├── critical-refactoring.md                        # Phase 1 PR template
│   ├── performance-optimization.md                    # Phase 2 PR template
│   └── architecture-improvement.md                    # Phase 3 PR template
├── tests/
│   ├── test_routes_refactor_scaffold.py               # Phase 1 tests
│   ├── test_performance_optimization_scaffold.py      # Phase 2 tests
│   └── test_architecture_patterns_scaffold.py         # Phase 3 tests
├── docs/
│   ├── task-dashboards/
│   │   └── refactoring-progress-20250929.html         # Progress dashboard
│   ├── task-guides/
│   │   └── refactoring-guide-20250929.md              # Complete guide
│   └── code-review-reports/
│       └── code-review-agent_2025-09-26-03.md         # Original review
```

---

## Task Workflow (TL;DR)

### 1. Pick Task
```bash
# View tasks in CSV
grep "pending" tasks.csv

# Check dependencies
grep "TASK-20250929-001" tasks.csv
```

### 2. Create Branch
```bash
git checkout refactor/auth-routes-20250929
# Or use automated script
```

### 3. Implement
```bash
# Read task description in tasks.csv
# Review test scaffold
# Implement changes
# Run tests frequently
pytest tests/ -v
```

### 4. Commit
```bash
git add .
git commit -m "refactor: extract authentication routes

- Moved login, register, logout routes
- Created app/routes/auth.py
- All tests pass

Task: TASK-20250929-001

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 5. Create PR
```bash
git push origin refactor/auth-routes-20250929

# Create PR using template
gh pr create --title "TASK-20250929-001: Extract authentication routes" \
             --body-file .github/pull_request_template/critical-refactoring.md
```

### 6. Merge & Update
```bash
# After approval, merge PR
# Update tasks.csv: change status to "completed"
# Move to next task
```

---

## Dependencies Graph

```
Phase 1:
TASK-001 (auth) ────┐
                    ├──> TASK-002 (quotes) ──> TASK-003 (work orders) ──> TASK-005 (interfaces)
TASK-004 (CSV) ─────┘

Phase 2:
TASK-003 ──> TASK-006 (DB queries) ──┬──> TASK-007 (caching)
TASK-004 ──> TASK-008 (CSV stream) ──┘

Phase 3:
TASK-006 ──> TASK-009 (command) ──> TASK-010 (templates) ──> TASK-011 (factories)
```

**Critical Path**: TASK-001 → TASK-002 → TASK-003 → TASK-005 → TASK-006 → TASK-009 → TASK-010 → TASK-011

**Parallel Opportunities**:
- TASK-001 and TASK-004 can run simultaneously
- TASK-007 and TASK-008 can run simultaneously after their dependencies

---

## Success Metrics

### Code Quality Targets

| Metric | Before | After Target |
|--------|--------|--------------|
| main.py lines | 2,273 | <500 |
| Cyclomatic complexity (max) | 19 | <10 |
| Maintainability index | 0.00 | >70 |
| Code duplication | ~8% | <5% |
| Test coverage | 85% | >85% |

### Performance Targets

| Metric | Before | After Target |
|--------|--------|--------------|
| Quote calculation | 200ms | <50ms |
| Database queries | 45/request | <10/request |
| Formula evaluation | Baseline | 60% faster |
| CSV file support | ~10MB | 100MB |

---

## Quick Links

### Documentation
- **Comprehensive Guide**: [docs/task-guides/refactoring-guide-20250929.md](docs/task-guides/refactoring-guide-20250929.md)
- **Code Review Report**: [docs/code-review-reports/code-review-agent_2025-09-26-03.md](docs/code-review-reports/code-review-agent_2025-09-26-03.md)
- **Project Documentation**: [CLAUDE.md](CLAUDE.md)

### Tools
- **Task Dashboard**: [docs/task-dashboards/refactoring-progress-20250929.html](docs/task-dashboards/refactoring-progress-20250929.html)
- **Task Tracker**: [tasks.csv](tasks.csv)
- **Branch Scripts**: [scripts/branches/](scripts/branches/)
- **PR Templates**: [.github/pull_request_template/](.github/pull_request_template/)
- **Test Scaffolds**: [tests/test_*_scaffold.py](tests/)

---

## Troubleshooting

### Issue: Branch Already Exists
```bash
# Delete and recreate
git branch -D refactor/auth-routes-20250929
git checkout -b refactor/auth-routes-20250929
```

### Issue: Tests Failing
```bash
# Check if on correct branch
git branch --show-current

# Verify dependencies installed
pip install -r requirements.txt

# Run specific test
pytest tests/test_routes_refactor_scaffold.py::TestAuthenticationRoutesExtraction -v
```

### Issue: Can't Find Task Details
```bash
# Search tasks.csv
grep "TASK-20250929-001" tasks.csv

# View in readable format
cat tasks.csv | column -t -s','
```

---

## Phase Completion Checklist

### Phase 1 Complete When:
- [ ] main.py reduced to <500 lines
- [ ] All routes extracted to app/routes/
- [ ] CSV test complexity <10
- [ ] Service interfaces implemented
- [ ] All tests passing
- [ ] No API contract changes

### Phase 2 Complete When:
- [ ] Quote calculation <100ms
- [ ] Database queries reduced by 80%
- [ ] Formula evaluation 60% faster
- [ ] CSV streaming supports 100MB files
- [ ] Performance benchmarks show improvement
- [ ] No functionality regression

### Phase 3 Complete When:
- [ ] Command pattern implemented
- [ ] Template business logic extracted
- [ ] Factory pattern implemented
- [ ] SOLID principles adherence 80%
- [ ] Maintainability index >70
- [ ] All tests passing

---

## Next Steps (UPDATED FOR HOTFIX)

### 🔴 IMMEDIATE - Critical Path (This Week)

1. ✅ **HOTFIX-20251001-001: Fix Router Data Processing** - COMPLETE
   ```bash
   # ✅ Created app/presenters/quote_presenter.py
   # ✅ Extracted 85 lines of data processing logic
   # ✅ Updated router to use presenter
   # ✅ Re-enabled router registration
   # ✅ Deployed to production (Oct 1, 2025 21:30 UTC)
   ```
   **Completed**: 1 day | **Unblocked**: TASK-012

2. **TASK-012: Remove Duplicates** - READY TO START
   ```bash
   git checkout -b refactor/cleanup-duplicate-routes-20250929-v2
   # Remove ~674 lines from main.py
   ```
   **Estimated**: 0.5 days

3. **HOTFIX-20251001-002: Add Integration Tests** - CAN PROCEED IN PARALLEL
   ```bash
   # Add template rendering tests
   pytest tests/test_integration_quotes.py -v
   ```
   **Estimated**: 1-2 days

### This Week Actions

4. **TASK-004**: CSV Test Complexity (can run in parallel)
5. **Review RCA Document**:
   ```bash
   cat HOTFIX-20251001-RCA.md
   ```

### Next 2 Weeks

6. **DEVOPS-20251001-001**: Docker Build Improvements
7. **PROCESS-20251001-001**: Route Extraction Protocol ✅ **COMPLETE** - See [docs/ROUTE-EXTRACTION-PROTOCOL.md](docs/ROUTE-EXTRACTION-PROTOCOL.md)
8. **TASK-005**: Service Interfaces

### This Week

- Complete Phase 1 critical tasks
- Establish baseline performance metrics
- Set up code quality monitoring

### Next 2 Weeks

- Complete all Phase 1 tasks
- Begin Phase 2 performance optimization
- Monitor and document improvements

### This Month

- Complete all 3 phases
- Achieve all success metrics
- Document lessons learned

---

## Support

For detailed guidance on any task:
1. Read task description in `tasks.csv`
2. Review test scaffold in `tests/test_*_scaffold.py`
3. Consult comprehensive guide: `docs/task-guides/refactoring-guide-20250929.md`
4. Review code review report for context: `docs/code-review-reports/code-review-agent_2025-09-26-03.md`

---

**Ready to start?** Run:
```bash
bash scripts/branches/create-phase-1-branches.sh
git checkout refactor/auth-routes-20250929
```

**Good luck with the refactoring!**

Generated by Task Package Generator Agent | 2025-09-29