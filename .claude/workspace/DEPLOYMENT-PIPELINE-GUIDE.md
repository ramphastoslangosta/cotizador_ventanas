# Complete Development Pipeline Guide

**Created**: 2025-10-31
**Purpose**: Document the complete SDLC pipeline for all tasks

---

## 📋 Development Pipeline Stages

Every task should go through these stages, reflected in tasks.csv status field:

### Stage 1: Development (`in-progress`)
- Coding on feature branch
- Unit tests created
- Integration tests created
- Local testing complete

### Stage 2: Code Review (`code-review`)
- Peer review completed
- All review comments addressed
- Branch ready to merge

### Stage 3: Merged to Main (`merged`)
- Merged to main branch with --no-ff
- Pushed to GitHub
- Ready for test deployment

### Stage 4: Test Environment (`deployed-test`)
- Deployed to test droplet (port 8001)
- Database migrations applied
- Initial smoke tests passed
- 24-hour monitoring in progress

### Stage 5: Test Monitoring (`monitoring-test`)
- 24-hour monitoring period active
- Hourly/4-hour checks performed
- Issues tracked and resolved
- Final decision: APPROVE or ROLLBACK

### Stage 6: Production Deployment (`deployed-production`)
- Deployed to production droplet (port 8000)
- Database migrations applied
- Production smoke tests passed
- Beta users notified

### Stage 7: Production Monitoring (`monitoring-production`)
- 7-day monitoring period
- Daily health checks
- User feedback collected
- Performance metrics tracked

### Stage 8: Complete (`completed`)
- All monitoring complete
- No issues found
- Feature fully adopted
- Task closed

---

## 🔄 tasks.csv Status Values

Update tasks.csv `status` field as task progresses through pipeline:

| Status | Description | Duration | Next Step |
|--------|-------------|----------|-----------|
| `pending` | Not started | - | Start development |
| `in-progress` | Active development | Variable | Complete code |
| `code-review` | Awaiting review | 1-2 days | Address feedback |
| `merged` | Merged to main | Minutes | Deploy to test |
| `deployed-test` | Running on test (8001) | 24+ hours | Monitor |
| `monitoring-test` | Test monitoring active | 24 hours | Approve/reject |
| `deployed-production` | Running on prod (8000) | 7+ days | Monitor |
| `monitoring-production` | Prod monitoring active | 7 days | Close task |
| `completed` | Fully complete | - | Archive |
| `blocked` | Dependency issue | Variable | Unblock |
| `on-hold` | Paused | Variable | Resume |

---

## 🚀 Deployment Commands

### Test Environment (Port 8001)

```bash
# 1. Ensure on main branch with latest code
git checkout main
git pull origin main

# 2. Deploy to test
bash scripts/deploy-test.sh

# 3. Verify deployment
curl http://159.65.174.94:8001/api/health

# 4. Apply database migrations (if any)
docker exec ventanas-test-app alembic upgrade head

# 5. Verify migration
docker exec ventanas-test-db psql -U ventanas_user -d ventanas_test_db \
  -c "\dt"  # List tables

# 6. Run smoke tests
# - Open http://159.65.174.94:8001
# - Test key functionality
# - Check logs: docker logs ventanas-test-app --tail 100
```

### Production Environment (Port 8000)

**ONLY after 24-hour test monitoring passes**

```bash
# 1. Backup production database
docker exec ventanas-prod-db pg_dump -U ventanas_user ventanas_db > \
  backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Deploy to production
bash scripts/deploy-production.sh

# 3. Apply migrations
docker exec ventanas-prod-app alembic upgrade head

# 4. Verify deployment
curl http://159.65.174.94:8000/api/health

# 5. Production smoke tests
# - Open http://159.65.174.94:8000
# - Test all features
# - Notify beta users
```

---

## 📊 Monitoring Checklist Template

### Test Environment (24 Hours)

**Hour 0 (Deployment)**
- [ ] Application starts successfully
- [ ] Health endpoint responds (200 OK)
- [ ] Database migrations applied
- [ ] UI accessible
- [ ] Key features work
- [ ] No errors in logs

**Hour 4, 8, 12, 16, 20, 24**
- [ ] Application still running
- [ ] Health endpoint responds
- [ ] No errors in logs
- [ ] Performance acceptable

**Hour 24 (Final Decision)**
- [ ] All checks passed
- [ ] Performance metrics collected
- [ ] DECISION: APPROVE FOR PRODUCTION

### Production Environment (7 Days)

**Day 1-7 (Daily Checks)**
- [ ] Application stable
- [ ] No user-reported issues
- [ ] Logs clean
- [ ] Performance normal

**Day 7 (Final Review)**
- [ ] Feature fully adopted
- [ ] No rollbacks needed
- [ ] Mark task as COMPLETED

---

## 📝 tasks.csv Notes Field Format

Use the `notes` field (last column) to track deployment pipeline status:

```
"🚀 DEPLOYED TO PRODUCTION (Date) - MONITORING COMPLETE.
✅ TEST ENV (Date) - 24h monitoring passed, zero issues.
✅ DEVELOPMENT COMPLETE (Date) - Brief summary.
DEPLOYMENT PIPELINE: [1/4] ✅ Code [2/4] ✅ Merged [3/4] ✅ Test [4/4] ✅ Prod"
```

**Example (Complete Pipeline)**:
```
"🎉 DEPLOYED TO PRODUCTION (Nov 3, 2025) - Week 1 monitoring complete, zero issues, feature fully adopted.
✅ TEST ENV (Oct 31, 2025 17:00) - 24h monitoring passed. Performance: 45ms avg response. Zero errors.
✅ MERGED TO MAIN (Oct 31, 2025 16:57) - Commit 204cef8. 16 commits, 12 files changed.
✅ DEVELOPMENT COMPLETE (Oct 31, 2025) - All 9 steps completed successfully. UAT: ALL TESTS PASSED.
DEPLOYMENT PIPELINE: [1/4] ✅ Code complete [2/4] ✅ Merged to main [3/4] ✅ Test env [4/4] ✅ Production.
Workspace: .claude/workspace/ARCH-20251029-002/. See DEPLOYMENT-TRACKING.md."
```

---

## 🔥 Rollback Procedures

### Test Environment Rollback

```bash
# 1. Stop test container
docker-compose -f docker-compose.test.yml down

# 2. Rollback database (if migration applied)
docker exec ventanas-test-app alembic downgrade -1

# 3. Reset code (if needed)
git checkout main
git reset --hard <previous-commit>
git push --force origin main

# 4. Redeploy
bash scripts/deploy-test.sh
```

### Production Rollback

```bash
# 1. Stop production container
docker-compose -f docker-compose.beta.yml down

# 2. Restore database from backup
docker exec ventanas-prod-db psql -U ventanas_user ventanas_db < \
  backup_YYYYMMDD_HHMMSS.sql

# 3. Rollback code
git checkout main
git revert <bad-commit>
git push origin main

# 4. Redeploy
bash scripts/deploy-production.sh

# 5. Notify users
# - Post rollback notice
# - Explain what happened
# - Timeline for fix
```

---

## 📧 Stakeholder Communication

### Test Deployment Notification

**To**: Team
**Subject**: [TEST] ARCH-20251029-002 Deployed to Test Environment

```
Hi team,

ARCH-20251029-002 (ProductCategory System) has been deployed to the test environment:
- URL: http://159.65.174.94:8001
- Deployed: Oct 31, 2025 17:00
- Monitoring: 24 hours (until Nov 1, 2025 17:00)

Please test the following:
- Create door products
- Create railing products
- Verify existing window products still work

Report any issues to #dev-channel.

Production deployment planned for Nov 1 (pending test monitoring).
```

### Production Deployment Notification

**To**: Beta Users
**Subject**: [PRODUCTION] New Feature: Doors, Railings, and Louvers Support

```
Hi [Name],

We've deployed a major feature that unblocks your DPTOS DZITYÁ project:

NEW: You can now create and quote:
- Doors (sliding, swing, pivot, louver)
- Railings (glass infill, aluminum picket, etc.)
- Louvers and canopies
- Skylights and curtain walls

Your 213 windows + 6 railings + 4 louvers + 77 glass pieces project is now 100% quotable.

URL: http://159.65.174.94:8000

If you encounter any issues, please contact support@company.com.

Thank you!
```

---

## 🎯 Success Metrics

Track these metrics for each deployment:

### Technical Metrics
- [ ] Deployment time: _______ minutes
- [ ] Downtime: _______ seconds (target: 0)
- [ ] Response time: _______ ms (target: <500ms)
- [ ] Error rate: _______ % (target: 0%)
- [ ] Database migration time: _______ seconds

### Business Metrics
- [ ] Features used: _______ (e.g., doors created: 5)
- [ ] User adoption rate: _______ %
- [ ] Support tickets: _______ (target: 0 critical)
- [ ] User satisfaction: _______ / 5

---

## ✅ Best Practices

1. **Always** use `--no-ff` for merges (preserve commit history)
2. **Always** push to GitHub before deploying
3. **Always** deploy to test before production
4. **Always** monitor test for 24 hours minimum
5. **Always** backup production database before deploying
6. **Never** skip the monitoring period
7. **Never** deploy on Fridays (weekend monitoring difficult)
8. **Never** deploy without smoke tests
9. **Document** every deployment in workspace
10. **Update** tasks.csv status after each stage

---

## 🔗 Related Documents

- `.claude/workspace/{TASK_ID}/DEPLOYMENT-TRACKING.md` - Per-task tracking
- `scripts/deploy-test.sh` - Test deployment script
- `scripts/deploy-production.sh` - Production deployment script
- `docs/DEPLOYMENT-RUNBOOK.md` - Detailed runbook (if exists)

---

**Last Updated**: 2025-10-31
**Version**: 1.0
**Maintainer**: Development Team
