# Network Error Prevention Guide
## DEVOPS-20251001-001 - Lessons Learned

**Created:** 2025-10-03
**Author:** Based on test environment deployment issues
**Purpose:** Prevent Docker network isolation and database connectivity issues during production deployment

---

## Executive Summary

During test environment deployment (159.65.174.94:8001), we encountered **Docker network isolation** that prevented the application from connecting to the database. This guide documents preventive measures for production deployment.

---

## Root Cause Analysis

### Test Environment Issue
**Problem:** Application container couldn't connect to database despite correct DATABASE_URL

**Root Cause:**
```
ventanas-test-app       → app-test_default network
ventanas-test-db        → app-test_ventanas-test-network
ventanas-test-redis     → app-test_ventanas-test-network
```

**Result:** Containers on different Docker networks cannot communicate by hostname

**Solution Applied:**
```bash
docker network connect app-test_ventanas-test-network ventanas-test-app
```

---

## Production Environment Analysis

### Current Production Setup ✅

**Production is CORRECTLY configured** (unlike test environment):

1. **docker-compose.beta.yml defines ALL services:**
   - ✅ `app` service
   - ✅ `postgres` service
   - ✅ `redis` service
   - ✅ All use same network: `ventanas-network`

2. **All containers on same network:**
   ```
   app_ventanas-network:
   - ventanas-beta-app
   - ventanas-beta-db
   - ventanas-beta-redis
   ```

3. **DATABASE_URL correctly configured:**
   ```
   DATABASE_URL=postgresql://ventanas_user:simple123@postgres:5432/ventanas_beta_db
   ```
   - Uses service name `postgres` (not container name)
   - Service name resolves within `ventanas-network`

### Why Production Should Work

| Aspect | Test Environment ❌ | Production ✅ |
|--------|-------------------|--------------|
| **docker-compose** | Only defines `app` service | Defines all services (app, postgres, redis) |
| **Database service** | External/orphaned container | Defined in compose file |
| **Network** | Separate networks (isolation) | Same network (connected) |
| **DATABASE_URL** | Used container name initially | Uses service name |
| **depends_on** | Not configured | Properly configured |

---

## Pre-Deployment Prevention Measures

### 1. Run Pre-Deployment Verification Script

**New script created:** `scripts/pre-deploy-check.sh`

```bash
# Local verification (before pushing)
bash scripts/pre-deploy-check.sh docker-compose.beta.yml

# Remote verification (on production server)
ssh root@159.65.174.94 "cd /home/ventanas/app && bash scripts/pre-deploy-check.sh"
```

**What it checks:**
- ✅ Docker compose file exists and is valid
- ✅ .env file exists with DATABASE_URL
- ✅ DATABASE_URL hostname matches docker-compose service
- ✅ Docker networks are properly configured
- ✅ No orphaned containers on different networks
- ✅ Logs directory permissions
- ✅ Database hostname reachable from app container

### 2. Verify Network Configuration

**Before deployment:**
```bash
# Check network exists and all containers are on it
docker network inspect app_ventanas-network --format '{{range .Containers}}{{.Name}}{{println}}{{end}}'

# Expected output:
# ventanas-beta-app
# ventanas-beta-db
# ventanas-beta-redis
```

**If containers missing from network:**
```bash
# Connect missing containers
docker network connect app_ventanas-network <container-name>
```

### 3. Verify DATABASE_URL Format

**Check .env file:**
```bash
grep DATABASE_URL .env
```

**Expected format (for docker-compose deployment):**
```
DATABASE_URL=postgresql://user:password@SERVICE_NAME:5432/database
                                      ^^^^^^^^^^^^
                                      Must match service name in docker-compose
```

**Common mistakes:**
- ❌ Using container name: `@ventanas-beta-db:5432` (fails if container recreated)
- ❌ Using localhost: `@localhost:5432` (fails in containerized environment)
- ❌ Using IP address: `@172.20.0.3:5432` (fails if IP changes)
- ✅ Using service name: `@postgres:5432` (works via Docker DNS)

### 4. Environment Variable Updates

**IMPORTANT:** Environment variable changes require container recreation, not just restart

```bash
# ❌ WRONG: Changes won't take effect
docker restart ventanas-beta-app

# ✅ CORRECT: Forces reload of environment variables
docker-compose -f docker-compose.beta.yml down
docker-compose -f docker-compose.beta.yml up -d
```

### 5. Logs Directory Permissions

**Before deployment:**
```bash
# Ensure logs directory exists and is writable
mkdir -p logs
chmod -R 777 logs
```

**Verification:**
```bash
ls -la logs/
# Should show: drwxrwxrwx
```

---

## Production Deployment Checklist

Use this checklist before deploying to production (159.65.174.94:8000):

- [ ] **1. Run pre-deployment verification script**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && bash scripts/pre-deploy-check.sh"
  ```

- [ ] **2. Verify all production containers on same network**
  ```bash
  ssh root@159.65.174.94 "docker network inspect app_ventanas-network"
  ```

- [ ] **3. Check DATABASE_URL uses service name**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && grep DATABASE_URL .env"
  ```

