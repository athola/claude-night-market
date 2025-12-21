# Phase 3: Parallel Execution

Dispatch subagents for independent tasks concurrently.

## Group Independent Tasks

Identify tasks that can run concurrently:

- Tasks from different files
- Tasks with no shared state
- Tasks that don't modify same code paths

## Dispatch Parallel Subagents

For independent tasks, dispatch concurrently using the Task tool:

```
Task tool (general-purpose) [PARALLEL]:
  description: "Issue #42 - Task 1: Create auth middleware"
  prompt: |
    You are implementing Task 1 from Issue #42.

    Issue context:
    [Issue body and requirements]

    Your job:
    1. Implement exactly what the task specifies
    2. Follow TDD - write failing test first
    3. Implement until tests pass
    4. Verify no regressions
    5. Commit your work with conventional commit format

    Report: Implementation summary, test results, files changed
```

```
Task tool (general-purpose) [PARALLEL]:
  description: "Issue #43 - Task 1: Fix validation bug"
  prompt: |
    You are implementing Task 1 from Issue #43.
    [Same structure as above]
```

## Await Parallel Results

Collect results from all parallel subagents before proceeding:

```
Parallel Batch 1: Issues #42, #43
  [2 subagents running in parallel...]
  #42 Task 1: Complete (auth middleware)
  #43 Task 1: Complete (validation fix)
```

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Fresh Context** | Each subagent starts clean, avoiding context pollution |
| **TDD by Default** | Subagents write failing tests first |
| **Conventional Commits** | Each task commits with proper format |
| **Isolation** | Tasks don't share state between subagents |

## Next Phase

After parallel execution completes, proceed to [quality-gates.md](quality-gates.md) for batch review.
