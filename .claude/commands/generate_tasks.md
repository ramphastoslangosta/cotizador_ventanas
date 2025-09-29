---
description: Generate actionable development tasks from code review findings using the task-package-generator agent
allowed-tools: Read, Bash, Glob, task-package-generator
argument-hint: [code-review-report-path] - Path to the code review report (optional, defaults to latest)
---

# Generate Tasks

Transform code review analysis into structured development tasks with complete workflow scaffolding including git branches, PR templates, test scaffolds, and progress tracking.

## Pre-Generation Discovery

### Locate Code Review Report
```bash
# Find the most recent code review report
LATEST_REVIEW=$(ls -t docs/code-review-reports/code-review-agent_*.md 2>/dev/null | head -1)

if [ -z "$LATEST_REVIEW" ]; then
    echo "❌ No code review report found. Please run 'code-review' first."
    exit 1
fi

echo "📋 Found code review report: $LATEST_REVIEW"
echo "📊 Report summary:"
head -30 "$LATEST_REVIEW"
```

### Read Existing Task Tracker
```bash
# Check current task state
if [ -f "tasks.csv" ]; then
    echo "📝 Current task tracker status:"
    echo "Total tasks: $(tail -n +2 tasks.csv | wc -l)"
    echo "Completed: $(grep -c ",completed," tasks.csv 2>/dev/null || echo 0)"
    echo "In progress: $(grep -c ",in-progress," tasks.csv 2>/dev/null || echo 0)"
    echo "Pending: $(grep -c ",pending," tasks.csv 2>/dev/null || echo 0)"
else
    echo "📝 No existing task tracker found. Will create new tasks.csv"
fi
```

### Analyze Project Structure
```bash
# Detect project type and structure
echo "🔍 Analyzing project structure..."

# Find main source directories
find . -maxdepth 2 -type d \( -name "src" -o -name "app" -o -name "lib" -o -name "pkg" \) 2>/dev/null

# Detect test framework
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    echo "🧪 Test Framework: pytest"
elif [ -f "jest.config.js" ] || [ -f "jest.config.ts" ]; then
    echo "🧪 Test Framework: jest"
elif [ -f "go.mod" ]; then
    echo "🧪 Test Framework: go test"
fi

# Check git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📦 Git repository detected"
    echo "Current branch: $(git branch --show-current)"
    echo "Latest commit: $(git log -1 --oneline)"
else
    echo "⚠️  No git repository found. Git workflow scaffolding will be limited."
fi
```

## Task Generation Execution

### Invoke Task Package Generator Agent
```
@task-package-generator

Please generate a comprehensive task package from the code review findings with the following parameters:

**Input Source**: ${LATEST_REVIEW:-docs/code-review-reports/code-review-agent_*.md}
**Analysis Date**: $(date +%Y-%m-%d)
**Project Context**:
- Repository: $(git remote get-url origin 2>/dev/null || echo "Local project")
- Current Branch: $(git branch --show-current 2>/dev/null || echo "N/A")
- Technology Stack: [Auto-detected from project files]
- Test Framework: [Auto-detected from config files]

**Generation Scope**: Complete task package including:
1. **tasks.csv Updates**: Structured task entries with dependencies
2. **Git Branch Scaffolds**: Pre-configured branches for each refactoring phase
3. **PR Templates**: Customized pull request templates per task category
4. **Test Scaffolds**: Empty test files with proper structure
5. **Progress Dashboard**: HTML dashboard for team visibility

**Task Categorization Requirements**:
- **Critical Tasks**: Security vulnerabilities, system-breaking bugs
- **High Priority**: Performance bottlenecks, maintainability issues
- **Medium Priority**: Architecture improvements, code quality enhancements
- **Low Priority**: Documentation updates, minor refactors

**Output Specifications**:
1. **tasks.csv Format**:
   - Columns: task_id, title, description, priority, status, phase, estimated_effort, dependencies, branch_name, pr_template, test_file
   - Compatible with existing task tracker structure
   - Include atomic task breakdown from code review phases

2. **Git Workflow Scaffolding**:
   - Create branch naming convention: `{type}/{scope}-{date}`
   - Generate branch creation scripts
   - Setup branch protection rules (if applicable)

3. **PR Template Generation**:
   - Security fixes template
   - Performance optimization template
   - Refactoring template
   - Include checklist from code review findings

4. **Test Scaffold Creation**:
   - Create empty test files matching new code structure
   - Include test case templates
   - Setup test runner configurations

5. **Progress Dashboard**:
   - HTML dashboard at: `docs/task-dashboards/refactoring-progress-{timestamp}.html`
   - Real-time task status visualization
   - Dependency graph display
   - Burndown chart preparation

**Execution Instructions**:
- Preserve existing completed tasks in tasks.csv
- Generate unique task IDs following pattern: TASK-{YYYYMMDD}-{NNN}
- Create all necessary directories automatically
- Include rollback procedures for each task
- Add estimated completion dates based on effort estimates

**Expected Artifacts**:
1. ✅ Updated tasks.csv with new actionable tasks
2. ✅ Git branch scaffold scripts in scripts/branches/
3. ✅ PR templates in .github/pull_request_template/
4. ✅ Test scaffolds in appropriate test directories
5. ✅ Progress dashboard at docs/task-dashboards/
6. ✅ Task execution guide at docs/task-guides/refactoring-guide-{timestamp}.md
```

