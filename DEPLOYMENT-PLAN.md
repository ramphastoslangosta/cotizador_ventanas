# Deployment Plan: TASK-001, TASK-002, TASK-003
**Created:** September 30, 2025
**Target:** Production Beta Deployment
**Strategy:** Incremental deployment with testing validation

---

## 📋 Deployment Overview

### Sequence
1. **TASK-003** → Production (already tested in test env)
2. **TASK-001** → Test env → Production
3. **TASK-002** → Test env → Production

### Rationale
- TASK-003 already validated in test environment
- TASK-001 and TASK-002 need test environment validation first
- Incremental approach reduces risk
- Each deployment can be validated independently

---

## 🚀 TASK-003: Production Deployment

### Status
- ✅ Code complete
- ✅ Tested in test environment
- ✅ All issues fixed
- ✅ Documentation complete
- ⚠️ Ready for production deployment

### Pre-Deployment Checklist
- [x] Test environment verified working
- [x] All routes functional
- [x] Database connections stable
- [x] API endpoints returning correct data
- [x] Frontend working correctly
- [x] Documentation created
- [ ] **Production backup created**
- [ ] Deployment window scheduled

### Deployment Steps

#### 1. Backup Production Database
```bash
ssh root@159.65.174.94 "docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/prod_backup_before_task003_\$(date +%Y%m%d_%H%M%S).sql"

# Verify backup
ssh root@159.65.174.94 "ls -lh /tmp/prod_backup_before_task003_*.sql | tail -1"
```

#### 2. Deploy Code to Production
```bash
# Pull latest code
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  git fetch origin && \
  git checkout refactor/workorder-material-routes-20250929 && \
  git pull origin refactor/workorder-material-routes-20250929"

# Verify current branch
ssh root@159.65.174.94 "cd /home/ventanas/app && git branch --show-current"
```

#### 3. Rebuild and Restart
```bash
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  docker-compose build app && \
  docker-compose up -d app"
```

#### 4. Monitor Deployment
```bash
# Wait for container to start
sleep 10

# Check container status
ssh root@159.65.174.94 "docker ps | grep ventanas-beta-app"

# Check logs for errors
ssh root@159.65.174.94 "docker logs ventanas-beta-app --tail 50"

# Check application logs
ssh root@159.65.174.94 "tail -50 /home/ventanas/app/logs/error.log"
```

#### 5. Verify Deployment
```bash
# Test if app responds
ssh root@159.65.174.94 "curl -I http://localhost:8000"

# Test login endpoint
ssh root@159.65.174.94 "curl -X POST http://localhost:8000/web/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'email=admin@test.com&password=admin123' -I"

# Test materials API
ssh root@159.65.174.94 "curl http://localhost:8000/api/materials/by-category"

# Test work orders page (via browser)
# http://159.65.174.94:8000/work-orders
```

### Verification Checklist
- [ ] Container running and healthy
- [ ] No errors in logs
- [ ] Login works
- [ ] Materials catalog loads
- [ ] Color dropdown shows options
- [ ] Work orders page accessible
- [ ] Quote-to-work-order conversion works

### Rollback Plan (If Needed)
```bash
# 1. Checkout previous version
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  git checkout main"

# 2. Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  docker-compose build app && \
  docker-compose up -d app"

# 3. Verify rollback
ssh root@159.65.174.94 "curl -I http://localhost:8000"
```

### Post-Deployment
- [ ] Monitor logs for 30 minutes
- [ ] Test all critical user flows
- [ ] Update TASK_STATUS.md
- [ ] Notify team of deployment

### Expected Duration
- **Deployment**: 15-20 minutes
- **Verification**: 15-20 minutes
- **Total**: ~40 minutes

---

## 🧪 TASK-001: Auth Routes Deployment

### Status
- ✅ Code complete (on branch `refactor/auth-routes-20250929`)
- ❌ Not tested in test environment yet
- ❌ Not deployed to production

