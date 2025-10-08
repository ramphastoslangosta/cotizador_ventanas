# Test Environment Deployment Guide
## ARCH-20251007-001: Glass Pricing Database Implementation

**Target**: Production droplet test environment (port 8001)
**IP**: 159.65.174.94
**Date**: 2025-10-08

---

## Pre-Deployment Checklist

- [x] Feature branch merged to main
- [x] All tests passed in local Docker
- [x] Code pushed to origin/main
- [ ] SSH access to droplet confirmed
- [ ] Test environment currently running
- [ ] Database backup created

---

## Deployment Steps

### Step 1: Connect to Droplet
```bash
ssh root@159.65.174.94
# Or your configured SSH alias
```

### Step 2: Navigate to Project Directory
```bash
cd /root/cotizador_ventanas
# Or wherever the project is located

# Verify current directory
pwd
ls -la
```

### Step 3: Check Current Status
```bash
# Check current branch and commits
git branch
git log --oneline | head -5

# Check running containers
docker ps | grep cotizador
```

### Step 4: Pull Latest Changes
```bash
# Fetch latest from origin
git fetch origin

# Pull main branch
git checkout main
git pull origin main

# Verify we have the glass pricing commits
git log --oneline | grep -i "glass\|ARCH-20251007"
```

Expected output should show:
- `d79559d docs: update tasks.csv - mark ARCH-20251007-001 as completed`
- `3ccf738 Merge arch/glass-pricing-database-20251007`

### Step 5: Deploy to Test Environment (Port 8001)
```bash
# Deploy using test deployment script
bash scripts/deploy-test.sh
```

**What this does:**
- Builds Docker image with latest code
- Starts containers on port 8001
- Runs health checks
- Verifies deployment

**Expected output:**
```
Building test environment...
✅ Build complete
Starting containers...
✅ Containers started
Health check: OK
🎉 Test deployment complete on port 8001
```

### Step 6: Verify Containers Running
```bash
# Check container status
docker ps | grep test

# Should see:
# cotizador_test_app     (port 8001)
# cotizador_test_db      (postgres)
# cotizador_test_redis   (redis)
```

### Step 7: Check Application Logs
```bash
# View recent logs
docker logs cotizador_test_app --tail 50

# Look for:
# - "Application startup complete"
# - No errors
# - Uvicorn running on 0.0.0.0:8001
```

### Step 8: Create Glass Materials in Test Database
```bash
docker exec cotizador_test_app python -c "
from database import SessionLocal, DatabaseMaterialService
from models.product_bom_models import MaterialUnit
from decimal import Decimal

db = SessionLocal()
material_service = DatabaseMaterialService(db)

# Glass materials with correct codes
glass_materials = [
    ('VID-CLARO-4', 'Vidrio Claro 4mm', Decimal('85.00')),
    ('VID-CLARO-6', 'Vidrio Claro 6mm', Decimal('120.00')),
    ('VID-BRONCE-4', 'Vidrio Bronce 4mm', Decimal('95.00')),
    ('VID-BRONCE-6', 'Vidrio Bronce 6mm', Decimal('135.00')),
    ('VID-REFLECTIVO-6', 'Vidrio Reflectivo 6mm', Decimal('180.00')),
    ('VID-LAMINADO-6', 'Vidrio Laminado 6mm', Decimal('220.00')),
]

created_count = 0
for code, name, cost in glass_materials:
    existing = material_service.get_material_by_code(code)
    if not existing:
        material_service.create_material(
            name=name,
            code=code,
            unit=MaterialUnit.M2.value,
            category='Vidrio',
            cost_per_unit=cost,
            description=f'{name} para ventanas'
        )
        print(f'✓ Created: {code} - {name} - \${cost}/m²')
        created_count += 1
    else:
        print(f'⚠ Already exists: {code}')

print(f'\n✅ Glass materials setup complete: {created_count} created')
db.close()
"
```

**Expected output:**
```
✓ Created: VID-CLARO-4 - Vidrio Claro 4mm - $85.00/m²
✓ Created: VID-CLARO-6 - Vidrio Claro 6mm - $120.00/m²
✓ Created: VID-BRONCE-4 - Vidrio Bronce 4mm - $95.00/m²
✓ Created: VID-BRONCE-6 - Vidrio Bronce 6mm - $135.00/m²
✓ Created: VID-REFLECTIVO-6 - Vidrio Reflectivo 6mm - $180.00/m²
✓ Created: VID-LAMINADO-6 - Vidrio Laminado 6mm - $220.00/m²

✅ Glass materials setup complete: 6 created
```

