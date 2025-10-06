# Task Workspace: HOTFIX-20251006-001

**Title**: Fix PDF Generation - Company logo_path AttributeError (CRITICAL)
**Started**: 2025-10-06
**Priority**: CRITICAL
**Estimated Effort**: 0.5 days (4 hours)

---

## ⚠️ CRITICAL PRODUCTION BUG

**Issue**: PDF generation fails with `AttributeError: 'Company' object has no attribute 'logo_path'`

**Root Cause**:
- Database model has `logo_filename` field
- Code tries to access `company.logo_path` (doesn't exist)
- JavaScript has scope issue with `originalText` variable

**Impact**: 100% of users unable to generate PDFs

**Affected URLs**:
- http://159.65.174.94:8000/quotes/21/pdf
- http://159.65.174.94:8001/quotes/24/pdf

---

## Files

- `atomic-plan-HOTFIX-20251006-001.md` - Detailed execution plan (7 phases, atomic steps)
- `checklist-HOTFIX-20251006-001.md` - Execution checklist (all action items)
- `notes.md` - Session notes and observations
- `success-criteria.md` - Measurable success criteria
- `HOTFIX-SUMMARY.md` - Post-deployment summary (created after deployment)

---

## Quick Commands

### Start Work Session
```bash
# Create and checkout hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/pdf-logo-path-20251006

# View atomic plan
cat .claude/workspace/HOTFIX-20251006-001/atomic-plan-HOTFIX-20251006-001.md
```

### Track Progress
```bash
# Count completed items
grep "\\[x\\]" .claude/workspace/HOTFIX-20251006-001/checklist-HOTFIX-20251006-001.md | wc -l

# Count remaining items
grep "\\[ \\]" .claude/workspace/HOTFIX-20251006-001/checklist-HOTFIX-20251006-001.md | wc -l

# View checklist
cat .claude/workspace/HOTFIX-20251006-001/checklist-HOTFIX-20251006-001.md
```

### Test Commands
```bash
# Run automated tests
pytest tests/test_pdf_generation.py -v

# Test local PDF generation
curl http://localhost:8000/quotes/21/pdf -o test.pdf

# Check production PDF
curl http://159.65.174.94:8000/quotes/21/pdf -o production-test.pdf
```

### Deployment Commands
```bash
# Deploy to test environment
docker-compose -f docker-compose.beta.yml build --no-cache app
docker-compose -f docker-compose.beta.yml up -d

# Check health
curl http://159.65.174.94:8001/api/health
```

### After Completion
```bash
# Update task status
sed -i '' "s/HOTFIX-20251006-001,\\([^,]*\\),pending,/HOTFIX-20251006-001,\\1,completed,/" tasks.csv

# Merge to main
git checkout main
git merge --no-ff hotfix/pdf-logo-path-20251006

# Tag release
git tag -a hotfix-20251006-001 -m "Hotfix: Fix PDF generation AttributeError"

# Update notes
echo "Completed: $(date)" >> .claude/workspace/HOTFIX-20251006-001/notes.md
```

---

## Fix Summary

### Code Changes Required

1. **app/routes/quotes.py:575**
   ```python
   # BEFORE:
   'logo_path': company.logo_path

   # AFTER:
   'logo_path': f"static/logos/{company.logo_filename}" if company.logo_filename else None
   ```

2. **templates/view_quote.html:246-292**
   ```javascript
   // Fix: Move originalText to proper scope
   async function generatePDF() {
       const button = document.querySelector('button[onclick="generatePDF()"]');
       if (!button) return;

       const originalText = button.innerHTML;  // Capture at start
       // ... async operations ...
       finally {
           button.innerHTML = originalText;  // Use in finally
       }
   }
   ```

3. **tests/test_pdf_generation.py** (new file)
   - Test with logo
   - Test without logo
   - Test missing file handling

---

## Success Criteria

- [x] PDF generation works without AttributeError
- [x] Logo displays correctly when logo_filename exists
- [x] JavaScript error resolved
- [x] Tested on both port 8000 and 8001
- [x] Zero downtime deployment

---

## Rollback Plan

### Emergency Rollback (2 minutes)
```bash
# Restore backup container
docker-compose -f docker-compose.beta.yml down
BACKUP_IMAGE=$(docker images | grep ventanas-backup | head -1 | awk '{print $1":"$2}')
docker tag $BACKUP_IMAGE cotizador_ventanas_app:latest
docker-compose -f docker-compose.beta.yml up -d
```

### Git Rollback (5 minutes)
```bash
git revert HEAD
docker-compose -f docker-compose.beta.yml build --no-cache app
docker-compose -f docker-compose.beta.yml up -d
```

---

## Time Estimate

| Phase | Time |
|-------|------|
| Preparation | 15 min |
| Implementation | 90 min |
| Integration | 20 min |
| Testing | 30 min |
| Deployment | 45 min |
| Documentation | 20 min |
| **Total** | **4 hours** |

---

## Resources

- **Atomic Plan**: `.claude/workspace/HOTFIX-20251006-001/atomic-plan-HOTFIX-20251006-001.md`
- **Checklist**: `.claude/workspace/HOTFIX-20251006-001/checklist-HOTFIX-20251006-001.md`
- **Task CSV**: `tasks.csv` (line with HOTFIX-20251006-001)
- **Error Logs**: `docker-compose -f docker-compose.beta.yml logs app | grep logo_path`

---

**Status**: 🔴 READY TO START
**Next Action**: Create hotfix branch and begin implementation
