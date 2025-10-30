---
description: Clean up abandoned and stale workspaces based on configurable age and activity thresholds
allowed-tools: Read, Write, Bash, Glob
argument-hint: [--dry-run] [--days N] [--force] - Options for cleanup behavior
---

# Cleanup Workspaces

Automatically identify and remove abandoned workspaces that haven't been modified for a specified period (default: 30 days) and have low or no progress. Provides safety mechanisms including dry-run mode, confirmation prompts, and backup before deletion.

## Configuration

### Default Thresholds
```bash
# Configurable via arguments or defaults
DAYS_THRESHOLD=${DAYS_THRESHOLD:-30}      # Days since last modification
PROGRESS_THRESHOLD=${PROGRESS_THRESHOLD:-10}  # Minimum progress % to keep
DRY_RUN=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --days)
            DAYS_THRESHOLD="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --progress-threshold)
            PROGRESS_THRESHOLD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: /cleanup-workspaces [--dry-run] [--days N] [--force] [--progress-threshold N]"
            exit 1
            ;;
    esac
done

echo "🧹 Workspace Cleanup Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Age threshold: $DAYS_THRESHOLD days"
echo "  Progress threshold: $PROGRESS_THRESHOLD%"
echo "  Dry run: $DRY_RUN"
echo "  Force (no confirmation): $FORCE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
```

## Discovery

### Find All Workspaces
```bash
WORKSPACES=$(find workspace -maxdepth 1 -type d -name "*-*" 2>/dev/null | grep -v "archive" | sort)

if [ -z "$WORKSPACES" ]; then
    echo "📭 No workspaces found"
    exit 0
fi

WORKSPACE_COUNT=$(echo "$WORKSPACES" | wc -l | tr -d ' ')
echo "📂 Scanning $WORKSPACE_COUNT workspace(s) for cleanup candidates..."
echo ""
```

### Analyze Each Workspace
```bash
# Arrays to store cleanup candidates
CLEANUP_CANDIDATES=()
CLEANUP_REASONS=()

for WORKSPACE_DIR in $WORKSPACES; do
    TASK_ID=$(basename "$WORKSPACE_DIR")

    # Skip if workspace is empty or inaccessible
    if [ ! -r "$WORKSPACE_DIR" ]; then
        continue
    fi

    # Get workspace metadata
    CHECKLIST_FILE="$WORKSPACE_DIR/checklist-$TASK_ID.md"
    NOTES_FILE="$WORKSPACE_DIR/notes.md"
    README_FILE="$WORKSPACE_DIR/README.md"

    # Calculate progress
    if [ -f "$CHECKLIST_FILE" ]; then
        TOTAL_ITEMS=$(grep -E "\[ \]|\[x\]" "$CHECKLIST_FILE" 2>/dev/null | wc -l | tr -d ' ')
        COMPLETED_ITEMS=$(grep "\[x\]" "$CHECKLIST_FILE" 2>/dev/null | wc -l | tr -d ' ')

        if [ "$TOTAL_ITEMS" -gt 0 ]; then
            PROGRESS_PCT=$(( COMPLETED_ITEMS * 100 / TOTAL_ITEMS ))
        else
            PROGRESS_PCT=0
        fi
    else
        PROGRESS_PCT=0
        TOTAL_ITEMS=0
        COMPLETED_ITEMS=0
    fi

    # Calculate days since last modification
    if [ -f "$NOTES_FILE" ]; then
        LAST_MODIFIED_TIMESTAMP=$(stat -f %m "$NOTES_FILE" 2>/dev/null || echo 0)
    elif [ -f "$README_FILE" ]; then
        LAST_MODIFIED_TIMESTAMP=$(stat -f %m "$README_FILE" 2>/dev/null || echo 0)
    else
        LAST_MODIFIED_TIMESTAMP=$(stat -f %m "$WORKSPACE_DIR" 2>/dev/null || echo 0)
    fi

    CURRENT_TIMESTAMP=$(date +%s)
    DAYS_SINCE_MODIFIED=$(( (CURRENT_TIMESTAMP - LAST_MODIFIED_TIMESTAMP) / 86400 ))

    # Determine if workspace should be cleaned up
    SHOULD_CLEANUP=false
    CLEANUP_REASON=""

    # Rule 1: Completed workspaces should be archived, not cleaned up
    if [ "$PROGRESS_PCT" -eq 100 ]; then
        CLEANUP_REASON="⚠️  Completed (should archive instead)"
        # Don't add to cleanup candidates for deletion
        echo "  ℹ️  $TASK_ID: $CLEANUP_REASON"
        continue
    fi

    # Rule 2: Abandoned (old + low progress)
    if [ "$DAYS_SINCE_MODIFIED" -gt "$DAYS_THRESHOLD" ] && [ "$PROGRESS_PCT" -lt "$PROGRESS_THRESHOLD" ]; then
        SHOULD_CLEANUP=true
        CLEANUP_REASON="Abandoned: ${DAYS_SINCE_MODIFIED}d old, ${PROGRESS_PCT}% progress"
    fi

    # Rule 3: Empty workspace (no progress, old)
    if [ "$PROGRESS_PCT" -eq 0 ] && [ "$DAYS_SINCE_MODIFIED" -gt 7 ]; then
        SHOULD_CLEANUP=true
        CLEANUP_REASON="Empty: ${DAYS_SINCE_MODIFIED}d old, 0% progress"
    fi

    # Rule 4: Stale but significant progress
    if [ "$DAYS_SINCE_MODIFIED" -gt "$DAYS_THRESHOLD" ] && [ "$PROGRESS_PCT" -ge "$PROGRESS_THRESHOLD" ] && [ "$PROGRESS_PCT" -lt 100 ]; then
        # Don't auto-cleanup, requires review
        echo "  ⏸️  $TASK_ID: Stale but has ${PROGRESS_PCT}% progress (${DAYS_SINCE_MODIFIED}d old) - requires manual review"
        continue
    fi

    # Add to cleanup candidates
    if [ "$SHOULD_CLEANUP" = true ]; then
        CLEANUP_CANDIDATES+=("$TASK_ID")
        CLEANUP_REASONS+=("$CLEANUP_REASON")
    fi
done

CLEANUP_COUNT=${#CLEANUP_CANDIDATES[@]}
```

