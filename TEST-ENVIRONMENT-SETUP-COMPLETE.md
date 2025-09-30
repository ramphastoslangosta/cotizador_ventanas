# Test Environment Setup - Complete ✅

**Date**: 2025-09-29
**Status**: ✅ Ready for use
**Location**: Droplet at 159.65.174.94:/home/ventanas/app/

---

## 🎉 What Was Created

### 1. Test Docker Compose Configuration
**File**: `/home/ventanas/app/docker-compose.test.yml`

Complete isolated test environment with:
- **Separate containers**: ventanas-test-app, ventanas-test-db, ventanas-test-redis
- **Separate ports**: 8001 (app), 5433 (db), 6380 (redis)
- **Separate database**: ventanas_test_db
- **Separate network**: ventanas-test-network (172.21.0.0/16)
- **Separate volumes**: postgres_test_data, redis_test_data
- **Debug mode enabled**: For detailed logging
- **Optimized resources**: Lower memory limits for testing

### 2. Directory Structure
```
/home/ventanas/app/
├── docker-compose.test.yml        # Test configuration
├── docker-compose.beta.yml        # Production configuration (unchanged)
├── logs/
│   ├── test/                      # Test environment logs (separate)
│   └── ...                        # Production logs (unchanged)
├── backups/
│   ├── test/                      # Test backups (separate)
│   └── ...                        # Production backups (unchanged)
├── scripts/
│   └── test-environment-check.sh  # Verification script
└── TEST_ENVIRONMENT_GUIDE.md      # Complete usage guide
```

### 3. Documentation
**File**: `/home/ventanas/app/TEST_ENVIRONMENT_GUIDE.md`

Comprehensive guide covering:
- Quick start instructions
- Complete testing workflow
- Common operations
- Troubleshooting
- Test vs Production comparison
- Testing checklist template
- Best practices

### 4. Verification Script
**File**: `/home/ventanas/app/scripts/test-environment-check.sh`

Automated verification that checks:
- Configuration files exist
- Test directories are set up
- Container status
- Production beta is unaffected
- Port availability
- Health endpoints
- Container health status
- Recent error logs

---

## 🚀 Quick Start Guide

### Starting Test Environment

```bash
# SSH to droplet
ssh root@159.65.174.94

# Navigate to app directory
cd /home/ventanas/app

# Verify production is running (should be on main branch)
docker-compose -f docker-compose.beta.yml ps
git branch

# Checkout test branch (example: TASK-003)
git fetch origin
git checkout refactor/workorder-material-routes-20250929

# Start test environment
docker-compose -f docker-compose.test.yml up -d --build

# Wait for startup (about 20-30 seconds)
sleep 30

# Verify test environment
bash scripts/test-environment-check.sh

# Test health endpoint
curl http://localhost:8001/api/health

# Expected response:
# {"status":"healthy","service":"ventanas-quotation-system"}
```

### Viewing Test Logs

```bash
# Follow logs in real-time
docker-compose -f docker-compose.test.yml logs -f app

# View last 50 lines
docker-compose -f docker-compose.test.yml logs --tail=50 app

# Check for errors
docker-compose -f docker-compose.test.yml logs app | grep -i error
```

### Testing Routes (TASK-003 Example)

```bash
# Work order routes
curl http://localhost:8001/work-orders
curl http://localhost:8001/api/work-orders

# Material routes
curl http://localhost:8001/materials_catalog
curl http://localhost:8001/api/materials
curl http://localhost:8001/api/materials/by-category

# Products routes
curl http://localhost:8001/products_catalog
curl http://localhost:8001/api/products
```

### Stopping Test Environment

```bash
# Stop containers (keeps data)
docker-compose -f docker-compose.test.yml stop

# Stop and remove (keeps volumes for next time)
docker-compose -f docker-compose.test.yml down

# Full cleanup including data (fresh start next time)
docker-compose -f docker-compose.test.yml down -v
```

---

## 📊 Test vs Production Comparison

| **Aspect** | **Test Environment** | **Production Beta** |
|------------|---------------------|---------------------|
| Compose file | docker-compose.test.yml | docker-compose.beta.yml |
| App port | 8001 | 8000 |
| DB port | 5433 | 5432 |
| Redis port | 6380 | 6379 |
| Database | ventanas_test_db | ventanas_beta_db |
| Network | 172.21.0.0/16 | 172.20.0.0/16 |
| Containers | ventanas-test-* | ventanas-beta-* |
| Debug mode | Enabled | Disabled |
| Purpose | Testing new features | Stable service |

**Key Benefit**: Both environments can run **simultaneously** without conflicts!

---

## ✅ Verification Results

Current status (as of 2025-09-29):

```
✓ docker-compose.test.yml exists
✓ logs/test directory exists
✓ backups/test directory exists
✓ Production beta app is still running
⚠ Test containers not running (normal when not testing)
```

**Production Status**: ✅ Unaffected and operational
**Test Environment**: ✅ Ready to start when needed

---

## 🎯 Next Steps - Using Test Environment for TASK-003

Now that test environment is ready, follow this workflow:

### Step 1: Fix Templates Issue (Local)
```bash
# On local machine
cd /Users/rafaellang/cotizador/cotizador_ventanas

# Fix templates import issue
# Option A: Move templates to config.py (recommended)
# Edit config.py, add templates
# Edit both router files to import from config

# Test locally
python -c "from app.routes import work_orders"
python -c "from app.routes import materials"

# If imports work, commit and push
git add config.py app/routes/*.py
git commit -m "fix(TASK-003): resolve templates import issue"
git push origin refactor/workorder-material-routes-20250929
```

