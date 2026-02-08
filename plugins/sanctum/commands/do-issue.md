---
name: do-issue
description: Implement issues (GitHub/GitLab/Bitbucket) using progressive analyze-specify-plan-implement workflow
usage: /do-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--from <step>] [--to <step>] [--scope auto|minor|medium|major]
---

# Do Issue(s)

A progressive workflow for implementing issues from the detected git platform (GitHub, GitLab, or Bitbucket), following the attune pattern:
**analyze** → **specify** → **plan** → **implement** → **validate** → **complete**

## When To Use

Use this command when you need to:
- Implementing fixes for one or more issues (GitHub, GitLab, or Bitbucket)
- Progressive issue resolution with validation
- Addressing a particular issue or ticket that is referenced

## When NOT To Use

- Simple changes that don't need the full workflow
- Work already completed through another sanctum command

## Quick Reference

```
/do-issue 42                  # Full workflow for issue #42
/do-issue 42 --from plan      # Skip analysis/specify, start at planning
/do-issue 42 --to plan        # Stop after planning (dry run)
/do-issue 42 --scope minor    # Auto-skip steps for minor fixes
/do-issue 42 43 44            # Multiple issues with dependency analysis
```

## Workflow Steps Overview

| Step | Purpose | Skip When |
|------|---------|-----------|
| **1. Analyze** | Fetch issue, understand requirements | Already familiar with issue |
| **2. Specify** | Clarify acceptance criteria | Criteria are clear |
| **3. Plan** | Break down into tasks, identify dependencies | Single obvious fix |
| **4. Implement** | Apply code changes with TDD | Just need validation |
| **5. Validate** | Run tests, quality gates | Already validated |
| **6. Complete** | Update issue, create PR | Just needed implementation |

## Intelligent Step-Skipping

The workflow auto-detects scope and suggests step-skipping:

**Minor scope** (typo fix, config change):
- Skip: Analyze, Specify, Plan
- Run: Implement → Validate → Complete

**Medium scope** (single feature, clear requirements):
- Skip: Specify (if criteria clear)
- Run: Analyze → Plan → Implement → Validate → Complete

**Major scope** (multi-file, complex requirements):
- Run all steps

```bash
# Detect scope automatically
/do-issue 42 --scope auto

# Override with explicit scope
/do-issue 42 --scope minor
/do-issue 42 --scope medium
/do-issue 42 --scope major
```

---

## Step 1: Analyze (Discovery & Context)

**Purpose**: Understand the issue and gather all relevant context.

**Skip when**: You're already familiar with the issue (e.g., you just created it).

### 1.1 Fetch Issue Details

```bash
# GitHub
gh issue view ISSUE_NUMBER --json number,title,body,labels,state,assignees
gh issue view ISSUE_NUMBER --comments

# GitLab
glab issue view ISSUE_NUMBER
```

### 1.2 Understand Requirements

Extract from the issue:
- **Problem statement**: What's broken or missing?
- **Expected behavior**: What should happen?
- **Acceptance criteria**: How do we know it's fixed?
- **Related context**: Links, screenshots, error logs

### 1.3 Check Related Issues

```bash
# GitHub
gh issue list --search "related keywords" --json number,title
gh issue view ISSUE_NUMBER --json milestone,project

# GitLab
glab issue list --search "related keywords"
glab issue view ISSUE_NUMBER
```

**Step 1 Output**: Issue understanding, context gathered

---

## Step 2: Specify (Clarify Requirements)

**Purpose**: Ensure acceptance criteria are clear and testable.

**Skip when**: Issue already has clear acceptance criteria in Given-When-Then format.

### 2.1 Extract Acceptance Criteria

If the issue has explicit criteria, extract them:
```markdown
**Acceptance Criteria from Issue:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### 2.2 Clarify Ambiguous Requirements

If criteria are unclear, add clarifying comments to the issue:
```bash
# GitHub
gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
## Clarification Questions

Before implementing, I'd like to clarify:

1. **[Ambiguous point]**: Should this be X or Y?
2. **[Missing detail]**: What happens when Z?

