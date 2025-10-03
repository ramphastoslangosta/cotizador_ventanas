# Execution Checklist: DEVOPS-20251001-001

## PHASE 1: PREPARATION
- [ ] Review HOTFIX-20251001-RCA.md for context
- [ ] Check current Docker setup
- [ ] Verify test environment accessible
- [x] Create task branch: `devops/docker-build-improvements-20251001`
- [ ] Backup Dockerfile and docker-compose.beta.yml
- [ ] Document baseline build metrics

## PHASE 2: IMPLEMENTATION

### Dockerfile Improvements
- [ ] Add Python cache clearing after `COPY . .`
- [ ] Add build verification step
- [ ] Verify chmod +x scripts/*.sh exists
- [ ] Test Dockerfile builds locally

### Deployment Scripts
- [ ] Create scripts/deploy-production.sh
- [ ] Create scripts/deploy-test.sh
- [ ] Set execute permissions on scripts
- [ ] Test script syntax validation

### Docker Compose
- [ ] Update health check settings in docker-compose.beta.yml
- [ ] Create docker-compose.test.yml
- [ ] Validate YAML syntax

## PHASE 3: INTEGRATION & TESTING
- [ ] Make scripts executable
- [ ] Build Docker image locally
- [ ] Verify build verification messages appear
- [ ] Verify Python cache cleared
- [ ] Test deployment script dry-run

## PHASE 4: DOCUMENTATION
- [ ] Create docs/DEPLOYMENT-RUNBOOK.md
- [ ] Update CLAUDE.md with Docker deployment section
- [ ] Create success criteria document
- [ ] Document all troubleshooting steps

## PHASE 5: DEPLOYMENT VERIFICATION
- [ ] Deploy to test environment (port 8001)
- [ ] Verify health checks passing
- [ ] Verify build verification in logs
- [ ] Test deployment script end-to-end
- [ ] Confirm no Python cache issues
- [ ] Create pre-production checklist

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
