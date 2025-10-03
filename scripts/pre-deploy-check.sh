#!/bin/bash
# scripts/pre-deploy-check.sh
# Pre-deployment verification script to prevent network and configuration issues
# Created based on lessons learned from DEVOPS-20251001-001

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        PRE-DEPLOYMENT VERIFICATION SCRIPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

COMPOSE_FILE="${1:-docker-compose.beta.yml}"
ENV_FILE=".env"
ERRORS=0

# === CHECK 1: Docker Compose File Exists ===
echo "📋 [1/8] Checking Docker Compose file..."
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ ERROR: $COMPOSE_FILE not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ $COMPOSE_FILE exists"
fi
echo ""

# === CHECK 2: Environment File Exists ===
echo "📋 [2/8] Checking environment file..."
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: $ENV_FILE not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ $ENV_FILE exists"
fi
echo ""

# === CHECK 3: Validate DATABASE_URL Format ===
echo "📋 [3/8] Validating DATABASE_URL..."
if [ -f "$ENV_FILE" ]; then
    DATABASE_URL=$(grep "^DATABASE_URL=" "$ENV_FILE" | cut -d '=' -f2- | tr -d '"')
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ ERROR: DATABASE_URL not found in $ENV_FILE"
        ERRORS=$((ERRORS + 1))
    else
        echo "   DATABASE_URL: $DATABASE_URL"

        # Extract hostname from DATABASE_URL
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        echo "   Database hostname: $DB_HOST"

        # Check if hostname matches a service in docker-compose
        if grep -q "^\s*$DB_HOST:" "$COMPOSE_FILE" 2>/dev/null; then
            echo "✅ Database hostname '$DB_HOST' matches docker-compose service"
        else
            echo "⚠️  WARNING: Database hostname '$DB_HOST' not found as service in $COMPOSE_FILE"
            echo "   This is OK if using external database container"
        fi
    fi
else
    echo "⏭️  Skipping (no .env file)"
fi
echo ""

# === CHECK 4: Check Docker Networks ===
echo "📋 [4/8] Checking Docker networks..."
if command -v docker &> /dev/null; then
    # Extract network name from docker-compose
    NETWORK_NAME=$(grep -A 2 "^networks:" "$COMPOSE_FILE" | grep -v "^networks:" | grep -v "^\s*driver:" | head -1 | sed 's/://g' | xargs)

    if [ -n "$NETWORK_NAME" ]; then
        echo "   Expected network: $NETWORK_NAME"

        # Check if network exists
        FULL_NETWORK_NAME=$(docker network ls --format '{{.Name}}' | grep "$NETWORK_NAME" || true)
        if [ -n "$FULL_NETWORK_NAME" ]; then
            echo "✅ Network exists: $FULL_NETWORK_NAME"

            # List containers on this network
            echo "   Containers on network:"
            docker network inspect "$FULL_NETWORK_NAME" --format '{{range .Containers}}   - {{.Name}}{{println}}{{end}}' || true
        else
            echo "⚠️  WARNING: Network '$NETWORK_NAME' not found (will be created on deployment)"
        fi
    else
        echo "⚠️  WARNING: No custom network defined in $COMPOSE_FILE"
    fi
else
    echo "⏭️  Skipping (Docker not available)"
fi
echo ""

# === CHECK 5: Check Running Containers ===
echo "📋 [5/8] Checking running containers..."
if command -v docker &> /dev/null; then
    # Extract service names from docker-compose
    echo "   Services defined in $COMPOSE_FILE:"
    grep "^\s*[a-z_-]*:" "$COMPOSE_FILE" | grep -v "^#" | sed 's/://g' | xargs | grep -v "version\|volumes\|networks" || true

    echo ""
    echo "   Currently running containers:"
    docker ps --format '   - {{.Names}} ({{.Status}})' || true
else
    echo "⏭️  Skipping (Docker not available)"
fi
echo ""

# === CHECK 6: Check for Orphaned Containers ===
echo "📋 [6/8] Checking for potential orphaned containers..."
if command -v docker &> /dev/null; then
    # Look for containers with similar names but not in current compose
    ORPHANS=$(docker ps -a --format '{{.Names}}' | grep -E '(ventanas|postgres|redis)' | wc -l || echo "0")
    if [ "$ORPHANS" -gt 0 ]; then
        echo "⚠️  Found $ORPHANS container(s) with ventanas/postgres/redis in name"
        docker ps -a --format '   - {{.Names}} ({{.Status}})' | grep -E '(ventanas|postgres|redis)' || true
        echo ""
        echo "   RECOMMENDATION: Ensure these containers are on the same network or update DATABASE_URL"
    else
        echo "✅ No orphaned containers detected"
    fi
else
    echo "⏭️  Skipping (Docker not available)"
fi
echo ""

# === CHECK 7: Verify Logs Directory ===
echo "📋 [7/8] Checking logs directory..."
if [ -d "logs" ]; then
    if [ -w "logs" ]; then
        echo "✅ logs/ directory exists and is writable"
    else
        echo "⚠️  WARNING: logs/ directory exists but may not be writable"
        echo "   Run: chmod -R 777 logs"
    fi
else
    echo "⚠️  WARNING: logs/ directory does not exist"
    echo "   Creating logs directory..."
    mkdir -p logs
    chmod -R 777 logs
    echo "✅ logs/ directory created"
fi
echo ""

# === CHECK 8: Test Database Connection (if in same network) ===
echo "📋 [8/8] Testing database connectivity..."
if command -v docker &> /dev/null && [ -n "$DB_HOST" ]; then
    # Try to find app container
    APP_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'app' | head -1 || true)

    if [ -n "$APP_CONTAINER" ]; then
        echo "   Testing from container: $APP_CONTAINER"

        # Try to ping database host
        DB_REACHABLE=$(docker exec "$APP_CONTAINER" sh -c "getent hosts $DB_HOST" 2>/dev/null || echo "")

        if [ -n "$DB_REACHABLE" ]; then
            echo "✅ Database host '$DB_HOST' is reachable from app container"
        else
            echo "⚠️  WARNING: Database host '$DB_HOST' is NOT reachable from app container"
            echo "   This may indicate a network isolation issue"
            echo "   SOLUTION: Connect app container to database network:"
            echo "   docker network connect <db-network> $APP_CONTAINER"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "⏭️  Skipping (no app container running)"
    fi
else
    echo "⏭️  Skipping (Docker not available or no DATABASE_URL)"
fi
echo ""

# === SUMMARY ===
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ PRE-DEPLOYMENT CHECK PASSED - Safe to deploy"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "⚠️  PRE-DEPLOYMENT CHECK FOUND $ERRORS ISSUE(S)"
    echo "   Review warnings above before deploying"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
