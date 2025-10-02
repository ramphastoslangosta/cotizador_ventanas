# TASK-012: Test Environment Deployment Plan

**Objective**: Deploy duplicate route cleanup to test environment (port 8001) for verification before production deployment.

**Risk Level**: 🟢 LOW (test environment only, no production impact)

---

## Pre-Deployment Checklist

### 1. Verify Current State
- [ ] Confirm PR #9 is created and ready
- [ ] Verify all tests passed locally
- [ ] Check production is currently stable
- [ ] Document current production state

### 2. Prepare Test Environment
- [ ] SSH access to droplet (159.65.174.94) confirmed
- [ ] Test port 8001 is available
- [ ] Git repository access from droplet confirmed
- [ ] Test environment configuration ready

---

## Deployment Steps

### Step 1: Connect to Droplet
```bash
# SSH into the droplet
ssh user@159.65.174.94

# Navigate to application directory
cd /path/to/cotizador_ventanas

# Check current status
git status
git branch
```

**Expected**: Currently on a stable branch (main or previous test branch)

### Step 2: Fetch Latest Changes
```bash
# Fetch all branches from remote
git fetch origin

# Check if our branch is available
git branch -r | grep refactor/cleanup-duplicate-routes-20250929
```

**Expected**: Should see `origin/refactor/cleanup-duplicate-routes-20250929`

### Step 3: Create/Switch to Test Branch
```bash
# Option A: If test branch doesn't exist locally
git checkout -b test-task-012 origin/refactor/cleanup-duplicate-routes-20250929

# Option B: If test branch exists, update it
git checkout test-task-012
git pull origin refactor/cleanup-duplicate-routes-20250929

# Verify we're on the right commit
git log --oneline -5
```

**Expected**: Should see commits:
- a865427 (or latest): docs: PR #9 created
- 008f617: refactor(TASK-012): remove duplicate quote routes

### Step 4: Check Environment Configuration
```bash
# Verify .env file exists and has correct settings
ls -la .env
cat .env | grep -E "DATABASE_URL|PORT" | head -5

# Check virtual environment
source venv/bin/activate || python -m venv venv && source venv/bin/activate

# Verify Python version
python --version
```

**Expected**: 
- .env exists with DATABASE_URL configured
- Python 3.9+ 
- Virtual environment activates

### Step 5: Install/Update Dependencies
```bash
# Install/update dependencies (if needed)
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "fastapi|uvicorn|sqlalchemy"
```

**Expected**: All packages installed successfully

### Step 6: Verify Code Changes
```bash
# Check main.py line count (should be ~1,561 lines)
wc -l main.py

# Verify routes removed (should be no duplicates)
grep -c "^@app.*quotes" main.py

# Check router registration
grep "include_router.*quote" main.py
```

**Expected**:
- main.py: ~1,561 lines (reduced from ~1,979)
- Minimal @app.get/post routes for quotes
- Router registration present

### Step 7: Test Application Import
```bash
# Test that application can import without errors
python -c "
import sys
sys.path.insert(0, '.')
import main
print(f'✅ Application imported successfully')
print(f'Total routes: {len(main.app.routes)}')
"
```

**Expected**:
- Application imports without errors
- Route count: 95 (reduced from 104)

### Step 8: Check for Running Test Instance
```bash
# Check if port 8001 is in use
lsof -i :8001 || echo "Port 8001 is free"

# If port is in use, stop existing test instance
# pkill -f "uvicorn.*8001" or systemctl stop test-app
```

**Expected**: Port 8001 available or cleaned up

### Step 9: Start Test Environment
```bash
# Start application on port 8001 in background
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/test-app-8001.log 2>&1 &

# Capture PID
TEST_PID=$!
echo "Test app started with PID: $TEST_PID"

# Wait for startup
sleep 5

# Verify process is running
ps -p $TEST_PID
```

**Expected**: Process running with PID captured

### Step 10: Verify Test Environment Started
```bash
# Check logs for errors
tail -20 /tmp/test-app-8001.log

# Test basic connectivity
curl -I http://localhost:8001/login

# Check route count via API (if available)
# Or verify via logs
```

**Expected**:
- No startup errors in logs
- HTTP 200 response from login page
- Application running normally

---

## Verification Tests

### Test Suite 1: Critical Pages (from localhost on droplet)
```bash
# Test 1: Login page
curl -s http://localhost:8001/login | grep -q "login" && echo "✅ Login page OK" || echo "❌ Login FAIL"

# Test 2: Register page  
curl -s http://localhost:8001/register | grep -q "register" && echo "✅ Register page OK" || echo "❌ Register FAIL"

# Test 3: Quotes list (should redirect)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/quotes)
[ "$STATUS" = "307" ] && echo "✅ Quotes redirect OK" || echo "⚠️ Quotes status: $STATUS"

# Test 4: New quote (should redirect)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/quotes/new)
[ "$STATUS" = "307" ] && echo "✅ New quote redirect OK" || echo "⚠️ New quote status: $STATUS"

# Test 5: Dashboard (should redirect)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/dashboard)
[ "$STATUS" = "307" ] && echo "✅ Dashboard redirect OK" || echo "⚠️ Dashboard status: $STATUS"

# Test 6: API materials (should require auth)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/materials)
[ "$STATUS" = "401" ] && echo "✅ API auth OK" || echo "⚠️ API status: $STATUS"
```

