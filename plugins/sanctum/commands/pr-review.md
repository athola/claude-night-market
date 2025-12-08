---
description: Scope-focused PR review that validates against original requirements and routes out-of-scope findings to GitHub issues
usage: /pr-review [<pr-number> | <pr-url>]
---

# PR Code Review (Scope-Focused)

Perform a disciplined code review that validates the PR against its original requirements and prevents scope creep. Issues outside the branch's defined scope are captured as GitHub issues for future work, not blocking items for this PR.

## Philosophy

**Prevent overengineering.** Each branch should be tightly scoped to its original requirements. A PR review is NOT the place to identify every possible improvement - it's the place to validate that the implementation meets its stated goals and doesn't introduce regressions.

### In-Scope (Address Now)
- Requirements from the original plan/spec for this branch
- Bugs introduced by this change
- Breaking changes affecting existing consumers
- Security vulnerabilities
- Test coverage for new/changed code paths

### Out-of-Scope (Create GitHub Issue)
- "Nice to have" improvements not in requirements
- Refactoring suggestions beyond the change scope
- Style/convention changes in untouched code
- Feature ideas sparked by the changes
- Technical debt in adjacent code

## Arguments

- No argument: Reviews the PR for current branch
- `<pr-number>`: Review specific PR by number (e.g., `/pr-review 123`)
- `<pr-url>`: Review PR by URL (e.g., `/pr-review https://github.com/owner/repo/pull/123`)

## Workflow

Use the `sanctum:pr-review` skill to execute this review.

### 1. Identify the PR

```bash
# If no argument, get PR for current branch
gh pr view --json number,url,headRefName,baseRefName,title,body

# If argument provided, use it directly
gh pr view <argument> --json number,url,headRefName,baseRefName,title,body
```

### 2. Establish Scope Baseline

**Critical Step**: Before reviewing code, establish what this PR is supposed to accomplish.

Search for scope-defining artifacts:
1. **Plan file**: `docs/plans/*-<branch-name>*.md` or `plan.md`
2. **Spec file**: `spec.md` or `docs/specs/*.md`
3. **Tasks file**: `tasks.md` with completed items
4. **PR description**: The `body` from step 1
5. **Commit messages**: Understand incremental intent

```bash
# Check for plan artifacts
ls docs/plans/ 2>/dev/null | head -5
cat plan.md 2>/dev/null | head -50
cat spec.md 2>/dev/null | head -50

# Get commit history for this branch
gh pr view <pr-number> --json commits --jq '.commits[].messageHeadline'
```

Summarize: "This PR aims to: [extracted scope]"

### 3. Get PR Changes

```bash
# Files changed
gh pr diff <pr-number> --name-only

# Full diff
gh pr diff <pr-number>

# Stats
gh pr view <pr-number> --json additions,deletions,changedFiles
```

### 4. Scope-Aware Review

Run `pensive:unified-review` with scope context.

For EACH finding, classify:

| Category | Criteria | Action |
|----------|----------|--------|
| **BLOCKING** | Bug/security issue introduced by this change | Must fix before merge |
| **IN-SCOPE** | Directly relates to stated requirements | Should address in this PR |
| **SUGGESTION** | Improvement within changed files, not required | Author decides |
| **BACKLOG** | Good idea but outside this PR's scope | Create GitHub issue |
| **IGNORE** | Nitpick or preference not worth tracking | Skip |

### 5. Create GitHub Issues for Backlog Items

For each BACKLOG finding:

```bash
gh issue create \
  --title "[Tech Debt] <brief title>" \
  --body "## Context
Identified during PR #<number> review.

## Details
<finding details>

## Suggested Approach
<recommendation>

## Priority
Low - Not blocking for current implementation

---
*Created by pr-review during PR #<number>*" \
  --label "tech-debt,backlog"
```

### 6. Output

```markdown
## PR #<number>: <title>

### Scope Summary
**Original Requirements:**
- [requirement 1 from plan]
- [requirement 2 from plan]

**Implementation Coverage:**
- [x] Requirement 1: Implemented in file.py
- [x] Requirement 2: Implemented in other.py
- [ ] Requirement 3: Missing or incomplete

---

### Blocking Issues (Must Fix)
> These issues must be resolved before merge.

1. **[B1] Issue title**
   - Location: `file:line`
   - Issue: description
   - Fix: recommendation

### In-Scope Issues (Should Address)
> Related to requirements; recommended to fix in this PR.

1. **[S1] Issue title**
   - Location: `file:line`
   - Issue: description

### Suggestions (Author's Discretion)
> Nice improvements but not required.

1. **[G1]** Consider using X instead of Y in `file:line`

### Backlog (GitHub Issues Created)
> Out of scope for this PR. Tracked for future work.

1. **[#<issue>]** <issue title> - <brief reason it's out of scope>
2. **[#<issue>]** <issue title>

---

### Recommendation

**[APPROVE / APPROVE WITH CHANGES / REQUEST CHANGES]**

Rationale: [1-2 sentences explaining the decision based on scope compliance]
```

## Examples

```bash
# Review PR for current branch against its plan
/pr-review

# Review specific PR
/pr-review 42

# Review PR from URL
/pr-review https://github.com/org/repo/pull/123
```

## Notes

- Requires `gh` CLI installed and authenticated
- Creates GitHub issues for backlog items (can be disabled by declining)
- Focus is on scope compliance, not perfection
- Use `/fix-pr` after receiving feedback to address issues
