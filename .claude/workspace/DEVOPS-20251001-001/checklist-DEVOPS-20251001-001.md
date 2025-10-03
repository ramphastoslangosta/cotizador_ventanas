# Execution Checklist: DEVOPS-20251001-001

## PHASE 1: PREPARATION
- [ ] Review HOTFIX-20251001-RCA.md for context
- [ ] Check current Docker setup
- [ ] Verify test environment accessible
- [x] Create task branch: `devops/docker-build-improvements-20251001`
- [x] Backup Dockerfile and docker-compose.beta.yml
- [x] Document baseline build metrics

## PHASE 2: IMPLEMENTATION

### Dockerfile Improvements
- [x] Add Python cache clearing after `COPY . .`
- [x] Add build verification step
- [x] Verify chmod +x scripts/*.sh exists
- [x] Test Dockerfile builds locally

### Deployment Scripts
- [x] Create scripts/deploy-production.sh
- [x] Create scripts/deploy-test.sh
- [x] Set execute permissions on scripts
- [ ] Test script syntax validation

### Docker Compose
- [x] Update health check settings in docker-compose.beta.yml
- [x] Create docker-compose.test.yml
- [ ] Validate YAML syntax

## PHASE 3: INTEGRATION & TESTING
- [ ] Make scripts executable
- [ ] Build Docker image locally
- [ ] Verify build verification messages appear
- [ ] Verify Python cache cleared
- [x] Test deployment script dry-run

## PHASE 4: DOCUMENTATION
- [x] Create docs/DEPLOYMENT-RUNBOOK.md
- [x] Update CLAUDE.md with Docker deployment section
- [x] Create success criteria document
- [ ] Document all troubleshooting steps

## PHASE 5: DEPLOYMENT VERIFICATION
- [x] Deploy to test environment (port 8001)
- [ ] Verify health checks passing
- [x] Verify build verification in logs
- [x] Test deployment script end-to-end
- [ ] Confirm no Python cache issues
- [x] Create pre-production checklist

## PHASE 6: FINALIZATION
- [ ] Final code review
- [ ] Push branch to remote
- [ ] Create pull request
- [ ] Update task notes

## POST-MERGE (After PR Approval)
- [ ] Merge to main
- [ ] Deploy to test environment
- [ ] Monitor test environment 24 hours
- [ ] Deploy to production
- [ ] Monitor production 1 week
- [ ] Mark task as completed in tasks.csv

## COMMITS CHECKLIST
- [ ] Commit 1: Python cache clearing in Dockerfile
- [ ] Commit 2: Build verification in Dockerfile
- [ ] Commit 3: Production deployment script
- [ ] Commit 4: Test environment deployment script
- [ ] Commit 5: Health check improvements
- [ ] Commit 6: Test environment docker-compose
- [ ] Commit 7: Deployment runbook
- [ ] Commit 8: CLAUDE.md updates
