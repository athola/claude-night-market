---
name: fix-pr
description: Address PR review feedback using progressive workflow
usage: /fix-pr [<pr-number> | <pr-url>] [--dry-run] [--from <step>] [--to <step>] [--commit-strategy single|separate|manual]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Fix

<identification>
triggers: fix PR, address review, PR feedback, review comments

use_when:
- Responding to PR review comments systematically
- Iterating on PR after reviewer feedback
</identification>

A progressive workflow for addressing PR review feedback, following the attune pattern:
**analyze** → **triage** → **plan** → **fix** → **validate** → **complete**

## Quick Reference

```bash
/fix-pr                    # Full workflow
/fix-pr --from triage      # Skip analysis, start at triage
/fix-pr --to plan          # Stop after planning (dry run)
/fix-pr --scope minor      # Auto-skip steps for minor fixes
```

## Workflow Steps Overview

| Step | Purpose | Skip When |
|------|---------|-----------|
| **1. Analyze** | Fetch PR, comments, context | Already familiar with PR |
| **2. Triage** | Classify comments by type/priority | Single simple fix |
| **3. Plan** | Generate fix strategies | Fixes are obvious |
| **4. Fix** | Apply code changes | Just need validation |
| **5. Validate** | Run tests, version checks | Already validated |
| **6. Complete** | **Reconcile ALL unworked items**, **reply to & resolve threads** (MANDATORY), create issues, post summary | Never - issue tracking & thread resolution enforced |

**Detailed Steps**: See [Workflow Steps](fix-pr-modules/workflow-steps.md)

## Intelligent Step-Skipping

The workflow auto-detects scope and suggests step-skipping:

**Minor scope** (1-2 simple comments):
- Skip: Analyze, Triage, Plan
- Run: Fix → Validate → Complete

**Medium scope** (3-5 comments, clear fixes):
- Skip: Analyze (if familiar)
- Run: Triage → Plan → Fix → Validate → Complete

**Major scope** (6+ comments, complex changes):
- Run all steps

```bash
# Detect scope automatically
/fix-pr --scope auto

# Override with explicit scope
/fix-pr --scope minor
/fix-pr --scope medium
/fix-pr --scope major
```

## Documentation

| Document | Purpose |
|----------|---------|
| **[Workflow Steps](fix-pr-modules/workflow-steps.md)** | Detailed guide for each step (Analyze → Complete) |
| **[Configuration & Options](fix-pr-modules/configuration-options.md)** | Command options, configuration, best practices |
| **[Troubleshooting](fix-pr-modules/troubleshooting-fixes.md)** | Error handling, known issues, migration notes |

## Common Usage Examples

### Basic Usage
```bash
# Full workflow for PR
/fix-pr 123

# With PR URL
/fix-pr https://github.com/org/repo/pull/123
```

### Step Control
```bash
# Skip to specific step
/fix-pr --from plan

# Stop at specific step (dry run)
/fix-pr --to plan

# Run specific range
/fix-pr --from triage --to validate
```

### Commit Strategies
```bash
# Single commit for all fixes (default)
/fix-pr --commit-strategy single

# Separate commit per fix
/fix-pr --commit-strategy separate

# Manual commits (for complex cases)
/fix-pr --commit-strategy manual
```

### Scope Control
```bash
# Auto-detect scope
/fix-pr --scope auto

# Force minor workflow (skip to fix)
/fix-pr --scope minor
```

## Quick Start

1. **Simple PR fixes** (1-2 comments):
   ```bash
   /fix-pr <pr-number> --scope minor
   ```

2. **Medium complexity** (3-5 comments):
   ```bash
   /fix-pr <pr-number>
   ```

3. **Complex refactoring** (6+ comments):
   ```bash
   /fix-pr <pr-number> --scope major
   ```

4. **Just planning** (dry run):
   ```bash
   /fix-pr <pr-number> --to plan
   ```

## War Room Checkpoint (Automatic)

**Purpose**: Assess whether complex PR feedback warrants expert deliberation before planning fixes.

**Auto-triggers when** (moderate approach):
- Scope is major (6+ comments), OR
- Conflicting reviewer feedback detected, OR
- Multiple refactoring suggestions (>2), OR
- Breaking change required by reviewer

**Checkpoint invocation** (automatic, after Step 2 Triage):

