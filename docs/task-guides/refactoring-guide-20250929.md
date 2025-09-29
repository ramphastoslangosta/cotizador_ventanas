# Refactoring Execution Guide
**Generated**: 2025-09-29
**Project**: FastAPI Window Quotation System
**Code Review**: [code-review-agent_2025-09-26-03.md](../code-review-reports/code-review-agent_2025-09-26-03.md)

---

## Overview

This guide provides complete instructions for executing the 3-phase refactoring initiative derived from the comprehensive code review. The refactoring addresses critical architectural issues, performance bottlenecks, and code quality improvements.

### Refactoring Summary
- **Total Tasks**: 11 tasks across 3 phases
- **Estimated Effort**: 12-15 days
- **Risk Level**: Medium (High for Phase 1)
- **Overall Health Score**: 78/100 (current)
- **Target Health Score**: 90+ (after completion)

### Quick Links
- **Task Tracker**: [tasks.csv](../../tasks.csv)
- **Progress Dashboard**: [refactoring-progress-20250929.html](../task-dashboards/refactoring-progress-20250929.html)
- **Branch Scripts**: [scripts/branches/](../../scripts/branches/)
- **PR Templates**: [.github/pull_request_template/](../../.github/pull_request_template/)

---

## Phase Overview

### Phase 1: Critical Architecture Refactoring (5-6 days, HIGH RISK)
**Goal**: Decompose main.py monolith and fix critical complexity issues

**Tasks**:
1. TASK-20250929-001: Extract authentication routes (2 days)
2. TASK-20250929-002: Extract quote routes (2 days)
3. TASK-20250929-003: Extract work order & material routes (2 days)
4. TASK-20250929-004: Fix CSV test complexity (1 day)
5. TASK-20250929-005: Implement service interfaces (2 days)

**Critical Success Factors**:
- All existing tests must pass unchanged
- No API contract changes
- Atomic commits with clear rollback points
- Comprehensive testing after each task

### Phase 2: Performance Optimization (4-5 days, MEDIUM RISK)
**Goal**: Eliminate performance bottlenecks and improve response times

**Tasks**:
6. TASK-20250929-006: Optimize database queries (2 days)
7. TASK-20250929-007: Implement formula caching (1 day)
8. TASK-20250929-008: Implement CSV streaming (2 days)

**Performance Targets**:
- Quote calculation: 200ms → 50ms (-75%)
- Database queries: Reduce by 80%
- Formula evaluation: 60% faster
- CSV processing: Support up to 100MB files

### Phase 3: Code Quality & Architecture (3-4 days, LOW RISK)
**Goal**: Implement design patterns and improve maintainability

**Tasks**:
9. TASK-20250929-009: Implement command pattern (2 days)
10. TASK-20250929-010: Extract template business logic (1 day)
11. TASK-20250929-011: Implement factory pattern (1 day)

**Quality Targets**:
- Cyclomatic complexity: Max 10
- Maintainability index: >70 for all files
- SOLID principles: 80% adherence

---

## Getting Started

### Prerequisites

1. **Review Code Review Report**:
   ```bash
   open docs/code-review-reports/code-review-agent_2025-09-26-03.md
   ```

2. **Review Task List**:
   ```bash
   open tasks.csv
   # Or view in dashboard
   open docs/task-dashboards/refactoring-progress-20250929.html
   ```

3. **Verify Development Environment**:
   ```bash
   # Ensure you're on main branch
   git checkout main
   git pull origin main

   # Verify all tests pass baseline
   pytest tests/ -v

   # Verify application runs
   python main.py
   ```

4. **Establish Performance Baseline** (important for Phase 2):
   ```bash
   # Run performance benchmarks
   pytest tests/test_performance.py --benchmark-only

   # Record baseline metrics
   # - Quote calculation time: ~200ms
   # - Database queries per request: ~45 queries
   ```

### Task Selection Strategy

**Sequential Execution** (Recommended):
- Follow task order due to dependencies
- Complete Phase 1 before Phase 2
- Start with TASK-20250929-001