### Pre-Deployment Checklist
- [x] Code complete
- [x] Branch exists: `refactor/auth-routes-20250929`
- [ ] Test environment verification
- [ ] Production deployment

### Phase 1: Deploy to Test Environment

#### 1. Deploy to Test
```bash
# Pull code to test environment
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git fetch origin && \
  git checkout refactor/auth-routes-20250929 && \
  git pull origin refactor/auth-routes-20250929"

# Verify branch
ssh root@159.65.174.94 "cd /home/ventanas/app-test && git branch --show-current"

# Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"
```

#### 2. Monitor Test Deployment
```bash
# Wait for startup
sleep 10

# Check logs
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 50"

# Test endpoint
ssh root@159.65.174.94 "curl -I http://localhost:8001"
```

#### 3. Test Auth Routes
```bash
# Test login
ssh root@159.65.174.94 "curl -X POST http://localhost:8001/web/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'email=admin@test.com&password=admin123' -v"

# Test register page
ssh root@159.65.174.94 "curl -I http://localhost:8001/register"

# Test /auth/me endpoint
ssh root@159.65.174.94 "curl http://localhost:8001/auth/me"
```

#### 4. Manual Testing in Test Environment
**URL:** http://159.65.174.94:8001

Test these flows:
- [ ] Login with existing user
- [ ] Logout
- [ ] Register new user
- [ ] Session persistence
- [ ] Protected routes redirect to login
- [ ] /auth/me returns user info when logged in

#### 5. Fix Any Issues
If issues are found:
1. Document the issue
2. Fix in local environment
3. Commit and push fix
4. Redeploy to test environment
5. Re-test

### Phase 2: Deploy to Production (After Test Verification)

#### 1. Pre-Deployment
```bash
# Backup production database
ssh root@159.65.174.94 "docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/prod_backup_before_task001_\$(date +%Y%m%d_%H%M%S).sql"
```

#### 2. Deploy to Production
```bash
# Pull code
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  git fetch origin && \
  git checkout refactor/auth-routes-20250929 && \
  git pull origin refactor/auth-routes-20250929"

# Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  docker-compose build app && \
  docker-compose up -d app"
```

#### 3. Verify Production Deployment
```bash
# Check status
ssh root@159.65.174.94 "docker ps | grep ventanas-beta-app"

# Check logs
ssh root@159.65.174.94 "docker logs ventanas-beta-app --tail 50"

# Test login
ssh root@159.65.174.94 "curl -I http://localhost:8000/login"
```

### Files Created/Modified
- `app/routes/auth.py` (274 lines) - Auth routes
- `app/dependencies/auth.py` (101 lines) - Auth dependencies
- `main.py` - Router registration

### Expected Duration
- **Test Deployment**: 20 minutes
- **Testing**: 30 minutes
- **Production Deployment**: 15 minutes
- **Total**: ~65 minutes

---

## 📊 TASK-002: Quote Routes Deployment

### Status
- ✅ Code complete (on branch `refactor/quote-routes-20250929`)
- ❌ Not tested in test environment yet
- ❌ Not deployed to production

### Pre-Deployment Checklist
- [x] Code complete
- [x] Branch exists: `refactor/quote-routes-20250929`
- [ ] Test environment verification
- [ ] Production deployment

### Phase 1: Deploy to Test Environment

#### 1. Deploy to Test
```bash
# Pull code to test environment
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  git fetch origin && \
  git checkout refactor/quote-routes-20250929 && \
  git pull origin refactor/quote-routes-20250929"

# Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app-test && \
  docker-compose -f docker-compose.test.yml build app && \
  docker-compose -f docker-compose.test.yml up -d app"
```

#### 2. Monitor Test Deployment
```bash
# Wait and check logs
sleep 10
ssh root@159.65.174.94 "docker logs ventanas-test-app --tail 50"
```

#### 3. Test Quote Routes
```bash
# Test quote list page
ssh root@159.65.174.94 "curl -I http://localhost:8001/quotes"

# Test new quote page
ssh root@159.65.174.94 "curl -I http://localhost:8001/quotes/new"

# Test quote calculation API
ssh root@159.65.174.94 "curl http://localhost:8001/quotes/calculate"
```

