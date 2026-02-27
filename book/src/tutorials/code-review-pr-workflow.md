# Code Review and PR Workflow

The most common daily workflow: review your changes, commit them cleanly, create a PR, and address reviewer feedback.

---

## Scenario

You've finished working on a feature branch. You have uncommitted changes and need to get them reviewed, committed, and merged.

## Step 1: Understand What Changed

Start by catching up on your own work:

```
/catchup
```

This summarizes recent changes: which files were modified, what the commit history looks like, and what's currently unstaged. Useful even for your own branch, especially after stepping away.

## Step 2: Self-Review Before Committing

Run a code review on your changes before anyone else sees them:

```
/code-review
```

This analyzes your uncommitted and staged changes. The review covers:

- **Bugs**: Logic errors, off-by-one mistakes, null handling
- **Style**: Naming, formatting, consistency with existing patterns
- **Architecture**: Does the change fit the codebase design?
- **Tests**: Are changes covered by tests?

Fix any issues found before proceeding.

### Targeted Reviews

If your change is in a specific domain, use a focused review:

```
/bug-review           # Focus on defect detection
/test-review          # Evaluate test coverage and quality
/architecture-review  # Check design patterns and structure
```

## Step 3: Commit with a Clean Message

Stage your changes and generate a commit message:

```
/commit-msg
```

This analyzes staged changes and produces a conventional commit message. It:

1. Classifies the change type (feat, fix, refactor, docs, test)
2. Identifies the appropriate scope
3. Writes a concise description of the _intent_ (why, not what)

Example output:

```
feat(api): add rate limiting to public endpoints

Implements per-user rate limiting with configurable thresholds.
Requests exceeding the limit receive 429 responses with retry-after headers.
```

You review the message and approve or edit it before the commit is created.

## Step 4: Prepare the Pull Request

With your changes committed, prepare a PR:

```
/prepare-pr
```

This runs a multi-step workflow:

1. **Workspace analysis** - reviews all commits on the branch
2. **Quality gates** - runs tests and lint checks
3. **Scope check** - flags if the branch has drifted beyond its original intent
4. **PR description** - generates a description with summary, test plan, and checklist

The PR is created with a description that reviewers can actually use.

## Step 5: Address Review Feedback

After reviewers comment on your PR, use:

```
/fix-pr
```

This reads the PR review comments and works through them:

1. Fetches all unresolved review threads
2. Groups feedback by type (required changes, suggestions, questions)
3. Addresses each item: makes code changes, responds to questions
4. Resolves threads as changes are made

### Resolve Threads in Bulk

After addressing feedback, resolve all completed threads:

```
/resolve-threads
```

This batch-resolves review threads that have been addressed by code changes.

## Step 6: Review a Teammate's PR

You can also review PRs from others:

```
/pr-review 123
```

This reviews PR #123:

1. Reads the PR description and all changed files
2. Checks changes against the stated scope
3. Identifies potential issues organized by severity
4. Produces a review with specific feedback

## What You've Learned

- **Self-review** before committing catches issues early
- **Conventional commits** via `/commit-msg` maintain a clean git history
- **PR preparation** via `/prepare-pr` automates quality gates and descriptions
- **Feedback handling** via `/fix-pr` works through review comments one by one
- **PR review** via `/pr-review` gives you a thorough analysis of others' work

## Command Reference

| Step | Command | Plugin |
|------|---------|--------|
| Catch up | `/catchup` | imbue |
| Self-review | `/code-review` | pensive |
| Commit | `/commit-msg` | sanctum |
| Create PR | `/prepare-pr` | sanctum |
| Fix feedback | `/fix-pr` | sanctum |
| Resolve threads | `/resolve-threads` | sanctum |
| Review others | `/pr-review` | sanctum |

---

**Difficulty:** Beginner
**Prerequisites:** [Your First Session](skills-showcase.md)
**Duration:** 10 minutes
