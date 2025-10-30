---
description: Analyze the AI documentation system itself - meta-review of commands, agents, and workflows
allowed-tools: Read, Bash, Glob, Grep
argument-hint: none
---

# AI Prime

Understand the AI documentation system by analyzing its own structure: agents, commands, workflows, and design patterns.

## Read Core System Files

- code-reviewer-architect (agent definition)
- task-package-generator (agent definition)
- code-review (command)
- generate_tasks (command)
- prime (command - for comparison)
- atomic-plan (command)
- execute-task (command)

## Execute Analysis

```bash
# Count system components
echo "=== AI Documentation System Inventory ==="
echo "Agents: $(ls -1 agents/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Commands: $(ls -1 commands/*.md 2>/dev/null | wc -l | tr -d ' ')"

# Analyze agent complexity
echo ""
echo "=== Agent Instruction Sizes ==="
for agent in agents/*.md 2>/dev/null; do
    lines=$(wc -l < "$agent" 2>/dev/null | tr -d ' ')
    name=$(basename "$agent" .md)
    echo "  $name: $lines lines"
done

# Analyze command complexity
echo ""
echo "=== Command Complexity ==="
for cmd in commands/*.md 2>/dev/null; do
    lines=$(wc -l < "$cmd" 2>/dev/null | tr -d ' ')
    bash_blocks=$(grep -c '```bash' "$cmd" 2>/dev/null || echo 0)
    name=$(basename "$cmd" .md)
    echo "  $name: $lines lines, $bash_blocks bash blocks"
done

# Identify agent invocations
echo ""
echo "=== Command → Agent Relationships ==="
grep -h "allowed-tools:.*-architect\|allowed-tools:.*-generator\|allowed-tools:.*-purpose" commands/*.md 2>/dev/null | \
    sed 's/allowed-tools://g' | sort -u

# Check for shared patterns
echo ""
echo "=== Common Patterns ==="
echo "Commands using Bash: $(grep -l 'allowed-tools:.*Bash' commands/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Commands using Read: $(grep -l 'allowed-tools:.*Read' commands/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Commands using Glob: $(grep -l 'allowed-tools:.*Glob' commands/*.md 2>/dev/null | wc -l | tr -d ' ')"

# Identify potential issues
echo ""
echo "=== Quality Checks ==="
echo "Commands >300 lines: $(for f in commands/*.md; do wc -l < "$f"; done | awk '$1 > 300' | wc -l | tr -d ' ')"
echo "Agents >400 lines: $(for f in agents/*.md; do wc -l < "$f"; done | awk '$1 > 400' | wc -l | tr -d ' ')"

# Find documentation gaps
echo ""
echo "=== Documentation Coverage ==="
for cmd in commands/*.md; do
    name=$(basename "$cmd" .md)
    if ! grep -q "## Expected Outcomes" "$cmd" 2>/dev/null; then
        echo "  ⚠️  $name: Missing 'Expected Outcomes' section"
    fi
    if ! grep -q "argument-hint:" "$cmd" 2>/dev/null; then
        echo "  ⚠️  $name: Missing 'argument-hint' in frontmatter"
    fi
done

# Workflow dependencies
echo ""
echo "=== Workflow Chain ==="
echo "1. prime → 2. code-review → 3. generate_tasks → 4. atomic-plan → 5. execute-task"
echo ""
echo "Verification:"
grep -l "code-review" commands/*.md 2>/dev/null | sed 's|commands/||g;s|.md||g' | head -3
grep -l "generate_tasks\|generate-tasks" commands/*.md 2>/dev/null | sed 's|commands/||g;s|.md||g' | head -3
grep -l "atomic-plan" commands/*.md 2>/dev/null | sed 's|commands/||g;s|.md||g' | head -3
```

## Report Format

**System Architecture:**
- Total agents: {count}
- Total commands: {count}
- Primary workflow: {describe end-to-end flow}
- Agent models used: {sonnet, etc}

**Core Components:**
For each agent/command:
`{Name} ({Type}) - {Lines} lines - {Primary Purpose}`

**Design Patterns Observed:**
- Agent invocation pattern: {how commands call agents}
- Bash script structure: {common patterns}
- File organization: {docs/, scripts/, .claude/}
- Error handling: {assessment}

**System Health Assessment:**
- Complexity metrics: {avg lines, max lines, distribution}
- Documentation quality: {completeness, consistency}
- Maintainability concerns: {identified issues}
- Workflow completeness: {gaps or missing links}

**Immediate Observations:**
- Strengths: {top 3}
- Weaknesses: {top 3}
- Missing capabilities: {what's not covered}

**Recommended Improvements:**
1. {Highest priority improvement}
2. {Second priority}
3. {Third priority}

---

**Purpose**: This meta-command enables the AI system to understand its own structure, making it self-aware for improvements and troubleshooting.