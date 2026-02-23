# Phase 3: Parallel Execution

Dispatch subagents for independent tasks concurrently.

## CRITICAL: Execute Nonconflicting Tasks in Parallel

**When you have multiple NONCONFLICTING tasks, invoke ALL Task tools in a SINGLE response.**

This is NOT optional - parallel execution is the default for nonconflicting tasks.

## Identify Nonconflicting Tasks

Tasks can run in parallel ONLY when ALL conditions are met:

✅ **Safe for parallel execution:**
- Tasks modify **different files** (no overlap)
- Tasks have **no shared state** (independent data)
- Tasks don't modify **same code paths** (no merge conflicts)
- Tasks have **satisfied dependencies** (no blocking)
- Tasks don't depend on **each other's outputs**

❌ **NOT safe for parallel execution:**
- Tasks modify the **same file** or related files
- Tasks share **configuration** or **global state**
- Tasks have **sequential dependencies**
- Tasks touch **overlapping code paths** that could conflict
- Tasks need results from **each other**
- Both tasks are `[R:RED]` (compounding risk prohibited)
- Either task is `[R:CRITICAL]` (always executes solo)

## Analyze Task Conflicts BEFORE Dispatching

**MANDATORY**: Perform conflict analysis before parallel execution:

```markdown
Analyzing tasks for parallel execution:

Task 1 (Issue #42): Create auth middleware in src/auth/middleware.py
Task 2 (Issue #43): Fix validation bug in src/validators/schema.py
Task 3 (Issue #44): Add logging to src/utils/logger.py

Conflict Check:
- Files: ✅ No overlap (middleware.py, schema.py, logger.py are different)
- Dependencies: ✅ No sequential dependencies between tasks
- State: ✅ No shared configuration or database schema
- Code paths: ✅ Independent modules, no import conflicts

Decision: Execute Tasks 1, 2, 3 in PARALLEL (3 Task tool invocations in single response)
```

**COUNTER-EXAMPLE** - Sequential execution required:

```markdown
Task A (Issue #50): Refactor User model in models/user.py
Task B (Issue #51): Add authentication using User model

Conflict Check:
- Files: ❌ Task B depends on Task A's User model changes
- Dependencies: ❌ Task B needs Task A's output
- Code paths: ❌ Both touch authentication flow

Decision: Execute SEQUENTIALLY (Task A first, then Task B)
```

## Risk-Tier Parallel Safety

When tasks have `[R:TIER]` markers (from `leyline:risk-classification`), apply these additional constraints:

| Task A Tier | Task B Tier | Parallel? | Reason |
|-------------|-------------|-----------|--------|
| GREEN | Any | Yes | Low risk, independent |
| YELLOW | YELLOW | Yes | Standard caution |
| YELLOW | RED | Yes | With conflict monitoring |
| RED | RED | **No** | Compounding risk too high |
| Any | CRITICAL | **No** | CRITICAL always solo |

Tasks without `[R:TIER]` markers are treated as GREEN (backward compatible).

## Dispatch Parallel Subagents

**CORRECT PATTERN** - Multiple Task tool invocations in ONE response:

```text
I'll execute these 3 nonconflicting tasks in parallel:

Task(description: "Issue #42 - Create auth middleware")
Task(description: "Issue #43 - Fix validation bug")
Task(description: "Issue #44 - Add logging feature")

Each task will:
1. Implement in its designated file (no conflicts)
2. Follow TDD - write failing test first
3. Verify no regressions
4. Commit with conventional format
```

**WRONG PATTERN** - Sequential invocations:

```text
❌ Task(description: "Issue #42")
   [wait for result]
   Task(description: "Issue #43")
   [wait for result]

This wastes time when tasks are nonconflicting!
```

## Await Parallel Results

Collect results from all parallel subagents before proceeding:

```
Parallel Batch 1: Issues #42, #43, #44 (3 tasks)
  [3 subagents running in parallel...]

  ✅ #42: Complete (auth middleware in src/auth/middleware.py)
  ✅ #43: Complete (validation fix in src/validators/schema.py)
  ✅ #44: Complete (logging in src/utils/logger.py)

All tasks completed without conflicts.
```

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Fresh Context** | Each subagent starts clean, avoiding context pollution |
| **TDD by Default** | Subagents write failing tests first |
| **Conventional Commits** | Each task commits with proper format |
| **Isolation** | Tasks don't share state between subagents |

## Agent Teams (Default Execution Backend)

Agent teams is the **default** for parallel execution in do-issue. Teammates coordinate via filesystem-based messaging, which prevents merge conflicts and duplicate work that Task tool batches would only catch at the review gate.

Use `--no-agent-teams` to fall back to Task tool dispatch when coordination overhead isn't justified.

### Automatic Downgrade

Agent teams is skipped (Task tool or inline used instead) when:
- Single issue with `--scope minor` (no parallelism needed)
- tmux is not installed or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is unset
- `--no-agent-teams` flag is explicitly passed

### When Task Tool Is Better

| Scenario | Recommendation |
|----------|---------------|
| Single issue, minor scope | Inline execution (no dispatch at all) |
| 2-3 fully independent issues, no shared files | Task tool is simpler, `--no-agent-teams` |
| 3+ issues with shared files or dependencies | Agent teams (default) |
| 5+ issues, complex dependency graph | Agent teams (default) |

### Agent Teams Execution Pattern

```text
Lead agent creates team: do-issue-{timestamp}
  Spawns: worker-1 (Sonnet), worker-2 (Sonnet), worker-3 (Sonnet)

Lead assigns tasks via inbox:
  worker-1: "Implement #42 (auth middleware) in src/auth/"
  worker-2: "Fix #43 (validation bug) in src/validators/"
  worker-3: "Add #44 (logging) in src/utils/"

Mid-execution coordination:
  worker-1 → worker-3: "I added auth logging to src/auth/log.py —
    don't duplicate in your logging task"
  worker-3 → worker-1: "Acknowledged, will import from your module"

Lead collects completion messages, runs quality gates, shuts down team.
```

### Key Difference from Task Tool

Task tool subagents are **fire-and-forget** — they can't communicate mid-execution. Agent teams teammates can **send messages to each other** when they discover shared concerns. This prevents merge conflicts and duplicate work that Task tool batches would catch only at the review gate.

### Fallback

If tmux is unavailable or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not set, `--agent-teams` silently falls back to standard Task tool dispatch.

## Worktree Isolation for Parallel Safety (Claude Code 2.1.49+)

Subagents with `isolation: worktree` in their frontmatter run in a temporary git worktree, providing filesystem-level isolation without relying on conflict analysis alone.

- **Use case**: When parallel tasks touch files in the same directory or have uncertain conflict boundaries
- **Benefit**: Each agent gets its own working copy — merge conflicts are resolved at worktree merge time, not during execution
- **Auto-cleanup**: Empty worktrees are removed automatically; worktrees with commits are preserved for review
- **Combine with conflict analysis**: Worktree isolation is a safety net, not a replacement for the conflict check above — still analyze dependencies before dispatching

## Next Phase

After parallel execution completes, proceed to [quality-gates.md](quality-gates.md) for batch review.