#### 4. Manual Testing in Test Environment
**URL:** http://159.65.174.94:8001

Test these flows:
- [ ] View quote list
- [ ] Create new quote
- [ ] Calculate quote with window items
- [ ] Edit quote (QE-001 feature)
- [ ] View quote details
- [ ] Generate PDF
- [ ] Delete quote
- [ ] Quote search/filter

#### 5. Test Integration with Other Features
Since TASK-001 and TASK-003 may be deployed:
- [ ] Login → Create quote
- [ ] Create quote → Convert to work order (if TASK-003 deployed)
- [ ] Quote with material color selection

### Phase 2: Deploy to Production (After Test Verification)

#### 1. Pre-Deployment
```bash
# Backup production database
ssh root@159.65.174.94 "docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/prod_backup_before_task002_\$(date +%Y%m%d_%H%M%S).sql"
```

#### 2. Deploy to Production
```bash
# Pull code
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  git fetch origin && \
  git checkout refactor/quote-routes-20250929 && \
  git pull origin refactor/quote-routes-20250929"

# Rebuild and restart
ssh root@159.65.174.94 "cd /home/ventanas/app && \
  docker-compose build app && \
  docker-compose up -d app"
```

#### 3. Verify Production Deployment
```bash
# Check status
ssh root@159.65.174.94 "docker ps | grep ventanas-beta-app"

# Check logs
ssh root@159.65.174.94 "docker logs ventanas-beta-app --tail 50"

# Test quotes page
ssh root@159.65.174.94 "curl -I http://localhost:8000/quotes"
```

### Files Created/Modified
- `app/routes/quotes.py` (659 lines) - Quote routes
- `main.py` - Router registration

### Expected Duration
- **Test Deployment**: 20 minutes
- **Testing**: 45 minutes (more complex functionality)
- **Production Deployment**: 15 minutes
- **Total**: ~80 minutes

---

## 📅 Deployment Schedule

### Recommended Timeline

#### Day 1: TASK-003 Production Deployment
**Time Required:** ~1 hour
1. Create production backup (5 min)
2. Deploy code (10 min)
3. Verify deployment (20 min)
4. Monitor and test (25 min)

**Success Criteria:**
- Production running TASK-003 code
- All routes working
- No errors in logs
- User can access work orders and materials

---

#### Day 2: TASK-001 Test Deployment
**Time Required:** ~1 hour
1. Deploy to test environment (10 min)
2. Test auth routes (30 min)
3. Fix any issues (20 min)
4. Re-test if needed

**Success Criteria:**
- Test environment running TASK-001 code
- All auth routes working
- Login/logout functional
- Ready for production deployment

---

#### Day 3: TASK-001 Production Deployment
**Time Required:** ~30 minutes
1. Create production backup (5 min)
2. Deploy code (10 min)
3. Verify deployment (15 min)

**Success Criteria:**
- Production running TASK-001 + TASK-003 code
- Auth system working
- No functionality broken

---

#### Day 4: TASK-002 Test Deployment
**Time Required:** ~1.5 hours
1. Deploy to test environment (10 min)
2. Test quote routes (45 min)
3. Fix any issues (30 min)
4. Re-test if needed

**Success Criteria:**
- Test environment running TASK-002 code
- All quote features working
- Integration with auth working
- Ready for production deployment

---

#### Day 5: TASK-002 Production Deployment
**Time Required:** ~45 minutes
1. Create production backup (5 min)
2. Deploy code (10 min)
3. Verify deployment (30 min)

**Success Criteria:**
- Production running all three task branches
- Complete refactored routing system live
- All features working together

---

## 🔄 Complete Deployment Commands

