# Feature Development Lifecycle

Walk through building a feature from specification to merged PR. This tutorial covers the full development cycle using real commands across multiple plugins.

---

## Scenario

You've been asked to add a new capability to your project. You need to specify what you're building, plan the implementation, write the code, and get it reviewed and merged.

## Step 1: Start with a Specification

Don't jump straight to code. Start by defining what you're building:

```
/speckit-specify Add rate limiting to the API endpoints
```

This invokes the `spec-kit` plugin's specification skill. It will:

1. Ask clarifying questions about requirements (limits, scope, behavior)
2. Create a `spec.md` with user stories, acceptance criteria, and constraints
3. Identify edge cases you might not have considered

The spec becomes the source of truth for the feature.

### Refine the Spec

If the spec needs clarification:

```
/speckit-clarify
```

This asks targeted questions to resolve ambiguities. "Should rate limits be per-user or per-IP?" "What HTTP status code for rate-limited requests?"

## Step 2: Plan the Implementation

With a clear spec, generate an implementation plan:

```
/speckit-plan
```

This produces a phased plan showing:

- Which files to create or modify
- Dependencies between changes
- Test strategy for each phase
- Estimated scope per phase

### Generate Tasks

Break the plan into ordered tasks:

```
/speckit-tasks
```

This creates a `tasks.md` with dependency-ordered implementation steps. Each task is specific enough to implement independently.

## Step 3: Implement

Execute the tasks:

```
/speckit-implement
```

This processes tasks from `tasks.md` in dependency order. For each task, it:

1. Reads the task requirements
2. Writes a failing test (TDD approach)
3. Implements the minimum code to pass
4. Moves to the next task

You can also implement tasks selectively:

```
/speckit-implement --phase 1
```

### Check Consistency

After implementing, verify the spec, plan, and code are aligned:

```
/speckit-analyze
```

This cross-checks all artifacts: spec requirements against tests, plan phases against implementation, task completion against acceptance criteria.

## Step 4: Review Your Work

Before committing, review what you've built:

```
/code-review
```

This runs pensive's review system against your changes. For a feature like this, you might also run:

```
/architecture-review
```

This checks whether your implementation fits the existing architecture. Are you adding rate limiting in the right layer? Does it follow existing patterns?

## Step 5: Commit and Create a PR

Stage your changes and generate a commit message:

```
/commit-msg
```

This analyzes staged changes and drafts a conventional commit message. It classifies the change type (feat, fix, refactor) and summarizes the intent.

Then prepare the pull request:

```
/prepare-pr
```

This runs quality gates (tests, lint, scope check) and generates a PR description with:

- Summary of changes
- Test plan
- Breaking changes (if any)

## What You've Learned

- **spec-kit** handles the specification → plan → tasks → implementation pipeline
- **pensive** provides code review before you commit
- **sanctum** handles git operations: commits, PRs, quality gates
- Plugins collaborate through the workflow. You don't orchestrate them manually.

## Command Reference

| Phase | Command | Plugin |
|-------|---------|--------|
| Specify | `/speckit-specify` | spec-kit |
| Clarify | `/speckit-clarify` | spec-kit |
| Plan | `/speckit-plan` | spec-kit |
| Tasks | `/speckit-tasks` | spec-kit |
| Implement | `/speckit-implement` | spec-kit |
| Analyze | `/speckit-analyze` | spec-kit |
| Review | `/code-review` | pensive |
| Commit | `/commit-msg` | sanctum |
| PR | `/prepare-pr` | sanctum |

---

**Difficulty:** Intermediate
**Prerequisites:** [Your First Session](skills-showcase.md)
**Duration:** 15 minutes (following along with a real feature)
