# Lessons Learned: Test Environment Setup & Debugging
**Date:** September 30, 2025
**Sprint:** TASK-003 Route Extraction Deployment
**Environment:** Test Environment (port 8001)

---

## Executive Summary

During the deployment and testing of TASK-003 (work order and material routes extraction), we encountered multiple issues that revealed critical insights about environment configuration, Docker containerization, and database management. This document captures those lessons to prevent similar issues in the future.

---

## Issue 1: Color Dropdown Not Displaying Options

### Problem Statement
After deploying to test environment, the color dropdown in the quote form appeared empty despite materials and colors existing in the database.

### Root Causes Identified

#### 1. Missing `has_colors` Flag in API Response
**Location:** `app/routes/materials.py:316-340`

**Issue:** Frontend JavaScript filtered materials using `m.has_colors` flag, but backend API didn't return this field.

```javascript
// Frontend code in new_quote.html:490
const profilesWithColors = data.categories.Perfiles.filter(
    m => m.has_colors && m.colors.length > 0
);
```

**Backend response was missing:**
```python
"has_colors": len(material_data["colors"]) > 0
```

**Lesson Learned:** Always verify that backend API responses match frontend expectations. Document API contracts clearly.

#### 2. Incorrect Database Model Attributes
**Location:** `app/routes/materials.py:318-322`

**Issue:** Route used wrong attribute names from old database schema:
- ❌ `material.product_code` → ✅ `material.code`
- ❌ `material.material_type` → ✅ `material.unit`
- ❌ `material.unit_price` → ✅ `material.cost_per_unit`
- ❌ `material.selling_unit` → ✅ `material.selling_unit_length_m`

**Error:**
```
AttributeError: 'AppMaterial' object has no attribute 'product_code'
```

**Lesson Learned:** When extracting routes from monolithic `main.py`, verify that attribute names match the current database schema. Old code may reference deprecated fields.

#### 3. Incomplete Material-Color Relationships
**Location:** Database `material_colors` table

**Issue:** Only 8 out of 126 profile materials had color assignments in production database.

**Discovery Process:**
```sql
-- Query to find materials without colors
SELECT m.id, m.name, COUNT(mc.color_id) as color_count
FROM app_materials m
LEFT JOIN material_colors mc ON m.id = mc.material_id
WHERE m.category = 'Perfiles'
GROUP BY m.id, m.name
ORDER BY m.id;

-- Result: 118 profiles had color_count = 0
```

**Lesson Learned:** Data integrity issues in production won't be discovered until thorough testing. Implement database constraints or validation to ensure critical relationships exist.

---

## Issue 2: Login Returning Internal Server Error (500)

### Problem Statement
After fresh database migration, login attempts resulted in HTTP 500 errors with cryptic middleware exceptions.

### Root Cause
**Location:** `/home/ventanas/app-test/.env`

**Issue:** The `.env` file contained incorrect database name:
```bash
# WRONG
DATABASE_URL=postgresql://ventanas_user:simple123@postgres:5432/ventanas_beta_db

# CORRECT
DATABASE_URL=postgresql://ventanas_user:simple123@postgres:5432/ventanas_test_db
```

**Why This Happened:**
1. The `.env` file was copied from production setup
2. Docker `COPY . .` command included `.env` file in image
3. Environment variables in `.env` file override `docker-compose.yml` variables
4. App tried connecting to `ventanas_beta_db` which doesn't exist in test container

**Error in Logs:**
```
psycopg2.OperationalError: connection to server at "postgres" (172.21.0.3),
port 5432 failed: FATAL: database "ventanas_beta_db" does not exist
```

### Debugging Process That Led to Discovery

1. **Initial Error:** Generic 500 Internal Server Error on login
2. **Docker logs:** Showed middleware exceptions but not root cause
3. **Checked application logs:**
   ```bash
   tail -200 /home/ventanas/app-test/logs/test/error.log
   ```
4. **Found database connection error** in detailed traceback
5. **Verified container env vars:**
   ```bash
   docker exec ventanas-test-app env | grep DATABASE
   ```
   Showed correct `ventanas_test_db` ✓
6. **Checked .env file:**
   ```bash
   cat /home/ventanas/app-test/.env | grep DATABASE
   ```
   Found incorrect `ventanas_beta_db` ✗

### Lesson Learned

**Critical:** Environment variable precedence in Docker containers:
1. Container `.env` file (highest priority - **this caught us**)
2. `docker-compose.yml` environment section
3. Dockerfile ENV directives
4. System environment variables (lowest priority)

**Best Practice:** Test and production environments must have separate, explicitly managed `.env` files that are NOT copied into Docker images.

---

## Issue 3: Stale Database State After Failed Deployments

### Problem Statement
After multiple deployment attempts, database was in inconsistent state with missing tables, causing cryptic errors.

### Root Cause
Previous failed deployments left the database in partial states without proper cleanup.

### Solution Applied
Performed complete database refresh:
1. Backed up production database
2. Dropped test database completely
3. Recreated fresh test database
4. Restored production backup

