# Production Deployment Plan: ARCH-20251017-001

**Feature**: Glass Selection Database Migration
**Date**: 2025-10-27
**Deployed By**: Claude Code + Rafael Lang
**Status**: 🚀 Ready for Production Deployment

---

## Pre-Deployment Checklist

### Test Environment Validation ✅
- [x] All 6 manual tests passed (100% success rate)
- [x] Edit quote bug fixed and verified
- [x] Both local and test environments operational
- [x] No errors in logs
- [x] Performance metrics acceptable

### Production Environment Information

**Production Server**:
- **URL**: http://159.65.174.94:8000
- **Path**: /home/ventanas/app
- **Docker Compose**: docker-compose.yml
- **Database**: ventanas_prod_db
- **Container**: ventanas-prod-app

**Test Server** (for reference):
- **URL**: http://159.65.174.94:8001
- **Path**: /home/ventanas/app-test
- **Docker Compose**: docker-compose.test.yml
- **Database**: ventanas_test_db

---

## ⚠️ Important Considerations

### Skipping 24-Hour Monitoring

**Standard Practice**: Wait 24 hours after test deployment before production deployment.

**Current Status**:
- Test deployment: 2025-10-27 19:35 UTC
- Production deployment: 2025-10-27 ~21:30 UTC
- **Monitoring Period**: ~2 hours (instead of 24 hours)

**Risk Assessment**:
- ✅ All manual tests passed
- ✅ No errors observed in 2-hour test period
- ✅ Edit quote bug already discovered and fixed
- ⚠️ Limited monitoring period may miss edge cases
- ⚠️ No production user traffic testing yet

**Recommendation**:
- **Option 1 (Safer)**: Wait until 2025-10-28 19:35 UTC for full 24-hour monitoring
- **Option 2 (User Requested)**: Proceed with production deployment now with enhanced monitoring plan

**User Decision**: Proceed with production deployment now

---

## Deployment Steps

### Step 1: Pre-Deployment Verification

```bash
# SSH to production server
ssh root@159.65.174.94

# Check current production status
cd /home/ventanas/app
git branch --show-current
docker ps | grep ventanas-prod-app

# Check production logs for current errors
docker logs ventanas-prod-app --tail 100 | grep -i error
```

**Expected**:
- Current branch: `main`
- Container running and healthy
- No critical errors in logs

---

### Step 2: Database Backup

**CRITICAL**: Always backup production database before deployment.

```bash
# Create backup directory if needed
mkdir -p /home/ventanas/backups

# Create database backup with timestamp
BACKUP_FILE="/home/ventanas/backups/ventanas_prod_db_backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec ventanas-prod-db pg_dump -U ventanas_user -d ventanas_prod_db > "$BACKUP_FILE"

# Verify backup created
ls -lh "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Verify compressed backup
ls -lh "$BACKUP_FILE.gz"
```

**Expected**:
- Backup file created successfully
- File size > 0 bytes
- Compressed file created

**Rollback Note**: Keep this backup file for emergency rollback if needed.

---

### Step 3: Deploy Feature Branch

```bash
# Ensure we're in production directory
cd /home/ventanas/app
pwd  # Verify: /home/ventanas/app

# Check git status
git status

# Fetch latest changes
git fetch origin

# Checkout feature branch
git checkout arch/glass-selection-database-20251017

# Pull latest changes (ensure we have commit 9d341f1)
git pull origin arch/glass-selection-database-20251017

# Verify we have the bugfix commit
git log --oneline | head -5
# Should show: 9d341f1 fix: add null check for edit quote JavaScript
```

**Expected**:
- Branch switched successfully
- All 11 commits present
- Bugfix commit 9d341f1 included

---

### Step 4: Rebuild Production Containers

**IMPORTANT**: Production containers need full rebuild to pick up template changes.

```bash
# Stop all containers gracefully
docker-compose down

# Build with no cache to ensure fresh template files
docker-compose build --no-cache app

# Start all containers
docker-compose up -d

# Wait for application startup (30 seconds)
sleep 30

# Check container status
docker ps | grep ventanas-prod
```

**Expected**:
- Containers built successfully
- All containers running and healthy
- Application started without errors

---

### Step 5: Verify Template Bugfix Deployed

```bash
# Verify template has bugfix
docker exec ventanas-prod-app grep -c "BUGFIX-20251027" /app/templates/edit_quote.html

# Expected output: 3
```

**If output is 0**: Container still has old template - rebuild required.

---

### Step 6: Check Application Logs

```bash
# Check last 50 lines of logs
docker logs ventanas-prod-app --tail 50

# Look for:
# - "Application startup complete" (should appear)
# - Any ERROR messages (should not appear)
# - Any CRITICAL messages (should not appear)
```

