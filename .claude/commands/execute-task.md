---
description: Execute an atomic task plan step-by-step using an existing workspace
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
argument-hint: TASK-ID (e.g., HOTFIX-20251001-002)
---

# Execute Task

Execute the next step in an atomic task plan. This command implements the plan defined in `atomic-plan-{TASK_ID}.md` by executing one step at a time.

## Workflow

1. **Read workspace files** to understand current state
2. **Identify next pending step** from checklist
3. **Execute the step** following atomic plan instructions exactly
4. **Run test checkpoint** (MANDATORY - execution stops if tests fail)
5. **Verify success** against expected output from plan
6. **Commit implementation changes** with message from plan
7. **Update all workspace documentation** (checklist, notes, README)
8. **Commit documentation updates** separately
9. **Report completion** and wait for next instruction

**Critical Rule:** Steps 4-5 are gates. If tests fail, stop completely. No commits, no documentation updates, no progression.

## Read Required Files

```bash
TASK_ID="${1}"

# Validation
if [ -z "$TASK_ID" ]; then
    echo "❌ Usage: /execute-task TASK-ID"
    exit 1
fi

WORKSPACE_DIR=".claude/workspace/$TASK_ID"
if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "❌ Workspace not found: $WORKSPACE_DIR"
    exit 1
fi

# Read all required files
cat "$WORKSPACE_DIR/atomic-plan-$TASK_ID.md"
cat "$WORKSPACE_DIR/checklist-$TASK_ID.md"
cat "$WORKSPACE_DIR/README.md"
cat "$WORKSPACE_DIR/notes.md"
```

**Files to analyze:**
- `atomic-plan-{TASK_ID}.md` - Detailed implementation steps with code, commands, and test checkpoints
- `checklist-{TASK_ID}.md` - Progress tracker with [ ] and [x] items
- `README.md` - Quick reference and success criteria
- `notes.md` - Session log

## Instructions for Execution

After reading the workspace files, follow this execution protocol:

### Step 1: Analyze Current State

Determine:
- How many checklist items are complete (count `[x]`)
- Which step is next (first `[ ]` item)
- Current git branch and uncommitted changes
- Last session notes entry

**Report current state:**
```
📊 Current State:
- Progress: {completed}/{total} items ({percent}%)
- Branch: {current_branch}
- Uncommitted: {file_count} files
- Next Step: {next_checklist_item}
```

### Step 2: Extract Next Step Details

From `atomic-plan-{TASK_ID}.md`, find the section corresponding to the next checklist item.

Extract:
- Step number and title
- Estimated time
- Files to create/modify
- Exact code to write
- Test checkpoint command
- Expected test output
- Commit message
- Success criteria

**Display extracted step:**
```
🎯 Executing Step {N}: {title}

Files to modify:
- {file_1}
- {file_2}

Test checkpoint:
{test_command}

Expected result:
{expected_output}
```

### Step 3: Execute the Step

**For code changes:**
- Use `Write` or `Edit` tools to create/modify files exactly as specified in atomic plan
- Copy code blocks from plan verbatim (do not improvise)
- Follow formatting and structure from plan

**For bash commands:**
- Use `Bash` tool to run commands from plan
- Capture output and verify success

**Ask before proceeding only if:**
- The atomic plan instructions are ambiguous or incomplete
- Test checkpoint fails and root cause is unclear
- You need to deviate from the plan for a valid reason

Otherwise, execute autonomously following the plan.

### Step 4: Run Test Checkpoint (CRITICAL)

**This step is MANDATORY - Never skip test checkpoints.**

Execute the test command specified in the atomic plan:

```bash
# Run the test checkpoint from plan
{test_command_from_plan}
```

**Verify before proceeding:**
- ✅ Output matches expected result from plan
- ✅ All tests pass (green)
- ✅ No errors or warnings
- ✅ Exit code is 0

**If test checkpoint fails:**
1. ❌ **STOP IMMEDIATELY** - Do not proceed to commit
2. Display full error output
3. Analyze root cause
4. Show relevant code snippet causing failure
5. Propose specific fix
6. Ask user: "Test failed. Should I: (a) fix and retry, (b) rollback, or (c) wait for guidance?"
7. **Do NOT mark step complete**
8. **Do NOT move to next step**
9. **Do NOT commit changes**

**Document test result:**
```bash
# Add to notes immediately
echo "- Test checkpoint: {PASSED/FAILED}" >> .claude/workspace/$TASK_ID/notes.md
if [ $? -eq 0 ]; then
    echo "  ✅ All tests passed" >> .claude/workspace/$TASK_ID/notes.md
else
    echo "  ❌ Test failed - stopping execution" >> .claude/workspace/$TASK_ID/notes.md
fi
```

### Step 5: Commit Changes

Use the exact commit message from atomic plan:

```bash
git add {files_from_plan}
git commit -m "{exact_message_from_plan}"
```

### Step 6: Update Progress & Documentation

**Update all workspace documentation immediately after successful commit:**

#### 6.1 Update Checklist
```bash
# Mark current item complete
sed -i '' 's/- \[ \] {exact_item_text}/- [x] {exact_item_text}/' \
  .claude/workspace/$TASK_ID/checklist-$TASK_ID.md

# Verify update
grep "{exact_item_text}" .claude/workspace/$TASK_ID/checklist-$TASK_ID.md
```

