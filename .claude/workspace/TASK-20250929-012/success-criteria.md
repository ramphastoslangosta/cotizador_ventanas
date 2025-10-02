# TASK-012 Success Criteria

## Primary Objectives

### 1. All Duplicate Auth Routes Removed
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] No @app decorators for auth routes in main.py
- [ ] All auth routes in app/routes/auth.py only
- [ ] Login, register, logout routes work correctly

**Verification**:
```bash
# Count auth route decorators in main.py
grep -E "@app\.(get|post).*/(login|register|logout)" main.py | wc -l
# Expected: 0

# Verify auth router has routes
grep -E "@router\.(get|post).*/(login|register|logout)" app/routes/auth.py | wc -l
# Expected: >0
```

---

### 2. All Duplicate Quote Routes Removed
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] No @app decorators for quote routes in main.py (except core calculation routes)
- [ ] All quote CRUD routes in app/routes/quotes.py only
- [ ] Quote list, view, create, edit routes work correctly

**Verification**:
```bash
# Count quote route decorators in main.py
grep -E "@app\.(get|post|put|delete).*/quotes" main.py | wc -l
# Expected: 0 or small number (only core routes like /quotes/calculate)

# Verify quotes router has routes
grep -E "@router\.(get|post|put|delete).*/quotes" app/routes/quotes.py | wc -l
# Expected: >0
```

---

### 3. All Tests Pass
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] All 13 integration tests pass
- [ ] No new test failures introduced
- [ ] Test coverage maintained

**Verification**:
```bash
pytest tests/ -v --tb=short
# Expected output: ====== 13 passed in X.XXs ======
```

---

### 4. Application Starts Successfully
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] Python imports work without errors
- [ ] FastAPI application initializes
- [ ] Server starts on port 8000
- [ ] No startup errors in logs

**Verification**:
```bash
timeout 10s python main.py &
APP_PID=$!
sleep 3
if ps -p $APP_PID > /dev/null; then
    echo "✅ Application running"
    kill $APP_PID
else
    echo "❌ Application failed to start"
fi
```

---

### 5. Route Count Maintained
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] Total route count = 104
- [ ] No routes lost during cleanup
- [ ] Router registration working correctly

**Verification**:
```bash
python -c "import main; print(f'Routes: {len(main.app.routes)}')"
# Expected: Routes: 104
```

---

### 6. No Broken Imports or References
**Status**: ⬜ Pending Verification

**Acceptance**:
- [ ] All imports in main.py resolve correctly
- [ ] No circular import errors
- [ ] All router imports working
- [ ] No missing module errors

**Verification**:
```bash
python -c "import main; print('✅ Imports successful')"
# Expected: ✅ Imports successful

# Check for import errors
python main.py 2>&1 | grep -i "importerror\|modulenotfounderror" || echo "✅ No import errors"
```

---

## Secondary Objectives

### 7. Code Quality Improvements
**Status**: ⬜ Pending

**Acceptance**:
- [ ] main.py reduced by ~670 lines (or documented why not)
- [ ] Cleaner separation of concerns
- [ ] Better code organization
- [ ] Easier to maintain

**Verification**:
```bash
# Before: ~1,978 lines
# After: ~1,308 lines (if duplicates removed)
wc -l main.py
```

---

### 8. Documentation Updated
**Status**: ⬜ Pending

**Acceptance**:
- [ ] tasks.csv status updated to "completed"
- [ ] TASK_STATUS.md updated with completion details
- [ ] Completion summary created
- [ ] Workspace archived

**Verification**:
```bash
grep "TASK-20250929-012" tasks.csv | grep "completed"
# Should show task as completed
```

---

## Test Scenarios

### Scenario 1: Auth Routes Work
```bash
# Start app
python main.py &
APP_PID=$!
sleep 3

# Test login page
curl -s http://localhost:8000/login | grep -q "login"
echo "Login page: $?"  # 0 = success

# Test register page
curl -s http://localhost:8000/register | grep -q "register"
echo "Register page: $?"  # 0 = success

# Cleanup
kill $APP_PID
```

**Expected**: All pages return successfully

---

### Scenario 2: Quote Routes Work
```bash
# Start app
python main.py &
APP_PID=$!
sleep 3

# Test quotes list
curl -s http://localhost:8000/quotes | grep -q "Cotizaciones"
echo "Quotes list: $?"  # 0 = success

# Test new quote page
curl -s http://localhost:8000/quotes/new | grep -q "Nueva Cotización"
echo "New quote: $?"  # 0 = success

# Cleanup
kill $APP_PID
```

**Expected**: All pages return successfully

---

### Scenario 3: Critical Workflows
```bash
# Test dashboard redirect (no auth)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard)
echo "Dashboard redirect: $STATUS"
# Expected: 302 or 307 (redirect to login)

# Test API endpoints
curl -s http://localhost:8000/api/materials | grep -q "\["
echo "API materials: $?"  # 0 = success
```

**Expected**: Redirects and API calls work

---

## Rollback Criteria

Trigger rollback if any of these occur:

- ❌ Tests fail after changes
- ❌ Application fails to start
- ❌ Route count drops below 104
- ❌ Critical page returns 500 error
- ❌ Import errors occur
- ❌ Production smoke tests fail

### Rollback Command
```bash
git checkout main.py tasks.csv TASK_STATUS.md
pytest tests/ -q  # Verify rollback worked
```

---

## Completion Checklist

Mark each criterion as complete:

- [ ] ✅ Objective 1: Duplicate auth routes removed
- [ ] ✅ Objective 2: Duplicate quote routes removed
- [ ] ✅ Objective 3: All tests pass
- [ ] ✅ Objective 4: Application starts successfully
- [ ] ✅ Objective 5: Route count = 104
- [ ] ✅ Objective 6: No broken imports
- [ ] ✅ Objective 7: Code quality improved
- [ ] ✅ Objective 8: Documentation updated

**Overall Status**: ⬜ Not Started

---

## Sign-Off

**Developer**: _________________
**Date**: _________________
**Verification**: All criteria met ✅ / Issues found ❌

**Notes**:
_Add any additional notes or caveats_
