# TASK-003 Deployment Blocker - Dockerfile Issue

**Date**: 2025-09-29
**Status**: ⚠️ BLOCKED - Cannot deploy to droplet
**Issue**: Dockerfile dependency package name change

---

## 🚨 Problem

Docker build fails on droplet with the following error:

```
E: Package 'libgdk-pixbuf2.0-dev' has no installation candidate
However the following packages replace it:
  libgdk-pixbuf-xlib-2.0-dev
```

### Root Cause

The package `libgdk-pixbuf2.0-dev` has been obsoleted in Debian Trixie (the base for `python:3.11-slim`). It has been replaced by `libgdk-pixbuf-xlib-2.0-dev`.

### Impact

- ❌ Cannot rebuild Docker container with new code
- ❌ Cannot test TASK-003 work order and material routes on droplet
- ⚠️ Old container running main branch (not TASK-003)
- ✅ PR #6 created and code pushed successfully
- ✅ Local code validated (syntax checks passed)

---

## 🔧 Solution

### Quick Fix (Immediate)

Update the Dockerfile to use the correct package name:

**File**: `Dockerfile`
**Line**: ~15-25 (the RUN apt-get install section)

**Change**:
```dockerfile
# OLD (broken)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \      # ❌ Obsolete package
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

**To**:
```dockerfile
# NEW (fixed)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-xlib-2.0-dev \  # ✅ New package name
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

---

## 📋 Deployment Steps After Fix

### 1. Fix Dockerfile

```bash
# On local machine
cd /Users/rafaellang/cotizador/cotizador_ventanas

# Edit Dockerfile to change package name
# (see above)

# Commit fix
git add Dockerfile
git commit -m "fix(docker): update libgdk-pixbuf package name for Debian Trixie

Replace obsolete libgdk-pixbuf2.0-dev with libgdk-pixbuf-xlib-2.0-dev
to fix Docker build on python:3.11-slim base image.

Fixes: TASK-003 deployment blocker

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to TASK-003 branch
git push origin refactor/workorder-material-routes-20250929
```

### 2. Deploy to Droplet

```bash
# SSH to droplet
ssh root@159.65.174.94

# Navigate to app directory
cd /home/ventanas/app

# Pull latest changes (includes Dockerfile fix)
git pull origin refactor/workorder-material-routes-20250929

# Stop container
docker-compose -f docker-compose.beta.yml stop app

# Rebuild with fix
docker-compose -f docker-compose.beta.yml up -d --build app

# Wait for startup
sleep 15

# Verify
curl http://localhost:8000/api/health
```

### 3. Test TASK-003 Routes

After successful deployment, run the testing checklist:

#### Work Order Routes
```bash
# Test work orders list page
curl http://159.65.174.94:8000/work-orders

# Test API endpoints
curl http://159.65.174.94:8000/api/work-orders

# Test with authentication (get cookie first)
curl -c cookies.txt -X POST http://159.65.174.94:8000/web/login \
  -d "email=test@example.com&password=password"

curl -b cookies.txt http://159.65.174.94:8000/work-orders
curl -b cookies.txt http://159.65.174.94:8000/api/work-orders
```

#### Material Routes
```bash
# Test materials catalog page
curl -b cookies.txt http://159.65.174.94:8000/materials_catalog

# Test products catalog page
curl -b cookies.txt http://159.65.174.94:8000/products_catalog

# Test API endpoints
curl -b cookies.txt http://159.65.174.94:8000/api/materials
curl -b cookies.txt http://159.65.174.94:8000/api/products
curl -b cookies.txt http://159.65.174.94:8000/api/materials/by-category
```

---

## 🎯 Testing Checklist

Once deployment succeeds, verify:

### Work Orders (9 routes)
- [ ] GET /work-orders (HTML list page)
- [ ] GET /work-orders/{id} (HTML detail page)
- [ ] POST /api/work-orders/from-quote
- [ ] GET /api/work-orders
- [ ] GET /api/work-orders/{id}
- [ ] PUT /api/work-orders/{id}/status
- [ ] PUT /api/work-orders/{id}
- [ ] DELETE /api/work-orders/{id}
- [ ] QTO-001: Quote → Work Order conversion

### Materials & Products (21 routes)
- [ ] GET /materials_catalog (HTML)
- [ ] GET /products_catalog (HTML)
- [ ] GET /api/materials
- [ ] POST /api/materials
- [ ] PUT /api/materials/{id}
- [ ] DELETE /api/materials/{id}
- [ ] GET /api/products
- [ ] POST /api/products
- [ ] PUT /api/products/{id}
- [ ] DELETE /api/products/{id}
- [ ] GET /api/materials/{id}/colors
- [ ] POST /api/materials/{id}/colors
- [ ] DELETE /api/materials/colors/{id}
- [ ] GET /api/materials/by-category
- [ ] GET /api/materials/csv/export
- [ ] POST /api/materials/csv/import
- [ ] GET /api/materials/csv/template
- [ ] GET /api/products/csv/export
- [ ] POST /api/products/csv/import
- [ ] GET /api/products/csv/template
- [ ] Material-color relationships work

---

## 📊 Current Status

### Completed ✅
- TASK-003 code written and committed
- PR #6 created: https://github.com/ramphastoslangosta/cotizador_ventanas/pull/6
- Code pushed to GitHub
- Local syntax validation passed
- Comprehensive documentation created

### Blocked ⚠️
- Docker build fails on droplet
- Cannot deploy new routers to testing environment
- Testing checklist cannot be completed

### Required Actions
1. ✅ Fix Dockerfile package name (see solution above)
2. ⏳ Push Dockerfile fix to branch
3. ⏳ Rebuild container on droplet
4. ⏳ Run testing checklist
5. ⏳ Verify all 30 routes work

---

## 🔗 Related Files

- **Dockerfile**: Needs libgdk-pixbuf package update
- **PR #6**: https://github.com/ramphastoslangosta/cotizador_ventanas/pull/6
- **PUSH_STRATEGY.md**: Overall push strategy
- **TASK_STATUS.md**: Task progress tracking
- **app/routes/work_orders.py**: Work order routes (335 lines)
- **app/routes/materials.py**: Material routes (517 lines)

---

## 💡 Prevention

### For Future Deployments

1. **Test Docker builds locally** before pushing
2. **Pin base image versions** to avoid unexpected updates:
   ```dockerfile
   FROM python:3.11.9-slim  # Instead of python:3.11-slim
   ```
3. **Use multi-stage builds** to minimize dependencies
4. **Consider Alpine Linux** base image as alternative

### Alternative: Use main branch Dockerfile

If the droplet's main branch has a working Dockerfile, you could:
```bash
git checkout main -- Dockerfile
git add Dockerfile
git commit -m "fix: use working Dockerfile from main branch"
```

---

## ⏱️ Time Estimate

- **Dockerfile fix**: 5 minutes
- **Build + deploy**: 10 minutes
- **Testing**: 30-45 minutes
- **Total**: ~1 hour

---

**Status**: Waiting for Dockerfile fix to proceed with testing

**Next Action**: Apply Dockerfile fix and redeploy

---

*Document created: 2025-09-29*
*Last updated: After TASK-003 deployment attempt*