## Post-Generation Actions

### Verify Generated Artifacts
```bash
echo "🔍 Verifying generated artifacts..."

# Check tasks.csv update
if [ -f "tasks.csv" ]; then
    NEW_TASKS=$(tail -n +2 tasks.csv | wc -l)
    echo "✅ tasks.csv updated: $NEW_TASKS total tasks"
    echo "📋 New tasks preview:"
    tail -5 tasks.csv
else
    echo "❌ tasks.csv not found"
fi

# Check branch scaffolds
if [ -d "scripts/branches" ]; then
    BRANCH_SCRIPTS=$(find scripts/branches -name "*.sh" | wc -l)
    echo "✅ Branch scaffolds created: $BRANCH_SCRIPTS scripts"
    ls -lh scripts/branches/
else
    echo "⚠️  No branch scaffolds directory found"
fi

# Check PR templates
if [ -d ".github/pull_request_template" ]; then
    PR_TEMPLATES=$(find .github/pull_request_template -name "*.md" | wc -l)
    echo "✅ PR templates created: $PR_TEMPLATES templates"
    ls -lh .github/pull_request_template/
else
    echo "⚠️  No PR templates directory found"
fi

# Check test scaffolds
if [ -d "tests" ]; then
    NEW_TESTS=$(find tests -name "*_test_scaffold.py" -o -name "*_test_scaffold.js" 2>/dev/null | wc -l)
    echo "✅ Test scaffolds created: $NEW_TESTS files"
else
    echo "⚠️  Tests directory not found"
fi

# Check progress dashboard
DASHBOARD=$(ls -t docs/task-dashboards/refactoring-progress-*.html 2>/dev/null | head -1)
if [ -n "$DASHBOARD" ]; then
    echo "✅ Progress dashboard created: $DASHBOARD"
    echo "🌐 Open dashboard: file://$(pwd)/$DASHBOARD"
else
    echo "⚠️  Progress dashboard not found"
fi
```

### Initialize Git Workflow
```bash
# Make branch scripts executable
if [ -d "scripts/branches" ]; then
    chmod +x scripts/branches/*.sh
    echo "✅ Branch scripts are executable"
fi

# Create initial branches (optional, requires confirmation)
echo ""
read -p "🚀 Initialize git branches now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌿 Creating branches..."
    for script in scripts/branches/*.sh; do
        echo "Executing: $script"
        bash "$script"
    done
    echo "✅ Branches initialized"
    git branch -a
fi
```

### Generate Quick Start Guide
```bash
# Create developer quick start
cat > TASK_QUICKSTART.md << 'EOF'
# Refactoring Tasks Quick Start

## 📋 Task Overview
- **Total Tasks**: $(tail -n +2 tasks.csv | wc -l)
- **Critical Priority**: $(grep -c ",critical," tasks.csv)
- **High Priority**: $(grep -c ",high," tasks.csv)
- **Progress Dashboard**: [View Dashboard](docs/task-dashboards/refactoring-progress-*.html)

## 🚀 Getting Started

### 1. Review Tasks
```bash
# View all pending tasks
grep ",pending," tasks.csv

