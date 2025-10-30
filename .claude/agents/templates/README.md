# Agent Templates

This directory contains template files used by the `task-package-generator` agent to create workflow scaffolding and documentation.

## Purpose

Templates are extracted from the agent definition to:
- **Reduce agent complexity** (827 → 251 lines, 69% reduction)
- **Improve maintainability** (edit templates without modifying agent code)
- **Enable customization** (teams can customize templates per project)
- **Facilitate testing** (templates can be validated independently)

## Template Files

### 1. `branch-script.sh` (651 bytes)
**Purpose**: Git branch creation script template for refactoring phases

**Placeholders**:
- `{N}` - Phase number (1, 2, 3)
- `{Phase Title}` - Descriptive phase title
- `{TIMESTAMP}` - ISO timestamp
- `{BRANCH_COMMANDS}` - Generated git checkout -b commands
- `{COUNT}` - Number of branches created
- `{PHASE_PREFIX}` - Prefix for filtering branches

**Output**: `scripts/branches/create-phase-{N}-branches.sh`

### 2. `pr-template-security.md` (2.0 KB)
**Purpose**: Pull request template for security vulnerability fixes

**Key Sections**:
- Vulnerability description and severity
- Root cause analysis
- Solution implementation checklist
- Testing evidence (before/after)
- OWASP Top 10 security checklist
- Deployment plan and rollback procedure

**Output**: `.github/pull_request_template/security-fix.md`

### 3. `pr-template-performance.md` (2.6 KB)
**Purpose**: Pull request template for performance optimizations

**Key Sections**:
- Performance issue description
- Bottleneck identification
- Optimization implementation
- Benchmarking results (before/after metrics)
- Performance impact analysis
- Load testing verification

**Output**: `.github/pull_request_template/performance-optimization.md`

### 4. `pr-template-architecture.md` (3.1 KB)
**Purpose**: Pull request template for architecture refactoring

**Key Sections**:
- Architecture issue description
- Current vs. target state (patterns, coupling, SOLID compliance)
- Design pattern implementation
- Code complexity metrics (before/after)
- Breaking changes and migration plan
- Knowledge transfer documentation

**Output**: `.github/pull_request_template/architecture-refactor.md`

### 5. `test-scaffold.py` (3.7 KB)
**Purpose**: Python test file scaffold with pytest structure

**Included Test Classes**:
- `Test{FeatureName}` - Unit tests with fixtures
- `Test{FeatureName}Integration` - End-to-end tests
- `Test{FeatureName}Performance` - Benchmark tests
- `Test{FeatureName}Security` - Security validation tests
- `Test{FeatureName}Rollback` - Backward compatibility tests

**Output**: `tests/test_{feature}_scaffold.py`

### 6. `dashboard.html` (14 KB)
**Purpose**: Interactive HTML progress dashboard with metrics and filtering

**Features**:
- Real-time progress metrics (completion %, velocity, ETA)
- Phase progress bars (Phase 1/2/3)
- Task table with filtering (priority, status, phase)
- Dependency visualization
- Auto-refresh every 5 minutes
- Responsive design (mobile-friendly)

**Output**: `docs/task-dashboards/refactoring-progress-{timestamp}.html`

## Usage by Agent

The `task-package-generator` agent follows this workflow:

1. **Read template** using Read tool: `Read agents/templates/{template-name}`
2. **Replace placeholders** with task-specific values
3. **Write output** to appropriate location
4. **Make executable** (for shell scripts): `chmod +x`

Example from agent:
```
# Read dashboard template
template = Read("agents/templates/dashboard.html")

# Replace placeholders
output = template.replace("{PROJECT_NAME}", project_name)
              .replace("{COMPLETION_PCT}", completion_pct)
              .replace("{TASK_ROWS}", task_rows_html)

# Write to output location
Write("docs/task-dashboards/refactoring-progress-20251008.html", output)
```

## Customization

Teams can customize templates for their specific needs:

1. **Copy template** to project root (preserves original)
2. **Modify content** (add/remove sections, change styling)
3. **Update agent invocation** to use custom path

Example:
```bash
# Create project-specific template
cp agents/templates/pr-template-security.md .claude/custom-pr-security.md

# Edit custom template
vim .claude/custom-pr-security.md

# Agent will prefer custom templates over defaults
```

## Validation

Templates can be validated independently:

```bash
# Check for required placeholders
grep -o '{[A-Z_]*}' agents/templates/dashboard.html | sort -u

# Verify template syntax (HTML)
tidy -q -e agents/templates/dashboard.html

# Test placeholder replacement
cat agents/templates/branch-script.sh | sed 's/{N}/1/g' | bash -n
```

## Maintenance

When updating templates:

1. ✅ Test placeholder replacement with sample data
2. ✅ Verify output format matches expected structure
3. ✅ Update placeholder documentation in agent definition
4. ✅ Test generated output in actual workflow
5. ✅ Update this README with any changes

## File Statistics

- **Total template lines**: 918 lines
- **Total template size**: ~26 KB
- **Agent size reduction**: 576 lines (69% reduction from 827 → 251 lines)
- **Maintainability improvement**: Templates now independently editable

## Related Files

- **Agent Definition**: `/agents/task-package-generator.md`
- **Command**: `/commands/generate_tasks.md`
- **Workflow**: See CLAUDE.md for complete workflow chain
