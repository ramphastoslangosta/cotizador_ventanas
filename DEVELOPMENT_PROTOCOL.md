# Development Protocol - Window Quotation System

## 🔄 **Standard Development Workflow**

This document establishes the protocol for making changes to the Window Quotation System deployed on DigitalOcean.

---

## 📋 **Pre-Development Checklist**

### 1. **System Analysis Phase**
- [ ] Study existing code structure and dependencies
- [ ] Identify all affected files and components
- [ ] Review database schema and model relationships
- [ ] Check for existing similar implementations
- [ ] Document current state vs desired state

### 2. **Planning Phase**
- [ ] Check `utilities/tasks.csv` for related tasks and sprint planning
- [ ] Create TodoWrite task list for the immediate changes
- [ ] Update task status in CSV sprint planner
- [ ] Break down complex changes into smaller steps
- [ ] Identify potential breaking changes or dependencies
- [ ] Plan rollback strategy if needed

### 3. **Sprint Integration**
- [ ] Verify task is assigned to current sprint in `utilities/tasks.csv`
- [ ] Update task status to "in-progress" when starting work
- [ ] Reference task_id in commit messages for traceability
- [ ] Update acceptance criteria completion status

---

## 🛠️ **Development Process**

### **Step 1: Local Development**
```bash
# Work on local machine first
cd "/Users/rafaellang/Library/Mobile Documents/com~apple~CloudDocs/Proyectos/cotizador_v1/fastapi-auth-example"

# Make all necessary changes locally
# Test changes locally if possible
```

### **Step 2: Code Review & Validation**
- [ ] Review all changes for consistency
- [ ] Ensure proper error handling
- [ ] Verify database model compatibility
- [ ] Check for security implications
- [ ] Validate business logic

### **Step 3: Enhanced Git Workflow**

#### **3.1 Branching Strategy**
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/[feature-name]
# OR for hotfixes
git checkout -b hotfix/[issue-description]

# Work on your changes in the feature branch
```

#### **3.2 Commit Standards (Conventional Commits)**
```bash
# Stage specific files (avoid git add .)
git add [specific_files]

# Commit with conventional format
git commit -m "[type]([scope]): [description]

[optional body explaining the what and why]

- Specific change 1
- Specific change 2
- Any breaking changes noted

BREAKING CHANGE: [description if applicable]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Commit types: feat, fix, docs, style, refactor, test, chore
# Examples with task ID references:
# feat(UXE-001,auth): add user session timeout functionality
# fix(CUX-001,bom): correct material quantity calculation
# docs(ST-001,api): update endpoint documentation
# 
# Legacy format (without task IDs):
# feat(auth): add user session timeout functionality
# fix(bom): correct material quantity calculation
```

#### **3.3 Pre-Push Validation**
```bash
# Run tests if available
python -m pytest  # or appropriate test command

# Check code formatting (if using black)
black --check .

# Lint check (if using flake8/pylint)
flake8 .

# Push feature branch
git push origin feature/[feature-name]
```

#### **3.4 Pull Request Workflow**
```bash
# Create PR via GitHub CLI (recommended)
gh pr create --title "[type]: Brief description" --body "
## Summary
- Change summary point 1  
- Change summary point 2

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)  
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Local testing performed
- [ ] No new warnings/errors
- [ ] Database migrations tested (if applicable)

## Deployment Notes
- [ ] No special deployment steps required
- [ ] Environment variables added/changed: [list]
- [ ] Database changes require: [description]

## Checklist
- [ ] Code follows project conventions
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Tests updated (if applicable)
"

# OR create PR via web interface at: https://github.com/[username]/[repo]/pull/new
```

#### **3.5 Merge to Main (After PR Approval)**
```bash
# Ensure PR is approved and checks pass
# Merge via GitHub interface (preferred) OR:

git checkout main
git pull origin main
git merge --no-ff feature/[feature-name]
git push origin main

# Clean up feature branch
git branch -d feature/[feature-name]
git push origin --delete feature/[feature-name]
```

#### **3.6 Direct Push Protocol (Emergency Only)**
For urgent hotfixes when PR workflow would cause delays:
```bash
# Only for critical production issues
git checkout main
git pull origin main