Please confirm so I can proceed with the correct approach.
EOF
)"
```

### 2.3 Generate Testable Criteria

Convert vague requirements to testable acceptance criteria:
```markdown
**Testable Acceptance Criteria:**
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [edge case], when [action], then [appropriate handling]
- [ ] Tests added for new functionality
- [ ] Documentation updated (if applicable)
```

**Step 2 Output**: Clear, testable acceptance criteria

---

## Step 3: Plan (Task Breakdown)

**Purpose**: Break down the issue into implementable tasks with dependencies.

**Skip when**: Single obvious fix with no subtasks needed.

### 3.1 Identify Components to Change

```bash
# Analyze codebase to find relevant files
# (use your knowledge of the codebase structure)
```

List files that likely need changes:
- `path/to/file1.py` - [reason]
- `path/to/file2.py` - [reason]
- `tests/test_file1.py` - [add tests]

### 3.2 Create Task Breakdown

For medium/major scope issues, create a task list:

```markdown
### Task Plan for Issue #ISSUE_NUMBER

**Tasks:**
1. [ ] TASK-1: [Description] - [estimate]
   - Dependencies: None
   - Files: file1.py

2. [ ] TASK-2: [Description] - [estimate]
   - Dependencies: TASK-1
   - Files: file2.py

3. [ ] TASK-3: Add tests - [estimate]
   - Dependencies: TASK-1, TASK-2
   - Files: tests/

**Parallel execution possible:** TASK-1 and TASK-2 if independent
```

### 3.3 Dependency Analysis (Multiple Issues)

When fixing multiple issues, analyze dependencies:
```bash
# For /do-issue 42 43 44
# Analyze which can run in parallel vs. sequential
```

| Issue | Dependencies | Execution |
|-------|--------------|-----------|
| #42 | None | Parallel Group A |
| #43 | None | Parallel Group A |
| #44 | #42 | Sequential after #42 |

### 3.4 War Room Checkpoint (Automatic)

**Purpose**: Assess whether complex multi-issue work warrants expert deliberation.

**Auto-triggers when** (moderate approach):
- 3+ issues being implemented, OR
- Dependency conflicts detected between issues, OR
- Overlapping file changes identified (same files in multiple issues), OR
- Single issue touches critical modules (auth, database schema, API contracts)

**Checkpoint invocation** (automatic, no user action needed):

```markdown
Skill(attune:war-room-checkpoint) with context:
  source_command: "do-issue"
  decision_needed: "Execution strategy for issues #42, #43, #44"
  issues_involved: [42, 43, 44]
  files_affected: [list of overlapping files]
  conflict_description: "Issues #42 and #44 both modify auth middleware"
  profile: [from user settings, default: "default"]
```

**Response handling**:

| RS Score | Mode | Action |
|----------|------|--------|
| RS <= 0.40 | Express | Quick recommendation returned, continue immediately |
| RS 0.41-0.60 | Lightweight | 3-expert panel deliberates, ~5 min |
| RS 0.61-0.80 | Full Council | 7-expert panel deliberates, ~15 min |
| RS > 0.80 | Delphi | Iterative consensus, ~30 min |

**Auto-continue logic**:
- If War Room confidence > 0.8: Orders applied automatically
- If confidence <= 0.8: User prompted to confirm approach

**Example checkpoint output**:

```
War Room Checkpoint: /do-issue
────────────────────────────────
Decision: Execution strategy for issues #42, #43, #44

Assessment:
  RS: 0.52 (Type 1B - Heavy Door)
  Mode: Lightweight (3 experts)
  Confidence: 0.87

Recommendation:
  1. Implement #42 first (establishes auth base)
  2. Then #43 in parallel (independent parser fix)
  3. Defer #44 to separate PR (scope creep detected)

Rationale: Issues #42 and #44 both touch auth module.
Combining risks merge conflicts and unclear rollback.

