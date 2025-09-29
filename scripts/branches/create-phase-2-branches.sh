#!/bin/bash
# Phase 2: Performance Optimization
# Generated: 2025-09-29 by task-package-generator
# Tasks: TASK-20250929-006 through TASK-20250929-008

set -e

echo "=========================================="
echo "Creating Phase 2 Performance Branches"
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

echo "Creating Phase 2 branches..."
echo ""

# Task TASK-20250929-006: Optimize database queries
echo "[1/3] Creating branch for BOM query optimization..."
git checkout -b perf/bom-query-optimization-20250929
git push -u origin perf/bom-query-optimization-20250929
git checkout main
echo "    Branch: perf/bom-query-optimization-20250929 created"

# Task TASK-20250929-007: Formula evaluation caching
echo "[2/3] Creating branch for formula caching..."
git checkout -b perf/formula-caching-20250929
git push -u origin perf/formula-caching-20250929
git checkout main
echo "    Branch: perf/formula-caching-20250929 created"

# Task TASK-20250929-008: CSV streaming
echo "[3/3] Creating branch for CSV streaming..."
git checkout -b perf/csv-streaming-20250929
git push -u origin perf/csv-streaming-20250929
git checkout main
echo "    Branch: perf/csv-streaming-20250929 created"

echo ""
echo "=========================================="
echo "Phase 2 Branches Created Successfully"
echo "=========================================="
echo ""
echo "Summary: 3 branches created"
echo ""
echo "Phase 2 Branches:"
git branch | grep "perf/.*-20250929"
echo ""
echo "Next Steps:"
echo "1. Complete Phase 1 tasks first (dependencies)"
echo "2. Review tasks.csv for task details"
echo "3. Checkout branch: git checkout perf/bom-query-optimization-20250929"
echo "4. Begin work on TASK-20250929-006"
echo ""
echo "Performance Targets:"
echo "- Quote calculation: 200ms → 50ms"
echo "- Database queries: Reduce by 80%"
echo "- Formula evaluation: 60% faster"
echo "- CSV processing: Support up to 100MB files"
echo ""