# Make minimal changes
git add [specific_files]
git commit -m "hotfix: [critical-issue-description]

- Minimal change to resolve critical issue
- Will create follow-up PR for proper review

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
# MUST follow up with proper PR for code review
```

### **Step 4: Deployment to DigitalOcean**
```bash
# SSH to droplet
ssh root@159.65.174.94

# Navigate to app directory
cd /home/ventanas/app

# Pull latest changes
git pull origin main

# Stop current services
docker-compose -f docker-compose.beta.yml stop app

# Remove old image if needed
docker rmi app-app  # Only if significant changes

# Rebuild and start
docker-compose -f docker-compose.beta.yml up -d --build app

# Wait for startup
sleep 15

# Verify deployment
curl http://localhost:8000/health
```

### **Step 5: Post-Deployment Verification**
```bash
# Check container status
docker-compose -f docker-compose.beta.yml ps

# Check logs for errors
docker-compose -f docker-compose.beta.yml logs app --tail=20

# Test key functionality
curl -I http://localhost:8000/
```

---

## 🌿 **Git Branching Strategy**

### **Branch Types and Naming Conventions**

#### **Main Branches:**
- **`main`**: Production-ready code, always deployable
- **`develop`**: Integration branch for features (optional for small teams)

#### **Supporting Branches:**

**Feature Branches:**
- **Naming**: `feature/[issue-number]-[brief-description]` or `feature/[brief-description]`
- **Purpose**: New features or enhancements
- **Examples**: `feature/123-user-authentication`, `feature/pdf-export`
- **Lifetime**: Created from main, merged back via PR, then deleted

**Hotfix Branches:**
- **Naming**: `hotfix/[issue-number]-[brief-description]` or `hotfix/[brief-description]`  
- **Purpose**: Critical production fixes
- **Examples**: `hotfix/security-vulnerability`, `hotfix/login-error`
- **Lifetime**: Created from main, merged back immediately, then deleted

**Chore Branches:**
- **Naming**: `chore/[description]`
- **Purpose**: Maintenance, dependency updates, documentation
- **Examples**: `chore/update-dependencies`, `chore/refactor-services`

### **Branch Protection Rules (GitHub Settings)**

For production repositories, configure these settings:

```yaml
# .github/branch-protection-rules.yml (reference)
main:
  required_status_checks:
    - "Continuous Integration"
    - "Security Scan"
  enforce_admins: false
  require_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
    restrict_dismissals: false
  restrictions: null
  allow_force_pushes: false
  allow_deletions: false
```

### **Workflow for Different Change Types**

#### **Feature Development (Standard):**
```bash
git checkout main
git pull origin main
git checkout -b feature/new-quotation-features
# ... make changes ...
git push origin feature/new-quotation-features
# Create PR, get review, merge via GitHub
```

#### **Hotfix (Critical):**
```bash
git checkout main
git pull origin main
git checkout -b hotfix/fix-calculation-bug
# ... make minimal fix ...
git push origin hotfix/fix-calculation-bug
# Create PR with "hotfix" label, expedited review
```

#### **Documentation/Chore:**
```bash
git checkout main
git pull origin main
git checkout -b chore/update-development-protocol
# ... make changes ...
git push origin chore/update-development-protocol
# Create PR, standard review process
```

---

## 📝 **Commit Message Standards**

### **Conventional Commits Format**

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
[type]([optional scope]): [description]

[optional body]

[optional footer(s)]
```