[Auto-continuing with War Room orders...]
```

**Skip conditions** (checkpoint not invoked):
- Single issue with scope=minor
- `--skip-war-room` flag (escape hatch)
- All issues are clearly independent (no shared files, no dependency chain)

**Step 3 Output**: Task breakdown with dependencies (War Room-validated if triggered)

---

## Step 4: Implement (Apply Changes)

**Purpose**: Apply code changes following TDD methodology.

**Skip when**: Just need validation (already made changes manually).

### 4.1 Create Feature Branch

```bash
# Create branch for the issue
git checkout -b fix/issue-ISSUE_NUMBER
# Or for multiple issues:
git checkout -b fix/issues-42-43-44
```

### 4.2 Test-Driven Development

Follow TDD cycle for each task:

```bash
# 1. Write failing test (RED)
# 2. Implement minimal code to pass (GREEN)
# 3. Refactor for quality (REFACTOR)
# 4. Repeat until task complete
```

### 4.3 Apply Fixes Systematically

For each task:
1. Read code context (±20 lines)
2. Write failing test first
3. Apply fix with Edit tool
4. Verify test passes
5. Refactor if needed
6. Mark task complete

### 4.4 Commit Changes

Use conventional commit format:
```bash
git commit -m "fix(scope): description

Fixes #ISSUE_NUMBER"
```

**Step 4 Output**: Code changes committed

---

## Step 5: Validate (Test & Verify)

**Purpose**: Ensure all changes are correct and quality gates pass.

**Skip when**: Already validated manually.

### 5.1 Run Targeted Tests

```bash
# Run tests related to changed files
pytest tests/test_affected.py -v

# Run full test suite
make test
```

### 5.2 Run Quality Gates

```bash
# Full quality check
make test && make lint && make build

# Or project-specific
uv run pytest tests/ -v
uv run ruff check .
uv run mypy src/
```

### 5.3 Verify Acceptance Criteria

Check each acceptance criterion:
```markdown
### Acceptance Criteria Verification

- [x] Criterion 1 - VERIFIED: [how]
- [x] Criterion 2 - VERIFIED: [how]
- [x] Criterion 3 - VERIFIED: [how]
```

### 5.4 Optional: Run /attune:validate

For project structure verification:
```bash
/attune:validate
```

**Step 5 Output**: All tests passing, quality gates green

---

## Step 6: Complete (Update Issue & Create PR)

**Purpose**: Update the issue, create PR, and close the loop.

**Skip when**: Just needed implementation without GitHub workflow.

### 6.1 Push Changes

```bash
git push -u origin fix/issue-ISSUE_NUMBER
```

### 6.2 Create Pull/Merge Request

```bash
# GitHub
gh pr create --title "fix(scope): description" --body "$(cat <<'EOF'
## Summary

Fixes #ISSUE_NUMBER

[Brief description of what was fixed]

## Changes

- [List of changes made]

## Test Plan

- [x] Unit tests added/updated
- [x] Integration tests pass
- [x] Quality gates pass

## Acceptance Criteria

- [x] [Criterion 1 from issue]
- [x] [Criterion 2 from issue]
EOF
)"

# GitLab
glab mr create --title "fix(scope): description" --description "$(cat <<'EOF'
## Summary

Closes #ISSUE_NUMBER

[Brief description of what was fixed]
EOF
)"
```

### 6.3 Update Issue

Comment on the issue with fix details:
```bash
# GitHub
gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
## Fix Implemented

This issue has been addressed in PR #PR_NUMBER.

**Changes Made:**
- [Summary of changes]

**Testing:**
- All tests pass
- Quality gates green