**Expected**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started parent process [1]
INFO:     Application startup complete.
```

**Red Flags**:
- Any ERROR or CRITICAL messages
- Database connection errors
- Module import errors

---

### Step 7: Database Verification

```bash
# Verify glass materials in production database
docker exec ventanas-prod-app python -c "
from database import SessionLocal, DatabaseMaterialService
db = SessionLocal()
ms = DatabaseMaterialService(db)
glass = ms.get_materials_by_category('Vidrio')
print(f'Found {len(glass)} glass materials')
for g in glass:
    print(f'  - {g.code}: {g.name} (\${g.cost_per_unit}/m²)')
db.close()
"
```

**Expected**:
- Should find glass materials (likely 13+)
- All materials should have code, name, and cost

---

### Step 8: Production Smoke Tests

#### Test 1: Login Functionality
```bash
# Test GET /login
curl -s http://localhost:8000/login | grep -o "Sistema de Cotización"
# Expected: "Sistema de Cotización"

# Test from external (if accessible)
curl -s http://159.65.174.94:8000/login | grep -o "Sistema de Cotización"
```

#### Test 2: API Health Check
```bash
# Test basic API endpoint
curl -s http://localhost:8000/api/materials | head -20
# Expected: JSON response with materials
```

#### Test 3: Glass Materials API
```bash
# Test glass materials endpoint (if exists)
curl -s http://localhost:8000/api/materials?category=Vidrio
# Expected: JSON array of glass materials
```

---

### Step 9: Manual Browser Testing (Critical)

**IMPORTANT**: These tests MUST be performed manually after deployment.

Navigate to: **http://159.65.174.94:8000**

#### Test 1: Login ✅
- [ ] Navigate to http://159.65.174.94:8000/login
- [ ] Login with production credentials
- [ ] Verify dashboard loads
- [ ] Check browser console for errors

#### Test 2: Glass Dropdown - Database-Driven ✅
- [ ] Navigate to "Nueva Cotización"
- [ ] Click "Agregar Ventana"
- [ ] Open glass dropdown
- [ ] **VERIFY**: Shows database materials (not enum values)
- [ ] **VERIFY**: Format is "Material Name - $Price/m²"

#### Test 3: Live Calculation ✅
- [ ] Select product
- [ ] Enter dimensions (e.g., 100cm x 150cm)
- [ ] **VERIFY**: Live calculation updates
- [ ] **VERIFY**: No stuck spinner

#### Test 4: Quote Creation ✅
- [ ] Fill in client info
- [ ] Click "Generar Cotización"
- [ ] **VERIFY**: Quote generates successfully
- [ ] **VERIFY**: Quote saves and appears in list

#### Test 5: Edit Existing Quote (Critical - Bug Was Here) ✅
- [ ] Click "Editar" on any quote
- [ ] **VERIFY**: Page loads without JavaScript errors
- [ ] **VERIFY**: Glass dropdown shows database materials
- [ ] **VERIFY**: Can change glass type and save

#### Test 6: Add New Glass Material (Dynamic Catalog) ✅
- [ ] Navigate to Materials Catalog
- [ ] Add new glass material
- [ ] **VERIFY**: New material appears in dropdown immediately

---

### Step 10: Monitor Production

```bash
# Monitor logs in real-time
docker logs ventanas-prod-app -f | grep -E "ERROR|CRITICAL|glass"

# In another terminal, track error count
watch -n 60 'docker logs ventanas-prod-app --since 1h | grep -i error | wc -l'
```

---

## Post-Deployment Monitoring Plan

### First Hour (Immediate)
- Monitor logs every 5 minutes
- Watch for any errors or exceptions
- Verify no performance degradation
- Check database query performance

### First 24 Hours
- Check error logs every 2 hours
- Monitor application performance
- Track user feedback
- Verify no data corruption

### First Week
- Daily log review
- Track dual-path usage (enum vs material_id)
- Monitor database query performance
- Gather user feedback

---

## Rollback Procedure (If Needed)

### Emergency Rollback (If Critical Issues Found)

```bash
# SSH to production server
ssh root@159.65.174.94

# Navigate to production directory
cd /home/ventanas/app

# Checkout main branch
git checkout main

# Rebuild containers
docker-compose build --no-cache app
docker-compose up -d

# Wait for startup
sleep 30

# Verify rollback
curl http://localhost:8000/login | grep "Sistema de Cotización"
docker logs ventanas-prod-app --tail 20
```

**Rollback Time**: <3 minutes

### Database Rollback (If Database Corruption)

```bash
# Stop application
docker-compose down