### Quick Deploy: TASK-003 to Production
```bash
# Full deployment script
ssh root@159.65.174.94 'bash -s' <<'EOF'
set -e
echo "🚀 Deploying TASK-003 to Production..."

# Backup
echo "📦 Creating backup..."
docker exec ventanas-beta-db sh -c \
  'PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER \
  -d ventanas_beta_db --clean --if-exists' \
  > /tmp/prod_backup_task003_$(date +%Y%m%d_%H%M%S).sql

# Deploy
echo "🔄 Pulling code..."
cd /home/ventanas/app
git fetch origin
git checkout refactor/workorder-material-routes-20250929
git pull origin refactor/workorder-material-routes-20250929

echo "🏗️  Building..."
docker-compose build app

echo "🚀 Restarting..."
docker-compose up -d app

echo "⏳ Waiting for startup..."
sleep 10

echo "✅ Checking status..."
docker ps | grep ventanas-beta-app
docker logs ventanas-beta-app --tail 20

echo "✨ Deployment complete!"
EOF
```

### Quick Deploy: TASK-001 to Test
```bash
ssh root@159.65.174.94 'bash -s' <<'EOF'
set -e
echo "🧪 Deploying TASK-001 to Test Environment..."

cd /home/ventanas/app-test
git fetch origin
git checkout refactor/auth-routes-20250929
git pull origin refactor/auth-routes-20250929

docker-compose -f docker-compose.test.yml build app
docker-compose -f docker-compose.test.yml up -d app

sleep 10
docker logs ventanas-test-app --tail 20

echo "✨ Test deployment complete!"
echo "🔗 Test at: http://159.65.174.94:8001"
EOF
```

### Quick Deploy: TASK-002 to Test
```bash
ssh root@159.65.174.94 'bash -s' <<'EOF'
set -e
echo "🧪 Deploying TASK-002 to Test Environment..."

cd /home/ventanas/app-test
git fetch origin
git checkout refactor/quote-routes-20250929
git pull origin refactor/quote-routes-20250929

docker-compose -f docker-compose.test.yml build app
docker-compose -f docker-compose.test.yml up -d app

sleep 10
docker logs ventanas-test-app --tail 20

echo "✨ Test deployment complete!"
echo "🔗 Test at: http://159.65.174.94:8001"
EOF
```

---

## 📊 Deployment Progress Tracker

### TASK-003
- [ ] Production backup created
- [ ] Code deployed
- [ ] Container restarted
- [ ] Logs checked (no errors)
- [ ] Login tested
- [ ] Materials catalog tested
- [ ] Work orders tested
- [ ] Monitoring (30 minutes)
- [ ] Status: ⬜ Not Started

### TASK-001
- [ ] Test deployment
- [ ] Test verification
- [ ] Issues fixed (if any)
- [ ] Production backup created
- [ ] Production deployment
- [ ] Production verification
- [ ] Status: ⬜ Not Started

### TASK-002
- [ ] Test deployment
- [ ] Test verification
- [ ] Issues fixed (if any)
- [ ] Production backup created
- [ ] Production deployment
- [ ] Production verification
- [ ] Status: ⬜ Not Started

---

## ⚠️ Important Notes

### Database Compatibility
All three tasks use the same database schema - no migrations required.

### Router Precedence
- FastAPI registers routers in order
- New routers take precedence over old routes in main.py
- Duplicate routes in main.py are never reached
- Safe to deploy without removing duplicates (TASK-012 can come later)

### Rollback Strategy
Each deployment can be independently rolled back:
```bash
# Rollback to main branch
git checkout main
docker-compose build app
docker-compose up -d app
```

### Monitoring
After each deployment, monitor:
- Docker container logs
- Application log files (`/home/ventanas/app/logs/`)
- User reports
- Error rates

---

## 📚 Reference Documentation

- **Test Environment Guide**: `docs/TEST-ENVIRONMENT-GUIDE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Quick Reference**: `docs/QUICK-TROUBLESHOOTING-CHECKLIST.md`
- **Lessons Learned**: `docs/LESSONS-LEARNED-TEST-ENV-20250930.md`

---

**Ready to begin?** Start with TASK-003 production deployment.

*Created: 2025-09-30*
*Generated with [Claude Code](https://claude.com/claude-code)*