### Step 9: Verify Glass Materials in Database
```bash
docker exec cotizador_test_db psql -U ventanas_user -d ventanas_test_db -c "
SELECT code, name, cost_per_unit, category
FROM app_materials
WHERE category = 'Vidrio'
ORDER BY code;
"
```

**Expected output:**
```
       code       |           name           | cost_per_unit | category
------------------+--------------------------+---------------+----------
 VID-BRONCE-4     | Vidrio Bronce 4mm        |       95.0000 | Vidrio
 VID-BRONCE-6     | Vidrio Bronce 6mm        |      135.0000 | Vidrio
 VID-CLARO-4      | Vidrio Claro 4mm         |       85.0000 | Vidrio
 VID-CLARO-6      | Vidrio Claro 6mm         |      120.0000 | Vidrio
 VID-LAMINADO-6   | Vidrio Laminado 6mm      |      220.0000 | Vidrio
 VID-REFLECTIVO-6 | Vidrio Reflectivo 6mm    |      180.0000 | Vidrio
 VID-TEMP-6       | Vidrio Templado 6mm      |      195.0000 | Vidrio
(7 rows)
```

### Step 10: Run Verification Script
```bash
# Copy verification script
cat > /tmp/verify_glass_pricing.py << 'EOF'
from database import SessionLocal, DatabaseMaterialService
from services.product_bom_service_db import ProductBOMServiceDB, GLASS_TYPE_TO_MATERIAL_CODE
from models.quote_models import GlassType
from decimal import Decimal

db = SessionLocal()
material_service = DatabaseMaterialService(db)
bom_service = ProductBOMServiceDB(db)

print("\n" + "="*60)
print("GLASS PRICING VERIFICATION - TEST ENVIRONMENT")
print("="*60)

# Test all glass types
print("\n1. Glass Prices from Database:")
all_ok = True
for glass_type, material_code in GLASS_TYPE_TO_MATERIAL_CODE.items():
    material = material_service.get_material_by_code(material_code)
    if material:
        price = bom_service.get_glass_cost_per_m2(glass_type)
        print(f"  ✓ {glass_type.value}: ${price}/m² (code: {material_code})")
    else:
        print(f"  ✗ {glass_type.value}: NOT FOUND (code: {material_code})")
        all_ok = False

# Test price update
print("\n2. Price Update Test:")
glass_type = GlassType.CLARO_6MM
material = material_service.get_material_by_code('VID-CLARO-6')
original_price = material.cost_per_unit
test_price = original_price * Decimal("1.25")

material_service.update_material(material.id, cost_per_unit=test_price)
bom_service.clear_glass_price_cache()
updated_price = bom_service.get_glass_cost_per_m2(glass_type)

if updated_price == test_price:
    print(f"  ✓ Price update successful: ${original_price} → ${test_price}")
    # Restore
    material_service.update_material(material.id, cost_per_unit=original_price)
    bom_service.clear_glass_price_cache()
    print(f"  ✓ Restored original price: ${original_price}")
else:
    print(f"  ✗ Price update failed")
    all_ok = False

print("\n" + "="*60)
if all_ok:
    print("✅ ALL TESTS PASSED - Implementation working correctly!")
else:
    print("❌ SOME TESTS FAILED - Check configuration")
print("="*60 + "\n")

db.close()
EOF

# Run verification
docker exec -i cotizador_test_app python < /tmp/verify_glass_pricing.py
```

### Step 11: Test via Browser/API

**Access test environment:**
```
http://159.65.174.94:8001/
```

**Test checklist:**
- [ ] Login page loads
- [ ] Dashboard accessible
- [ ] Materials catalog loads (`/materials_catalog`)
- [ ] Glass materials visible (VID-CLARO-4, VID-CLARO-6, etc.)
- [ ] Can create new quote (`/quotes/new`)
- [ ] Quote calculation works with database glass prices

**API test (from local machine):**
```bash
# Test health endpoint
curl http://159.65.174.94:8001/

# Test materials API (requires authentication)
# You'll need to login first to get session cookie
```

---

## Post-Deployment Verification