**Parallel Execution** (Advanced):
- Independent tasks can run in parallel:
  - TASK-20250929-001 and TASK-20250929-004 (no dependencies)
  - TASK-20250929-007 and TASK-20250929-008 (both depend on prior phase)

---

## Task Execution Workflow

### Step 1: Pick a Task

```bash
# Check task dependencies in tasks.csv
grep "TASK-20250929-001" tasks.csv

# Verify dependencies completed
# dependencies column must show "none" or completed task IDs
```

### Step 2: Create Feature Branch

**Option A: Use Automated Script**
```bash
# For Phase 1 tasks
bash scripts/branches/create-phase-1-branches.sh

# For Phase 2 tasks
bash scripts/branches/create-phase-2-branches.sh

# For Phase 3 tasks
bash scripts/branches/create-phase-3-branches.sh
```

**Option B: Manual Branch Creation**
```bash
# Example for TASK-20250929-001
git checkout main
git pull origin main
git checkout -b refactor/auth-routes-20250929
git push -u origin refactor/auth-routes-20250929
```

### Step 3: Implement Changes

**Read Task Details**:
```bash
# View task in tasks.csv
awk -F',' '/TASK-20250929-001/ {print}' tasks.csv

# View test scaffold
cat tests/test_routes_refactor_scaffold.py
```

**Implementation Checklist**:
- [ ] Read task description and acceptance criteria
- [ ] Review related code sections from code review report
- [ ] Create test cases first (TDD approach recommended)
- [ ] Implement changes incrementally
- [ ] Run tests after each significant change
- [ ] Document complex logic with comments

**Testing During Development**:
```bash
# Run related tests frequently
pytest tests/test_routes_refactor_scaffold.py -v -k "auth"

# Run full test suite before commit
pytest tests/ -v

# Check code quality
radon cc main.py -a  # Check complexity
black .  # Format code
```

### Step 4: Commit Changes

**Commit Message Format**:
```bash
git add <files>
git commit -m "$(cat <<'EOF'
<type>: <concise description>

<detailed explanation of changes>
- What was changed
- Why it was changed
- How it addresses the task

Acceptance Criteria Met:
- [x] Criterion 1
- [x] Criterion 2

Task: TASK-20250929-XXX

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Commit Types**:
- `refactor`: Code restructuring (Phase 1, 3)
- `perf`: Performance improvements (Phase 2)
- `test`: Test additions/modifications
- `docs`: Documentation updates

**Example Commit**:
```bash
git commit -m "$(cat <<'EOF'
refactor: extract authentication routes to app/routes/auth.py

Moved login, register, and logout routes from main.py to dedicated
auth.py module. This is part of decomposing the 2,273-line main.py
monolith.

Changes:
- Created app/routes/auth.py with authentication routes
- Created app/dependencies/auth.py for auth dependencies
- Updated main.py to register auth router
- All tests pass without modification
- API contracts unchanged

Acceptance Criteria Met:
- [x] All auth routes moved to auth.py
- [x] No API contract changes
- [x] All tests pass
- [x] Authentication flow unchanged

Reduces main.py by 287 lines.

Task: TASK-20250929-001

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 5: Create Pull Request

**Push Branch**:
```bash
git push origin <branch-name>
```

**Create PR Using Template**:
```bash
# Using GitHub CLI
gh pr create --title "TASK-20250929-001: Extract authentication routes" \
             --body-file .github/pull_request_template/critical-refactoring.md \
             --base main

# Or create via GitHub web interface
```

**Fill Out PR Template**:
- Task ID
- Summary of changes
- Testing evidence (paste pytest output)
- Performance impact (if applicable)
- Risk assessment
- Rollback procedure

**Request Reviews**:
- Phase 1 (critical): Require 2+ senior developers
- Phase 2 (performance): Require performance review
- Phase 3 (architecture): Require architecture review

### Step 6: Address Review Feedback

```bash
# Make requested changes
git add <files>
git commit -m "refactor: address PR review feedback

- Changed X based on reviewer comment
- Fixed Y as suggested
- Added test for edge case Z
"

git push origin <branch-name>
```