## Cleanup Candidate Review

### Display Candidates
```bash
if [ "$CLEANUP_COUNT" -eq 0 ]; then
    echo "✅ No workspaces need cleanup"
    echo ""
    echo "All workspaces are either:"
    echo "  • Active (recently modified)"
    echo "  • Making progress"
    echo "  • Completed (use /archive-workspace instead)"
    exit 0
fi

echo "🗑️  Found $CLEANUP_COUNT workspace(s) for cleanup:"
echo ""
echo "Task ID                Reason"
echo "────────────────────────────────────────────────────────────────────"

for i in "${!CLEANUP_CANDIDATES[@]}"; do
    printf "%-20s   %s\n" "${CLEANUP_CANDIDATES[$i]}" "${CLEANUP_REASONS[$i]}"
done

echo "────────────────────────────────────────────────────────────────────"
echo ""
```

### Safety Check - Review Before Delete
```bash
if [ "$DRY_RUN" = true ]; then
    echo "🏃 DRY RUN MODE - No workspaces will be deleted"
    echo ""
    echo "Would delete the following workspaces:"
    for TASK_ID in "${CLEANUP_CANDIDATES[@]}"; do
        WORKSPACE_SIZE=$(du -sh "workspace/$TASK_ID" 2>/dev/null | cut -f1)
        echo "  • $TASK_ID ($WORKSPACE_SIZE)"
    done
    echo ""
    echo "To perform actual cleanup, run without --dry-run:"
    echo "  /cleanup-workspaces"
    exit 0
fi

if [ "$FORCE" != true ]; then
    echo "⚠️  WARNING: This will permanently delete $CLEANUP_COUNT workspace(s)"
    echo ""
    echo "Workspaces to delete:"
    for TASK_ID in "${CLEANUP_CANDIDATES[@]}"; do
        WORKSPACE_SIZE=$(du -sh "workspace/$TASK_ID" 2>/dev/null | cut -f1)
        echo "  • $TASK_ID ($WORKSPACE_SIZE)"
    done
    echo ""
    read -p "Continue with deletion? (type 'yes' to confirm): " CONFIRMATION

    if [ "$CONFIRMATION" != "yes" ]; then
        echo "❌ Cleanup cancelled"
        exit 1
    fi
fi

echo ""
```

## Backup Before Deletion

