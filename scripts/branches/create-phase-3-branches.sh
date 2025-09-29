#!/bin/bash
# Phase 3: Code Quality & Architecture Improvements
# Generated: 2025-09-29 by task-package-generator
# Tasks: TASK-20250929-009 through TASK-20250929-011

set -e

echo "=========================================="
echo "Creating Phase 3 Architecture Branches"
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

echo "Creating Phase 3 branches..."
echo ""

# Task TASK-20250929-009: Command pattern for calculations
echo "[1/3] Creating branch for command pattern..."
git checkout -b arch/quote-command-pattern-20250929
git push -u origin arch/quote-command-pattern-20250929
git checkout main
echo "    Branch: arch/quote-command-pattern-20250929 created"

# Task TASK-20250929-010: Extract template business logic
echo "[2/3] Creating branch for template logic extraction..."
git checkout -b arch/template-logic-extraction-20250929
git push -u origin arch/template-logic-extraction-20250929
git checkout main
echo "    Branch: arch/template-logic-extraction-20250929 created"

# Task TASK-20250929-011: Factory pattern for models
echo "[3/3] Creating branch for model factories..."
git checkout -b arch/model-factories-20250929
git push -u origin arch/model-factories-20250929
git checkout main
echo "    Branch: arch/model-factories-20250929 created"

echo ""
echo "=========================================="
echo "Phase 3 Branches Created Successfully"
echo "=========================================="
echo ""
echo "Summary: 3 branches created"
echo ""
echo "Phase 3 Branches:"
git branch | grep "arch/.*-20250929"
echo ""
echo "Next Steps:"
echo "1. Complete Phase 1 and Phase 2 tasks first"
echo "2. Review tasks.csv for task details"
echo "3. Checkout branch: git checkout arch/quote-command-pattern-20250929"
echo "4. Begin work on TASK-20250929-009"
echo ""
echo "Architecture Goals:"
echo "- Implement command pattern for calculations"
echo "- Separate business logic from templates"
echo "- Add factory pattern for model creation"
echo "- Improve SOLID principles adherence to 80%"
echo ""