### Step 7: Merge and Deploy

**After PR Approval**:
```bash
# Squash and merge via GitHub interface
# Or merge locally
git checkout main
git merge --squash <branch-name>
git commit -m "Merge TASK-20250929-001: Extract authentication routes"
git push origin main
```

**Post-Merge Verification**:
```bash
# Verify on main branch
git checkout main
git pull origin main

# Run full test suite
pytest tests/ -v --cov

# Run application smoke tests
python main.py &
SERVER_PID=$!
sleep 5

# Test critical endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs

kill $SERVER_PID
```

### Step 8: Update Task Status

**Manual Update** (tasks.csv):
```bash
# Change status from "pending" to "completed"
# Update notes column with completion date
```

**Update Dashboard**:
```bash
# Dashboard auto-updates from tasks.csv
# Refresh browser to see updated progress
open docs/task-dashboards/refactoring-progress-20250929.html
```

---

## Phase-Specific Guidance

### Phase 1: Critical Architecture Refactoring

#### Task 1: Extract Authentication Routes (TASK-20250929-001)

**Target Files**:
- `main.py` lines 795-830 (login/register/logout)

**New Structure**:
```
app/
├── routes/
│   ├── __init__.py
│   └── auth.py          # Authentication routes
├── dependencies/
│   ├── __init__.py
│   └── auth.py          # Auth dependencies
```

**Implementation Steps**:
1. Create `app/routes/auth.py`
2. Move `@app.post("/web_login")` to auth router
3. Move `@app.post("/register")` to auth router
4. Move `@app.get("/logout")` to auth router
5. Create `app/dependencies/auth.py` for `get_current_user_flexible`
6. Update `main.py` to register router: `app.include_router(auth_router)`
7. Run tests: `pytest tests/test_authentication.py -v`

**Success Criteria**:
- [ ] All auth tests pass
- [ ] Login flow works via web interface
- [ ] API authentication unchanged
- [ ] main.py reduced by ~300 lines

#### Task 2: Extract Quote Routes (TASK-20250929-002)

**Dependencies**: TASK-20250929-001 completed

**Target Files**:
- `main.py` lines 154-650 (quote routes and calculation)

**New Structure**:
```
app/
└── routes/
    └── quotes.py        # Quote CRUD and calculation
```

**Key Functions to Extract**:
- `calculate_window_item_from_bom()` - Move to service layer
- `@app.post("/quotes/calculate")` - Move to quotes router
- `@app.get("/quotes")` - Move to quotes router
- `@app.post("/quotes")` - Move to quotes router
- `@app.put("/quotes/{id}")` - Move to quotes router

**Success Criteria**:
- [ ] Quote calculation produces identical results
- [ ] CSV export/import functional
- [ ] Quote editing (QE-001) works
- [ ] main.py reduced by ~500 lines

#### Task 4: Fix CSV Test Complexity (TASK-20250929-004)

**Independent Task** (can run parallel to Task 1)

**Target File**:
- `run_csv_tests.py` (cyclomatic complexity: 31)

**Refactoring Strategy**:
```python
# Before: Monolithic test function
def test_csv_operations():
    # 200+ lines of test logic
    # Complexity: 31
    pass

# After: Test builder pattern
class CSVTestBuilder:
    def with_import_data(self, data): ...
    def with_export_config(self, config): ...
    def build(self): ...

def test_csv_import():
    # Focused test, complexity: 3
    test = CSVTestBuilder().with_import_data(data).build()
    assert test.run()

def test_csv_export():
    # Focused test, complexity: 2
    test = CSVTestBuilder().with_export_config(config).build()
    assert test.run()
```

**Success Criteria**:
- [ ] Cyclomatic complexity <10 for all functions
- [ ] All CSV tests still pass
- [ ] Test execution time unchanged or improved
- [ ] Code follows pytest best practices

### Phase 2: Performance Optimization

#### Task 6: Optimize Database Queries (TASK-20250929-006)

**Dependencies**: TASK-20250929-003 completed

**Problem**: N+1 query problem in BOM calculations

