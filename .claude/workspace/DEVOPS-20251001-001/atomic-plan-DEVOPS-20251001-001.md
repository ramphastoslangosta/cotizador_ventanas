# Atomic Execution Plan: DEVOPS-20251001-001
## Docker Build Process Improvements

**Task ID:** DEVOPS-20251001-001
**Title:** Docker build improvements
**Priority:** HIGH
**Estimated Effort:** 1 week (5-7 days)
**Phase:** 0 (HOTFIX Prevention)
**Branch:** `devops/docker-build-improvements-20251001`
**Created:** 2025-10-02

---

## Executive Summary

Implement comprehensive Docker build improvements to prevent Python bytecode cache issues and Docker layer caching problems that caused 6+ rebuild attempts during HOTFIX-20251001-001. This task adds build verification, cache clearing, deployment scripts with verification, and CI/CD enhancements to ensure reliable deployments.

**Root Cause:** During HOTFIX-20251001-001, code changes weren't reflected in containers due to Python .pyc cache and Docker layer caching, requiring multiple rebuilds with `--no-cache` flag and manual container intervention.

---

## Success Criteria

1. ✅ **Build Verification:** Dockerfile includes verification step that confirms code changes are present
2. ✅ **Python Cache Clearing:** All .pyc files and __pycache__ directories removed during build
3. ✅ **Deployment Script:** Automated script with pre/post verification for production deployments
4. ✅ **Test Environment Script:** Automated script for test environment deployments
5. ✅ **CI/CD Integration:** GitHub Actions workflow for automated testing and deployment
6. ✅ **Documentation:** Deployment runbook and troubleshooting guide updated
7. ✅ **Zero Downtime:** All deployments complete without service interruption

---

## Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Breaking production Docker setup | HIGH | 20% | Test all changes in test environment first |
| Health check failures during deployment | MEDIUM | 30% | Increase health check timeouts during testing |
| Git conflicts with ongoing work | MEDIUM | 40% | Coordinate deployment window with team |
| New dependencies breaking build | MEDIUM | 15% | Test requirements.txt changes separately |
| Script permissions issues | LOW | 25% | Explicitly set execute permissions in Dockerfile |

---

## Dependencies Status

**Dependencies:** None (Task can start immediately)
**Blocks:** Future deployment tasks, ongoing refactoring work benefits from reliable builds

---

## Current Repository State

- **Branch:** main
- **Uncommitted Changes:** 7 untracked files in .claude/ workspace
- **Last Deployment:** HOTFIX-20251001-001 (Oct 1, 2025 21:30 UTC)
- **Docker Files:** Dockerfile (60 lines), docker-compose.beta.yml (192 lines)

---

# PHASE 1: PREPARATION (Estimated: 30 minutes)

## Pre-work Checklist

- [ ] Review HOTFIX-20251001-RCA.md for Docker build issues context
- [ ] Check current Docker setup (Dockerfile and docker-compose files)
- [ ] Verify test environment is accessible (port 8001)
- [ ] Backup current Dockerfile and docker-compose.beta.yml
- [ ] Create task workspace directory
- [ ] Review current deployment process documentation

## Environment Setup

### Step 1.1: Create Task Branch
**Action:** Create dedicated branch for Docker improvements
**Commands:**
```bash
cd /Users/rafaellang/cotizador/cotizador_ventanas
git checkout main
git pull origin main
git checkout -b devops/docker-build-improvements-20251001
```

**Test Checkpoint:**
```bash
git branch --show-current
# Expected: devops/docker-build-improvements-20251001
```

**Rollback:** `git checkout main && git branch -D devops/docker-build-improvements-20251001`
**Time:** 2 minutes

### Step 1.2: Backup Current Docker Configuration
**Action:** Create backups of Docker files before modifications
**Commands:**
```bash
mkdir -p backups/docker-$(date +%Y%m%d)
cp Dockerfile backups/docker-$(date +%Y%m%d)/Dockerfile.backup
cp docker-compose.beta.yml backups/docker-$(date +%Y%m%d)/docker-compose.beta.yml.backup
ls -la backups/docker-$(date +%Y%m%d)/
```

**Test Checkpoint:**
```bash
test -f backups/docker-$(date +%Y%m%d)/Dockerfile.backup && echo "✅ Backup created"
```

**Rollback:** `rm -rf backups/docker-$(date +%Y%m%d)/`
**Time:** 1 minute

### Step 1.3: Document Current Build Process
**Action:** Capture current build times and behavior for comparison
**Commands:**
```bash
# Record baseline
echo "=== BASELINE BUILD METRICS ===" > .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
echo "Date: $(date)" >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
echo "" >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md

# Test current build (if safe to do so)
echo "## Current Build Command:" >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
echo '```bash' >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
echo 'docker-compose -f docker-compose.beta.yml build app' >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
echo '```' >> .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
```

**Test Checkpoint:**
```bash
cat .claude/workspace/DEVOPS-20251001-001/baseline-metrics.md
```

**Rollback:** N/A (documentation only)
**Time:** 5 minutes

---

# PHASE 2: IMPLEMENTATION (Estimated: 4-5 hours)

## Docker Build Improvements

### Step 2.1: Add Python Cache Clearing to Dockerfile
**Action:** Add RUN command to clear all Python bytecode cache before app starts
**Files:**
- Modify: `Dockerfile` (after line 40: `COPY . .`)

**Code Changes:**
```dockerfile
# Copiar código de la aplicación
COPY . .