### Create Cleanup Backup
```bash
BACKUP_DIR="workspace/.cleanup-backup"
BACKUP_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_PATH="$BACKUP_DIR/cleanup-$BACKUP_TIMESTAMP"

echo "💾 Creating backup before cleanup..."
mkdir -p "$BACKUP_PATH"

for TASK_ID in "${CLEANUP_CANDIDATES[@]}"; do
    WORKSPACE_DIR="workspace/$TASK_ID"

    if [ -d "$WORKSPACE_DIR" ]; then
        cp -R "$WORKSPACE_DIR" "$BACKUP_PATH/"
        echo "  ✓ Backed up: $TASK_ID"
    fi
done

BACKUP_SIZE=$(du -sh "$BACKUP_PATH" 2>/dev/null | cut -f1)
echo "✅ Backup created: $BACKUP_PATH ($BACKUP_SIZE)"
echo ""
```

### Create Deletion Manifest
```bash
MANIFEST_FILE="$BACKUP_PATH/CLEANUP_MANIFEST.txt"

cat > "$MANIFEST_FILE" << EOF
Cleanup Manifest
================

Cleanup Date: $(date +"%Y-%m-%d %H:%M:%S")
Executed By: $(whoami)@$(hostname)
Configuration:
  - Age Threshold: $DAYS_THRESHOLD days
  - Progress Threshold: $PROGRESS_THRESHOLD%
  - Force Mode: $FORCE

Workspaces Deleted:
EOF

for i in "${!CLEANUP_CANDIDATES[@]}"; do
    TASK_ID="${CLEANUP_CANDIDATES[$i]}"
    REASON="${CLEANUP_REASONS[$i]}"
    SIZE=$(du -sh "workspace/$TASK_ID" 2>/dev/null | cut -f1)

    echo "  - $TASK_ID" >> "$MANIFEST_FILE"
    echo "    Reason: $REASON" >> "$MANIFEST_FILE"
    echo "    Size: $SIZE" >> "$MANIFEST_FILE"
    echo "" >> "$MANIFEST_FILE"
done

cat >> "$MANIFEST_FILE" << EOF

Backup Location: $BACKUP_PATH
Restoration Command:
  cp -R $BACKUP_PATH/{TASK_ID} workspace/

Backup Retention:
  This backup will be automatically deleted after 90 days unless moved.
EOF

echo "✅ Manifest created: $MANIFEST_FILE"
echo ""
```

## Execution

### Delete Workspaces
```bash
echo "🗑️  Deleting workspaces..."
echo ""

DELETED_COUNT=0
FAILED_DELETIONS=()

for TASK_ID in "${CLEANUP_CANDIDATES[@]}"; do
    WORKSPACE_DIR="workspace/$TASK_ID"

    if [ -d "$WORKSPACE_DIR" ]; then
        if rm -rf "$WORKSPACE_DIR"; then
            echo "  ✓ Deleted: $TASK_ID"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        else
            echo "  ✗ Failed: $TASK_ID"
            FAILED_DELETIONS+=("$TASK_ID")
        fi
    else
        echo "  ⊗ Skipped: $TASK_ID (not found)"
    fi
done

echo ""
```

### Update tasks.csv
```bash
if [ -f "tasks.csv" ]; then
    echo "📝 Updating tasks.csv..."

    # Create backup
    cp tasks.csv tasks.csv.backup-cleanup-$BACKUP_TIMESTAMP

    for TASK_ID in "${CLEANUP_CANDIDATES[@]}"; do
        if grep -q "^$TASK_ID," tasks.csv; then
            # Mark as deleted in tasks.csv
            sed -i '' "s/^$TASK_ID,\([^,]*\),[^,]*,/$TASK_ID,\1,deleted,/" tasks.csv

            # Add deletion note
            CURRENT_NOTES=$(grep "^$TASK_ID," tasks.csv | cut -d',' -f12)
            NEW_NOTES="Cleanup: $BACKUP_TIMESTAMP. $CURRENT_NOTES"
            sed -i '' "s|^$TASK_ID,\(.*\),[^,]*$|\1,$NEW_NOTES|" tasks.csv

            echo "  ✓ Updated: $TASK_ID status to 'deleted'"
        fi
    done

    echo "✅ tasks.csv updated"
else
    echo "ℹ️  No tasks.csv found (skipping update)"
fi

echo ""
```

## Post-Cleanup Summary