### **Commit Types**

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add user session timeout` |
| `fix` | Bug fix | `fix(bom): correct material quantity calculation` |
| `docs` | Documentation only | `docs(api): update endpoint documentation` |
| `style` | Code style changes (formatting, etc.) | `style: fix indentation in main.py` |
| `refactor` | Code refactoring (no feature/bug changes) | `refactor(database): extract user service class` |
| `test` | Adding or updating tests | `test(auth): add session timeout tests` |
| `chore` | Maintenance tasks | `chore: update dependencies to latest versions` |
| `perf` | Performance improvements | `perf(bom): optimize material lookup queries` |
| `ci` | CI/CD changes | `ci: add automated testing workflow` |
| `build` | Build system or dependencies | `build: add new FastAPI dependency` |
| `revert` | Revert previous commit | `revert: "feat(auth): add session timeout"` |

### **Scopes (Optional but Recommended)**

Use scopes to indicate which part of the codebase is affected:

| Scope | Description |
|-------|-------------|
| `auth` | Authentication/authorization |
| `bom` | BOM calculations and services |
| `database` | Database models and operations |
| `api` | API endpoints and routing |
| `ui` | Frontend/templates |
| `config` | Configuration changes |
| `security` | Security-related changes |
| `deploy` | Deployment configuration |

### **Message Guidelines**

#### **Subject Line (First Line):**
- **Length**: Maximum 50 characters
- **Capitalization**: Lowercase after the colon
- **Tense**: Use imperative mood ("add" not "added" or "adds")
- **No period**: Don't end with a period

✅ **Good Examples:**
```
feat(auth): add password reset functionality
fix(bom): resolve material quantity miscalculation
docs: update deployment instructions
```

❌ **Bad Examples:**
```
Added password reset feature.  # Wrong tense, too long, has period
fix: fixed bug  # Too vague
Auth feature  # Missing type and colon
```

#### **Body (Optional):**
- **Length**: Wrap at 72 characters per line
- **Content**: Explain **what** and **why**, not **how**
- **Separation**: Blank line between subject and body

```bash
feat(quote): add export to CSV functionality

Users requested the ability to export quotation data to CSV format
for external analysis. This adds a new endpoint and UI button that
generates CSV files with all quote details including materials.

- Add /quotes/{id}/export endpoint
- Include CSV generation utility functions
- Add download button to quote detail page
```

#### **Footer (Optional):**
- **Breaking Changes**: Use `BREAKING CHANGE:` for incompatible API changes
- **Issue References**: Link to issues with `Closes #123` or `Fixes #456`
- **Co-authors**: Include `Co-authored-by:` for pair programming

```bash
feat(api): restructure material endpoints

BREAKING CHANGE: Material API endpoints now use /api/v2/materials
instead of /materials. Update all client integrations.

Closes #234
Fixes #567

Co-authored-by: Jane Developer <jane@example.com>
```

### **Project-Specific Requirements**

**Always include Claude Code attribution:**
```bash
feat(auth): add user session management

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### **Commit Message Templates**

Create `.gitmessage` template file:
```bash
# Title: Summary, imperative, start upper case, don't end with a period
# No more than 50 chars. #### 50 chars is here:  #

# Remember blank line between title and body.

# Body: Explain *what* and *why* (not *how*). Include task ID (Jira issue).
# Wrap at 72 chars. ################################## which is here:  #


# At the end: Include any information about Breaking Changes and also
# include any information about GitHub closing issues such as "Fixes #4"
# or "Closes #67".

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Set the template:
```bash
git config commit.template .gitmessage
```

---

## ⚙️ **Git Hooks and Automation**

### **Pre-commit Hooks Setup**

Git hooks help ensure code quality and consistency. Install pre-commit framework:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml in repository root
```

#### **Recommended Pre-commit Configuration**

Create `.pre-commit-config.yaml`:
```yaml
# .pre-commit-config.yaml
repos:
  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-json

  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  # Python import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  # Python linting
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  # Python security linting
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, ., -ll, --skip=B101,B601]

  # Commit message validation
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v2.1.1
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

#### **Installation and Setup**

```bash
# Install the git hook scripts
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg

# (Optional) Run against all files
pre-commit run --all-files
```

### **Manual Pre-push Checks**

If pre-commit is not available, run these checks manually before pushing:

