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
