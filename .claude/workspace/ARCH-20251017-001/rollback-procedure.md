# Rollback Procedure: ARCH-20251017-001

**Date**: 2025-10-27
**Issue**: POST /web/login returns 500 Internal Server Error
**Environment**: Test (http://159.65.174.94:8001)
**Status**: ⚠️ Rollback Required

---

## Issue Summary

**Problem**: After deploying ARCH-20251017-001 to test environment, the login endpoint fails with HTTP 500.

**Evidence**:
- ✅ GET /login works (page loads)
- ❌ POST /web/login fails (500 Internal Server Error)
- ✅ Container running and healthy
- ✅ Database connected (13 glass materials found)
- ✅ Local Docker environment works perfectly

**Root Cause Hypothesis**: Database schema mismatch between test environment and code expectations.

---

## Rollback Steps (MANUAL - SSH Unstable)

Due to SSH connection instability, these steps need to be executed manually on the droplet.

### Step 1: SSH to Droplet

```bash
ssh root@159.65.174.94
```

### Step 2: Navigate to Test Environment

```bash
cd /home/ventanas/app-test
pwd  # Verify: /home/ventanas/app-test
```

### Step 3: Check Current Branch

```bash
git branch --show-current
git log --oneline | head -5
```

Expected output: `arch/glass-selection-database-20251017`

### Step 4: Rollback to Main Branch

```bash
git checkout main
git pull origin main  # Ensure latest main
```

### Step 5: Restart Application

```bash
docker-compose -f docker-compose.test.yml restart app
```

### Step 6: Wait for Startup (30 seconds)

```bash
sleep 30
docker logs ventanas-test-app --tail 20
```

Look for: `Application startup complete.`

### Step 7: Verify Login Works

```bash
# Test GET /login
curl -s http://localhost:8001/login | grep -o "Sistema de Cotización"
# Expected: "Sistema de Cotización"

# Test POST /web/login
curl -X POST http://localhost:8001/web/login \
  -d "email=admin@test.com&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -v 2>&1 | grep "HTTP"
# Expected: "HTTP/1.1 302 Found" (redirect to dashboard)
```

---

## Investigation Steps (After Rollback)

### Step 1: Compare Database Schemas

**Export Test DB Schema:**
```bash
docker exec ventanas-test-db pg_dump -U ventanas_user -d ventanas_test_db --schema-only > /tmp/test-schema.sql
```

**Check Critical Tables:**
```bash
# Check user_sessions table
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "\d user_sessions"

# Check app_materials table
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "\d app_materials"

# Check if glass material codes exist
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "SELECT code FROM app_materials WHERE category = 'Vidrio' LIMIT 5;"
```

**Expected user_sessions columns:**
- id (uuid)
- token (text)
- user_id (uuid)
- created_at (timestamp)
- expires_at (timestamp)
- is_active (boolean)

**Expected app_materials columns:**
- id (bigint)
- name (text)
- code (text) ← **CRITICAL: Added in ARCH-20251007-001**
- unit (text)
- category (text)
- cost_per_unit (numeric)
- selling_unit_length_m (numeric)
- description (text)
- created_at (timestamp)
- updated_at (timestamp)
- is_active (boolean)

### Step 2: Check for Missing Migrations

**Check if ARCH-20251007-001 was deployed to test:**
```bash
# Check git history
cd /home/ventanas/app-test
git log --oneline --all | grep -E "ARCH-20251007|glass.*pricing"

# Check if migration files exist
ls -la alembic/versions/ | grep glass
```

**Check if material codes are populated:**
```bash
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "
SELECT COUNT(*) as total_materials,
       COUNT(code) as materials_with_code,
       COUNT(*) - COUNT(code) as materials_without_code
FROM app_materials;"
```

Expected: All materials should have codes.

### Step 3: Identify Missing Changes

**Compare branches:**
```bash
cd /home/ventanas/app-test

# Show differences between main and feature branch
git diff main..arch/glass-selection-database-20251017 --stat

# Check specific files
git diff main..arch/glass-selection-database-20251017 database.py
git diff main..arch/glass-selection-database-20251017 services/product_bom_service_db.py
```

---

## Fix Plan (After Investigation)

### Option A: Apply Missing ARCH-20251007-001 Changes

If test DB is missing ARCH-20251007-001 schema:

```bash
# 1. Checkout ARCH-20251007-001 branch (if it exists)
git checkout arch/glass-pricing-database-20251007

# 2. Run migrations (if Alembic is used)
docker exec ventanas-test-app alembic upgrade head

# OR manually add missing columns:
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "
ALTER TABLE app_materials ADD COLUMN IF NOT EXISTS code TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_materials_code ON app_materials(code);
"

# 3. Populate material codes
docker exec ventanas-test-app python -c "
from database import SessionLocal
from services.product_bom_service_db import initialize_sample_data
db = SessionLocal()
initialize_sample_data(db)
db.close()
"

# 4. Verify codes populated
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db -c "
SELECT code, name FROM app_materials WHERE category = 'Vidrio' LIMIT 5;
"
```

### Option B: Fresh Database with All Migrations

If schema is too diverged:

```bash
# 1. Backup current database
docker exec ventanas-test-db pg_dump -U ventanas_user -d ventanas_test_db > /tmp/backup-$(date +%Y%m%d-%H%M%S).sql

# 2. Drop and recreate database
docker exec ventanas-test-db psql -U ventanas_user -c "DROP DATABASE IF EXISTS ventanas_test_db;"
docker exec ventanas-test-db psql -U ventanas_user -c "CREATE DATABASE ventanas_test_db;"

# 3. Run migrations from scratch
docker exec ventanas-test-app alembic upgrade head

# OR initialize via code
docker exec ventanas-test-app python -c "
from database import Base, engine, SessionLocal
from services.product_bom_service_db import initialize_sample_data

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize sample data
db = SessionLocal()
initialize_sample_data(db)
db.close()
print('Database initialized successfully')
"
```

---

## Re-Deployment After Fix

Once database schema is corrected:

```bash
# 1. Verify main branch works
curl -X POST http://localhost:8001/web/login \
  -d "email=admin@test.com&password=admin123" \
  -v 2>&1 | grep "302"

# 2. Checkout feature branch
git checkout arch/glass-selection-database-20251017
git pull origin arch/glass-selection-database-20251017

# 3. Rebuild container
docker-compose -f docker-compose.test.yml down
docker-compose -f docker-compose.test.yml build --no-cache app
docker-compose -f docker-compose.test.yml up -d

# 4. Verify login works
sleep 30
curl -X POST http://localhost:8001/web/login \
  -d "email=admin@test.com&password=admin123" \
  -v 2>&1 | grep "302"

# 5. Test glass dropdown
# Open browser: http://159.65.174.94:8001/quotes/new
# Verify: Glass dropdown shows database materials
```

---

## Logs to Collect

```bash
# Application logs
docker logs ventanas-test-app --tail 200 > /tmp/app-logs-error.txt

# Database logs
docker logs ventanas-test-db --tail 100 > /tmp/db-logs.txt

# Container status
docker ps -a > /tmp/container-status.txt

# Git status
cd /home/ventanas/app-test
git status > /tmp/git-status.txt
git log --oneline | head -20 > /tmp/git-log.txt
```

---

## Prevention: Pre-Deployment Checklist

For future deployments:

1. [ ] Verify dependency branches are deployed first
2. [ ] Check database schema matches code expectations
3. [ ] Run migrations in test environment before code deployment
4. [ ] Test critical endpoints (login, main functionality) immediately after deployment
5. [ ] Have rollback plan ready before deploying
6. [ ] Monitor logs for first 5 minutes after deployment

---

## Status

- [x] Issue identified: POST /web/login 500 error
- [ ] Rollback to main branch (MANUAL - SSH unstable)
- [ ] Database schema comparison
- [ ] Root cause identified
- [ ] Fix applied
- [ ] Feature branch re-deployed
- [ ] Verification complete

---

**Created**: 2025-10-27
**Last Updated**: 2025-10-27
**Next Action**: Manual rollback via SSH (steps above)