```bash
# Backup production
docker exec ventanas-beta-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD \
  pg_dump -U $POSTGRES_USER -d ventanas_beta_db --clean --if-exists' \
  > production_backup.sql

# Drop and recreate test DB
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD \
  psql -U $POSTGRES_USER -d postgres -c "DROP DATABASE IF EXISTS ventanas_test_db;"'

docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD \
  psql -U $POSTGRES_USER -d postgres -c "CREATE DATABASE ventanas_test_db;"'

# Restore backup
cat production_backup.sql | docker exec -i ventanas-test-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db'
```

### Lesson Learned
Always start with a clean database state when debugging deployment issues. Don't attempt incremental fixes on corrupted database state.

---

## Issue 4: Difficulty Identifying Root Cause from Generic Errors

### Problem
- Frontend showed generic "Internal Server Error"
- Docker logs showed middleware stack traces without actual error
- Initial debugging focused on wrong areas (auth, routes)

### What Worked
1. **Application log files** provided detailed tracebacks
2. **Grepping for specific patterns** in large log files
3. **Reproducing errors with curl** to see exact HTTP responses
4. **Checking multiple sources:**
   - Docker container logs
   - Application log files (`/home/ventanas/app-test/logs/test/`)
   - Database logs
   - Environment variable inspection

### Lesson Learned
**Debugging Hierarchy for Production/Test Issues:**
1. ✅ Check application log files first (`error.log`, `application.log`)
2. ✅ Verify environment variables in running container
3. ✅ Check database connectivity and schema
4. ✅ Review recent code changes in deployed branch
5. ✅ Reproduce with minimal curl commands
6. ✅ Check Docker container health and resource usage

---

## Critical Insights for Future Deployments

### 1. Environment Configuration
- **Never share `.env` files** between production and test
- **Explicitly set environment** in docker-compose files
- **Add `.env` to `.dockerignore`** to prevent copying into images
- **Use environment-specific docker-compose files** (✅ we have this)

### 2. Database Management
- **Always backup before major changes**
- **Verify data relationships** after migrations
- **Use database constraints** to enforce data integrity
- **Document expected database state** for each environment

### 3. API Contract Management
- **Document API response schemas** explicitly
- **Keep frontend/backend in sync** during refactoring
- **Add API response validation tests**
- **Version API responses** when making breaking changes

### 4. Code Extraction Best Practices
When extracting routes from monolithic code:
- ✅ Verify all imports are correct
- ✅ Check attribute names match current models
- ✅ Test extracted routes in isolation first
- ✅ Verify database dependency injection works
- ✅ Don't assume old code matches current schema

### 5. Debugging Workflow
Established efficient debugging workflow:
```
1. Check application logs first (most detailed)
2. Verify environment configuration
3. Test database connectivity
4. Reproduce with curl/minimal request
5. Check recent code changes
6. Review middleware stack traces last (often misleading)
```

---

## Preventive Measures Implemented

### 1. Test Environment Checklist (Created)
See: `docs/TEST-ENVIRONMENT-GUIDE.md`

### 2. Code Fixes Applied
- ✅ Fixed attribute names in `app/routes/materials.py`
- ✅ Added `has_colors` flag to API response
- ✅ Corrected `.env` file for test environment
- ✅ Documented test environment interaction

### 3. Documentation Created
- ✅ This lessons learned document
- ✅ Test environment interaction guide
- ✅ Troubleshooting procedures
- ✅ Common error patterns reference

---

## Metrics

### Time Investment
- **Issue Discovery:** 15 minutes
- **Initial Debugging:** 45 minutes
- **Root Cause Identification:** 30 minutes
- **Fix Implementation:** 20 minutes
- **Verification & Testing:** 15 minutes
- **Documentation:** 30 minutes
- **Total:** ~2.5 hours

### Issues Resolved
1. Color dropdown API contract mismatch
2. Database attribute name errors
3. Environment configuration error
4. Data migration state management

### Technical Debt Addressed
- Incomplete material-color relationships (identified but not fixed in prod)
- Lack of test environment documentation
- Missing API contract specifications
- Unclear environment variable precedence

---

## Recommendations

### Immediate Actions
1. ✅ Document test environment procedures (this document)
2. ⚠️ Add missing color relationships to production database
3. ⚠️ Create API response schema documentation
4. ⚠️ Add `.env` to `.dockerignore`

### Short-term Improvements
1. Add integration tests for API contracts
2. Implement database seed scripts for test data
3. Create health check endpoint for database connectivity
4. Add environment variable validation on startup

### Long-term Improvements
1. Implement automated test environment provisioning
2. Add API versioning strategy
3. Create database migration testing framework
4. Implement automated regression testing suite

---

## Conclusion

The issues encountered during test environment setup revealed important gaps in our deployment and debugging processes. The most critical lessons were:

1. **Environment variables in `.env` files override docker-compose settings**
2. **Application log files are more valuable than Docker logs for debugging**
3. **Data relationships must be verified after migrations**
4. **API contracts must be explicitly documented and validated**

These lessons have been translated into concrete documentation and procedures to prevent similar issues in future deployments.

---

## Related Documents
- `docs/TEST-ENVIRONMENT-GUIDE.md` - Test environment interaction guide
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `TASK-003-DEPLOYMENT-BLOCKER.md` - Original deployment documentation

## Contributors
- Claude Code (Analysis & Documentation)
- Rafael Lang (Issue Reporting & Verification)

**Status:** ✅ Complete
**Next Review:** Before next major deployment
