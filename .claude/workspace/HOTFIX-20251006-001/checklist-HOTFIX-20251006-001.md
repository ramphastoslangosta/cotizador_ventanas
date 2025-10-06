# Execution Checklist: HOTFIX-20251006-001

## Phase 1: Preparation
- [ ] Verify current branch status
- [ ] Check production error logs for affected quotes
- [ ] Identify test quotes with and without logos
- [ ] Backup current production state
- [ ] Review Company model schema

## Phase 2: Implementation
- [x] Create hotfix branch from main
- [x] Fix Company logo_path AttributeError in quotes.py line 575
- [x] Fix JavaScript originalText scope issue in view_quote.html
- [ ] Search for additional logo_path usage in codebase
- [ ] Test PDF generation locally (with logo)
- [ ] Test PDF generation locally (without logo)
- [ ] Create automated test cases

## Phase 3: Integration
- [ ] Run all local tests
- [ ] Check for linting errors
- [ ] Verify import statements
- [ ] Check for circular dependencies

## Phase 4: Testing
- [ ] Build Docker image with no cache
- [ ] Deploy to test environment (port 8001)
- [ ] Test PDF with logo on port 8001
- [ ] Test PDF without logo on port 8001
- [ ] Verify no JavaScript errors in browser console
- [ ] Test error recovery scenarios

## Phase 5: Deployment
- [ ] Backup production container
- [ ] Push hotfix branch to remote
- [ ] Build production Docker image
- [ ] Deploy to production (port 8000)
- [ ] Run production smoke tests
- [ ] Verify quote 21 PDF generates
- [ ] Verify quote 24 PDF generates
- [ ] Monitor logs for 5 minutes
- [ ] Confirm no errors in production

## Phase 6: Documentation
- [ ] Update task status to completed in tasks.csv
- [ ] Create HOTFIX-SUMMARY.md
- [ ] Merge hotfix branch to main
- [ ] Tag release with hotfix version
- [ ] Update CHANGELOG.md
- [ ] Update CLAUDE.md with fix notes

## Code Changes Checklist
- [x] app/routes/quotes.py:575 fixed
- [x] templates/view_quote.html JavaScript scope fixed
- [ ] tests/test_pdf_generation.py created
- [ ] All changes committed atomically

## Verification Checklist
- [ ] PDF generation works on production
- [ ] No AttributeError in logs
- [ ] No JavaScript console errors
- [ ] Logo displays correctly when present
- [ ] Graceful handling when logo absent
- [ ] Button state restores properly
- [ ] All automated tests pass