Will close automatically when PR merges.
EOF
)"
```

```bash
# GitLab
glab issue note ISSUE_NUMBER --message "Fix implemented in MR !MR_NUMBER"
```

### 6.4 Link PR/MR to Issue (Auto-Close)

- **GitHub**: Ensure PR body contains "Fixes #ISSUE_NUMBER" for auto-close on merge.
- **GitLab**: Ensure MR body contains "Closes #ISSUE_NUMBER" for auto-close on merge.

**Step 6 Output**: PR created, issue updated

---

## Options Reference

| Option | Description |
|--------|-------------|
| `--dry-run` | Analyze and show planned tasks without executing |
| `--from <step>` | Start at specific step (analyze, specify, plan, implement, validate, complete) |
| `--to <step>` | Stop after specific step |
| `--scope <level>` | Set scope level (auto, minor, medium, major) |
| `--parallel` | Force parallel execution for multiple issues |
| `--no-review` | Skip code review between tasks (not recommended) |
| `--close` | Automatically close issues when implemented |
| `--dangerous` | Continue execution without pauses (batch mode, auto-continue on handoffs) |

## Multiple Issues

When implementing multiple issues:

```bash
/do-issue 42 43 44
```

The workflow:
1. **Analyzes all issues** in parallel
2. **Detects dependencies** between issues
3. **Plans execution order**:
   - Independent issues run in parallel
   - Dependent issues run sequentially
4. **Executes with code review** between batches
5. **Creates single PR** (or multiple if needed)

### Execution Mode for Batch Processing

When processing multiple issues, especially with `--dangerous` flag:

```bash
/do-issue 42 43 44 --dangerous
```

**Execution mode is automatically set to**:
```json
{
  "mode": "unattended",
  "auto_continue": true,
  "source_command": "do-issue",
  "remaining_tasks": ["#43", "#44"],
  "dangerous_mode": true
}
```

**Context Handoff Behavior**:
- If context reaches 80%, session state is saved with execution mode
- Continuation agent inherits `auto_continue: true`
- Processing continues WITHOUT pausing for user confirmation
- Only stops when ALL issues are complete or on error

This ensures batch operations complete fully even across multiple context handoffs.

### Example Multi-Issue Execution

```
/do-issue 42 43 44

Analyzing issues...
- #42: Add validation to user input
- #43: Fix null pointer in parser
- #44: Update validation error messages (depends on #42)

Execution Plan:
  Batch 1 (Parallel): #42, #43
  Batch 2 (Sequential): #44 (after #42)

Proceed? [Y/n]
```

## Integration with Attune Workflow

This command follows the attune-style progressive workflow pattern:

```
Attune Workflow        | /do-issue Equivalent
-----------------------|----------------------
/attune:brainstorm     | (issue created/assigned)
/attune:arch-init      | --
/attune:specify        | Step 1-2: Analyze + Specify
/attune:blueprint           | Step 3: Plan
/attune:init           | Step 4.1: Create branch
/attune:execute        | Step 4-5: Implement + Validate
/attune:validate       | (included in Step 5)
/attune:upgrade-project        | (optional: /attune:upgrade-project if project needs updates)
```

## Required Skills

This command uses skills from multiple plugins:

| Skill | Plugin | Purpose |
|-------|--------|---------|
| `subagent-driven-development` | superpowers | Task execution pattern |
| `writing-plans` | superpowers | Task breakdown structure |
| `test-driven-development` | superpowers | TDD workflow |
| `requesting-code-review` | superpowers | Quality gates |
| `finishing-a-development-branch` | superpowers | Finalization |

## Examples

### Example 1: Single Issue (Minor)

```bash
/do-issue 42 --scope minor

# Skips: Analyze, Specify, Plan
# Runs: Implement → Validate → Complete
```

### Example 2: Single Issue (Full Workflow)

```bash
/do-issue 42

# Runs all steps
```

### Example 3: Multiple Issues

```bash
/do-issue 42 43 44

# Analyzes dependencies
# Runs independent issues in parallel
# Sequences dependent issues
```

### Example 4: Dry Run Preview

```bash
/do-issue 42 --dry-run

# Shows planned tasks without executing
# Useful for reviewing scope
```

### Example 5: Start from Planning

```bash
/do-issue 42 --from plan

# Skips Analyze and Specify
# Useful when you already understand the issue
```

## See Also

- `/fix-pr` - Fix PR review feedback using same progressive workflow
- `/pr` - Prepare a PR for submission
- `/pr-review` - Review a PR and post findings
- `/attune:execute` - Execute implementation tasks systematically
- `/attune:validate` - Validate project structure
