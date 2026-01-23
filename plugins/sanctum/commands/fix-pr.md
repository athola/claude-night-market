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

## See Also

- `/pr` - Create pull request
- `/pr-review` - Review pull request
- `/update-tests` - Update test suite
- **Attune Workflow**: `plugins/attune/commands/attune.md`