#### 6.2 Update Session Notes
```bash
# Append to notes.md with structured format
cat >> .claude/workspace/$TASK_ID/notes.md << EOF

### Step {N}: {title}
- Started: {HH:MM when step began}
- Completed: $(date +%H:%M)
- Duration: {calculate duration}
- Files Modified:
  * {file_1}
  * {file_2}
- Test Result: ✅ Passed
- Commit: {commit_sha}
- Issues: {none or describe any challenges}
EOF
```

#### 6.3 Update README.md Progress Section (if exists)
If README.md has a progress section, update it:
```bash
# Calculate current progress
COMPLETED=$(grep "\[x\]" .claude/workspace/$TASK_ID/checklist-$TASK_ID.md | wc -l | tr -d ' ')
TOTAL=$(grep -E "\[ \]|\[x\]" .claude/workspace/$TASK_ID/checklist-$TASK_ID.md | wc -l | tr -d ' ')
PERCENT=$(( COMPLETED * 100 / TOTAL ))

# Update progress in README if it has a progress section
if grep -q "Progress:" .claude/workspace/$TASK_ID/README.md; then
    sed -i '' "s/Progress: [0-9]*\/[0-9]* ([0-9]*%)/Progress: $COMPLETED\/$TOTAL ($PERCENT%)/" \
      .claude/workspace/$TASK_ID/README.md
fi
```

#### 6.4 Update TASK_STATUS.md (Optional)
If this step represents a major milestone, update the main task status:
```bash
# Only update for significant milestones (e.g., phase completion)
# Example: After completing all preparation phase items
if [ "$COMPLETED" -eq "{preparation_phase_end_count}" ]; then
    echo "Updating TASK_STATUS.md - Preparation phase complete"
    # Update relevant section in TASK_STATUS.md
fi
```

#### 6.5 Commit Documentation Updates
```bash
# Commit the documentation updates separately for clean history
git add .claude/workspace/$TASK_ID/checklist-$TASK_ID.md
git add .claude/workspace/$TASK_ID/notes.md
git add .claude/workspace/$TASK_ID/README.md
git commit -m "docs: update workspace progress for step {N} ($TASK_ID)"
```

**Verification checklist for this step:**
- ✅ Checklist item marked [x]
- ✅ Notes.md updated with step details
- ✅ Commit SHA recorded
- ✅ Progress percentage updated (if applicable)
- ✅ Documentation changes committed

### Step 7: Report Completion

**Summary format:**
```
✅ Step {N} Complete: {title}

What was done:
- {action_1}
- {action_2}

Test result: ✅ Passed
Commit: {commit_sha}

Progress: {completed}/{total} ({percent}%)
Next: {next_step_title}

Ready to continue? Reply "yes" or "next" to execute next step.
```

## Example Execution Flow

**User:** `/execute-task HOTFIX-20251001-002`

**Assistant:**
1. Reads workspace files
2. Reports: "Progress: 3/64 (5%), Next: Write test_quote_routes_basic.py"
3. Extracts Step 1 details from atomic plan
4. Creates `tests/test_quote_routes_basic.py` with exact code from plan
5. Runs `pytest tests/test_quote_routes_basic.py -v`
6. Verifies tests pass
7. Commits with message: "test: add basic quote routes integration tests"
8. Updates checklist and notes
9. Reports completion and next step
10. Waits for user to say "next" before continuing

## Special Cases

### If Progress = 0% (First Execution)
- Check if feature branch exists (from README)
- Prompt to create branch if not exists
- Remind about session log setup
- Execute first preparation step

### If Test Checkpoint Fails
- **Stop execution immediately**
- Display error output
- Suggest potential fixes based on error
- Wait for user confirmation before proceeding
- Do NOT mark step complete
- Do NOT move to next step

### If Atomic Plan is Incomplete
- Report missing information
- Ask user to clarify or update plan
- Do NOT improvise or assume

### If Multiple Steps Can Be Batched
- Execute one step at a time by default
- Only batch if user explicitly requests "execute next 3 steps"
- Still run test checkpoints after each step
- Still commit after each step

## Key Principles

1. **Follow the plan exactly** - The atomic plan is the source of truth
2. **Test after every step** - Never skip test checkpoints
3. **Commit atomically** - Use exact messages from plan
4. **One step at a time** - Don't batch unless requested
5. **Stop on failure** - Never proceed if tests fail
6. **Update as you go** - Keep checklist and notes current
7. **Be autonomous** - Execute without asking unless there's ambiguity

## What NOT To Do

❌ Don't generate execution reports instead of executing
❌ Don't improvise code not in the plan
❌ Don't skip test checkpoints
❌ Don't batch multiple steps without permission
❌ Don't proceed when tests fail
❌ Don't modify commit messages from plan
❌ Don't forget to update checklist/notes

## Success Criteria

After each execution, verify:
- ✅ Code matches plan exactly
- ✅ Tests pass (green)
- ✅ Changes committed with correct message
- ✅ Checklist item marked [x]
- ✅ Notes updated with timestamp
- ✅ Ready for next step

---

**Remember:** This command should DO the work, not just report on it. Execute, test, commit, update, repeat.