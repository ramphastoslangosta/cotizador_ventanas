#!/bin/bash
# Verification script for Route Extraction Protocol
# Created: October 2, 2025
# Task: PROCESS-20251001-001

PROTOCOL_FILE="docs/ROUTE-EXTRACTION-PROTOCOL.md"
EXIT_CODE=0

echo "================================================"
echo "Route Extraction Protocol Verification"
echo "================================================"
echo ""

# Check file exists
if [ ! -f "$PROTOCOL_FILE" ]; then
    echo "❌ FAIL: Protocol file not found: $PROTOCOL_FILE"
    exit 1
fi

echo "✅ Protocol file exists: $PROTOCOL_FILE"
echo ""

# 1. Check section count
echo "1. Checking section count..."
SECTION_COUNT=$(grep -c "^## [0-9]" "$PROTOCOL_FILE")
if [ "$SECTION_COUNT" -eq 9 ]; then
    echo "   ✅ PASS: All 9 sections present"
else
    echo "   ❌ FAIL: Expected 9 sections, found $SECTION_COUNT"
    EXIT_CODE=1
fi

# 2. Check line count
echo "2. Checking line count..."
LINE_COUNT=$(wc -l < "$PROTOCOL_FILE")
if [ "$LINE_COUNT" -ge 500 ]; then
    echo "   ✅ PASS: $LINE_COUNT lines (target: 500+)"
else
    echo "   ❌ FAIL: $LINE_COUNT lines (target: 500+)"
    EXIT_CODE=1
fi

# 3. Check code examples
echo "3. Checking code examples..."
PYTHON_COUNT=$(grep -c '```python' "$PROTOCOL_FILE")
BASH_COUNT=$(grep -c '```bash' "$PROTOCOL_FILE")
HTML_COUNT=$(grep -c '```html' "$PROTOCOL_FILE")
TOTAL_EXAMPLES=$((PYTHON_COUNT + BASH_COUNT + HTML_COUNT))

if [ "$TOTAL_EXAMPLES" -ge 20 ]; then
    echo "   ✅ PASS: $TOTAL_EXAMPLES code examples (target: 20+)"
    echo "      - Python: $PYTHON_COUNT"
    echo "      - Bash: $BASH_COUNT"
    echo "      - HTML: $HTML_COUNT"
else
    echo "   ❌ FAIL: $TOTAL_EXAMPLES code examples (target: 20+)"
    EXIT_CODE=1
fi

# 4. Check checklist items
echo "4. Checking checklist items..."
CHECKLIST_COUNT=$(grep -c "^- \[ \]" "$PROTOCOL_FILE")
if [ "$CHECKLIST_COUNT" -ge 25 ]; then
    echo "   ✅ PASS: $CHECKLIST_COUNT checklist items (target: 25+)"
else
    echo "   ❌ FAIL: $CHECKLIST_COUNT checklist items (target: 25+)"
    EXIT_CODE=1
fi

# 5. Check HOTFIX references
echo "5. Checking HOTFIX-20251001-001 references..."
HOTFIX_COUNT=$(grep -ci "HOTFIX-20251001-001" "$PROTOCOL_FILE")
if [ "$HOTFIX_COUNT" -ge 5 ]; then
    echo "   ✅ PASS: $HOTFIX_COUNT HOTFIX mentions (target: 5+)"
else
    echo "   ❌ FAIL: $HOTFIX_COUNT HOTFIX mentions (target: 5+)"
    EXIT_CODE=1
fi

# 6. Check for placeholders
echo "6. Checking for placeholders..."
if grep -qE "\[(TODO|TBD|FIXME|XXX|\.\.\.|TBA)\]" "$PROTOCOL_FILE"; then
    echo "   ❌ FAIL: Placeholders found:"
    grep -nE "\[(TODO|TBD|FIXME|XXX|\.\.\.|TBA)\]" "$PROTOCOL_FILE"
    EXIT_CODE=1
else
    echo "   ✅ PASS: No placeholders found"
fi

# 7. Check required sections exist
echo "7. Checking required sections..."
REQUIRED_SECTIONS=(
    "Overview"
    "When to Use This Protocol"
    "Pre-Extraction Checklist"
    "Extraction Steps"
    "Testing Requirements"
    "Deployment Protocol"
    "Rollback Plan"
    "Case Studies"
    "Quick Reference"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "$section" "$PROTOCOL_FILE"; then
        echo "   ✅ Section found: $section"
    else
        echo "   ❌ Section missing: $section"
        EXIT_CODE=1
    fi
done

# 8. Check metadata
echo "8. Checking metadata..."
if grep -q "Protocol Version" "$PROTOCOL_FILE"; then
    echo "   ✅ Version info present"
else
    echo "   ❌ Version info missing"
    EXIT_CODE=1
fi

if grep -q "READY FOR USE" "$PROTOCOL_FILE"; then
    echo "   ✅ Status indicator present"
else
    echo "   ❌ Status indicator missing"
    EXIT_CODE=1
fi

# Summary
echo ""
echo "================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo "================================================"
    echo ""
    echo "Protocol is ready for use!"
    echo "File: $PROTOCOL_FILE"
    echo "Lines: $LINE_COUNT"
    echo "Code examples: $TOTAL_EXAMPLES"
    echo "Checklist items: $CHECKLIST_COUNT"
else
    echo "❌ SOME CHECKS FAILED"
    echo "================================================"
    echo ""
    echo "Please fix the issues above before deploying."
fi
echo ""

exit $EXIT_CODE
