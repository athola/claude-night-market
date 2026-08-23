---
name: do-issue
description: Implement issues (GitHub/GitLab/Bitbucket) using progressive analyze-specify-plan-implement workflow
usage: /do-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--from <step>] [--to <step>] [--scope auto|minor|medium|major]
---

# Do Issue(s)

A progressive workflow for implementing issues from the detected git platform (GitHub, GitLab, or Bitbucket), following the attune pattern:
**analyze** → **specify** → **plan** → **implement** → **validate** → **complete**

Invoke `Skill(sanctum:do-issue)`, which carries the six-step workflow, the
task planning, the parallel execution, the quality gates and the
completion steps. The arguments, step-skipping rules and War Room gate
below are applied by this command.

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

## War Room Checkpoint (Automatic)

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
| `--no-agent-teams` | Disable agent teams and use Task tool dispatch instead. Agent teams is **on by default** for parallel execution (auto-downgrades for `--scope minor`). |

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
