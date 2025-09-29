---
description: Perform comprehensive code analysis and generate structured refactoring recommendations using the code-reviewer-architect agent
allowed-tools: Read, Bash, Glob, Grep, code-reviewer-architect
argument-hint: [optional: scope] - Specify analysis scope (security, performance, architecture, full)
---

# Code Review

Invoke the code-reviewer-architect agent to perform comprehensive codebase analysis, identify technical debt, security vulnerabilities, and generate structured refactoring recommendations with atomic commit strategies.

## Pre-Analysis Discovery

### Read Core Files
- README.md (project overview and setup)
- package.json / requirements.txt / Cargo.toml (dependencies and scripts)
- .env.example (configuration structure)
- docker-compose.yml / Dockerfile (deployment configuration)
- src/ or app/ (main application code)
- tests/ (test coverage assessment)
- docs/ (existing documentation)

### Execute Analysis Commands
```bash
# Project structure analysis
find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.go" | head -30

# Code statistics
find . -name "*.py" -type f -exec wc -l {} + | sort -nr | head -10
find . -name "*.js" -o -name "*.ts" | xargs wc -l | sort -nr | head -10

# Dependency analysis
ls -la package*.json requirements*.txt Pipfile* go.mod pom.xml 2>/dev/null

# Git analysis (if available)
git log --oneline -10 2>/dev/null || echo "Git history not available"
git branch -a 2>/dev/null || echo "Git branches not available"

# Test coverage check
find . -name "*test*" -o -name "*spec*" | wc -l

# Security scan preparation
find . -name "*.env*" -o -name "*secret*" -o -name "*key*" | head -10
```

## Code Analysis Execution

### Invoke Code Reviewer Agent
```
@code-reviewer-architect

Please perform a comprehensive code analysis of this codebase with the following parameters:

**Analysis Scope**: [full/security/performance/architecture - based on argument]
**Priority Focus**: 
- Security vulnerabilities (OWASP Top 10)
- Performance bottlenecks
- Code quality and maintainability  
- Architecture improvements

**Context Information**:
- Project Type: [Detected from file structure]
- Technology Stack: [Languages/frameworks found]
- Deployment Method: [Docker/traditional/cloud-native]
- Test Coverage: [Estimated from file analysis]

**Specific Analysis Requests**:
1. Identify critical security vulnerabilities requiring immediate attention
2. Detect performance bottlenecks in core business logic
3. Assess code quality metrics (complexity, duplication, maintainability)
4. Evaluate architecture adherence to SOLID principles
5. Generate atomic refactoring strategy with git workflow

**Expected Deliverables**:
1. Executive summary with health score and critical issues
2. Detailed technical debt assessment
3. Prioritized refactoring roadmap (3 phases max)
4. Atomic commit strategy for each improvement
5. Risk assessment with rollback procedures
6. Automated report generation to: docs/code-review-reports/code-review-agent_{timestamp}.md

Please ensure all recommendations include:
- Specific file paths and line numbers
- Before/after code examples where beneficial
- Estimated effort and business impact
- Testing strategy for each change
- Complete git branching and merge strategy
```

## Post-Analysis Actions

### Verify Report Generation
```bash
# Check if report was created
ls -la docs/code-review-reports/code-review-agent_*.md | tail -5

# Display report summary
if [ -f docs/code-review-reports/code-review-agent_*.md ]; then
    echo "=== LATEST CODE REVIEW REPORT ==="
    head -50 $(ls -t docs/code-review-reports/code-review-agent_*.md | head -1)
else
    echo "Report generation verification needed"
fi
```

### Create Action Items
```bash
# Create GitHub issues from critical findings (if GitHub CLI available)
gh issue list --label "code-review" 2>/dev/null || echo "GitHub CLI not configured"

# Create task tracking file
echo "# Code Review Action Items - $(date)" > code-review-actions.md
echo "Generated from: $(ls -t docs/code-review-reports/code-review-agent_*.md | head -1)" >> code-review-actions.md
```

## Expected Outcomes

After executing this command, you should receive:

### **Immediate Response**
1. **Health Score**: Overall codebase quality rating (0-100)
2. **Critical Issues**: Number of issues requiring immediate attention
3. **Top 3 Priorities**: Most important actions with business impact
4. **Report Location**: Exact path to generated detailed report

### **Generated Report File**
- **Location**: `docs/code-review-reports/code-review-agent_YYYY-MM-DD-HH.md`
- **Content**: Comprehensive analysis with executable refactoring plan
- **Format**: Structured markdown with tables, code examples, and workflows

### **Actionable Outputs**
1. **Security Fixes**: Immediate security vulnerabilities to address
2. **Performance Improvements**: Bottlenecks with quantified impact
3. **Refactoring Roadmap**: Phased approach with atomic commits
4. **Git Strategy**: Complete branching and merge workflow
5. **Success Metrics**: Measurable improvement targets
