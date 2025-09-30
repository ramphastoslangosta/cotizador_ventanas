# Troubleshooting Guide
**Sistema de Cotización de Ventanas**
**Version:** 1.0
**Last Updated:** September 30, 2025

---

## Table of Contents
1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Common Error Patterns](#common-error-patterns)
3. [Environment-Specific Issues](#environment-specific-issues)
4. [Database Issues](#database-issues)
5. [API & Frontend Issues](#api--frontend-issues)
6. [Authentication Issues](#authentication-issues)
7. [Performance Issues](#performance-issues)
8. [Emergency Procedures](#emergency-procedures)

---

## Quick Diagnostic Commands

### First Response (Run These First)

```bash
# 1. Check if containers are running
ssh root@159.65.174.94 "docker ps | grep ventanas-test"

# 2. Check recent logs
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 50"

# 3. Check error log file
ssh root@159.65.174.94 "tail -50 /home/ventanas/app-test/logs/test/error.log"

# 4. Test if app responds
ssh root@159.65.174.94 "curl -I http://localhost:8001"

# 5. Check database connectivity
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -l'"
```

---

## Common Error Patterns

### 1. Database Connection Errors

#### Pattern: "database does not exist"
```
psycopg2.OperationalError: database "ventanas_beta_db" does not exist
```

**Root Cause:** Wrong database name in configuration

**Diagnosis:**
```bash
# Check what database app is trying to connect to
ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep DATABASE"

# Check .env file
ssh root@159.65.174.94 "cat /home/ventanas/app-test/.env | grep DATABASE"

# List available databases
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -l'"
```

**Solution:**
```bash
# Fix .env file
ssh root@159.65.174.94 "sed -i 's/ventanas_beta_db/ventanas_test_db/g' \
  /home/ventanas/app-test/.env"

# Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"
```

#### Pattern: "relation does not exist"
```
psycopg2.errors.UndefinedTable: relation "users" does not exist
```

**Root Cause:** Database schema not initialized or corrupted

**Diagnosis:**
```bash
# Check if tables exist
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"\\dt\"'"

# Count tables
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM information_schema.tables \
  WHERE table_schema = \\\"public\\\";\"'"
```

**Solution:**
Perform fresh database migration (see Database Management section)

#### Pattern: "too many connections"
```
psycopg2.OperationalError: FATAL: too many clients already
```

**Root Cause:** Database connection pool exhausted

**Diagnosis:**
```bash
# Check active connections
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT count(*) FROM pg_stat_activity;\"'"

# Check connection limit
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SHOW max_connections;\"'"
```

**Solution:**
```bash
# Restart application to release connections
ssh root@159.65.174.94 "docker restart ventanas-test-app"

# If persists, restart database
ssh root@159.65.174.94 "docker restart ventanas-test-db"
```

---

### 2. AttributeError / Model Field Errors

#### Pattern: "object has no attribute"
```
AttributeError: 'AppMaterial' object has no attribute 'product_code'
```

**Root Cause:** Code uses outdated field names

**Diagnosis:**
```bash
# Check database model definition
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  grep -A 20 'class AppMaterial' database.py"

# Check recent code changes
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git diff HEAD~5 --name-only | grep -E 'routes|database'"
```

**Solution:**
1. Identify correct field name from `database.py`
2. Update route file with correct attribute name
3. Commit and deploy fix

**Common Mappings:**
```python
# OLD → NEW
product_code → code
material_type → unit
unit_price → cost_per_unit
selling_unit → selling_unit_length_m
```

---

### 3. Internal Server Error (500)

#### Pattern: Generic 500 without details

**Diagnosis Steps:**
```bash
# 1. Check error log (most detailed)
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/error.log \
  | grep -A 30 'UNEXPECTED EXCEPTION\|Traceback'"

# 2. Check application log
ssh root@159.65.174.94 "tail -100 /home/ventanas/app-test/logs/test/application.log"

# 3. Reproduce with curl to see exact response
ssh root@159.65.174.94 "curl -v http://localhost:8001/ENDPOINT_PATH"

# 4. Check for Python syntax errors
ssh root@159.65.174.94 "docker logs ventanas-test-app 2>&1 | \
  grep -E 'SyntaxError|IndentationError|ImportError'"
```

**Common Causes:**
1. Database connection issues
2. Missing or incorrect model attributes
3. Import errors
4. Python syntax errors
5. Unhandled exceptions in route handlers

---

### 4. Frontend Issues

#### Pattern: Empty Dropdown / No Data Displayed

**Diagnosis:**
```bash
# 1. Check if API returns data
ssh root@159.65.174.94 "curl http://localhost:8001/api/materials/by-category \
  | python3 -m json.tool | head -50"

# 2. Check browser console (via browser dev tools)
# Look for JavaScript errors or failed fetch requests

# 3. Verify data exists in database
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM app_materials;\"'"

# 4. Check for missing relationships
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT m.id, m.name, COUNT(mc.color_id) as colors \
  FROM app_materials m LEFT JOIN material_colors mc ON m.id = mc.material_id \
  WHERE m.category = \\\"Perfiles\\\" GROUP BY m.id, m.name LIMIT 10;\"'"
```

**Solution Checklist:**
- [ ] API returns data (check with curl)
- [ ] Data exists in database
- [ ] Relationships exist (if dropdown depends on related data)
- [ ] API response format matches frontend expectations
- [ ] No JavaScript errors in browser console

#### Pattern: API Returns Data But Frontend Shows Error

**Common Causes:**
1. **Missing required fields** in API response
2. **Type mismatch** (string vs number, etc.)
3. **CORS issues** (if calling from different domain)
4. **Authentication issues**

**Diagnosis:**
```bash
# Check exact API response
curl -s http://159.65.174.94:8001/api/endpoint | python3 -m json.tool

# Compare with frontend expectations (check JavaScript code)
# Look for fields being accessed that might not exist
```

---

### 5. Authentication Issues

#### Pattern: Login Returns 401 Unauthorized

**Diagnosis:**
```bash
# 1. Test login endpoint
ssh root@159.65.174.94 "curl -v -X POST http://localhost:8001/web/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'email=admin@test.com&password=admin123'"

# 2. Check if user exists
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT id, email, is_active FROM users \
  WHERE email = \\\"admin@test.com\\\";\"'"

# 3. Check session table
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM user_sessions;\"'"
```

**Solutions:**
1. If user doesn't exist: Migrate production data or create test user
2. If password wrong: Reset password or use correct credentials
3. If is_active=false: Update user record

#### Pattern: Session Expires Too Quickly

**Check Configuration:**
```bash
ssh root@159.65.174.94 "docker exec ventanas-test-app env | grep SESSION"
```

**Verify:**
```python
# In config.py or .env
SESSION_EXPIRE_HOURS=8  # Should be reasonable value
```

---

### 6. Container Health Issues

#### Pattern: Container Constantly Restarting

**Diagnosis:**
```bash
# Check restart count and status
ssh root@159.65.174.94 "docker ps -a | grep ventanas-test-app"

# Check last 100 lines of logs
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 100"

# Check for specific errors
ssh root@159.65.174.94 "docker logs ventanas-test-app 2>&1 | \
  grep -E 'Error|Exception|Failed|Cannot'"

# Check container resources
ssh root@159.65.174.94 "docker stats ventanas-test-app --no-stream"
```

**Common Causes:**
1. **Application startup errors** (syntax errors, import errors)
2. **Database connection failures** (wrong credentials, database doesn't exist)
3. **Port conflicts** (port 8000 already in use)
4. **Memory issues** (container running out of memory)
5. **Missing dependencies** (requirements.txt not installed)

#### Pattern: Container Healthy But Not Responding

**Diagnosis:**
```bash
# Check if port is listening
ssh root@159.65.174.94 "netstat -tulpn | grep 8001"

# Test from inside container
ssh root@159.65.174.94 "docker exec ventanas-test-app curl -I http://localhost:8000"

# Check for worker process issues
ssh root@159.65.174.94 "docker exec ventanas-test-app ps aux"
```

**Solutions:**
1. Restart application container
2. Check nginx/reverse proxy configuration if applicable
3. Verify firewall rules

---

## Environment-Specific Issues

### Production vs Test Environment Confusion

**Symptoms:**
- Changes deployed to wrong environment
- Test data appearing in production
- Production credentials in test environment

**Prevention:**
```bash
# Always verify current environment before operations
ssh root@159.65.174.94 "docker ps | grep ventanas"

# Expected for TEST:
ventanas-test-app    # Port 8001
ventanas-test-db     # Port 5433
ventanas-test-redis  # Port 6380

# Expected for PRODUCTION:
ventanas-beta-app    # Port 8000
ventanas-beta-db     # Port 5432
ventanas-beta-redis  # Port 6379
```

**Environment Identification:**
```bash
# Check environment variable
ssh root@159.65.174.94 "docker exec CONTAINER_NAME env | grep ENVIRONMENT"

# Should show:
ENVIRONMENT=test  # for test
ENVIRONMENT=production  # for production
```

---

## Database Issues

### Complete Database Refresh Procedure

**When to Use:**
- Database schema is corrupted
- Multiple migration failures
- Need fresh production data in test
- Data integrity issues

**Procedure:**
```bash
# 1. Backup production (ALWAYS do this first)
ssh root@159.65.174.94 "docker exec ventanas-beta-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/prod_backup_\$(date +%Y%m%d_%H%M%S).sql"

# 2. Stop test application
ssh root@159.65.174.94 "docker stop ventanas-test-app"

# 3. Drop test database
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d postgres -c \"DROP DATABASE IF EXISTS ventanas_test_db;\"'"

# 4. Create fresh database
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d postgres -c \"CREATE DATABASE ventanas_test_db;\"'"

# 5. Restore backup
ssh root@159.65.174.94 "cat /tmp/prod_backup_TIMESTAMP.sql | \
  docker exec -i ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d ventanas_test_db'"

# 6. Verify restoration
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM users;\"'"

# 7. Start application
ssh root@159.65.174.94 "docker start ventanas-test-app"

# 8. Verify application works
sleep 5
ssh root@159.65.174.94 "curl -I http://localhost:8001"
```

### Fixing Missing Data Relationships

#### Colors Missing for Materials
```bash
# Check which materials are missing colors
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM app_materials m \
  WHERE m.category = \\\"Perfiles\\\" \
  AND NOT EXISTS (SELECT 1 FROM material_colors mc WHERE mc.material_id = m.id);\"'"

# Add all colors to materials missing them
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"INSERT INTO material_colors \
  (material_id, color_id, price_per_unit, is_available, created_at, updated_at) \
  SELECT m.id, c.id, m.cost_per_unit, true, NOW(), NOW() \
  FROM app_materials m CROSS JOIN colors c \
  WHERE m.category = \\\"Perfiles\\\" \
  AND NOT EXISTS (SELECT 1 FROM material_colors mc \
  WHERE mc.material_id = m.id AND mc.color_id = c.id);\"'"

# Verify
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT COUNT(*) FROM material_colors;\"'"
```

---

## API & Frontend Issues

### API Testing Checklist

```bash
# 1. Test endpoint exists
curl -I http://159.65.174.94:8001/api/endpoint

# 2. Test with authentication
curl -X POST http://159.65.174.94:8001/web/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'email=admin@test.com&password=admin123' \
  -c /tmp/cookies.txt

curl http://159.65.174.94:8001/api/endpoint -b /tmp/cookies.txt

# 3. Check response format
curl http://159.65.174.94:8001/api/endpoint | python3 -m json.tool

# 4. Check for errors in response
curl http://159.65.174.94:8001/api/endpoint 2>&1 | grep -i error
```

### Frontend Debugging

**Browser Console Checks:**
1. Open Developer Tools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed requests
4. Verify API responses in Network tab

**Common Frontend Issues:**
```javascript
// 1. Incorrect API URL
// Check: Is URL correct in fetch() calls?

// 2. Missing authentication
// Check: Are cookies/tokens being sent?

// 3. CORS errors
// Check: Is API endpoint returning correct CORS headers?

// 4. Data format mismatch
// Check: Does response format match what code expects?
```

---

## Performance Issues

### Slow Response Times

**Diagnosis:**
```bash
# 1. Check response time
time curl http://localhost:8001/api/endpoint

# 2. Check database query performance
ssh root@159.65.174.94 "docker exec ventanas-test-db \
  sh -c 'PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER \
  -d ventanas_test_db -c \"SELECT * FROM pg_stat_statements \
  ORDER BY mean_exec_time DESC LIMIT 10;\"'"

# 3. Check container resources
ssh root@159.65.174.94 "docker stats --no-stream"

# 4. Check for slow queries in logs
ssh root@159.65.174.94 "grep 'slow query' \
  /home/ventanas/app-test/logs/test/database.log"
```

**Solutions:**
1. Add database indexes for slow queries
2. Implement caching (Redis)
3. Optimize N+1 query problems
4. Increase container resources if needed

---

## Emergency Procedures

### Complete System Reset (Nuclear Option)

⚠️ **WARNING:** This will destroy all test data. Only use as last resort.

```bash
# 1. Backup everything first
ssh root@159.65.174.94 "cd /home/ventanas/app-test && tar -czf ~/app-test-backup-\$(date +%Y%m%d_%H%M%S).tar.gz ."

# 2. Stop all test containers
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml down -v"

# 3. Remove all containers and volumes
ssh root@159.65.174.94 "docker ps -a | grep ventanas-test | \
  awk '{print \$1}' | xargs docker rm -f"
ssh root@159.65.174.94 "docker volume ls | grep ventanas-test | \
  awk '{print \$2}' | xargs docker volume rm"

# 4. Pull latest code
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git fetch origin && \
  git reset --hard origin/refactor/workorder-material-routes-20250929"

# 5. Rebuild from scratch
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build --no-cache"

# 6. Start services
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml up -d"

# 7. Initialize database (follow database refresh procedure)

# 8. Verify system
ssh root@159.65.174.94 "docker ps | grep ventanas-test"
ssh root@159.65.174.94 "curl -I http://localhost:8001"
```

### Quick Restore from Production

If test environment is broken and you need it working ASAP:

```bash
# All-in-one restore script
ssh root@159.65.174.94 'bash -s' <<'EOF'
set -e
echo "🔄 Starting quick restore..."

# Backup production
echo "📦 Backing up production..."
docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' > /tmp/quick_restore.sql

# Stop test app
echo "🛑 Stopping test app..."
docker stop ventanas-test-app

# Drop and recreate database
echo "🗑️  Dropping test database..."
docker exec ventanas-test-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d postgres \
  -c "DROP DATABASE IF EXISTS ventanas_test_db;"'

echo "📝 Creating fresh database..."
docker exec ventanas-test-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d postgres \
  -c "CREATE DATABASE ventanas_test_db;"'

# Restore
echo "⬆️  Restoring backup..."
cat /tmp/quick_restore.sql | docker exec -i ventanas-test-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db'

# Start app
echo "🚀 Starting test app..."
docker start ventanas-test-app

# Wait and verify
echo "⏳ Waiting for app to start..."
sleep 5

echo "✅ Checking status..."
curl -I http://localhost:8001 2>&1 | head -1

echo "✨ Quick restore complete!"
EOF
```

---

## Getting Help

If you've exhausted all troubleshooting steps:

1. **Document the Issue:**
   - Exact error message
   - Steps to reproduce
   - What you've tried
   - Relevant log excerpts

2. **Gather Diagnostic Information:**
   ```bash
   # Save all relevant logs
   ssh root@159.65.174.94 "docker logs ventanas-test-app > /tmp/app.log 2>&1"
   ssh root@159.65.174.94 "tail -200 /home/ventanas/app-test/logs/test/error.log > /tmp/error.log"

   # Get environment info
   ssh root@159.65.174.94 "docker exec ventanas-test-app env > /tmp/env.txt"
   ssh root@159.65.174.94 "docker ps -a | grep ventanas > /tmp/containers.txt"
   ```

3. **Check Documentation:**
   - LESSONS-LEARNED-TEST-ENV-20250930.md
   - TEST-ENVIRONMENT-GUIDE.md
   - CLAUDE.md

4. **Seek Assistance:**
   - Provide all diagnostic information
   - Include steps already attempted
   - Share relevant code changes

---

## Related Documentation
- `LESSONS-LEARNED-TEST-ENV-20250930.md` - Detailed analysis of recent issues
- `TEST-ENVIRONMENT-GUIDE.md` - Complete test environment guide
- `CLAUDE.md` - Project architecture and development guidelines

**Last Updated:** September 30, 2025
**Maintained By:** Development Team