### Generate Summary Report
```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        CLEANUP COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Cleanup Summary:"
echo "   Candidates found: $CLEANUP_COUNT"
echo "   Successfully deleted: $DELETED_COUNT"
echo "   Failed deletions: ${#FAILED_DELETIONS[@]}"
echo ""

if [ ${#FAILED_DELETIONS[@]} -gt 0 ]; then
    echo "⚠️  Failed Deletions:"
    for TASK_ID in "${FAILED_DELETIONS[@]}"; do
        echo "   • $TASK_ID"
    done
    echo ""
fi

echo "💾 Backup Information:"
echo "   Location: $BACKUP_PATH"
echo "   Size: $BACKUP_SIZE"
echo "   Manifest: $MANIFEST_FILE"
echo ""

echo "✅ Space Reclaimed:"
SPACE_BEFORE=$(du -sh workspace 2>/dev/null | cut -f1)
echo "   Backup size: $BACKUP_SIZE"
echo "   Current workspace size: $SPACE_BEFORE"
echo ""

echo "📁 Remaining Workspaces:"
REMAINING_COUNT=$(find workspace -maxdepth 1 -type d -name "*-*" 2>/dev/null | grep -v "archive" | grep -v ".cleanup-backup" | wc -l | tr -d ' ')
echo "   Active workspaces: $REMAINING_COUNT"
echo ""

echo "🔗 Quick Actions:"
echo "   View backup: ls -la $BACKUP_PATH"
echo "   Read manifest: cat $MANIFEST_FILE"
echo "   Restore workspace: cp -R $BACKUP_PATH/{TASK_ID} workspace/"
echo "   List remaining: /list-workspaces"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### Cleanup Backup Retention
```bash
# Create retention reminder
RETENTION_FILE="$BACKUP_DIR/RETENTION_POLICY.txt"

if [ ! -f "$RETENTION_FILE" ]; then
    cat > "$RETENTION_FILE" << 'EOF'
Cleanup Backup Retention Policy
================================

Backups are created when workspaces are deleted via /cleanup-workspaces.

AUTOMATIC DELETION:
  • Backups older than 90 days will be automatically deleted
  • Weekly cleanup job removes expired backups

MANUAL RETENTION:
  • To keep a backup permanently, move it outside workspace/.cleanup-backup/
  • Example: mv workspace/.cleanup-backup/cleanup-20251008-143022 workspace/archive/

RESTORATION:
  • Restore a workspace: cp -R workspace/.cleanup-backup/cleanup-{timestamp}/{TASK_ID} workspace/
  • After restoration, update tasks.csv status if needed

CURRENT BACKUPS:
EOF
fi

# Add current backup to retention log
echo "  - cleanup-$BACKUP_TIMESTAMP: $DELETED_COUNT workspace(s), $BACKUP_SIZE" >> "$RETENTION_FILE"

echo "📋 Retention policy: $RETENTION_FILE"
echo ""
```

## Expected Outcomes

After executing this command, you should have:

### Immediate Results
1. **Workspaces deleted** - Abandoned workspaces removed from `workspace/` directory
2. **Backup created** - Full backup in `workspace/.cleanup-backup/cleanup-{timestamp}/`
3. **Manifest generated** - Detailed log of deleted workspaces
4. **tasks.csv updated** - Deleted tasks marked as "deleted" status
5. **Summary report** - Statistics on cleanup operation

### Backup Structure
```
workspace/
├── .cleanup-backup/
│   ├── RETENTION_POLICY.txt
│   ├── cleanup-20251008-143022/
│   │   ├── CLEANUP_MANIFEST.txt
│   │   ├── TASK-20250929-012/
│   │   │   └── [all workspace files]
│   │   └── PROCESS-20251001-001/
│   │       └── [all workspace files]
│   └── cleanup-20251008-150000/
│       └── ...
└── [active workspaces only]
```

## Use Cases

### Monthly Cleanup Routine
```bash
# First, review what would be deleted (dry run)
/cleanup-workspaces --dry-run

# If acceptable, perform cleanup
/cleanup-workspaces

# Then list remaining workspaces
/list-workspaces
```

### Custom Thresholds
```bash
# More aggressive: cleanup after 14 days
/cleanup-workspaces --days 14

# More conservative: cleanup only 0% progress
/cleanup-workspaces --progress-threshold 0