**Solution**:
```python
# Before: N+1 queries
def calculate_bom(product_id):
    product = db.query(Product).get(product_id)  # 1 query
    for bom_item in product.bom_items:  # N queries
        material = db.query(Material).get(bom_item.material_id)

# After: Eager loading
from sqlalchemy.orm import joinedload

def calculate_bom(product_id):
    product = db.query(Product)\
        .options(joinedload(Product.bom_items)\
        .joinedload(BOMItem.material))\
        .get(product_id)  # 1 query total
```

**Performance Testing**:
```bash
# Before optimization
pytest tests/test_performance_optimization_scaffold.py::test_quote_calculation_performance_improved --benchmark-only

# Record baseline: ~200ms

# After optimization
# Target: <50ms
```

**Success Criteria**:
- [ ] Database queries reduced by 80%
- [ ] Quote calculation <100ms
- [ ] pytest-benchmark shows improvement
- [ ] No functionality changes

#### Task 7: Formula Evaluation Caching (TASK-20250929-007)

**Target**: `security/formula_evaluator.py`

**Implementation**:
```python
from functools import lru_cache

class SafeFormulaEvaluator:
    @lru_cache(maxsize=128)
    def _parse_expression(self, formula: str):
        # Cache parsed expressions
        return ast.parse(formula, mode='eval')

    def evaluate_formula(self, formula: str, variables: dict):
        parsed = self._parse_expression(formula)
        return simple_eval(parsed, operators=self.ops, names=variables)
```

**Success Criteria**:
- [ ] LRU cache implemented
- [ ] Cache hit rate >70%
- [ ] Formula evaluation 60% faster
- [ ] Memory usage <50MB

### Phase 3: Architecture Improvements

#### Task 9: Command Pattern (TASK-20250929-009)

**New Structure**:
```
app/
└── commands/
    ├── __init__.py
    ├── base_command.py      # Abstract command
    └── quote_command.py     # Quote calculation command
```

**Implementation**:
```python
# base_command.py
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

# quote_command.py
class CalculateQuoteCommand(Command):
    def __init__(self, quote_service, quote_data):
        self.service = quote_service
        self.data = quote_data
        self.previous_state = None

    def execute(self):
        self.previous_state = self.data.copy()
        return self.service.calculate(self.data)

    def undo(self):
        if self.previous_state:
            self.data.update(self.previous_state)
```

**Benefits**:
- Encapsulates calculation logic
- Enables undo/redo functionality
- Improves testability
- Supports command history

---

## Testing Strategy

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Benchmark critical operations
5. **Regression Tests**: Ensure no functionality lost

### Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_routes_refactor_scaffold.py -v

# Run tests matching pattern
pytest tests/ -v -k "auth"

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run performance benchmarks
pytest tests/ --benchmark-only

# Run security tests
pytest tests/test_security.py -v
```

### Test Fixtures

Use existing fixtures from `conftest.py`:
```python
@pytest.fixture
def db_session():
    # Database session for testing

@pytest.fixture
def test_user():
    # Test user fixture

@pytest.fixture
def test_quote():
    # Test quote fixture
```

---

## Rollback Procedures

### Quick Rollback (Production Emergency)

```bash
# Step 1: Identify problematic commit
git log --oneline -n 10

# Step 2: Revert the commit
git checkout main
git revert <commit-hash>
git push origin main

# Step 3: Verify rollback
pytest tests/ -v
python main.py  # Verify application starts

# Step 4: Monitor
# Check logs for errors
# Monitor error rates
# Verify critical endpoints
```

### Phase-Specific Rollback

**Phase 1 Rollback**:
```bash
# If main.py refactoring causes issues
git revert <refactor-commit-hash>

# Verify all routes work
pytest tests/test_authentication.py -v
pytest tests/test_quotes.py -v
```

**Phase 2 Rollback**:
```bash
# If performance optimization causes regression
git revert <perf-commit-hash>

