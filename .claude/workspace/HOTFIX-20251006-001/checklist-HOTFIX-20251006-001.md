# Execution Checklist: HOTFIX-20251006-001

## Phase 1: Preparation
- [x] Verify current branch status
- [x] Check production error logs for affected quotes
- [x] Identify test quotes with and without logos
- [x] Backup current production state
- [x] Review Company model schema

## Phase 2: Implementation
- [x] Create hotfix branch from main
- [x] Fix Company logo_path AttributeError in quotes.py line 575
- [x] Fix JavaScript originalText scope issue in view_quote.html
- [x] Search for additional logo_path usage in codebase
- [x] Test PDF generation locally (with logo)
- [x] Test PDF generation locally (without logo)
- [x] Create automated test cases
- [x] **DISCOVERED BUG**: Fix Quote.quote_data access in PDF generation

## Phase 3: Integration
- [x] Run all local tests
- [x] Check for linting errors
- [x] Verify import statements
- [x] Check for circular dependencies

## Phase 4: Testing
- [x] Build Docker image with no cache
- [x] Deploy to test environment (localhost:8000)
- [x] Test PDF with logo on localhost:8000
- [x] Test PDF without logo on localhost:8000
- [x] Verify no JavaScript errors in browser console
- [x] Test error recovery scenarios

## Phase 5: Deployment
- [ ] Backup production container
- [ ] Push hotfix branch to remote
- [ ] Build production Docker image
- [ ] Deploy to production (159.65.174.94:8000)
- [ ] Run production smoke tests
- [ ] Verify quote 21 PDF generates
- [ ] Verify quote 24 PDF generates
- [ ] Monitor logs for 5 minutes
- [ ] Confirm no errors in production

## Phase 6: Documentation
- [ ] Update task status to completed in tasks.csv
- [x] Create HOTFIX-SUMMARY.md
- [ ] Merge hotfix branch to main
- [ ] Tag release with hotfix version
- [ ] Update CHANGELOG.md
- [ ] Update CLAUDE.md with fix notes

## Code Changes Checklist
- [x] app/routes/quotes.py:575 fixed (logo_path AttributeError)
- [x] app/routes/quotes.py:580 fixed (Quote.quote_data access)
- [x] templates/view_quote.html JavaScript scope fixed
- [x] tests/test_pdf_generation.py created
- [x] All changes committed atomically (6 commits)

## Verification Checklist
- [x] PDF generation works on localhost
- [x] No AttributeError in logs
- [x] No JavaScript console errors
- [x] Logo displays correctly when present
- [x] Graceful handling when logo absent
- [x] Button state restores properly
- [x] All automated tests pass
