# Task Package Quickstart Guide

**Generated**: 2025-09-29
**Project**: FastAPI Window Quotation System Refactoring
**Total Tasks**: 11 tasks | **Estimated Effort**: 12-15 days

---

## Quick Overview

This task package provides a complete workflow for executing the refactoring roadmap identified in the code review. All tasks are tracked, documented, and ready for execution.

### What You Get
- 11 actionable tasks across 3 phases
- Branch creation scripts for all tasks
- PR templates for each phase type
- Test scaffolds ready to implement
- Interactive progress dashboard
- Comprehensive execution guide

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

## Task Phases

### Phase 1: Critical Architecture (5 tasks, 9 days)
**Focus**: Decompose 2,273-line main.py monolith

| Task | Description | Effort | Priority |
|------|-------------|--------|----------|
| TASK-20250929-001 | Extract authentication routes | 2 days | CRITICAL |
| TASK-20250929-002 | Extract quote routes | 2 days | CRITICAL |
| TASK-20250929-003 | Extract work order & material routes | 2 days | CRITICAL |
| TASK-20250929-004 | Fix CSV test complexity (31 → <10) | 1 day | HIGH |
| TASK-20250929-005 | Implement service interfaces (DIP) | 2 days | HIGH |

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

## Next Steps

### Immediate Actions (Today)

1. **Review task list**:
   ```bash
   open docs/task-dashboards/refactoring-progress-20250929.html
   ```

2. **Create Phase 1 branches**:
   ```bash
   bash scripts/branches/create-phase-1-branches.sh
   ```

3. **Start TASK-20250929-001**:
   ```bash
   git checkout refactor/auth-routes-20250929
   cat tests/test_routes_refactor_scaffold.py
   ```

4. **Read comprehensive guide**:
   ```bash
   open docs/task-guides/refactoring-guide-20250929.md
   ```

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