### Step 2: Deploy to Test Environment
```bash
# On droplet
ssh root@159.65.174.94
cd /home/ventanas/app

# Pull latest fixes
git fetch origin
git checkout refactor/workorder-material-routes-20250929
git pull origin refactor/workorder-material-routes-20250929

# Start test environment
docker-compose -f docker-compose.test.yml up -d --build

# Monitor startup
docker-compose -f docker-compose.test.yml logs -f app
# Wait for "Application startup complete"
```

### Step 3: Run Testing Checklist
```bash
# Verify test environment
bash scripts/test-environment-check.sh

# Test health
curl http://localhost:8001/api/health

# Test all 30 routes (9 work orders + 21 materials/products)
# Work Orders:
curl http://localhost:8001/work-orders
curl http://localhost:8001/api/work-orders
# ... (run complete checklist)

# Check logs for errors
docker-compose -f docker-compose.test.yml logs app | grep -i error
```

### Step 4: Deploy to Production (Only if tests pass)
```bash
# Switch to main branch
git checkout main

# Merge test branch
git merge refactor/workorder-material-routes-20250929

# Deploy to production beta
docker-compose -f docker-compose.beta.yml up -d --build

# Verify production
curl http://localhost:8000/api/health

# Stop test environment (no longer needed)
docker-compose -f docker-compose.test.yml down
```

---

## 🛡️ Safety Features

### Production Protection
- ✅ Completely separate containers (different names)
- ✅ Completely separate ports (no conflicts)
- ✅ Completely separate databases (no data mixing)
- ✅ Completely separate networks (no network interference)
- ✅ Separate volumes (independent data storage)
- ✅ Separate logs (easier troubleshooting)

### Resource Management
- ✅ Lower memory limits (512M vs 768M)
- ✅ Separate network subnet (172.21.x vs 172.20.x)
- ✅ Can stop when not testing (saves resources)
- ✅ Both environments can run simultaneously if needed

### Testing Safety
- ✅ Debug mode enabled (detailed logs)
- ✅ Quick rebuild capability (down -v && up)
- ✅ No impact on production data
- ✅ Easy cleanup (down -v removes everything)

---

## 📋 Pre-Deployment Checklist

Before deploying ANY code to production, use this checklist:

### Local Testing
- [ ] Syntax check passed: `python -m py_compile app/routes/*.py`
- [ ] Import check passed: `python -c "from app.routes import work_orders"`
- [ ] Local runtime test passed (optional)
- [ ] Docker build test passed (optional)

### Test Environment
- [ ] Test environment started successfully
- [ ] All containers show "healthy" status
- [ ] Health endpoint responds: `curl http://localhost:8001/api/health`
- [ ] All routes return expected responses
- [ ] No errors in logs
- [ ] Test runs for 1+ hours without issues (optional for soak testing)

### Production Deployment
- [ ] All test environment checks passed
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Rollback plan ready
- [ ] Production backup created (optional)

---

## 📞 Quick Reference

### Essential Commands

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d --build

# Check status
docker-compose -f docker-compose.test.yml ps
bash scripts/test-environment-check.sh

# View logs
docker-compose -f docker-compose.test.yml logs -f app

# Test health
curl http://localhost:8001/api/health

# Stop test environment
docker-compose -f docker-compose.test.yml down

# Full cleanup (fresh start)
docker-compose -f docker-compose.test.yml down -v
```

### Important Ports

- **Test App**: http://localhost:8001
- **Test Database**: localhost:5433
- **Test Redis**: localhost:6380
- **Production App**: http://localhost:8000 (unchanged)
- **Production Database**: localhost:5432 (unchanged)
- **Production Redis**: localhost:6379 (unchanged)

### Key Files

- **Test Config**: `docker-compose.test.yml`
- **Test Guide**: `TEST_ENVIRONMENT_GUIDE.md`
- **Verification Script**: `scripts/test-environment-check.sh`
- **Production Config**: `docker-compose.beta.yml` (unchanged)

---

## 🎓 What We Learned

From the TASK-003 incident, we established:

1. **Never test on production** - Even "beta" needs protection
2. **Test environment is mandatory** - Required for all deployments
3. **Verify locally first** - Catch issues before deployment
4. **Follow structured process** - Checklists prevent mistakes
5. **Isolate environments** - Separate containers, ports, databases

This test environment infrastructure ensures these lessons are applied going forward.

---

## ✨ Summary

### What's Ready
✅ Complete isolated test environment
✅ Comprehensive documentation
✅ Automated verification script
✅ Production remains unaffected
✅ Ready to test TASK-003

### What's Next
1. Fix templates import issue (local)
2. Deploy to test environment
3. Run full testing checklist
4. Only deploy to production after tests pass

### Key Benefits
- **Safe testing** without risking production
- **Simultaneous operation** (test + production)
- **Easy verification** with automated script
- **Complete isolation** (containers, ports, data)
- **Resource efficient** (stop when not testing)

---

**Status**: ✅ Test Environment Setup Complete
**Location**: 159.65.174.94:/home/ventanas/app/
**Ready**: Yes - can start testing immediately
**Documentation**: Complete and accessible on droplet

---

*Setup completed: 2025-09-29*
*Time to set up: ~30 minutes*
*Production impact: Zero*
*Ready for: TASK-003 testing and all future deployments*