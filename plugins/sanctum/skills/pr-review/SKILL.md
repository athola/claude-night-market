---
name: pr-review
description: Scope-focused PR code review that validates against original requirements and routes out-of-scope findings to GitHub issues. Prevents overengineering by distinguishing blocking issues from backlog items.
category: review
tags: [pr, review, scope, github, code-quality]
tools: [gh, pensive:unified-review]
usage_patterns:
  - scope-validation
  - backlog-triage
  - requirement-compliance
complexity: intermediate
estimated_tokens: 500
progressive_loading: true
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
  - pensive:unified-review
  - imbue:evidence-logging
---

# Scope-Focused PR Review

Review pull requests with discipline: validate against original requirements, prevent scope creep, and route out-of-scope findings to GitHub issues.

## Core Principle

**A PR review validates scope compliance, not code perfection.**

The goal is to ensure the implementation meets its stated requirements without introducing regressions. Improvements beyond the scope belong in future PRs.

## When to Use

- Before merging any feature branch
- When reviewing PRs from teammates
- To validate your own work before requesting review
- To generate a backlog of improvements discovered during review

## Scope Classification Framework

Every finding must be classified:

| Category | Definition | Action |
|----------|------------|--------|
| **BLOCKING** | Bug, security issue, or regression introduced by this change | Must fix before merge |
| **IN-SCOPE** | Issue directly related to stated requirements | Should address in this PR |
| **SUGGESTION** | Improvement within changed code, not required | Author decides |
| **BACKLOG** | Good idea but outside PR scope | Create GitHub issue |
| **IGNORE** | Nitpick, style preference, or not worth tracking | Skip entirely |

### Classification Examples

**BLOCKING:**
- Null pointer exception in new code path
- SQL injection in new endpoint
- Breaking change to public API without migration
- Test that was passing now fails

**IN-SCOPE:**
- Missing error handling specified in requirements
- Feature doesn't match spec behavior
- Incomplete implementation of planned functionality

**SUGGESTION:**
- Better variable name in changed function
- Slightly more efficient algorithm
- Additional edge case test

**BACKLOG:**
- Refactoring opportunity in adjacent code
- "While we're here" improvements
- Technical debt in files touched but not changed
- Features sparked by seeing the code

**IGNORE:**
- Personal style preferences
- Theoretical improvements with no practical impact
- Premature optimization suggestions

## Workflow

### Phase 1: Establish Scope Baseline

Before looking at ANY code, understand what this PR is supposed to accomplish.

**Search for scope artifacts in order:**

1. **Plan file**: Most authoritative
   ```bash
   ls docs/plans/ 2>/dev/null
   cat plan.md 2>/dev/null | head -100
   ```

2. **Spec file**: Requirements definition
   ```bash
   cat spec.md 2>/dev/null | head -100
   ```

3. **Tasks file**: Implementation checklist
   ```bash
   cat tasks.md 2>/dev/null
   ```

4. **PR description**: Author's intent
   ```bash
   gh pr view <number> --json body --jq '.body'
   ```

5. **Commit messages**: Incremental decisions
   ```bash
   gh pr view <number> --json commits --jq '.commits[].messageHeadline'
   ```

**Output:** A clear statement of scope:
> "This PR implements [feature X] as specified in plan.md. The requirements are:
> 1. [requirement]
> 2. [requirement]
> 3. [requirement]"

If no scope artifacts exist, flag this as a process issue but continue with PR description as the baseline.

### Phase 2: Gather Changes

```bash
# Changed files list
gh pr diff <number> --name-only

# Full diff
gh pr diff <number>

# Statistics
gh pr view <number> --json additions,deletions,changedFiles,commits
```

### Phase 3: Requirements Validation

Before detailed code review, check scope coverage:

- [ ] Each requirement has corresponding implementation
- [ ] No requirements are missing
- [ ] Implementation doesn't exceed requirements (overengineering signal)

### Phase 4: Code Review with Scope Context

Use `pensive:unified-review` on the changed files.

**Critical:** Evaluate each finding against the scope baseline:

```
Finding: "Function X lacks input validation"
Scope check: Is input validation mentioned in requirements?
  - YES → IN-SCOPE
  - NO, but it's a security issue → BLOCKING
  - NO, and it's a nice-to-have → BACKLOG
```

### Phase 5: Backlog Triage

For each BACKLOG item, create a GitHub issue:

```bash
gh issue create \
  --title "[Tech Debt] Brief description" \
  --body "## Context
Identified during PR #<number> review.

## Details
<what the improvement would address>

## Suggested Approach
<how to implement>

## Priority
Low - Improvement opportunity, not blocking

---
*Auto-created by pr-review*" \
  --label "tech-debt"
```

**Ask user before creating:** "I found N backlog items. Create GitHub issues? [y/n/select]"

### Phase 6: Generate Report

Structure the report by classification:

```markdown
## PR #X: Title

### Scope Compliance
**Requirements:** (from plan/spec)
1. [x] Requirement A - Implemented
2. [x] Requirement B - Implemented
3. [ ] Requirement C - **Missing**

### Blocking (0)
None - no critical issues found.

### In-Scope (2)
1. [S1] Missing validation for edge case
   - Location: api.py:45
   - Requirement: "Handle empty input gracefully"

### Suggestions (1)
1. [G1] Consider extracting helper function
   - Author's discretion

### Backlog → GitHub Issues (3)
1. #142 - Refactor authentication module
2. #143 - Add caching layer
3. #144 - Update deprecated dependency

### Recommendation
**APPROVE WITH CHANGES**
Address S1 (in-scope issue) before merge.
```

## Quality Gates

A PR should be approved when:
- [ ] All stated requirements are implemented
- [ ] No BLOCKING issues remain
- [ ] IN-SCOPE issues are resolved or acknowledged
- [ ] BACKLOG items are tracked as GitHub issues
- [ ] Tests cover new code paths

## Anti-Patterns to Avoid

### Don't: Scope Creep Review
> "While you're here, you should also refactor X, add feature Y, and fix Z in adjacent files."

**Do:** Create backlog issues, keep PR focused.

### Don't: Perfect is Enemy of Good
> "This works but could be 5% more efficient with different approach."

**Do:** If it meets requirements and has no bugs, it's ready.

### Don't: Blocking on Style
> "I prefer tabs over spaces."

**Do:** Use linters for style, reserve review for logic.

### Don't: Reviewing Unchanged Code
> "The file you imported from has some issues..."

**Do:** That's a separate PR. Create an issue if important.

## Integration with Other Tools

- **`/fix-pr`**: After review identifies issues, use this to address them
- **`/pr`**: To prepare a PR before review
- **`pensive:unified-review`**: For the actual code analysis
- **`pensive:bug-review`**: For deeper bug hunting if needed

## Exit Criteria

- Scope baseline established
- All changes reviewed against scope
- Findings classified correctly
- Backlog items tracked as issues
- Clear recommendation provided
