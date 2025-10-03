# Pre-Production Deployment Checklist

## Code Review
- [ ] All commits reviewed and approved
- [ ] No debug code or test comments in main branch
- [ ] CLAUDE.md updated with deployment info
- [ ] Deployment runbook reviewed

## Testing
- [ ] Test environment deployment successful
- [ ] Build verification messages confirmed in logs
- [ ] Health checks passing in test environment
- [ ] No Python cache issues observed
- [ ] Deployment script completed without errors

## Documentation
- [ ] DEPLOYMENT-RUNBOOK.md complete and accurate
- [ ] Troubleshooting section includes common issues
- [ ] Rollback procedures documented and tested
- [ ] Team briefed on new deployment process

## Backups
- [ ] Recent database backup exists
- [ ] Current deployment logs backed up
- [ ] Git tag created for current production version

## Monitoring
- [ ] Health check endpoint working
- [ ] Log monitoring configured
- [ ] Alert contacts updated

## Rollback Plan
- [ ] Rollback procedure tested in test environment
- [ ] Previous stable commit identified: `git log --oneline -5`
- [ ] Rollback script ready if needed

## Team Communication
- [ ] Team notified of deployment window
- [ ] On-call engineer available
- [ ] Deployment time scheduled (low-traffic window)

## Production Deployment Steps

1. Create production backup:
   ```bash
   bash scripts/create-backup.sh  # If exists, or manual backup
   ```

2. Tag current production version:
   ```bash
   git tag -a v5.0.0-pre-devops-improvements -m "Before DEVOPS-20251001-001"
   ```

3. Deploy to production:
   ```bash
   bash scripts/deploy-production.sh
   ```

4. Monitor for 1 hour:
   ```bash
   docker-compose -f docker-compose.beta.yml logs -f app | grep -i error
   ```

5. Mark task complete:
   ```bash
   # Update tasks.csv status to completed
   ```

## Post-Deployment Monitoring (First 24 Hours)

- [ ] Hour 1: Check logs for errors
- [ ] Hour 2: Verify user logins working
- [ ] Hour 4: Check quotes creation workflow
- [ ] Hour 8: Review error rates
- [ ] Hour 24: Full system health check

## Success Metrics

- ✅ Single deployment attempt (no rebuilds needed)
- ✅ Zero downtime during deployment
- ✅ All endpoints responding normally
- ✅ No stale code issues reported
- ✅ Health checks passing consistently
