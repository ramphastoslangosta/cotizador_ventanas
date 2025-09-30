# Test Environment Interaction Guide
**Version:** 1.0
**Last Updated:** September 30, 2025
**Maintainer:** Development Team

---

## Table of Contents
1. [Environment Overview](#environment-overview)
2. [Access & Authentication](#access--authentication)
3. [Common Operations](#common-operations)
4. [Deployment Procedures](#deployment-procedures)
5. [Database Management](#database-management)
6. [Debugging & Troubleshooting](#debugging--troubleshooting)
7. [Best Practices](#best-practices)

---

## Environment Overview

### Test Environment Details
- **URL:** http://159.65.174.94:8001
- **Purpose:** Pre-production testing and validation
- **Database:** `ventanas_test_db` (PostgreSQL 15)
- **Redis:** Port 6380
- **Docker Compose File:** `docker-compose.test.yml`
- **Application Path:** `/home/ventanas/app-test/`
- **Logs Path:** `/home/ventanas/app-test/logs/test/`

### Container Names
```
ventanas-test-app      - FastAPI application (port 8001)
ventanas-test-db       - PostgreSQL database (port 5433)
ventanas-test-redis    - Redis cache (port 6380)
```

### Git Branch
- **Current Branch:** `refactor/workorder-material-routes-20250929`
- **Tracking:** `origin/refactor/workorder-material-routes-20250929`

---

## Access & Authentication

### SSH Access to Server
```bash
ssh root@159.65.174.94
```

### Test User Accounts
Production users are available in test environment after data migration:

```
Email: admin@test.com
Password: admin123
```

(Note: Use actual production credentials after migration)

### Accessing Test Application
```bash
# Via browser
http://159.65.174.94:8001

# Via curl (from server)
curl http://localhost:8001

# Via curl (with authentication)
curl -X POST http://localhost:8001/web/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'email=admin@test.com&password=admin123'
```

---

## Common Operations

### 1. Checking Environment Status

#### Check All Containers
```bash
ssh root@159.65.174.94 "docker ps -a | grep ventanas-test"
```

Expected output:
```
ventanas-test-app    Up X hours (healthy)    0.0.0.0:8001->8000/tcp
ventanas-test-db     Up X hours (healthy)    0.0.0.0:5433->5432/tcp
ventanas-test-redis  Up X hours (healthy)    0.0.0.0:6380->6379/tcp
```

#### Check Container Health
```bash
ssh root@159.65.174.94 "docker inspect ventanas-test-app | grep -A 5 Health"
```

#### Check Application Logs
```bash
# Live logs (follow mode)
ssh root@159.65.174.94 "docker logs -f ventanas-test-app"

# Last 50 lines
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 50"

# Errors only
ssh root@159.65.174.94 "docker logs ventanas-test-app 2>&1 | grep -i error"
```

#### Check Application Log Files
```bash
# Error log
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/error.log"

# Application log
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/application.log"

# Database log
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/database.log"

# Security log
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/security.log"
```

### 2. Restarting Services

#### Restart Application Only
```bash
ssh root@159.65.174.94 "docker restart ventanas-test-app"
```

#### Restart All Test Containers
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml restart"
```

#### Full Restart (Stop → Start)
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml down && \
  docker-compose -f docker-compose.test.yml up -d"
```

### 3. Viewing Environment Variables

#### Check Docker Compose Config
```bash
ssh root@159.65.174.94 "cat /home/ventanas/app-test/docker-compose.test.yml | grep -A 10 environment"
```

#### Check Container Environment Variables
```bash
# All environment variables
ssh root@159.65.174.94 "docker exec ventanas-test-app env"

# Database related
ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep DATABASE"

# Redis related
ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep REDIS"
```

#### Check .env File
```bash
ssh root@159.65.174.94 "cat /home/ventanas/app-test/.env"
```

⚠️ **IMPORTANT:** The `.env` file should contain test-specific values:
```bash
DATABASE_URL=postgresql://ventanas_user:simple123@postgres:5432/ventanas_test_db
```

### 4. Checking Git Status

#### Current Branch and Status
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && git status"
```

#### Recent Commits
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && git log --oneline -5"
```

#### Check for Uncommitted Changes
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && git diff"
```

---

## Deployment Procedures

### Standard Deployment Workflow

#### 1. Commit and Push Changes Locally
```bash
# On local machine
git add <files>
git commit -m "Your commit message"
git push origin refactor/workorder-material-routes-20250929
```

#### 2. Pull Changes on Test Server
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git fetch origin && \
  git pull origin refactor/workorder-material-routes-20250929"
```

#### 3. Rebuild Docker Image
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build app"
```

#### 4. Restart Application
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml up -d app"
```

#### 5. Verify Deployment
```bash
# Check container started
ssh root@159.65.174.94 "docker ps | grep ventanas-test-app"

# Check logs for errors
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 30"

# Test application responds
ssh root@159.65.174.94 "curl -I http://localhost:8001"
```

### Quick Deployment (All Steps Combined)
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git pull origin refactor/workorder-material-routes-20250929 && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app && \
  sleep 5 && \
  docker logs ventanas-test-app --tail 20"
```

### Rolling Back Deployment

#### Rollback to Previous Commit
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git log --oneline -5"  # Find commit hash to rollback to

ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git reset --hard <commit-hash> && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"
```

---

## Database Management

### Accessing the Database

#### Using psql Interactive Shell
```bash
ssh root@159.65.174.94 "docker exec -it ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db'"
```

#### Running SQL Queries
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db \
  -c \"SELECT * FROM users LIMIT 5;\"'"
```

### Common Database Queries

#### Check Table Counts
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db -c \
  \"SELECT \\\"Users\\\" as table_name, COUNT(*) FROM users
   UNION ALL SELECT \\\"Quotes\\\", COUNT(*) FROM quotes
   UNION ALL SELECT \\\"Work Orders\\\", COUNT(*) FROM work_orders
   UNION ALL SELECT \\\"Materials\\\", COUNT(*) FROM app_materials;\"'"
```

#### List All Tables
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db \
  -c \"\\dt\"'"
```

#### Check Database Size
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db \
  -c \"SELECT pg_size_pretty(pg_database_size(\\\"ventanas_test_db\\\"));\"'"
```

### Database Backup and Restore

#### Create Backup
```bash
# Backup production database
ssh root@159.65.174.94 "docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/production_backup_\$(date +%Y%m%d_%H%M%S).sql"

# Verify backup
ssh root@159.65.174.94 "ls -lh /tmp/production_backup_*.sql | tail -1"
```

#### Restore Backup to Test Environment
```bash
# 1. Stop test application
ssh root@159.65.174.94 "docker stop ventanas-test-app"

# 2. Drop test database
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres \
  -c \"DROP DATABASE IF EXISTS ventanas_test_db;\"'"

# 3. Create fresh database
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres \
  -c \"CREATE DATABASE ventanas_test_db;\"'"

# 4. Restore backup
ssh root@159.65.174.94 "cat /tmp/production_backup_YYYYMMDD_HHMMSS.sql | \
  docker exec -i ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db'"

# 5. Restart application
ssh root@159.65.174.94 "docker start ventanas-test-app"

# 6. Verify data
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db \
  -c \"SELECT COUNT(*) FROM users;\"'"
```

### Adding Missing Data Relationships

#### Example: Add Colors to All Profile Materials
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db -c \
  \"INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available, created_at, updated_at)
   SELECT m.id, c.id, m.cost_per_unit, true, NOW(), NOW()
   FROM app_materials m
   CROSS JOIN colors c
   WHERE m.category = \\\"Perfiles\\\"
   AND NOT EXISTS (
     SELECT 1 FROM material_colors mc
     WHERE mc.material_id = m.id AND mc.color_id = c.id
   );\"'"
```

---

## Debugging & Troubleshooting

### Debugging Checklist

When encountering issues, follow this order:

1. ✅ **Check application logs** (most detailed information)
   ```bash
   ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/error.log"
   ```

2. ✅ **Verify environment variables**
   ```bash
   ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep DATABASE"
   ssh root@159.65.174.94 "cat /home/ventanas/app-test/.env | grep DATABASE"
   ```

3. ✅ **Check database connectivity**
   ```bash
   ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
     'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -l'"
   ```

4. ✅ **Review recent code changes**
   ```bash
   ssh root@159.65.174.94 "cd /home/ventanas/app-test && git log --oneline -5"
   ```

5. ✅ **Reproduce with minimal request**
   ```bash
   ssh root@159.65.174.94 "curl -v http://localhost:8001/api/materials"
   ```

6. ✅ **Check container resources**
   ```bash
   ssh root@159.65.174.94 "docker stats ventanas-test-app --no-stream"
   ```

### Common Issues and Solutions

#### Issue: "Internal Server Error" on Login

**Symptoms:**
- HTTP 500 on `/web/login`
- Generic error message

**Check:**
```bash
# 1. Check error logs
tail -50 /home/ventanas/app-test/logs/test/error.log

# 2. Look for database connection errors
grep "database.*does not exist" /home/ventanas/app-test/logs/test/error.log

# 3. Verify DATABASE_URL
docker exec ventanas-test-app env | grep DATABASE
cat /home/ventanas/app-test/.env | grep DATABASE
```

**Solution:**
If `.env` has wrong database name, fix it:
```bash
ssh root@159.65.174.94 "sed -i 's/ventanas_beta_db/ventanas_test_db/g' \
  /home/ventanas/app-test/.env && \
  cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"
```

#### Issue: API Returns 500 with AttributeError

**Symptoms:**
- API endpoint returns 500
- Logs show `AttributeError: 'Model' object has no attribute 'field_name'`

**Check:**
```bash
# Check recent changes to route files
cd /home/ventanas/app-test && git diff HEAD~1 app/routes/
```

**Solution:**
Verify model attribute names match database schema. Check `database.py` for correct field names.

#### Issue: Empty Dropdown / Missing Data

**Symptoms:**
- Frontend dropdown shows no options
- API returns data but frontend doesn't display it

**Check:**
```bash
# 1. Test API directly
curl http://localhost:8001/api/materials/by-category

# 2. Check database for relationships
docker exec ventanas-test-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db \
  -c "SELECT COUNT(*) FROM material_colors;"'
```

**Solution:**
- Verify API response includes all required fields
- Check browser console for JavaScript errors
- Verify data relationships exist in database

#### Issue: Container Keeps Restarting

**Symptoms:**
- Container status shows "Restarting"
- Application not accessible

**Check:**
```bash
# Check container logs
docker logs ventanas-test-app --tail 100

# Check if port is already in use
netstat -tulpn | grep 8001

# Check for syntax errors in code
docker logs ventanas-test-app 2>&1 | grep "SyntaxError\|ModuleNotFoundError"
```

**Solution:**
1. Fix code errors if found
2. Check for port conflicts
3. Verify all dependencies are installed

---

## Best Practices

### 1. Environment Hygiene

✅ **DO:**
- Keep test environment in sync with production structure
- Use separate `.env` files for test and production
- Document all manual changes made to test environment
- Backup database before major changes
- Clean up test data periodically

❌ **DON'T:**
- Share `.env` files between environments
- Make manual changes without documenting them
- Leave test environment in broken state
- Test destructive operations without backup

### 2. Deployment Safety

✅ **DO:**
- Test changes in test environment first
- Verify logs after deployment
- Keep production branch separate from test branch
- Use git tags for production deployments
- Document deployment steps

❌ **DON'T:**
- Deploy directly to production without testing
- Skip verification steps
- Deploy with failing tests
- Deploy without checking logs

### 3. Database Management

✅ **DO:**
- Backup before major database changes
- Use migrations for schema changes
- Verify data integrity after migrations
- Document database changes
- Keep production data fresh in test environment

❌ **DON'T:**
- Modify database schema manually
- Skip data validation
- Keep stale test data
- Test migrations directly in production

### 4. Debugging Efficiency

✅ **DO:**
- Check application logs first
- Use curl to reproduce API issues
- Verify environment variables
- Test one change at a time
- Document solutions for common issues

❌ **DON'T:**
- Make multiple changes without testing
- Skip log analysis
- Assume environment is correct
- Debug in production first

---

## Quick Reference Commands

### Essential Commands Cheat Sheet

```bash
# Status check
ssh root@159.65.174.94 "docker ps | grep ventanas-test"

# View logs
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 50"
ssh root@159.65.174.94 "tail -50 /home/ventanas/app-test/logs/test/error.log"

# Deploy changes
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git pull && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"

# Restart app
ssh root@159.65.174.94 "docker restart ventanas-test-app"

# Database query
ssh root@159.65.174.94 "docker exec ventanas-test-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db \
  -c \"YOUR_QUERY_HERE\"'"

# Check environment
ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep DATABASE"

# Test endpoint
ssh root@159.65.174.94 "curl -I http://localhost:8001"
```

---

## Troubleshooting Flowchart

```
Issue Occurs
    ↓
Check Application Logs
    ↓
Error Found? → YES → Check Error Type
    ↓                       ↓
    NO              Database Error?
    ↓                   ↓
Verify Environment    YES → Check DATABASE_URL in .env
Variables                → Verify database exists
    ↓                    → Test connection
Check Docker Logs        ↓
    ↓                   NO
Test with curl           ↓
    ↓               API Error?
Verify Database          ↓
Connectivity          YES → Check model attributes
    ↓                   → Verify API response format
Reproduce Locally        → Check frontend expects
    ↓
Still Stuck?
    ↓
1. Document exact error
2. Check LESSONS-LEARNED doc
3. Check TROUBLESHOOTING.md
4. Seek assistance with logs
```

---

## Support & Additional Resources

### Documentation
- `LESSONS-LEARNED-TEST-ENV-20250930.md` - Detailed lessons from recent issues
- `TROUBLESHOOTING.md` - Common problems and solutions
- `CLAUDE.md` - Project architecture and guidelines

### Getting Help
1. Check this guide first
2. Review lessons learned document
3. Search application logs for similar errors
4. Document your issue with:
   - Exact error message
   - Steps to reproduce
   - Environment state (logs, env vars)
   - Recent changes made

---

## Changelog

### Version 1.0 (September 30, 2025)
- Initial creation after TASK-003 deployment issues
- Documented standard procedures
- Added debugging workflows
- Created quick reference section

---

**Document Maintained By:** Development Team
**Last Reviewed:** September 30, 2025
**Next Review:** Before next major deployment