**Expected**: All 6 tests pass ✅

### Test Suite 2: External Access (from your local machine)
```bash
# Test externally accessible endpoint
curl -I http://159.65.174.94:8001/login

# Test a few critical routes
curl -s http://159.65.174.94:8001/login | grep -q "login"
curl -s -o /dev/null -w "%{http_code}" http://159.65.174.94:8001/quotes
```

**Expected**: Accessible from external IP, routes working

### Test Suite 3: Route Verification
```bash
# From inside droplet, verify route count
python -c "
import sys
sys.path.insert(0, '.')
import main

routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
print(f'Total routes: {len(routes)}')

# Check key quote routes still exist
quote_routes = ['/quotes/new', '/quotes', '/quotes/{quote_id}']
for route in quote_routes:
    if route in routes:
        print(f'✅ {route}')
    else:
        print(f'❌ MISSING: {route}')
"
```

**Expected**: 95 routes, all key routes present

### Test Suite 4: Application Logs
```bash
# Monitor logs for errors
tail -f /tmp/test-app-8001.log

# Check for any error patterns
grep -i "error\|exception\|failed" /tmp/test-app-8001.log | tail -20
```

**Expected**: No critical errors, normal operation logs

---

## Success Criteria

### Must Pass (Blocking)
- ✅ Application starts without errors
- ✅ Port 8001 accessible internally
- ✅ All 6 critical page tests pass
- ✅ Route count = 95
- ✅ No exceptions in logs

### Should Pass (Important)
- ✅ External access works (port 8001 from internet)
- ✅ All quote routes functional via router
- ✅ No performance degradation
- ✅ Database connections working

### Nice to Have
- ✅ Memory usage stable
- ✅ Response times normal (<500ms)
- ✅ No unexpected warnings in logs

---

## Monitoring Period

### Short-term (15 minutes)
- Monitor logs continuously
- Test all critical endpoints multiple times
- Check for memory leaks or errors
- Verify database connections stable

### Medium-term (1 hour)
- Leave test environment running
- Perform additional manual testing
- Test authenticated workflows (if possible)
- Monitor resource usage

### Long-term (24 hours - optional)
- Leave running overnight (if safe)
- Check logs next day for issues
- Compare with production metrics

---

## Rollback Procedure

### If Issues Found

**Immediate Rollback:**
```bash
# Stop test application
kill $TEST_PID
# or
pkill -f "uvicorn.*8001"

# Switch back to main branch
git checkout main

# Restart test environment on main
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/test-app-8001.log 2>&1 &

# Verify rollback successful
curl -I http://localhost:8001/login
```

**Document Issues:**
```bash
# Save error logs
cp /tmp/test-app-8001.log ~/task-012-test-failure-$(date +%Y%m%d-%H%M%S).log

# Document what went wrong
echo "Issue encountered at $(date): [description]" >> ~/task-012-issues.txt
```

**Expected**: Test environment back to stable state in <2 minutes

---

## Production Deployment Decision

### Deploy to Production IF:
- ✅ All test suite tests pass
- ✅ No errors in test environment logs
- ✅ Test environment stable for 15+ minutes
- ✅ Route count verified (95 routes)
- ✅ All functionality working as expected
- ✅ PR #9 approved and merged

### DO NOT Deploy IF:
- ❌ Any test failures
- ❌ Errors or exceptions in logs
- ❌ Application fails to start
- ❌ Route count incorrect
- ❌ Performance issues observed
- ❌ Database connection problems

---

## Post-Test Actions

### If Tests Pass
1. Document test results in workspace notes
2. Update checklist: mark "Deploy to test environment" complete
3. Create deployment summary
4. Proceed with production deployment plan

### If Tests Fail
1. Stop test environment
2. Document failure details
3. Rollback to main branch
4. Investigate root cause
5. Fix issues in PR #9
6. Re-run test deployment

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Pre-deployment checks | 5 min | 5 min |
| SSH and setup | 5 min | 10 min |
| Code deployment | 5 min | 15 min |
| Application startup | 2 min | 17 min |
| Test execution | 5 min | 22 min |
| Monitoring | 15 min | 37 min |
| **Total** | **37 min** | - |

**Buffer**: Add 10-15 minutes for unexpected issues

---

## Key Commands Reference

### Quick Status Check
```bash
# Check if test app is running
ps aux | grep "uvicorn.*8001"
lsof -i :8001

# Quick test all endpoints
for endpoint in /login /register /quotes /dashboard; do
  echo -n "Testing $endpoint: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8001$endpoint
  echo ""
done
```

### Quick Stop Test Environment
```bash
pkill -f "uvicorn.*8001"
```

### Quick Start Test Environment
```bash
cd /path/to/cotizador_ventanas
source venv/bin/activate
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/test-app-8001.log 2>&1 &
```

---

**Plan Created**: 2025-10-02
**Task**: TASK-20250929-012
**Risk Level**: 🟢 LOW (test environment only)
**Estimated Time**: 40-50 minutes
**Ready to Execute**: ✅ Yes
