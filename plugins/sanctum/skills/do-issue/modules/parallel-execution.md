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

## Next Phase

After parallel execution completes, proceed to [quality-gates.md](quality-gates.md) for batch review.