# Combined
/cleanup-workspaces --days 14 --progress-threshold 5
```

### Automated Cleanup (Cron)
```bash
# Weekly cleanup with email report
0 0 * * 0 cd /path/to/ai-docs && /cleanup-workspaces --force --days 30 | mail -s "Workspace Cleanup Report" team@example.com
```

### Before Major Work
```bash
# Clean slate before new sprint
/cleanup-workspaces --dry-run  # Review first
/cleanup-workspaces            # Execute
/list-workspaces               # Verify clean state
```

## Restoration

### Restore Deleted Workspace
```bash
# Find backup
ls -la workspace/.cleanup-backup/

# View manifest
cat workspace/.cleanup-backup/cleanup-20251008-143022/CLEANUP_MANIFEST.txt

# Restore specific workspace
cp -R workspace/.cleanup-backup/cleanup-20251008-143022/TASK-20250929-012 workspace/

# Update tasks.csv
sed -i '' "s/^TASK-20250929-012,\([^,]*\),deleted,/TASK-20250929-012,\1,in-progress,/" tasks.csv
```

### Restore All from Backup
```bash
# Restore entire cleanup batch
BACKUP_DIR="workspace/.cleanup-backup/cleanup-20251008-143022"
for WORKSPACE in $BACKUP_DIR/*-*/; do
    TASK_ID=$(basename "$WORKSPACE")
    if [[ "$TASK_ID" =~ ^[A-Z]+-[0-9]+-[0-9]+$ ]]; then
        cp -R "$WORKSPACE" workspace/
        echo "Restored: $TASK_ID"
    fi
done
```

## Backup Maintenance

### View All Backups
```bash
# List all cleanup backups
ls -lht workspace/.cleanup-backup/

# Total backup size
du -sh workspace/.cleanup-backup
```

### Remove Old Backups (>90 days)
```bash
# Find backups older than 90 days
find workspace/.cleanup-backup -maxdepth 1 -type d -name "cleanup-*" -mtime +90

# Delete old backups
find workspace/.cleanup-backup -maxdepth 1 -type d -name "cleanup-*" -mtime +90 -exec rm -rf {} \;
```

## Troubleshooting

### Workspace Won't Delete
```bash
# Error: Permission denied
# Solution: Check permissions
ls -la workspace/TASK-ID
chmod -R u+w workspace/TASK-ID
/cleanup-workspaces
```

### Backup Directory Full
```bash
# Error: No space for backup
# Solution: Remove old backups first
du -sh workspace/.cleanup-backup/*
rm -rf workspace/.cleanup-backup/cleanup-{old-timestamp}
```

### Accidental Deletion
```bash
# Solution: Restore from backup immediately
LATEST_BACKUP=$(ls -t workspace/.cleanup-backup/ | head -1)
cat workspace/.cleanup-backup/$LATEST_BACKUP/CLEANUP_MANIFEST.txt
cp -R workspace/.cleanup-backup/$LATEST_BACKUP/{TASK_ID} workspace/
```

### Wrong Workspace Deleted
```bash
# Solution: Check cleanup criteria
# Adjust thresholds to be more conservative
/cleanup-workspaces --days 60 --progress-threshold 5
```

## Best Practices

1. **Always dry-run first** - Review candidates before deletion
2. **Regular cleanup schedule** - Weekly or monthly routine
3. **Monitor backup size** - Delete old backups after 90 days
4. **Review stale workspaces** - Manually check workspaces with >10% progress
5. **Archive before cleanup** - Archive completed workspaces first
6. **Document restoration** - Keep restoration instructions handy

## Safety Features

✅ **Dry Run Mode** - Preview deletions without executing
✅ **Confirmation Prompt** - Requires explicit "yes" to proceed
✅ **Automatic Backup** - Full backup before any deletion
✅ **Deletion Manifest** - Detailed log of what was deleted
✅ **Restoration Commands** - Included in manifest and output
✅ **tasks.csv Update** - Tracks deleted workspaces
✅ **Progress Threshold** - Protects workspaces with significant progress
✅ **Retention Policy** - Automatic backup cleanup after 90 days

## Integration with Other Commands

### Complete Workflow
```bash
# 1. List all workspaces
/list-workspaces

# 2. Archive completed ones
/list-workspaces completed | while read TASK _; do
    /archive-workspace $TASK
done

# 3. Review cleanup candidates
/cleanup-workspaces --dry-run

# 4. Execute cleanup
/cleanup-workspaces

# 5. Verify final state
/list-workspaces
```