### Verify Deployment Success
```bash
# Check container health
docker ps | grep test

# Check application logs for errors
docker logs cotizador_test_app --tail 100 | grep -i error

# Check database connectivity
docker exec cotizador_test_app python -c "from database import SessionLocal; db = SessionLocal(); print('✓ DB connected'); db.close()"

# Verify glass materials count
docker exec cotizador_test_db psql -U ventanas_user -d ventanas_test_db -c "SELECT COUNT(*) FROM app_materials WHERE category = 'Vidrio';"
```

Expected: **7 rows** (or more if old materials exist)

---

## Smoke Tests

### Test 1: Glass Price Retrieval
```bash
docker exec cotizador_test_app python -c "
from database import SessionLocal
from services.product_bom_service_db import ProductBOMServiceDB
from models.quote_models import GlassType

db = SessionLocal()
service = ProductBOMServiceDB(db)
price = service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
print(f'CLARO_6MM price: \${price}/m²')
assert price == 120.00, f'Expected \$120, got \${price}'
print('✅ Test passed')
db.close()
"
```

### Test 2: Quote Calculation
```bash
docker exec cotizador_test_app python -c "
from database import SessionLocal
from services.product_bom_service_db import ProductBOMServiceDB
from models.quote_models import GlassType
from decimal import Decimal

db = SessionLocal()
service = ProductBOMServiceDB(db)

# Calculate glass cost for 1.5m² window
area = Decimal('1.5')
waste = Decimal('1.05')
glass_price = service.get_glass_cost_per_m2(GlassType.CLARO_6MM)
total = area * glass_price * waste

print(f'Quote calculation test:')
print(f'  Area: {area} m²')
print(f'  Glass price: \${glass_price}/m²')
print(f'  Waste factor: {waste}')
print(f'  Total: \${total:.2f}')
assert total == Decimal('189.00'), f'Expected \$189.00, got \${total}'
print('✅ Test passed')
db.close()
"
```

### Test 3: Price Update via Materials Catalog

**Manual test via browser:**
1. Login to test environment: `http://159.65.174.94:8001/`
2. Navigate to Materials Catalog
3. Find "Vidrio Claro 6mm" (VID-CLARO-6)
4. Edit price: $120.00 → $150.00
5. Save changes
6. Create new quote with CLARO_6MM glass
7. Verify glass cost uses new price ($150)

---

## Monitoring (24-Hour Period)

### Application Logs
```bash
# Monitor logs in real-time
docker logs cotizador_test_app -f

# Check for errors
docker logs cotizador_test_app --since 1h | grep -i "error\|warning\|fail"

# Check glass pricing logs
docker logs cotizador_test_app --since 1h | grep -i "glass"
```

### Database Monitoring
```bash
# Check for slow queries
docker exec cotizador_test_db psql -U ventanas_user -d ventanas_test_db -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%app_materials%'
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Monitor active connections
docker exec cotizador_test_db psql -U ventanas_user -d ventanas_test_db -c "
SELECT COUNT(*) as active_connections FROM pg_stat_activity;
"
```

### Performance Metrics
Monitor for 24 hours:
- [ ] Quote calculation time <200ms
- [ ] Glass price lookup <5ms (cached)
- [ ] No database errors
- [ ] No application crashes
- [ ] Memory usage stable
- [ ] CPU usage normal

---

## Rollback Plan (If Issues Found)

### Quick Rollback to Previous Version
```bash
# Stop test environment
docker-compose -f docker-compose.test.yml down

# Checkout previous commit
git checkout 523c7a7  # Before glass pricing merge

# Rebuild and deploy
bash scripts/deploy-test.sh

# Verify rollback
curl http://159.65.174.94:8001/
```

### Keep Test Environment, Fix Issues
```bash
# If minor issues, fix on main and redeploy
git pull origin main
bash scripts/deploy-test.sh
```

---

## Success Criteria

Before promoting to production (port 8000):
- [ ] All smoke tests passed
- [ ] 24-hour monitoring shows no issues
- [ ] Glass price updates via UI working
- [ ] No performance degradation
- [ ] No database errors
- [ ] All existing features still working
- [ ] User acceptance testing completed

---

## Timeline

**Day 1 (Today)**: Deploy to test environment
**Days 2-3**: Monitor and test
**Day 4**: Decision point - promote to production or fix issues

---

## Notes

- Test environment shares database with production
- Be careful not to modify production data
- Test environment runs on same droplet, different port
- If test successful, promotion to production is low risk

---

**Deployment Started**: 2025-10-08
**Deployed By**: [Your name]
**Status**: [ ] In Progress [ ] Complete [ ] Failed