```markdown
Skill(attune:war-room-checkpoint) with context:
  source_command: "fix-pr"
  decision_needed: "Fix strategy for PR #123 review feedback"
  blocking_items: [
    {type: "refactor", description: "Reviewer A: Extract service class"},
    {type: "refactor", description: "Reviewer B: Keep inline, add tests only"},
    {type: "breaking", description: "API signature change required"}
  ]
  files_affected: [files from triage analysis]
  profile: [from user settings, default: "default"]
```

**War Room Questions** (when escalated):
- "How do we reconcile conflicting reviewer suggestions?"
- "Should we push back on any suggestions as out-of-scope?"
- "Is a multi-commit or multi-PR approach appropriate?"

**Response handling**:

| RS Score | Mode | Action |
|----------|------|--------|
| RS <= 0.40 | Express | Quick recommendation, continue |
| RS 0.41-0.60 | Lightweight | Panel reviews conflicting feedback |
| RS > 0.60 | Full Council | Full deliberation on approach |

**Auto-continue logic**:
- If confidence > 0.8: Apply War Room's fix strategy
- If confidence <= 0.8: Present options to user

**Skip conditions**:
- Scope is minor or medium with clear fixes
- No conflicting feedback
- Single reviewer, straightforward comments

## Integration

This command integrates with:
- **attune workflow**: Follows analyze → triage → plan → fix → validate pattern
- **gh CLI**: Fetches PR data, resolves threads, updates issues
- **git**: Commits changes, pushes updates
- **test suite**: Runs verification after fixes
- **Claude Code Tasks** (2.1.16+): Progress tracking with native Tasks system

### Claude Code Tasks Integration

When running in Claude Code 2.1.16+, workflow steps are tracked via native Tasks:

```python
from tasks_manager import TasksManager
manager = TasksManager(
    project_path=Path("."),
    fallback_state_file=Path(".sanctum/fix-pr-state.json"),
)

# Each workflow step becomes a task
for step in ["analyze", "triage", "plan", "fix", "validate", "complete"]:
    task_id = manager.ensure_task_exists(f"PR Fix: {step}")
    # Execute step...
    manager.update_task_status(task_id, "complete")
```

**Benefits**:
- Resume interrupted PR fix workflows across sessions
- Tasks visible in VS Code sidebar
- Dependency tracking (can't validate before fix)
- Cross-session state with `CLAUDE_CODE_TASK_LIST_ID="sanctum-fix-pr-{pr_number}"`

## Getting Help

- **Workflow Details**: See [Workflow Steps](fix-pr-modules/workflow-steps.md)
- **Options Reference**: See [Configuration & Options](fix-pr-modules/configuration-options.md)
- **Troubleshooting**: See [Troubleshooting](fix-pr-modules/troubleshooting-fixes.md)

## Mandatory Exit Gate

**⛔ CRITICAL: The workflow is NOT complete until this gate passes.**

Before reporting completion, you MUST run this verification:

```bash
# Get PR info
REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=$(echo "$REPO_FULL" | cut -d'/' -f1)
REPO=$(echo "$REPO_FULL" | cut -d'/' -f2)
PR_NUM=$(gh pr view --json number -q .number)

# Check for unresolved threads
UNRESOLVED=$(gh api graphql -f query="
query {
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $PR_NUM) {
      reviewThreads(first: 100) {
        nodes { isResolved }
      }
    }
  }
}" --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length')

if [[ "$UNRESOLVED" -gt 0 ]]; then
  echo "❌ EXIT GATE FAILED: $UNRESOLVED unresolved threads"
  echo "Run Step 6 (Complete) before reporting workflow complete"
  exit 1
else
  echo "✓ EXIT GATE PASSED: All threads resolved"
fi
```

**This gate is NOT optional.** If threads remain unresolved:
1. Execute [Step 6: Complete](fix-pr-modules/steps/6-complete.md)
2. Reply to each thread with fix description
3. Resolve each thread via GraphQL
4. Re-run this gate until it passes

**The `--to` flag cannot skip Step 6** - use `--to validate` for dry runs, but completing the workflow always requires thread resolution.

## See Also

- `/pr` - Create pull request
- `/pr-review` - Review pull request
- `/update-tests` - Update test suite
- **Attune Workflow**: `plugins/attune/commands/attune.md`