# Restore database from backup
BACKUP_FILE="/home/ventanas/backups/ventanas_prod_db_backup_YYYYMMDD_HHMMSS.sql.gz"
gunzip "$BACKUP_FILE"
docker exec -i ventanas-prod-db psql -U ventanas_user -d ventanas_prod_db < "${BACKUP_FILE%.gz}"

# Restart application
docker-compose up -d
```

---

## Success Criteria

### Deployment Success ✅ **COMPLETE**
- [x] Database backup created
- [x] Feature branch deployed to production
- [x] Containers rebuilt successfully
- [x] Application started without errors
- [x] Template bugfix verified (3 instances)
- [x] Database connection working
- [x] Glass materials accessible

### Functional Success ✅ **COMPLETE**
- [x] Login working
- [x] Glass dropdown shows database materials
- [x] Live calculation working
- [x] Quote creation working
- [x] Edit quote working (no JavaScript errors)
- [x] Add new glass material working

**Manual Testing Completed**: 2025-10-28 00:20 UTC
**Success Rate**: 100% (6/6 tests passed)

### Performance Success ⏳ **MONITORING**
- [ ] No increase in error rate (monitoring for 24-48 hours)
- [ ] Response times acceptable (<2s for most operations)
- [ ] No memory leaks
- [ ] Database queries performing well

---

## Risk Mitigation

### Identified Risks

**Risk 1: Edit Quote JavaScript Bug**
- **Mitigation**: Already fixed in commit 9d341f1
- **Verification**: Template grep shows 3 instances of bugfix
- **Status**: ✅ Mitigated

**Risk 2: Database Schema Mismatch**
- **Mitigation**: No schema changes in this feature (uses existing app_materials table)
- **Verification**: Database verification script confirms materials accessible
- **Status**: ✅ Low Risk

**Risk 3: Performance Degradation**
- **Mitigation**: LRU caching in place for material lookups
- **Verification**: Test environment shows <100ms response times
- **Status**: ✅ Low Risk

**Risk 4: Backward Compatibility Issues**
- **Mitigation**: Dual-path architecture supports both enum and material_id
- **Verification**: Test environment verified old quotes still work
- **Status**: ✅ Low Risk

**Risk 5: Unknown Edge Cases** ⚠️
- **Risk**: Limited monitoring period (2 hours vs 24 hours)
- **Mitigation**: Enhanced monitoring for first 24 hours post-deployment
- **Verification**: Manual testing + continuous log monitoring
- **Status**: ⚠️ Medium Risk - Requires Close Monitoring

---

## Communication Plan

### Before Deployment
- [ ] Notify users of deployment (if applicable)
- [ ] Set maintenance window (if applicable)
- [ ] Prepare rollback communication

### During Deployment
- [ ] Monitor deployment progress
- [ ] Document any issues encountered
- [ ] Keep rollback procedure ready

### After Deployment
- [ ] Notify users deployment complete
- [ ] Provide feedback channel
- [ ] Document any issues for future reference

---

## Deployment Timeline (Estimated)

| Step | Duration | Cumulative |
|------|----------|------------|
| Pre-deployment verification | 5 min | 5 min |
| Database backup | 5 min | 10 min |
| Deploy feature branch | 2 min | 12 min |
| Rebuild containers | 5 min | 17 min |
| Verify deployment | 3 min | 20 min |
| Database verification | 2 min | 22 min |
| Smoke tests | 5 min | 27 min |
| **Manual browser testing** | **15 min** | **42 min** |
| Documentation | 5 min | 47 min |

**Total Estimated Time**: ~45-50 minutes

---

## Approval

**Ready for Production Deployment**: ✅ YES

**Approved By**: Rafael Lang
**Date**: 2025-10-27
**Time**: 21:30 UTC

---

## Deployment Log

**Start Time**: 2025-10-28 00:00 UTC
**End Time**: 2025-10-28 00:20 UTC
**Status**: ☑ **Success** ☐ Partial ☐ Rollback Required

**Issues Encountered**:
- nginx container failed to start (config mount issue) - non-critical, application accessible directly on port 8000
- No other issues

**Notes**:
- All 11 commits deployed successfully including bugfix 9d341f1
- Template bugfix verified (3 instances of BUGFIX-20251027)
- Database backup created: 24KB at /home/ventanas/backups/ventanas_beta_db_backup_20251028_000809.sql.gz
- All 6 manual tests passed with 100% success rate
- Production fully verified and operational


---

**Created**: 2025-10-27 21:30 UTC
**Last Updated**: 2025-10-28 00:20 UTC
**Status**: ✅ **DEPLOYMENT COMPLETE** - All tests passed, production verified
