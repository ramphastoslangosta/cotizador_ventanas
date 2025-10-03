# Task Workspace: DEVOPS-20251001-001

**Title:** Docker build improvements
**Started:** 2025-10-02
**Priority:** HIGH
**Estimated Effort:** 1 week (5-7 days)
**Status:** Ready to start

---

## Overview

Implement comprehensive Docker build improvements to prevent Python bytecode cache and Docker layer caching issues that caused deployment problems during HOTFIX-20251001-001.

**Root Cause Reference:** During HOTFIX-20251001-001, multiple rebuild attempts didn't update the container due to Python .pyc cache and Docker layer caching, requiring 6 rebuilds with `--no-cache` flag.

---

## Files

- `atomic-plan-DEVOPS-20251001-001.md` - Detailed step-by-step execution plan
- `checklist-DEVOPS-20251001-001.md` - Execution checklist (tick off items as complete)
- `notes.md` - Session notes and observations
- `success-criteria.md` - (Will be created during documentation phase)
- `pre-production-checklist.md` - (Will be created during deployment verification)

---

## Quick Commands

### Start Work Session
```bash
cd /Users/rafaellang/cotizador/cotizador_ventanas
git checkout -b devops/docker-build-improvements-20251001
cat .claude/workspace/DEVOPS-20251001-001/atomic-plan-DEVOPS-20251001-001.md
```

### Track Progress
```bash
# Completed items
grep "\[x\]" .claude/workspace/DEVOPS-20251001-001/checklist-DEVOPS-20251001-001.md | wc -l

# Remaining items
grep "\[ \]" .claude/workspace/DEVOPS-20251001-001/checklist-DEVOPS-20251001-001.md | wc -l

# View checklist
cat .claude/workspace/DEVOPS-20251001-001/checklist-DEVOPS-20251001-001.md
```

### Test Deployment
```bash
# Test environment deployment
bash scripts/deploy-test.sh

# Verify test environment
curl http://localhost:8001/api/health | jq
```

---

## Success Criteria

1. ✅ **Build Verification:** Dockerfile includes verification step confirming code changes
2. ✅ **Python Cache Clearing:** All .pyc files and __pycache__ removed during build
3. ✅ **Deployment Script:** Automated script with pre/post verification
4. ✅ **Test Environment:** Separate test deployment capability (port 8001)
5. ⏳ **Production Tested:** Awaiting production deployment
6. ✅ **Documentation:** Complete runbook created
7. ⏳ **Zero Downtime:** To be verified in production

---

## Key Deliverables

### Code Changes
1. **Dockerfile:**
   - Python cache clearing after COPY step
   - Build verification step (imports, route count)

2. **Deployment Scripts:**
   - `scripts/deploy-production.sh` - Production with verification
   - `scripts/deploy-test.sh` - Test environment (port 8001)

3. **Docker Compose:**
   - Updated health check settings (90s start period, 5 retries)
   - New test environment config (docker-compose.test.yml)

### Documentation
1. **docs/DEPLOYMENT-RUNBOOK.md:**
   - Standard deployment procedure
   - Hotfix deployment procedure
   - Troubleshooting guide
   - Rollback procedures

2. **CLAUDE.md:**
   - Docker deployment section
   - Quick reference commands

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Preparation | 30 min | Setup, backups, baseline |
| Implementation | 4-5 hours | Dockerfile, scripts, compose |
| Testing | 2-3 hours | Local build, verification |
| Documentation | 1-2 hours | Runbook, updates |
| Verification | 1-2 hours | Test environment deploy |
| Finalization | 30 min | Review, PR |
| **TOTAL** | **9-13 hours** | **~2 work days** |

---

## Related Tasks

- **Root Cause:** HOTFIX-20251001-001 (router data processing fix)
- **Prevents:** Future Python cache deployment issues
- **Depends On:** None (can start immediately)
- **Blocks:** None (but improves all future deployments)

---

## Testing Strategy

1. **Local Build Testing:**
   - Build Dockerfile locally
   - Verify build verification messages
   - Confirm Python cache cleared

2. **Test Environment:**
   - Deploy to port 8001
   - Monitor for 24 hours
   - Verify no stale code issues

3. **Production:**
   - Deploy during low-traffic window
   - Monitor health checks
   - Verify zero downtime
   - Monitor for 1 week

---

## Rollback Plan

### If Issues Arise During Development
```bash
# Rollback all changes
git checkout main
git branch -D devops/docker-build-improvements-20251001
```

### If Issues After Deployment
```bash
# Rollback to previous commit
git checkout <previous-stable-commit>
bash scripts/deploy-production.sh
```

---

## Notes During Execution

Add observations, issues, and solutions here as you work:

- [ ] **Date:** YYYY-MM-DD - Note...

---

## Completion Steps

After all code changes complete:

1. ✅ Merge PR to main
2. ⏳ Deploy to test environment
3. ⏳ Monitor test for 24 hours
4. ⏳ Deploy to production
5. ⏳ Monitor production for 1 week
6. ⏳ Update tasks.csv status to completed

```bash
# Mark task complete in tasks.csv
sed -i '' 's/DEVOPS-20251001-001,\([^,]*\),pending,/DEVOPS-20251001-001,\1,completed,/' tasks.csv

# Verify
grep "DEVOPS-20251001-001" tasks.csv
```

---

## Contact / Questions

- **Task Owner:** DevOps Team
- **Related RCA:** HOTFIX-20251001-RCA.md
- **Deployment Runbook:** docs/DEPLOYMENT-RUNBOOK.md (after creation)

---

**Last Updated:** 2025-10-02
**Workspace:** `.claude/workspace/DEVOPS-20251001-001/`
