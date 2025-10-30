#!/bin/bash
# Phase {N}: {Phase Title}
# Generated: {TIMESTAMP} by task-package-generator

set -e

echo "🌿 Creating Phase {N} branches..."

# Verify on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Create branches for each task
{BRANCH_COMMANDS}

# Return to main
git checkout main
echo "✅ All Phase {N} branches created successfully"
echo "📋 Summary: {COUNT} branches created"
git branch | grep "{PHASE_PREFIX}"