```bash
#!/bin/bash
# save as scripts/pre-push-check.sh

echo "🔍 Running pre-push checks..."

# Code formatting check
echo "Checking code formatting..."
black --check . || (echo "❌ Code formatting issues found. Run: black ." && exit 1)

# Import sorting check
echo "Checking import sorting..."
isort --check-only . || (echo "❌ Import sorting issues found. Run: isort ." && exit 1)

# Linting check
echo "Running linting..."
flake8 . || (echo "❌ Linting issues found." && exit 1)

# Security check
echo "Running security check..."
bandit -r . -ll --skip=B101,B601 || (echo "⚠️ Security issues found." && exit 1)

# Test execution (if tests exist)
if [ -f "test_*.py" ] || [ -d "tests/" ]; then
    echo "Running tests..."
    python -m pytest || (echo "❌ Tests failed." && exit 1)
fi

echo "✅ All pre-push checks passed!"
```

Make executable:
```bash
chmod +x scripts/pre-push-check.sh
```

### **GitHub Actions Workflow (CI/CD)**

Create `.github/workflows/ci.yml` for automated testing:

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt  # if exists
    
    - name: Code formatting check
      run: black --check .
    
    - name: Import sorting check
      run: isort --check-only .
    
    - name: Linting
      run: flake8 .
    
    - name: Security check
      run: bandit -r . -ll --skip=B101,B601
    
    - name: Type checking (if using mypy)
      run: mypy . --ignore-missing-imports
    
    - name: Run tests
      run: python -m pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
```

### **Useful Git Aliases**

Add these to your `.gitconfig` or run as commands:

```bash
# Pretty log with graph
git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

# Show current branch
git config --global alias.current "branch --show-current"

# Quick commit with conventional format
git config --global alias.cz "commit -m"

# Undo last commit (keep changes staged)
git config --global alias.uncommit "reset --soft HEAD~1"

# Show modified files
git config --global alias.changed "diff --name-only"

# Quick stash with message
git config --global alias.stash-quick "stash push -m"
```

### **Development Workflow Automation**

#### **Quick Setup Script**

Create `scripts/setup-dev.sh`:
```bash
#!/bin/bash
# Development environment setup

echo "🚀 Setting up development environment..."

# Install pre-commit if not installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install git hooks
echo "Installing git hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Set git commit template if exists
if [ -f ".gitmessage" ]; then
    echo "Setting git commit template..."
    git config commit.template .gitmessage
fi

echo "✅ Development environment ready!"
echo "💡 Use 'git cz \"type(scope): description\"' for commits"
```

### **Repository Health Monitoring**

#### **Branch Cleanup Script**

Create `scripts/cleanup-branches.sh`:
```bash
#!/bin/bash
# Clean up merged branches

echo "🧹 Cleaning up merged branches..."

# Fetch latest changes
git fetch origin

# Delete local branches that are merged
git branch --merged main | grep -v "main\|develop" | xargs -n 1 git branch -d

# Show remaining branches
echo "Remaining branches:"
git branch -a

echo "✅ Branch cleanup complete!"
```

### **Commit Quality Metrics**

Track commit quality with this script `scripts/commit-stats.sh`:
```bash
#!/bin/bash
# Analyze commit message quality

echo "📊 Commit Message Analysis (last 50 commits)"

# Count conventional commits
conventional=$(git log --oneline -50 | grep -E '^[a-f0-9]+ (feat|fix|docs|style|refactor|test|chore)' | wc -l)
total=$(git log --oneline -50 | wc -l)

echo "Conventional commits: $conventional/$total"

# Show commit types distribution
echo -e "\nCommit types:"
git log --oneline -50 | grep -oE '(feat|fix|docs|style|refactor|test|chore)' | sort | uniq -c | sort -rn

