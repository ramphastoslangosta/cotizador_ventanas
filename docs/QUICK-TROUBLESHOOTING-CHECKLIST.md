# Quick Troubleshooting Checklist
**Fast Reference for Common Issues**

---

## 🚨 Emergency First Steps

```bash
# 1. Is it running?
docker ps | grep ventanas-test

# 2. What's the error?
docker logs ventanas-test-app --tail 50
tail -50 /home/ventanas/app-test/logs/test/error.log

# 3. Can it connect to database?
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -l'

# 4. Does it respond?
curl -I http://localhost:8001
```

---

## Issue: Login Returns 500 Error

```bash
# ✓ Check database connection
tail -50 /home/ventanas/app-test/logs/test/error.log | grep "database.*does not exist"

# ✓ Verify DATABASE_URL
docker exec ventanas-test-app env | grep DATABASE
cat /home/ventanas/app-test/.env | grep DATABASE

# ✓ Fix if wrong database name
sed -i 's/ventanas_beta_db/ventanas_test_db/g' /home/ventanas/app-test/.env
cd /home/ventanas/app-test && docker-compose -f docker-compose.test.yml build app && docker-compose -f docker-compose.test.yml up -d app
```

---

## Issue: API Returns AttributeError

```bash
# ✓ Check error message
docker logs ventanas-test-app 2>&1 | grep AttributeError

# ✓ Verify model attributes
cd /home/ventanas/app-test && grep -A 20 "class AppMaterial" database.py

# ✓ Common fixes:
# product_code → code
# material_type → unit
# unit_price → cost_per_unit
# selling_unit → selling_unit_length_m
```

---

## Issue: Empty Dropdown / No Data

```bash
# ✓ Test API directly
curl http://localhost:8001/api/materials/by-category | python3 -m json.tool | head -50

# ✓ Check database has data
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db -c "SELECT COUNT(*) FROM app_materials;"'

# ✓ Check relationships
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db -c "SELECT COUNT(*) FROM material_colors;"'

# ✓ Add missing colors to materials
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db -c "INSERT INTO material_colors (material_id, color_id, price_per_unit, is_available, created_at, updated_at) SELECT m.id, c.id, m.cost_per_unit, true, NOW(), NOW() FROM app_materials m CROSS JOIN colors c WHERE m.category = '\''Perfiles'\'' AND NOT EXISTS (SELECT 1 FROM material_colors mc WHERE mc.material_id = m.id AND mc.color_id = c.id);"'
```

---

## Issue: Container Keeps Restarting

```bash
# ✓ Check why it's failing
docker logs ventanas-test-app --tail 100

# ✓ Look for specific errors
docker logs ventanas-test-app 2>&1 | grep -E "Error|Exception|Failed|Cannot"

# ✓ Check for syntax errors
docker logs ventanas-test-app 2>&1 | grep -E "SyntaxError|ImportError|ModuleNotFoundError"

# ✓ Restart fresh
docker restart ventanas-test-app
```

---

## Issue: Database Tables Don't Exist

```bash
# ✓ List current tables
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db -c "\dt"'

# ✓ Full database refresh needed
# 1. Backup production
docker exec ventanas-beta-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER -d ventanas_beta_db --clean --if-exists' > /tmp/backup.sql

# 2. Stop test app
docker stop ventanas-test-app

# 3. Drop test database
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d postgres -c "DROP DATABASE IF EXISTS ventanas_test_db;"'

# 4. Create fresh
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d postgres -c "CREATE DATABASE ventanas_test_db;"'

# 5. Restore
cat /tmp/backup.sql | docker exec -i ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db'

# 6. Start app
docker start ventanas-test-app
```

---

## Standard Deployment

```bash
# Full deployment process
cd /home/ventanas/app-test && \
  git pull origin refactor/workorder-material-routes-20250929 && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app && \
  sleep 5 && \
  docker logs ventanas-test-app --tail 20
```

---

## Quick Health Check

```bash
# All-in-one health check
echo "=== CONTAINERS ===" && \
docker ps | grep ventanas-test && \
echo -e "\n=== APP STATUS ===" && \
curl -I http://localhost:8001 2>&1 | head -1 && \
echo -e "\n=== DATABASE ===" && \
docker exec ventanas-test-db sh -c 'PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -d ventanas_test_db -c "SELECT '\''users'\'' as table, COUNT(*) FROM users UNION ALL SELECT '\''quotes'\'', COUNT(*) FROM quotes UNION ALL SELECT '\''materials'\'', COUNT(*) FROM app_materials;"' && \
echo -e "\n=== RECENT ERRORS ===" && \
tail -10 /home/ventanas/app-test/logs/test/error.log | grep -i error || echo "No recent errors"
```

---

## Environment Variable Check

```bash
# Critical environment variables
docker exec ventanas-test-app env | grep -E "DATABASE_URL|REDIS_URL|ENVIRONMENT|DEBUG"

# .env file check
cat /home/ventanas/app-test/.env | grep -E "DATABASE_URL|REDIS_URL"
```

---

## Common Fixes Quick Reference

| Issue | Quick Fix Command |
|-------|------------------|
| Wrong database name | `sed -i 's/ventanas_beta_db/ventanas_test_db/g' /home/ventanas/app-test/.env && docker-compose -f docker-compose.test.yml build app && docker-compose -f docker-compose.test.yml up -d app` |
| App won't start | `docker restart ventanas-test-app && docker logs ventanas-test-app --tail 50` |
| Database not responding | `docker restart ventanas-test-db && sleep 5 && docker restart ventanas-test-app` |
| Need fresh data | See "Database Tables Don't Exist" section above |
| Code changes not applied | `cd /home/ventanas/app-test && git pull && docker-compose -f docker-compose.test.yml build app && docker-compose -f docker-compose.test.yml up -d app` |

---

## Nuclear Option (Last Resort)

```bash
# ⚠️ This destroys all test data
cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml down -v && \
  git reset --hard origin/refactor/workorder-material-routes-20250929 && \
  docker-compose -f docker-compose.test.yml build --no-cache && \
  docker-compose -f docker-compose.test.yml up -d
```

---

## Need More Help?

See detailed documentation:
- `docs/TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `docs/TEST-ENVIRONMENT-GUIDE.md` - Complete test environment documentation
- `docs/LESSONS-LEARNED-TEST-ENV-20250930.md` - Detailed analysis of past issues

---

**Quick Access Commands:**

```bash
# SSH to server
ssh root@159.65.174.94

# View this checklist on server
cat /home/ventanas/app-test/docs/QUICK-TROUBLESHOOTING-CHECKLIST.md
```
