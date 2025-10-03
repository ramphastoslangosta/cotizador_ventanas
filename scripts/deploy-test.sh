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