# Show scope usage
echo -e "\nScopes used:"
git log --oneline -50 | grep -oE '\((.*?)\):' | sort | uniq -c | sort -rn
```

---

## 🗄️ **Database Changes Protocol**

### **For Schema Changes:**
1. **NEVER** directly modify database on droplet
2. Update SQLAlchemy models locally first
3. Test model changes thoroughly
4. Consider migration scripts for production
5. Document all schema changes

### **For Sample Data Updates:**
1. Update `initialize_sample_data()` function
2. Test data initialization locally if possible
3. On droplet, may need to:
   ```bash
   # Clear existing data if needed (CAUTION!)
   docker-compose -f docker-compose.beta.yml exec postgres psql -U ventanas_user -d ventanas_beta_db -c "TRUNCATE TABLE app_materials, app_products CASCADE;"
   
   # Re-initialize data
   docker-compose -f docker-compose.beta.yml exec app python -c "
   from database import get_db
   from services.product_bom_service_db import initialize_sample_data
   db = next(get_db())
   initialize_sample_data(db)
   db.close()
   "
   ```

---

## 🚨 **Emergency Procedures**

### **Rollback Process:**
```bash
# If deployment fails, quick rollback
git log --oneline -n 5  # Find previous working commit
git reset --hard [previous_commit_hash]
git push --force origin main

# On droplet
cd /home/ventanas/app
git pull origin main
docker-compose -f docker-compose.beta.yml restart app
```

### **Service Recovery:**
```bash
# If services are down
docker-compose -f docker-compose.beta.yml down
docker-compose -f docker-compose.beta.yml up -d