- [ ] **4. Verify logs directory permissions**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && ls -la logs/"
  ```

- [ ] **5. Check current container health**
  ```bash
  ssh root@159.65.174.94 "docker ps"
  ```

- [ ] **6. Backup current .env (if making changes)**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && cp .env .env.backup-$(date +%Y%m%d-%H%M%S)"
  ```

- [ ] **7. Pull latest code**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && git pull origin main"
  ```

- [ ] **8. Run deployment script**
  ```bash
  ssh root@159.65.174.94 "cd /home/ventanas/app && bash scripts/deploy-production.sh"
  ```

- [ ] **9. Verify health endpoint**
  ```bash
  ssh root@159.65.174.94 "curl -s http://localhost:8000/api/health/"
  ```

- [ ] **10. Test database connectivity from app**
  ```bash
  ssh root@159.65.174.94 "docker exec ventanas-beta-app python -c 'import psycopg2; conn = psycopg2.connect(...)'"
  ```

---

## Emergency Rollback Procedure

If network issues occur during production deployment:

### Quick Fix: Connect to Network
```bash
ssh root@159.65.174.94
docker network connect app_ventanas-network ventanas-beta-app
docker restart ventanas-beta-app
```

### Full Rollback: Restore Previous Version
```bash
ssh root@159.65.174.94
cd /home/ventanas/app

# Stop new containers
docker-compose -f docker-compose.beta.yml down

# Restore previous .env
cp .env.backup-YYYYMMDD-HHMMSS .env

# Checkout previous commit
git log --oneline -10  # Find commit hash
git checkout <previous-commit-hash>

# Rebuild with old code
docker-compose -f docker-compose.beta.yml up -d --build

# Verify health
curl http://localhost:8000/api/health/
```

---

## Network Troubleshooting Commands

### Diagnose Network Issues
```bash
# List all networks
docker network ls

# Inspect specific network
docker network inspect app_ventanas-network

# Check which network a container is on
docker inspect ventanas-beta-app --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}'

# List all containers with their networks
docker ps --format 'table {{.Names}}\t{{.Networks}}'
```

### Test Connectivity Between Containers
```bash
# From app container, test database connectivity
docker exec ventanas-beta-app getent hosts postgres

# Test with Python psycopg2
docker exec ventanas-beta-app python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://ventanas_user:simple123@postgres:5432/ventanas_beta_db')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

# Check DNS resolution
docker exec ventanas-beta-app nslookup postgres 2>/dev/null || \
docker exec ventanas-beta-app getent hosts postgres
```

### Fix Network Isolation
```bash
# Connect container to network
docker network connect app_ventanas-network ventanas-beta-app

# Verify connection
docker network inspect app_ventanas-network | grep ventanas-beta-app

# Restart container to apply
docker restart ventanas-beta-app
```

---

## Comparison: Test vs Production Setup

| Component | Test Environment | Production | Prevention |
|-----------|-----------------|------------|------------|
| **Compose File** | docker-compose.test.yml (minimal) | docker-compose.beta.yml (complete) | Use complete compose files |
| **Services Defined** | Only `app` | `app`, `postgres`, `redis`, `nginx` | Define all services in compose |
| **Database** | External/orphaned | Managed by compose | Include DB in compose |
| **Network** | Default + external | Single custom network | Use single network for all |
| **DATABASE_URL** | Fixed to container name | Service name (correct) | Use service names |
| **depends_on** | Not configured | Properly configured | Configure dependencies |

---

## Key Takeaways

### ✅ Production Advantages
1. **Complete docker-compose.beta.yml** - All services defined
2. **Unified network** - All containers on `ventanas-network`
3. **Service-based DNS** - DATABASE_URL uses service names
4. **Proper dependencies** - `depends_on` ensures startup order

### ⚠️ Test Environment Lessons
1. **Orphaned containers** - External containers can cause network isolation
2. **Incomplete compose files** - Minimal configs lead to network issues
3. **Container names vs service names** - Use service names for reliability
4. **Environment reload** - Container recreation needed for env var changes

### 🔧 Prevention Tools Created
1. **scripts/pre-deploy-check.sh** - Automated pre-deployment verification
2. **Network inspection commands** - Documented in this guide
3. **Rollback procedures** - Emergency recovery steps

---

## References

- Test Environment Issue: `.claude/workspace/DEVOPS-20251001-001/notes.md` (lines 443-527)
- Production Compose: `docker-compose.beta.yml`
- Deployment Runbook: `docs/DEPLOYMENT-RUNBOOK.md`
- Test Environment Guide: `docs/TEST-ENVIRONMENT-GUIDE.md`

---

**Status:** ✅ Production environment properly configured - network issues unlikely
**Confidence:** HIGH - docker-compose.beta.yml includes all services on single network
**Recommendation:** Run `scripts/pre-deploy-check.sh` before deployment for extra verification