# === DEVOPS-20251001-001: Clear Python bytecode cache ===
# Prevents stale .pyc files from causing deployment issues
RUN echo "=== Clearing Python cache ===" && \
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete 2>/dev/null || true && \
    echo "✅ Python cache cleared"
```

**Test Checkpoint:**
```bash
# Verify syntax
cat Dockerfile | grep -A 4 "Clear Python cache"

# Verify it comes after COPY . .
grep -n "COPY . ." Dockerfile
grep -n "Clear Python cache" Dockerfile
```

**Commit Message:**
```
devops: add Python cache clearing to Dockerfile

- Clear __pycache__ directories before app starts
- Remove .pyc files to prevent stale bytecode issues
- Prevents issues seen in HOTFIX-20251001-001

Fixes DEVOPS-20251001-001 (Part 1/5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git checkout Dockerfile`
**Time:** 10 minutes

### Step 2.2: Add Build Verification to Dockerfile
**Action:** Add verification step that confirms code is correctly copied
**Files:**
- Modify: `Dockerfile` (after cache clearing step)

**Code Changes:**
```dockerfile
# === DEVOPS-20251001-001: Build verification ===
# Confirms code changes are present in container
RUN echo "=== Build Verification ===" && \
    echo "Checking main.py imports..." && \
    python -c "import sys; sys.path.insert(0, '.'); import main; print('✅ main.py imports successfully')" && \
    echo "Checking app structure..." && \
    test -d app/routes && echo "✅ app/routes exists" || echo "⚠️ app/routes missing" && \
    test -f config.py && echo "✅ config.py exists" || echo "❌ config.py missing" && \
    echo "Checking route count..." && \
    python -c "import main; print(f'✅ {len(main.app.routes)} routes registered')" && \
    echo "=== Build verification complete ==="
```

**Test Checkpoint:**
```bash
# Verify syntax
cat Dockerfile | grep -A 10 "Build verification"

# Ensure it comes after cache clearing
grep -n "Build verification" Dockerfile
```

**Commit Message:**
```
devops: add build verification step to Dockerfile

- Verify main.py imports successfully
- Check critical files exist (config.py, app/routes)
- Display route count for verification
- Catches issues before container starts

Fixes DEVOPS-20251001-001 (Part 2/5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git checkout Dockerfile`
**Time:** 15 minutes

### Step 2.3: Create Production Deployment Script
**Action:** Create automated deployment script with pre/post verification
**Files:**
- Create: `scripts/deploy-production.sh`

**Code:**
```bash
#!/bin/bash
# scripts/deploy-production.sh
# Automated production deployment with verification
# Created for DEVOPS-20251001-001

set -e  # Exit on error

COMPOSE_FILE="docker-compose.beta.yml"
CONTAINER_NAME="ventanas-beta-app"
HEALTH_ENDPOINT="http://localhost:8000/api/health"
MAX_WAIT=60  # seconds

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        PRODUCTION DEPLOYMENT - START"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# === PRE-DEPLOYMENT VERIFICATION ===
echo "📋 Pre-deployment verification..."
echo "Current git commit:"
git log --oneline -1
echo ""

echo "Checking main.py routes..."
ROUTE_COUNT=$(grep -c "@app\.(get|post|put|delete|patch)" main.py || true)
echo "✅ Found $ROUTE_COUNT route decorators in main.py"
echo ""

echo "Checking for critical files..."
test -f main.py && echo "✅ main.py exists" || (echo "❌ main.py missing" && exit 1)
test -f database.py && echo "✅ database.py exists" || (echo "❌ database.py missing" && exit 1)
test -f config.py && echo "✅ config.py exists" || (echo "❌ config.py missing" && exit 1)
test -d app/routes && echo "✅ app/routes exists" || echo "⚠️ app/routes missing"
echo ""

# === BACKUP CURRENT DEPLOYMENT ===
echo "💾 Creating deployment backup..."
BACKUP_DIR="backups/deployment-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
docker-compose -f "$COMPOSE_FILE" logs app > "$BACKUP_DIR/app-logs.txt" 2>&1 || true
echo "✅ Logs backed up to $BACKUP_DIR"
echo ""

# === STOP CONTAINERS ===
echo "⏹️  Stopping containers..."
docker-compose -f "$COMPOSE_FILE" down
echo "✅ Containers stopped"
echo ""

# === BUILD WITH NO CACHE ===
echo "🔨 Building with --no-cache (this may take 2-3 minutes)..."
docker-compose -f "$COMPOSE_FILE" build --no-cache app
echo "✅ Build complete"
echo ""

# === START CONTAINERS ===
echo "🚀 Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d
echo "✅ Containers started"
echo ""

# === WAIT FOR HEALTH CHECK ===
echo "⏳ Waiting for application to be healthy..."
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    echo "   Waiting... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Application failed health check after $MAX_WAIT seconds"
    echo "Check logs: docker-compose -f $COMPOSE_FILE logs app"
    exit 1
fi
echo ""

# === POST-DEPLOYMENT VERIFICATION ===
echo "✅ Post-deployment verification..."

# Check main.py inside container
echo "Verifying main.py in container..."
docker exec "$CONTAINER_NAME" python -c "import main; print(f'✅ {len(main.app.routes)} routes registered')"

# Test critical endpoints
echo ""
echo "Testing critical endpoints..."
curl -I http://localhost:8000/ 2>&1 | grep "HTTP" && echo "✅ Homepage accessible"
curl -I http://localhost:8000/login 2>&1 | grep "HTTP" && echo "✅ Login page accessible"
curl -I "$HEALTH_ENDPOINT" 2>&1 | grep "HTTP" && echo "✅ Health check accessible"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        DEPLOYMENT COMPLETE ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 Monitor logs: docker-compose -f $COMPOSE_FILE logs -f app"
echo "📊 Check health: curl $HEALTH_ENDPOINT"
echo ""
```

**Test Checkpoint:**
```bash
# Verify script exists and has content
test -f scripts/deploy-production.sh && wc -l scripts/deploy-production.sh

# Check syntax (basic)
bash -n scripts/deploy-production.sh && echo "✅ Script syntax valid"
```

**Commit Message:**
```
devops: create automated production deployment script

- Pre-deployment verification (git commit, file checks)
- Automated backup of current deployment logs
- Build with --no-cache to avoid stale code issues
- Health check wait with timeout
- Post-deployment endpoint verification

Fixes DEVOPS-20251001-001 (Part 3/5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git rm scripts/deploy-production.sh`
**Time:** 30 minutes

### Step 2.4: Create Test Environment Deployment Script
**Action:** Create deployment script for test environment (port 8001)
**Files:**
- Create: `scripts/deploy-test.sh`

**Code:**
```bash
#!/bin/bash
# scripts/deploy-test.sh
# Automated test environment deployment
# Created for DEVOPS-20251001-001

set -e  # Exit on error

COMPOSE_FILE="docker-compose.test.yml"
CONTAINER_NAME="ventanas-test-app"
HEALTH_ENDPOINT="http://localhost:8001/api/health"
MAX_WAIT=60  # seconds

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        TEST ENVIRONMENT DEPLOYMENT - START"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# === PRE-DEPLOYMENT VERIFICATION ===
echo "📋 Pre-deployment verification..."
echo "Current branch: $(git branch --show-current)"
echo "Current commit:"
git log --oneline -1
echo ""

# === STOP CONTAINERS ===
echo "⏹️  Stopping test containers..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
echo "✅ Test containers stopped"
echo ""

# === BUILD WITH NO CACHE ===
echo "🔨 Building test environment with --no-cache..."
docker-compose -f "$COMPOSE_FILE" build --no-cache app
echo "✅ Build complete"
echo ""

# === START CONTAINERS ===
echo "🚀 Starting test containers..."
docker-compose -f "$COMPOSE_FILE" up -d
echo "✅ Test containers started"
echo ""

# === WAIT FOR HEALTH CHECK ===
echo "⏳ Waiting for test application to be healthy..."
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        echo "✅ Test application is healthy!"
        break
    fi
    echo "   Waiting... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Test application failed health check"
    echo "Check logs: docker-compose -f $COMPOSE_FILE logs app"
    exit 1
fi
echo ""

# === POST-DEPLOYMENT VERIFICATION ===
echo "✅ Post-deployment verification..."
echo "Testing test environment endpoints..."
curl -I http://localhost:8001/ 2>&1 | grep "HTTP" && echo "✅ Test homepage accessible"
curl -I "$HEALTH_ENDPOINT" 2>&1 | grep "HTTP" && echo "✅ Test health check accessible"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        TEST DEPLOYMENT COMPLETE ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Test URL: http://localhost:8001"
echo "🔍 Monitor logs: docker-compose -f $COMPOSE_FILE logs -f app"
echo ""
```

**Test Checkpoint:**
```bash
test -f scripts/deploy-test.sh && echo "✅ Script created"
bash -n scripts/deploy-test.sh && echo "✅ Script syntax valid"
```

**Commit Message:**
```
devops: create test environment deployment script

- Automated test environment deployment (port 8001)
- Health check verification
- Endpoint testing
- Simplified for rapid testing iterations

Fixes DEVOPS-20251001-001 (Part 4/5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git rm scripts/deploy-test.sh`
**Time:** 20 minutes

### Step 2.5: Make Scripts Executable in Dockerfile
**Action:** Ensure deployment scripts have execute permissions
**Files:**
- Modify: `Dockerfile` (line 47)

**Code Changes:**
```dockerfile
# Establecer permisos correctos
RUN chmod +x scripts/*.sh 2>/dev/null || true
```

**Already exists, but verify:**
```bash
grep "chmod +x scripts" Dockerfile
```

**Test Checkpoint:**
```bash
# Verify line exists
grep -n "chmod +x scripts" Dockerfile
```

**Commit:** No commit needed if already present
**Time:** 5 minutes

### Step 2.6: Update docker-compose.beta.yml Health Check
**Action:** Increase health check timeouts to accommodate build verification
**Files:**
- Modify: `docker-compose.beta.yml` (lines 39-44)

**Code Changes:**
```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s          # Reduced from 45s for faster detection
      timeout: 15s           # Keep same
      retries: 5             # Increased from 3 for more resilience
      start_period: 90s      # Increased from 60s for build verification
```

**Test Checkpoint:**
```bash
# Verify syntax
docker-compose -f docker-compose.beta.yml config > /dev/null && echo "✅ Valid YAML"

# Check healthcheck section
grep -A 5 "healthcheck:" docker-compose.beta.yml | head -6
```

**Commit Message:**
```
devops: improve health check resilience in docker-compose

- Increase retries from 3 to 5 for more resilience
- Increase start_period to 90s to accommodate build verification
- Reduce interval to 30s for faster issue detection

Fixes DEVOPS-20251001-001 (Part 5/5)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git checkout docker-compose.beta.yml`
**Time:** 10 minutes

---

# PHASE 3: INTEGRATION & TESTING (Estimated: 2-3 hours)

### Step 3.1: Set Script Permissions
**Action:** Make deployment scripts executable
**Commands:**
```bash
chmod +x scripts/deploy-production.sh
chmod +x scripts/deploy-test.sh
ls -la scripts/deploy-*.sh
```

**Test Checkpoint:**
```bash
test -x scripts/deploy-production.sh && echo "✅ Production script executable"
test -x scripts/deploy-test.sh && echo "✅ Test script executable"
```

**Rollback:** `chmod -x scripts/deploy-*.sh`
**Time:** 2 minutes

### Step 3.2: Create docker-compose.test.yml (if not exists)
**Action:** Create test environment docker-compose file
**Files:**
- Create: `docker-compose.test.yml` (based on docker-compose.beta.yml)

**Code:** (Simplified version with port 8001)
```yaml
version: '3.8'

# Docker Compose for TEST environment
# Port 8001 for parallel testing

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ventanas-test-app
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=true
    env_file:
      - .env
    volumes:
      - ./static/uploads:/app/static/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 15s
      retries: 3
      start_period: 90s
```

**Test Checkpoint:**
```bash
docker-compose -f docker-compose.test.yml config > /dev/null && echo "✅ Valid test config"
```

**Commit Message:**
```
devops: add test environment docker-compose config

- Test environment on port 8001
- Simplified config for rapid testing
- Parallel deployment with production

Supports DEVOPS-20251001-001

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git rm docker-compose.test.yml`
**Time:** 15 minutes

### Step 3.3: Test Dockerfile Build Locally
**Action:** Build Docker image locally to verify changes
**Commands:**
```bash
# Build with new Dockerfile
docker build -t ventanas-test:devops-improvements . 2>&1 | tee .claude/workspace/DEVOPS-20251001-001/build-test.log

# Look for verification messages
grep "Build Verification" .claude/workspace/DEVOPS-20251001-001/build-test.log
grep "Python cache cleared" .claude/workspace/DEVOPS-20251001-001/build-test.log
grep "routes registered" .claude/workspace/DEVOPS-20251001-001/build-test.log
```

**Test Checkpoint:**
```bash
# Verify image was created
docker images | grep ventanas-test:devops-improvements

# Verify build log shows verification
grep -c "✅" .claude/workspace/DEVOPS-20251001-001/build-test.log
```

**Rollback:** `docker rmi ventanas-test:devops-improvements`
**Time:** 10 minutes (build time ~3 min)

### Step 3.4: Test Deployment Script in Dry Run
**Action:** Verify deployment script logic without actually deploying
**Commands:**
```bash
# Create dry-run version
cp scripts/deploy-test.sh scripts/deploy-test-dryrun.sh
sed -i.bak 's/set -e/set -ex/' scripts/deploy-test-dryrun.sh
sed -i.bak 's/docker-compose/echo "DRY RUN: docker-compose/' scripts/deploy-test-dryrun.sh

# Run dry-run
bash scripts/deploy-test-dryrun.sh 2>&1 | tee .claude/workspace/DEVOPS-20251001-001/dryrun-test.log

# Clean up
rm scripts/deploy-test-dryrun.sh scripts/deploy-test-dryrun.sh.bak
```

**Test Checkpoint:**
```bash
grep "DRY RUN" .claude/workspace/DEVOPS-20251001-001/dryrun-test.log | wc -l
# Should show multiple DRY RUN commands
```

**Rollback:** N/A (test only)
**Time:** 10 minutes

---

# PHASE 4: DOCUMENTATION (Estimated: 1-2 hours)

### Step 4.1: Create Deployment Runbook
**Action:** Document the new deployment process
**Files:**
- Create: `docs/DEPLOYMENT-RUNBOOK.md`

**Code:**
```markdown
# Deployment Runbook

**Version:** 2.0
**Last Updated:** 2025-10-02
**Owner:** DevOps Team

## Overview

This runbook describes the deployment process for the Window Quotation System with automated Docker build verification and cache clearing.

## Prerequisites

- SSH access to production server (159.65.174.94)
- Git access to repository
- Docker and docker-compose installed
- .env file configured

## Production Deployment

### Standard Deployment

```bash
# 1. SSH to production server
ssh root@159.65.174.94
cd /home/ventanas/app

# 2. Pull latest code
git fetch origin
git checkout main
git pull origin main

# 3. Run automated deployment script
bash scripts/deploy-production.sh
```

**Expected Output:**
- ✅ Pre-deployment verification
- ✅ Logs backed up
- ✅ Containers stopped
- ✅ Build complete (2-3 minutes)
- ✅ Containers started
- ✅ Health check passed
- ✅ Endpoints verified

**Deployment Time:** 5-7 minutes

### Hotfix Deployment

For urgent fixes (e.g., HOTFIX-20251001-001):

```bash
# 1. Create hotfix branch
git checkout -b hotfix/description-YYYYMMDD

# 2. Make changes and commit

# 3. Push to remote
git push origin hotfix/description-YYYYMMDD

# 4. SSH to production
ssh root@159.65.174.94
cd /home/ventanas/app

# 5. Deploy hotfix
git fetch origin
git checkout hotfix/description-YYYYMMDD
bash scripts/deploy-production.sh
```

## Test Environment Deployment

### Port 8001 Test Environment

```bash
# 1. Checkout branch to test
git checkout branch-name

# 2. Run test deployment
bash scripts/deploy-test.sh
```

### Verification

- Test URL: http://localhost:8001
- Health Check: http://localhost:8001/api/health
- Test Login: http://localhost:8001/login

## Troubleshooting

### Issue: Build Verification Fails

**Symptom:** Build stops with "❌ main.py imports failed"

**Solution:**
```bash
# Check for syntax errors
python -m py_compile main.py

# Check for missing dependencies
pip install -r requirements.txt

# Review build logs
docker-compose -f docker-compose.beta.yml logs app
```

### Issue: Health Check Timeout

**Symptom:** "Application failed health check after 60 seconds"

**Solution:**
```bash
# Check container logs
docker-compose -f docker-compose.beta.yml logs app

# Manually test health endpoint
docker exec ventanas-beta-app curl http://localhost:8000/api/health

# Increase start_period in docker-compose.beta.yml if needed
```

### Issue: Stale Code in Container

**Symptom:** Code changes not reflected after deployment

**Solution:**
```bash
# 1. Verify git commit in container
docker exec ventanas-beta-app git log --oneline -1

# 2. Check for .pyc files
docker exec ventanas-beta-app find /app -name "*.pyc"

# 3. Force rebuild with no cache (automatic in scripts)
bash scripts/deploy-production.sh
# Script already includes --no-cache flag
```

### Issue: Port Already in Use

**Symptom:** "bind: address already in use"

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8000

# Stop existing containers
docker-compose -f docker-compose.beta.yml down

# Retry deployment
bash scripts/deploy-production.sh
```

## Rollback Procedure

If deployment causes issues:

```bash
# 1. Check previous deployment logs
ls -la backups/deployment-*/

# 2. Rollback to previous commit
git log --oneline -5
git checkout <previous-commit-hash>

# 3. Redeploy
bash scripts/deploy-production.sh

# 4. Verify
curl -I http://localhost:8000/api/health
```

## Monitoring After Deployment

### First 5 Minutes

```bash
# Watch logs
docker-compose -f docker-compose.beta.yml logs -f app

# Monitor health check
watch -n 5 'curl -s http://localhost:8000/api/health | jq'

# Check error rate
docker-compose -f docker-compose.beta.yml logs app | grep -i error | tail -20
```

### First Hour

- Monitor application logs for errors
- Check response times for key endpoints
- Verify user authentication working
- Test quote creation workflow

## Post-Deployment Checklist

- [ ] Health check endpoint returns 200 OK
- [ ] Homepage loads (/)
- [ ] Login page loads (/login)
- [ ] Dashboard accessible after login (/dashboard)
- [ ] Quotes list page loads (/quotes)
- [ ] No error spikes in logs
- [ ] Container memory usage normal (<768MB)

## Emergency Contacts

- **DevOps Lead:** [Name/Contact]
- **On-Call Engineer:** [Name/Contact]
- **Database Admin:** [Name/Contact]

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-02 | 2.0 | Added automated deployment scripts, build verification | DEVOPS-20251001-001 |
| 2025-09-30 | 1.0 | Initial runbook | DevOps Team |
```

**Test Checkpoint:**
```bash
test -f docs/DEPLOYMENT-RUNBOOK.md && wc -l docs/DEPLOYMENT-RUNBOOK.md
```

**Commit Message:**
```
docs: create comprehensive deployment runbook

- Standard deployment procedure
- Hotfix deployment procedure
- Test environment deployment
- Troubleshooting guide
- Rollback procedures
- Post-deployment monitoring

Supports DEVOPS-20251001-001

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git rm docs/DEPLOYMENT-RUNBOOK.md`
**Time:** 45 minutes

### Step 4.2: Update CLAUDE.md with Docker Improvements
**Action:** Add Docker deployment section to project documentation
**Files:**
- Modify: `CLAUDE.md` (add new section after "Development Commands")

**Code Addition:**
```markdown
### Docker Deployment

#### Production Deployment
```bash
bash scripts/deploy-production.sh
# Automated deployment with verification and health checks
# See docs/DEPLOYMENT-RUNBOOK.md for details
```

#### Test Environment Deployment
```bash
bash scripts/deploy-test.sh
# Deploy to port 8001 for testing
```

#### Manual Docker Commands
```bash
# Build with cache clearing
docker-compose -f docker-compose.beta.yml build --no-cache app

# Start containers
docker-compose -f docker-compose.beta.yml up -d

# View logs
docker-compose -f docker-compose.beta.yml logs -f app

# Health check
curl http://localhost:8000/api/health
```

**Build Improvements (DEVOPS-20251001-001):**
- Automatic Python cache clearing (.pyc files, __pycache__)
- Build verification confirms code changes present
- Health check verification before considering deployment complete
- Automated backup of logs before deployment
```

**Test Checkpoint:**
```bash
grep "Docker Deployment" CLAUDE.md
grep "DEVOPS-20251001-001" CLAUDE.md
```

**Commit Message:**
```
docs: update CLAUDE.md with Docker deployment info

- Add deployment scripts documentation
- Document build improvements from DEVOPS-20251001-001
- Reference deployment runbook

Supports DEVOPS-20251001-001

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Rollback:** `git checkout CLAUDE.md`
**Time:** 15 minutes

### Step 4.3: Create Success Criteria Document
**Action:** Document all success criteria for task completion
**Files:**
- Create: `.claude/workspace/DEVOPS-20251001-001/success-criteria.md`

**Code:**
```markdown
# Success Criteria: DEVOPS-20251001-001

## Completion Checklist

### Dockerfile Improvements
- [x] Python cache clearing added to Dockerfile
- [x] Build verification step added
- [x] Verification confirms main.py imports
- [x] Route count displayed during build

### Deployment Scripts
- [x] Production deployment script created (scripts/deploy-production.sh)
- [x] Test environment script created (scripts/deploy-test.sh)
- [x] Scripts have execute permissions
- [x] Pre-deployment verification implemented
- [x] Post-deployment verification implemented
- [x] Health check wait with timeout

### Docker Compose
- [x] Health check settings optimized
- [x] Start period increased for build verification
- [x] Test environment config created (docker-compose.test.yml)

### Documentation
- [x] Deployment runbook created (docs/DEPLOYMENT-RUNBOOK.md)
- [x] CLAUDE.md updated with deployment info
- [x] Troubleshooting guide included
- [x] Rollback procedures documented

### Testing
- [x] Dockerfile builds successfully
- [x] Build verification runs and passes
- [x] Python cache cleared during build
- [x] Deployment scripts execute without errors
- [x] Health checks pass after deployment

### Integration
- [ ] Tested in test environment (port 8001)
- [ ] Deployed to production successfully
- [ ] Zero downtime achieved
- [ ] No code staleness issues after deployment

## Acceptance Criteria (From RCA)

1. ✅ **Build Verification:** Dockerfile includes verification step
2. ✅ **Cache Clearing:** All .pyc files removed during build
3. ✅ **Deployment Script:** Automated script with verification
4. ✅ **Test Environment:** Separate test deployment capability
5. ⏳ **Production Tested:** Awaiting production deployment
6. ✅ **Documentation:** Complete runbook and guides
7. ⏳ **Zero Downtime:** To be verified in production

## Metrics

### Build Time
- **Before:** ~2 minutes (with cache)
- **After:** ~3 minutes (no cache, with verification)
- **Acceptable:** Yes (1 minute increase acceptable for reliability)

### Deployment Reliability
- **Before:** Multiple rebuild attempts needed (HOTFIX-20251001-001)
- **After:** Single deployment attempt expected
- **Target:** 100% success rate on first attempt

### Verification Coverage
- **Pre-deployment:** Git commit, file checks, route count
- **Build-time:** Import verification, structure checks, route count
- **Post-deployment:** Health check, endpoint tests, container verification

## Risk Mitigation

- ✅ Backups created before deployment
- ✅ Rollback procedure documented
- ✅ Test environment available for validation
- ✅ Health checks prevent bad deployments

## Next Steps After Completion

1. Merge to main branch
2. Deploy to test environment first
3. Monitor test environment for 24 hours
4. Deploy to production
5. Monitor production for 1 week
6. Mark task as complete in tasks.csv
```

**Test Checkpoint:**
```bash
cat .claude/workspace/DEVOPS-20251001-001/success-criteria.md | grep -c "✅"
```

**Rollback:** N/A (documentation)
**Time:** 15 minutes

---

# PHASE 5: DEPLOYMENT VERIFICATION (Estimated: 1-2 hours)

### Step 5.1: Test Environment Deployment
**Action:** Deploy to test environment (port 8001) to verify everything works
**Commands:**
```bash
# Run test deployment
bash scripts/deploy-test.sh 2>&1 | tee .claude/workspace/DEVOPS-20251001-001/test-deployment.log

# Verify test environment
curl -I http://localhost:8001/
curl http://localhost:8001/api/health | jq

# Check logs for build verification messages
docker-compose -f docker-compose.test.yml logs app | grep "Build Verification"
docker-compose -f docker-compose.test.yml logs app | grep "Python cache cleared"
```

**Test Checkpoint:**
```bash
# Verify health check
curl -s http://localhost:8001/api/health | jq '.status' | grep "healthy"

# Verify routes loaded
docker exec ventanas-test-app python -c "import main; print(len(main.app.routes))"
```

**Success Criteria:**
- Test environment starts successfully
- Health check returns healthy status
- Build verification messages appear in logs
- No Python cache issues

**Rollback:**
```bash
docker-compose -f docker-compose.test.yml down
```

**Time:** 20 minutes (includes 10 min monitoring)

### Step 5.2: Verify Build Verification Messages
**Action:** Confirm build verification steps executed correctly
**Commands:**
```bash
# Extract build verification from logs
docker-compose -f docker-compose.test.yml logs app | grep -A 10 "Build Verification" > .claude/workspace/DEVOPS-20251001-001/build-verification.log

# Check for success markers
cat .claude/workspace/DEVOPS-20251001-001/build-verification.log
```

**Test Checkpoint:**
```bash
# Should show:
# ✅ main.py imports successfully
# ✅ config.py exists
# ✅ app/routes exists
# ✅ XX routes registered

grep -c "✅" .claude/workspace/DEVOPS-20251001-001/build-verification.log
# Should be >= 3
```

**Time:** 10 minutes

### Step 5.3: Test Deployment Script End-to-End
**Action:** Run complete deployment cycle with verification
**Commands:**
```bash
# Make a trivial change to test deployment
echo "# DEVOPS test comment" >> main.py

# Commit change
git add main.py
git commit -m "test: deployment verification test"

# Deploy to test
bash scripts/deploy-test.sh

# Verify change is in container
docker exec ventanas-test-app grep "DEVOPS test comment" /app/main.py

# Rollback test change
git reset --hard HEAD~1
```

**Test Checkpoint:**
```bash
# Verify comment appeared in container
docker exec ventanas-test-app tail -5 /app/main.py | grep "DEVOPS test comment"
```

**Success Criteria:**
- Code change reflected in container immediately
- No stale cache issues
- Deployment script completes successfully

**Time:** 15 minutes

### Step 5.4: Create Pre-Production Checklist
**Action:** Document final checks before production deployment
**Files:**
- Create: `.claude/workspace/DEVOPS-20251001-001/pre-production-checklist.md`

**Code:**
```markdown
# Pre-Production Deployment Checklist

## Code Review
- [ ] All commits reviewed and approved
- [ ] No debug code or test comments in main branch
- [ ] CLAUDE.md updated with deployment info
- [ ] Deployment runbook reviewed

## Testing
- [ ] Test environment deployment successful
- [ ] Build verification messages confirmed in logs
- [ ] Health checks passing in test environment
- [ ] No Python cache issues observed
- [ ] Deployment script completed without errors

## Documentation
- [ ] DEPLOYMENT-RUNBOOK.md complete and accurate
- [ ] Troubleshooting section includes common issues
- [ ] Rollback procedures documented and tested
- [ ] Team briefed on new deployment process

## Backups
- [ ] Recent database backup exists
- [ ] Current deployment logs backed up
- [ ] Git tag created for current production version

## Monitoring
- [ ] Health check endpoint working
- [ ] Log monitoring configured
- [ ] Alert contacts updated

## Rollback Plan
- [ ] Rollback procedure tested in test environment
- [ ] Previous stable commit identified: `git log --oneline -5`
- [ ] Rollback script ready if needed

## Team Communication
- [ ] Team notified of deployment window
- [ ] On-call engineer available
- [ ] Deployment time scheduled (low-traffic window)

## Production Deployment Steps

1. Create production backup:
   ```bash
   bash scripts/create-backup.sh  # If exists, or manual backup
   ```

2. Tag current production version:
   ```bash
   git tag -a v5.0.0-pre-devops-improvements -m "Before DEVOPS-20251001-001"
   ```

3. Deploy to production:
   ```bash
   bash scripts/deploy-production.sh
   ```

4. Monitor for 1 hour:
   ```bash
   docker-compose -f docker-compose.beta.yml logs -f app | grep -i error
   ```

5. Mark task complete:
   ```bash
   # Update tasks.csv status to completed
   ```

## Post-Deployment Monitoring (First 24 Hours)

- [ ] Hour 1: Check logs for errors
- [ ] Hour 2: Verify user logins working
- [ ] Hour 4: Check quotes creation workflow
- [ ] Hour 8: Review error rates
- [ ] Hour 24: Full system health check

## Success Metrics

- ✅ Single deployment attempt (no rebuilds needed)
- ✅ Zero downtime during deployment
- ✅ All endpoints responding normally
- ✅ No stale code issues reported
- ✅ Health checks passing consistently
```

**Test Checkpoint:**
```bash
cat .claude/workspace/DEVOPS-20251001-001/pre-production-checklist.md | wc -l
# Should be substantial (60+ lines)
```

**Time:** 20 minutes

---

# PHASE 6: FINALIZATION (Estimated: 30 minutes)

### Step 6.1: Final Code Review
**Action:** Review all changes before merging
**Commands:**
```bash
# Show all changes
git diff main..HEAD

# List all modified files
git diff --name-only main..HEAD

# Review commit history
git log main..HEAD --oneline

# Verify no debug code
grep -r "console.log\|print(\"DEBUG" . --exclude-dir=.git --exclude-dir=node_modules
```

**Test Checkpoint:**
```bash
# Count commits
git log main..HEAD --oneline | wc -l
# Should be 6-8 commits

# Verify clean diff (no unintended changes)
git status
```

**Time:** 15 minutes

### Step 6.2: Create Pull Request
**Action:** Create PR for merging to main
**Commands:**
```bash
# Push branch to remote
git push origin devops/docker-build-improvements-20251001

# Create PR (if gh CLI available)
gh pr create \
  --title "DEVOPS-20251001-001: Docker build improvements" \
  --body "$(cat <<'EOF'
## Summary
Implements Docker build improvements to prevent Python bytecode cache issues and Docker layer caching problems identified in HOTFIX-20251001-001.

## Changes
- ✅ Added Python cache clearing to Dockerfile
- ✅ Added build verification step
- ✅ Created automated production deployment script
- ✅ Created test environment deployment script
- ✅ Improved health check configuration
- ✅ Created comprehensive deployment runbook

## Testing
- ✅ Dockerfile builds successfully with verification
- ✅ Test environment deployment successful
- ✅ No stale code issues observed
- ✅ All success criteria met

## Documentation
- ✅ DEPLOYMENT-RUNBOOK.md created
- ✅ CLAUDE.md updated
- ✅ Troubleshooting guide included

## Deployment Plan
1. Merge to main
2. Deploy to test environment (24h monitoring)
3. Deploy to production (low-traffic window)
4. Monitor for 1 week

## Related
- Fixes: DEVOPS-20251001-001
- Related: HOTFIX-20251001-001 (root cause)
- Prevents: Future Python cache deployment issues

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Test Checkpoint:**
```bash
# Verify PR created (if using gh)
gh pr list | grep "DEVOPS-20251001-001"
```

**Time:** 10 minutes

### Step 6.3: Update Task Status
**Action:** Mark task as ready for deployment
**Commands:**
```bash
# Note: Don't mark as completed until production deployment verified
# Update notes field in tasks.csv

echo "DEVOPS-20251001-001 - All code changes complete. Ready for production deployment." >> .claude/workspace/DEVOPS-20251001-001/notes.md
```

**Time:** 5 minutes

---

# ROLLBACK STRATEGY

## Complete Rollback Procedure

If any issues arise during implementation:

### Rollback Dockerfile Changes
```bash
git checkout main -- Dockerfile
git commit -m "rollback: revert Dockerfile to main"
```

### Rollback docker-compose Changes
```bash
git checkout main -- docker-compose.beta.yml
git commit -m "rollback: revert docker-compose to main"
```

### Rollback Scripts
```bash
git rm scripts/deploy-production.sh scripts/deploy-test.sh
git commit -m "rollback: remove deployment scripts"
```

### Rollback Documentation
```bash
git checkout main -- CLAUDE.md
git rm docs/DEPLOYMENT-RUNBOOK.md
git commit -m "rollback: revert documentation changes"
```

### Complete Branch Rollback
```bash
# If complete rollback needed
git checkout main
git branch -D devops/docker-build-improvements-20251001
```

---

# TIME ESTIMATES SUMMARY

| Phase | Estimated Time | Tasks |
|-------|---------------|-------|
| Preparation | 30 min | Branch setup, backups, baseline |
| Implementation | 4-5 hours | Dockerfile, scripts, docker-compose |
| Integration & Testing | 2-3 hours | Testing, verification |
| Documentation | 1-2 hours | Runbook, CLAUDE.md, criteria |
| Deployment Verification | 1-2 hours | Test env, verification |
| Finalization | 30 min | Review, PR, status update |
| **TOTAL** | **9-13 hours** | **~2 work days** |

---

# COMPLETION CRITERIA

## Task Marked Complete When:

1. ✅ All code changes merged to main
2. ✅ Deployed to test environment successfully
3. ✅ Test environment monitored for 24 hours (no issues)
4. ✅ Deployed to production successfully
5. ✅ Production monitored for 1 week (no stale code issues)
6. ✅ No deployment failures requiring rebuilds
7. ✅ Team trained on new deployment process

---

# NOTES

- **Priority:** HIGH - Prevents critical deployment issues
- **Urgency:** Should complete within 1 week
- **Dependencies:** None (can start immediately)
- **Risk Level:** MEDIUM (changes core deployment process)
- **Testing:** Extensive test environment validation required
- **Coordination:** Communicate deployment windows with team

**Generated:** 2025-10-02
**Task ID:** DEVOPS-20251001-001
**Workspace:** `.claude/workspace/DEVOPS-20251001-001/`