# Clear any caches
# Restart application
python main.py
```

**Phase 3 Rollback**:
```bash
# Architecture changes are low risk
git revert <arch-commit-hash>
```

### Rollback Testing

Always test rollback in staging first:
```bash
# In staging environment
git checkout staging
git cherry-pick <rollback-commit>
pytest tests/ -v
# Verify functionality
```

---

## Monitoring & Success Metrics

### Code Quality Metrics

**Before Refactoring**:
```bash
radon cc main.py -a
# Cyclomatic Complexity: 19 (max)
# Maintainability Index: 0.00 (main.py)
```

**Target After Refactoring**:
- Cyclomatic Complexity: <10 for all functions
- Maintainability Index: >70 for all files
- Code Duplication: <5%
- Test Coverage: >85%

**Measurement Commands**:
```bash
# Complexity
radon cc . -a --total-average

# Maintainability
radon mi . -s

# Security
bandit -r . -f json

# Test Coverage
pytest --cov=. --cov-report=term-missing
```

### Performance Metrics

**Track These Metrics**:
| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Quote Calculation | 200ms | <50ms | pytest-benchmark |
| Database Queries | 45/request | <10/request | SQLAlchemy echo |
| Page Load Time | 3s | <2s | Browser DevTools |
| Memory Usage | 250MB | <200MB | memory_profiler |

**Performance Monitoring**:
```bash
# Benchmark tests
pytest tests/test_performance.py --benchmark-only --benchmark-autosave

# Compare benchmarks
pytest-benchmark compare
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Tests Failing After Route Extraction

**Symptoms**: Import errors, route not found errors

**Solution**:
```bash
# Verify router registration
grep "include_router" main.py

# Check imports
grep "from app.routes" main.py

# Verify router prefix
# In route file, check: router = APIRouter(prefix="/quotes")
```

#### Issue 2: Performance Regression

**Symptoms**: Tests slower after optimization

**Solution**:
```bash
# Profile the code
python -m cProfile main.py

# Check for missing indexes
# In database.py, verify indexes on foreign keys

# Verify eager loading
# Check for .options(joinedload(...))
```

#### Issue 3: Circular Import Errors

**Symptoms**: `ImportError: cannot import name` after refactoring

**Solution**:
```python
# Use type hints with strings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User

def function(user: "User"):  # String annotation
    pass
```

#### Issue 4: Test Fixtures Not Found

**Symptoms**: `fixture 'db_session' not found`

**Solution**:
```bash
# Ensure conftest.py in correct location
ls tests/conftest.py

# Check fixture scope
# In conftest.py: @pytest.fixture(scope="function")
```

---

## Best Practices

### Code Style

- Follow PEP 8 style guide
- Use `black` for consistent formatting
- Use `isort` for import organization
- Maximum line length: 100 characters
- Use type hints for function signatures

### Git Workflow

- Create feature branch for each task
- Make atomic commits (one logical change per commit)
- Write descriptive commit messages
- Squash commits before merging to main
- Delete feature branches after merge

### Testing

- Write tests before implementation (TDD)
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent
- Mock external dependencies

### Documentation

- Update CLAUDE.md with architecture changes
- Document complex logic with comments
- Update API documentation
- Keep README.md current
- Document breaking changes

---

## Resources

### Internal Documentation
- [CLAUDE.md](/Users/rafaellang/cotizador/cotizador_ventanas/CLAUDE.md)
- [Code Review Report](../code-review-reports/code-review-agent_2025-09-26-03.md)
- [Project Structure](/Users/rafaellang/cotizador/cotizador_ventanas/PROJECT_STRUCTURE.md)

### External Resources
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Clean Code Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)

### Tools
- **radon**: Code complexity analysis
- **black**: Code formatting
- **pytest**: Testing framework
- **pytest-benchmark**: Performance testing
- **bandit**: Security scanning

---

## Support & Questions

For questions or issues during refactoring:

1. **Review this guide** for common solutions
2. **Check code review report** for context
3. **Review task acceptance criteria** in tasks.csv
4. **Examine test scaffolds** for implementation hints
5. **Consult team members** for architectural decisions

---

**Generated by**: Task Package Generator Agent
**Last Updated**: 2025-09-29
**Version**: 1.0
**Status**: Ready for execution