# View critical tasks only
grep ",critical," tasks.csv | grep ",pending,"
```

### 2. Start a Task
```bash
# Example: Start task TASK-20250929-001
TASK_ID="TASK-20250929-001"

# Get task details
grep "$TASK_ID" tasks.csv

# Checkout corresponding branch
BRANCH=$(grep "$TASK_ID" tasks.csv | cut -d',' -f9)
git checkout "$BRANCH"

# View PR template
TEMPLATE=$(grep "$TASK_ID" tasks.csv | cut -d',' -f10)
cat ".github/pull_request_template/$TEMPLATE"
```

### 3. Update Task Status
```bash
# Mark task as in-progress
sed -i '' "s/$TASK_ID,\([^,]*\),[^,]*,/$TASK_ID,\1,in-progress,/" tasks.csv

# Mark task as completed
sed -i '' "s/$TASK_ID,\([^,]*\),[^,]*,/$TASK_ID,\1,completed,/" tasks.csv
```

### 4. View Progress
```bash
# Generate updated dashboard
python scripts/generate_dashboard.py  # If provided

# Or open existing dashboard
open docs/task-dashboards/refactoring-progress-*.html
```

## 📚 Documentation
- [Complete Task Guide](docs/task-guides/refactoring-guide-*.md)
- [Code Review Report](docs/code-review-reports/code-review-agent-*.md)
- [Git Workflow Guide](docs/git-workflow.md)

## 🆘 Need Help?
- Review task dependencies: `grep "TASK-ID" tasks.csv | cut -d',' -f8`
- Check task effort estimate: `grep "TASK-ID" tasks.csv | cut -d',' -f7`
- View all tasks for a phase: `grep ",phase-1," tasks.csv`
EOF

echo "✅ Quick start guide created: TASK_QUICKSTART.md"
```

## Expected Outcomes

After executing this command, you should have:

### **Immediate Outputs**
1. **Updated tasks.csv**: New task entries appended with proper structure
2. **Branch Scaffolds**: Shell scripts to create all necessary git branches
3. **PR Templates**: Ready-to-use templates for each task category
4. **Test Scaffolds**: Empty test files with proper naming and structure
5. **Progress Dashboard**: Interactive HTML dashboard for tracking

### **File Structure Created**
```
project/
├── tasks.csv (updated)
├── TASK_QUICKSTART.md (new)
├── scripts/
│   └── branches/
│       ├── create-phase-1-branches.sh
│       ├── create-phase-2-branches.sh
│       └── create-phase-3-branches.sh
├── .github/
│   └── pull_request_template/
│       ├── security-fix.md
│       ├── performance-optimization.md
│       └── architecture-refactor.md
├── tests/
│   ├── test_phase1_scaffold.py
│   ├── test_phase2_scaffold.py
│   └── test_phase3_scaffold.py
└── docs/
    ├── task-dashboards/
    │   └── refactoring-progress-YYYY-MM-DD.html
    └── task-guides/
        └── refactoring-guide-YYYY-MM-DD.md
```

### **Task Management Integration**
- **CSV Format**: Compatible with Excel, Google Sheets, Jira import
- **Git Integration**: Branches linked to task IDs for traceability
- **Progress Tracking**: Dashboard updates automatically from tasks.csv
- **Dependency Management**: Tasks organized with clear dependency chains

### **Team Workflow Enabled**
1. **Developers**: Pick tasks from tasks.csv, checkout branch, follow PR template
2. **Managers**: Monitor progress via dashboard, track dependencies
3. **Reviewers**: Use PR templates to ensure complete implementation
4. **QA**: Reference test scaffolds for test case creation

## Troubleshooting

### No Code Review Report Found
```bash
# Solution: Run code review first
/code-review full
```

### Git Not Initialized
```bash
# Solution: Initialize git repository
git init
git add .
git commit -m "Initial commit before refactoring"
```

### Permission Issues on Scripts
```bash
# Solution: Make scripts executable
find scripts/branches -name "*.sh" -exec chmod +x {} \;
```

### Dashboard Not Displaying
```bash
# Solution: Check browser console, regenerate if needed
python scripts/generate_dashboard.py --force-regenerate
```