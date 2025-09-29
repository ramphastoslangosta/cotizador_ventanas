#!/bin/bash
# Phase 1: Critical Architecture Refactoring
# Generated: 2025-09-29 by task-package-generator
# Tasks: TASK-20250929-001 through TASK-20250929-005

set -e

echo "=========================================="
echo "Creating Phase 1 Refactoring Branches"
echo "=========================================="
echo ""

# Verify on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Warning: Not on main branch (currently on $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo "Current branch: $CURRENT_BRANCH"
echo ""

# Verify clean working tree
if ! git diff-index --quiet HEAD --; then
    echo "Error: Working tree has uncommitted changes"
    echo "Please commit or stash changes before creating branches"
    exit 1
fi

echo "Creating Phase 1 branches..."
echo ""

# Task TASK-20250929-001: Extract authentication routes
echo "[1/5] Creating branch for authentication routes extraction..."
git checkout -b refactor/auth-routes-20250929
git push -u origin refactor/auth-routes-20250929
git checkout main
echo "    Branch: refactor/auth-routes-20250929 created"

# Task TASK-20250929-002: Extract quote routes
echo "[2/5] Creating branch for quote routes extraction..."
git checkout -b refactor/quote-routes-20250929
git push -u origin refactor/quote-routes-20250929
git checkout main
echo "    Branch: refactor/quote-routes-20250929 created"

# Task TASK-20250929-003: Extract work order and material routes
echo "[3/5] Creating branch for work order and material routes..."
git checkout -b refactor/workorder-material-routes-20250929
git push -u origin refactor/workorder-material-routes-20250929
git checkout main
echo "    Branch: refactor/workorder-material-routes-20250929 created"

# Task TASK-20250929-004: Fix CSV test complexity
echo "[4/5] Creating branch for CSV test complexity fix..."
git checkout -b refactor/csv-tests-complexity-20250929
git push -u origin refactor/csv-tests-complexity-20250929
git checkout main
echo "    Branch: refactor/csv-tests-complexity-20250929 created"

# Task TASK-20250929-005: Implement service interfaces
echo "[5/5] Creating branch for service interfaces..."
git checkout -b refactor/service-interfaces-20250929
git push -u origin refactor/service-interfaces-20250929
git checkout main
echo "    Branch: refactor/service-interfaces-20250929 created"

echo ""
echo "=========================================="
echo "Phase 1 Branches Created Successfully"
echo "=========================================="
echo ""
echo "Summary: 5 branches created"
echo ""
echo "Phase 1 Branches:"
git branch | grep "refactor/.*-20250929"
echo ""
echo "Next Steps:"
echo "1. Review tasks.csv for task details"
echo "2. Checkout branch: git checkout refactor/auth-routes-20250929"
echo "3. Begin work on TASK-20250929-001"
echo "4. Follow development protocol for commits"
echo ""