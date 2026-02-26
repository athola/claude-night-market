# Debugging and Issue Resolution

Walk through the process of triaging a GitHub issue, debugging the problem, implementing a fix, and verifying the solution.

---

## Scenario

A user has filed GitHub issue #42: "API returns 500 when request body is empty." You need to investigate, fix it, and close the issue.

## Step 1: Understand the Context

Before diving in, catch up on recent changes that might be related:

```
/git-catchup
```

This shows recent commits, active branches, and areas of change. If someone recently modified the API layer, that context is immediately relevant.

## Step 2: Implement the Issue End-to-End

For well-defined issues, use the issue resolution command:

```
/do-issue 42
```

This reads the GitHub issue and orchestrates the full fix:

1. **Reads the issue** - title, description, labels, comments
2. **Plans the approach** - identifies affected files and tests needed
3. **Creates a branch** - based on the issue number
4. **Implements the fix** - with tests written first (TDD approach)
5. **Prepares a PR** - linking back to the issue

This is the fastest path from issue to PR. It handles the orchestration so you focus on reviewing the result.

## Step 3: Manual Debugging (When Needed)

Sometimes issues need investigation before you can fix them. For complex bugs, work through the problem step by step.

### Investigate the Problem

Start by reading the issue and understanding the reproduction steps. Then explore the relevant code:

```
Show me the API endpoint handlers that process request bodies
```

Claude will search the codebase, read the relevant files, and explain the code flow.

### Find the Root Cause

Ask Claude to trace the execution path:

```
Trace what happens when an empty POST body hits the /api/data endpoint
```

Claude reads the handler code, middleware, and validation layers to identify where the 500 error originates.

### Verify the Fix

After implementing a fix, verify it works:

```
Run the tests for the API endpoint module
```

Claude runs the relevant test suite and reports results. If tests fail, it analyzes the failure and suggests corrections.

## Step 4: Create the Issue (When You Find Bugs)

If you discover a bug while working, create an issue to track it:

```
/create-issue
```

This creates a formatted GitHub issue with:

- Clear title and description
- Reproduction steps
- Expected vs. actual behavior
- Labels and assignees

## Step 5: Close Resolved Issues

After your PR is merged, check if the issue can be closed:

```
/close-issue 42
```

This analyzes whether the issue's requirements have been met by reviewing the linked PR and test evidence.

## Debugging Tips

### Use Catchup for Context

When you inherit a bug you didn't create, `/catchup` gives you the recent history that led to the current state. This often reveals what change introduced the bug.

### Use Targeted Reviews

If you suspect a specific type of issue:

```
/bug-review    # Systematic bug hunting in recent changes
/test-review   # Check if tests actually cover the bug scenario
```

### Work Incrementally

For complex bugs:

1. Reproduce the bug (confirm you can trigger it)
2. Write a failing test that captures the bug
3. Fix the code until the test passes
4. Run the full test suite to check for regressions

## What You've Learned

- `/do-issue` handles the full lifecycle: read → plan → implement → PR
- `/create-issue` formats new issues with proper structure
- `/close-issue` verifies issues are resolved before closing
- `/git-catchup` provides historical context for debugging
- Targeted reviews (`/bug-review`, `/test-review`) focus analysis on specific concerns

## Command Reference

| Step | Command | Plugin |
|------|---------|--------|
| Context | `/git-catchup` | sanctum |
| Full fix | `/do-issue 42` | sanctum |
| Create issue | `/create-issue` | minister |
| Close issue | `/close-issue 42` | minister |
| Bug review | `/bug-review` | pensive |
| Test review | `/test-review` | pensive |
| Catchup | `/catchup` | imbue |

---

**Difficulty:** Intermediate
**Prerequisites:** [Your First Session](skills-showcase.md)
**Duration:** 10 minutes