# Check what's wrong
docker-compose -f docker-compose.beta.yml logs app --tail=50
```

---

## 📁 **File Organization Standards**

### **Key Files to Always Check:**
- `main.py` - Main application file
- `database.py` - Database models and services
- `config.py` - Configuration settings
- `services/product_bom_service_db.py` - Sample data initialization
- `models/` - Pydantic models
- `docker-compose.beta.yml` - Production configuration
- `.env` - Environment variables (server only)

### **Documentation Updates:**
- Update `CLAUDE.md` for significant changes
- Update `PROJECT_STRUCTURE.md` if needed
- Document API changes in comments

---

## 📊 **Sprint Planning and Task Management**

### **Sprint Planning Overview**

The project uses `utilities/tasks.csv` as the central sprint planner with the following structure:

| Column | Purpose | Values |
|--------|---------|---------|
| `sprint` | Sprint identifier | Sprint-2024-Q4, Sprint-2025-Q1, Sprint-Completed |
| `epic` | Feature grouping | Workflow-Management, Quote-Management, UX-Enhancement |
| `task_id` | Unique identifier | WF-001, QM-002, UXE-001 |
| `story_points` | Effort estimation | 1-13 (Fibonacci scale) |
| `priority` | Business priority | high, medium, low |
| `category` | Work type | feature, enhancement, bugfix, research |
| `status` | Current state | pending, in-progress, completed, blocked |
| `user_feedback_source` | Origin | Fernando-Beta-Testing, Original-Requirements |

### **Current Sprint Priorities (2025-Q1)**

**High Priority (Fernando Beta Feedback):**
- **UXE-001**: Formula system with buttons (8 points)
- **CUX-001**: Color assignment dropdowns (3 points) 
- **ST-001**: Quote status tracking (8 points)

**Medium Priority:**
- **WV-001**: Waste calculation visibility (5 points)
- **WR-001**: Waste association research (8 points)
- **DM-001**: Simplified Excel template (5 points)

### **Task Management Workflow**

#### **Starting a Task:**
1. Update CSV: Change status from `pending` to `in-progress`
2. Reference task ID in branch name: `feature/UXE-001-formula-buttons`
3. Include task ID in commit messages: `feat(UXE-001): add button-based formula builder`

#### **Completing a Task:**
1. Verify all acceptance criteria are met
2. Update CSV: Change status to `completed`
3. Include completion notes in technical_notes column
4. Reference in final commit message

#### **Sprint Velocity Tracking:**
- **Sprint-2024-Q4**: Focus on core quote management features
- **Sprint-2025-Q1**: UX improvements based on Fernando's feedback
- **Sprint-2025-Q2**: Advanced workflow and monitoring features
- **Sprint-2025-Q3**: Optimization and scaling features

### **Fernando Beta Testing Integration**

Tasks marked with `Fernando-Beta-Testing` source represent real user feedback and should be prioritized for immediate user experience improvements:

1. **Formula System UX** - Most critical feedback about difficulty understanding current system
2. **Color Assignment** - Prevents user errors in material selection
3. **Excel Template** - Reduces complexity for bulk data entry
4. **Waste Calculation Visibility** - Improves transparency in pricing
5. **Quote Status Tracking** - Essential for business workflow

---

## 🔧 **Common Tasks Quick Reference**

### **Add New Model:**
1. Update `database.py` SQLAlchemy model
2. Update corresponding Pydantic model in `models/`
3. Update database services if needed
4. Update sample data initialization
5. Test, commit, deploy

### **Add New Endpoint:**
1. Add route to `main.py`
2. Add corresponding template if needed
3. Update frontend JavaScript if needed
4. Test functionality locally
5. Commit and deploy

### **Fix Startup Issues:**
1. Check logs: `docker-compose -f docker-compose.beta.yml logs app --tail=30`
2. Common issues:
   - Missing environment variables
   - Database connection problems
   - Import errors
   - Permission issues with logs/static directories

### **Update Sample Data:**
1. Modify `initialize_sample_data()` function
2. Consider data dependencies and relationships
3. Test initialization logic
4. Deploy and re-initialize if needed

---

## 🎯 **Best Practices**

### **Git & Version Control:**
- **Always use feature branches** - Never commit directly to main
- **Write descriptive commit messages** - Follow conventional commit format with task IDs
- **Keep commits atomic** - One logical change per commit  
- **Review code thoroughly** - All changes should go through PR process
- **Maintain clean history** - Use squash merges for features
- **Use pre-commit hooks** - Ensure code quality before commits
- **Reference task IDs** - Include task_id from utilities/tasks.csv in commits and branches

### **Sprint Planning & Task Management:**
- **Check sprint priorities** - Review utilities/tasks.csv before starting work
- **Update task status** - Keep CSV updated with current progress
- **Follow story points** - Use Fibonacci scale (1,2,3,5,8,13) for effort estimation
- **Prioritize beta feedback** - Tasks from Fernando-Beta-Testing get highest priority
- **Reference acceptance criteria** - Ensure all criteria are met before completing tasks
- **Track velocity** - Monitor completed story points per sprint for planning

### **Code Quality:**
- Always use type hints
- Add docstrings for complex functions
- Handle errors gracefully
- Follow existing code patterns
- Use descriptive variable names
- **Run linting and formatting tools** before committing
- **Maintain test coverage** where applicable

### **Database:**
- Use transactions for related operations
- Always validate data before insertion
- Consider foreign key relationships
- Index important query fields
- **Test schema changes locally first**
- **Never modify production database directly**

### **Security:**
- Validate all user inputs
- Use parameterized queries
- Check permissions on file operations
- Never log sensitive information
- **Review security implications** in code reviews
- **Run security scans** via automated tools

### **Performance:**
- Optimize database queries
- Use appropriate indexes
- Monitor memory usage on 2GB droplet
- Consider caching for frequently accessed data
- **Profile performance-critical code paths**

### **Collaboration:**
- **Use descriptive PR titles and descriptions**
- **Request reviews from appropriate team members**
- **Address review feedback promptly**
- **Keep PRs focused and reasonably sized**
- **Document breaking changes clearly**
- **Communicate deployment requirements early**

---

## 📝 **Change Log Template**

When making significant changes, document them:

```markdown
## Change: [Brief Description]
**Date:** [YYYY-MM-DD]
**Files Modified:** [list of files]

### What Changed:
- [ ] Change 1
- [ ] Change 2

### Testing Performed:
- [ ] Test 1
- [ ] Test 2

### Deployment Notes:
- Any special deployment steps
- Environment variables added/changed
- Database migrations needed

### Rollback Plan:
- How to undo changes if needed
```

---

## 🚀 **Current System Status**

**Environment:** Production Beta on DigitalOcean  
**URL:** http://159.65.174.94:8000  
**Database:** PostgreSQL with initialized sample data  
**Status:** ✅ Operational (PDF generation temporarily disabled)  

**Last Major Update:** Fixed PDF imports and permissions issues  
**Next Planned:** Enhanced sample data with categories and colors  

---

*This protocol ensures consistent, safe, and trackable development practices for the Window Quotation System.*