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
