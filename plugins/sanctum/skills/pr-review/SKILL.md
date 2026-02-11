---
name: pr-review
description: 'Use this skill for scope-focused PR reviews. Use when reviewing PRs,
  validating against requirements, triaging findings to backlog, preventing overengineering.
  Do not use when preparing PRs - use pr-prep instead. DO NOT use when: deep code
  review - use pensive:unified-review.'
category: review
tags:
- pr
- review
- scope
- github
- gitlab
- code-quality
- knowledge-capture
- cross-platform
tools:
- gh / glab (platform-detected)
- pensive:unified-review
usage_patterns:
- scope-validation
- backlog-triage
- requirement-compliance
- knowledge-capture
complexity: intermediate
estimated_tokens: 500
progressive_loading: true
modules:
- knowledge-capture.md
- version-validation.md
dependencies:
- leyline:git-platform
- sanctum:shared
- sanctum:git-workspace-review
- sanctum:version-updates
- pensive:unified-review
- imbue:evidence-logging
- memory-palace:review-chamber
- scribe:slop-detector
- scribe:doc-generator
---
## Table of Contents

- [Core Principle](#core-principle)
- [When to Use](#when-to-use)
- [Scope Classification Framework](#scope-classification-framework)
- [Classification Examples](#classification-examples)
- [Workflow](#workflow)
- [Phase 1: Establish Scope Baseline](#phase-1-establish-scope-baseline)
- [Phase 2: Gather Changes](#phase-2-gather-changes)
- [Phase 3: Requirements Validation](#phase-3-requirements-validation)
- [Phase 1.5: Version Validation (MANDATORY)](#phase-15-version-validation-mandatory)
- [Phase 4: Code Review with Scope Context](#phase-4-code-review-with-scope-context)
- [Phase 5: Backlog Triage](#phase-5-backlog-triage)
- [Phase 6: Generate Report](#phase-6-generate-report)
- [Phase 7: Knowledge Capture](#phase-7-knowledge-capture)
- [Quality Gates](#quality-gates)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Don't: Scope Creep Review](#dont-scope-creep-review)
- [Don't: Perfect is Enemy of Good](#dont-perfect-is-enemy-of-good)
- [Don't: Blocking on Style](#dont-blocking-on-style)
- [Don't: Reviewing Unchanged Code](#dont-reviewing-unchanged-code)
- [Integration with Other Tools](#integration-with-other-tools)
- [Exit Criteria](#exit-criteria)


# Scope-Focused PR Review

Review pull/merge requests with discipline: validate against original requirements, prevent scope creep, and route out-of-scope findings to issues on the detected platform.

**Platform detection is automatic** via `leyline:git-platform`. Use `gh` for GitHub, `glab` for GitLab. Check session context for `git_platform:`.

## Core Principle

**A PR review validates scope compliance, not code perfection.**

The goal is to validate the implementation meets its stated requirements without introducing regressions. Improvements beyond the scope belong in future PRs.

## When To Use

- Before merging any feature branch
- When reviewing PRs from teammates
- To validate your own work before requesting review
- To generate a backlog of improvements discovered during review

## When NOT To Use

- Preparing PRs - use pr-prep instead
- Deep code
  review - use pensive:unified-review
- Preparing PRs - use pr-prep instead
- Deep code
  review - use pensive:unified-review

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

**Note:** Version validation (Phase 1.5) runs AFTER scope establishment but BEFORE code review. See `modules/version-validation.md` for details.

**Search for scope artifacts in order:**

1. **Plan file**: Most authoritative (check spec-kit locations first, then root)
   ```bash
   # Spec-kit feature plans (preferred - structured implementation blueprints)
   find specs -name "plan.md" -type f 2>/dev/null | head -1 | xargs cat 2>/dev/null | head -100
   # Legacy/alternative locations
   ls docs/plans/ 2>/dev/null
   # Root plan.md (may be Claude Plan Mode artifact from v2.0.51+)
   cat plan.md 2>/dev/null | head -100
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

2. **Spec file**: Requirements definition (check spec-kit locations first)
   ```bash
   find specs -name "spec.md" -type f 2>/dev/null | head -1 | xargs cat 2>/dev/null | head -100
   cat spec.md 2>/dev/null | head -100
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

3. **Tasks file**: Implementation checklist (check spec-kit locations first)
   ```bash
   find specs -name "tasks.md" -type f 2>/dev/null | head -1 | xargs cat 2>/dev/null
   cat tasks.md 2>/dev/null
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

4. **PR/MR description**: Author's intent
   ```bash
   # GitHub
   gh pr view <number> --json body --jq '.body'
   # GitLab
   glab mr view <number> --json description --jq '.description'
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

5. **Commit messages**: Incremental decisions
   ```bash
   # GitHub
   gh pr view <number> --json commits --jq '.commits[].messageHeadline'
   # GitLab
   glab mr view <number> --json commits
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

**Output:** A clear statement of scope:
> "This PR implements [feature X] as specified in plan.md. The requirements are:
> 1. [requirement]
> 2. [requirement]
> 3. [requirement]"

If no scope artifacts exist, flag this as a process issue but continue with PR description as the baseline.

### Phase 2: Gather Changes

```bash
# GitHub
gh pr diff <number> --name-only
gh pr diff <number>
gh pr view <number> --json additions,deletions,changedFiles,commits

# GitLab
glab mr diff <number>
glab mr view <number>
```
**Verification:** Run the command with `--help` flag to verify availability.

### Phase 3: Requirements Validation

Before detailed code review, check scope coverage:

- [ ] Each requirement has corresponding implementation
- [ ] No requirements are missing
- [ ] Implementation doesn't exceed requirements (overengineering signal)

### Phase 1.5: Version Validation (MANDATORY)

**Run version validation checks BEFORE code review.**

See `modules/version-validation.md` for detailed validation procedures.

**Quick reference:**
1. Check if bypass requested (`--skip-version-check`, label, or PR marker)
2. Detect if version files changed in PR diff
3. If changed, run project-specific validations:
   - Claude marketplace: Check marketplace.json vs plugin.json versions
   - Python: Check pyproject.toml vs __version__
   - Node: Check package.json vs package-lock.json
   - Rust: Check Cargo.toml vs Cargo.lock
4. Validate CHANGELOG has entry for new version
5. Check README/docs for version references
6. Classify findings as BLOCKING (or WAIVED if bypassed)

**All version mismatches are BLOCKING unless explicitly waived by maintainer.**

### Phase 4: Code Review with Scope Context

Use `pensive:unified-review` on the changed files. For comment quality assessment, see `modules/comment-guidelines.md`.

**Critical:** Evaluate each finding against the scope baseline:

```
**Verification:** Run the command with `--help` flag to verify availability.
Finding: "Function X lacks input validation"
Scope check: Is input validation mentioned in requirements?
  - YES → IN-SCOPE
  - NO, but it's a security issue → BLOCKING
  - NO, and it's a nice-to-have → BACKLOG
```
**Verification:** Run the command with `--help` flag to verify availability.

### Phase 5: Backlog Triage

For each BACKLOG item, create an issue on the detected platform:

```bash
# GitHub
gh issue create \
  --title "[Tech Debt] Brief description" \
  --body "## Context
Identified during PR #<number> review.
..." \
  --label "tech-debt"

# GitLab
glab issue create \
  --title "[Tech Debt] Brief description" \
  --description "## Context
Identified during MR !<number> review.
..." \
  --label "tech-debt"
```
**Verification:** Run the command with `--help` flag to verify availability.

**Ask user before creating:** "I found N backlog items. Create issues? [y/n/select]"

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
**Verification:** Run the command with `--help` flag to verify availability.

### Phase 7: Knowledge Capture

After generating the report, evaluate findings for knowledge capture into the project's review chamber.

**Trigger:** Automatically for findings scoring ≥60 on evaluation criteria.

```bash
# Capture significant findings to review-chamber
# Uses memory-palace:review-chamber evaluation framework
```
**Verification:** Run the command with `--help` flag to verify availability.

**Candidates for capture:**
- BLOCKING findings with architectural context → `decisions/`
- Recurring patterns seen in multiple PRs → `patterns/`
- Quality standards and conventions → `standards/`
- Post-mortem insights and learnings → `lessons/`

**Output:** Add to report:
```markdown
### Knowledge Captured 📚

| Entry ID | Title | Room |
|----------|-------|------|
| abc123 | JWT over sessions | decisions/ |
| def456 | Token refresh pattern | patterns/ |

View: `/review-room list --palace <project>`
```
**Verification:** Run the command with `--help` flag to verify availability.

See `modules/knowledge-capture.md` for full workflow.

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
- **`scribe:slop-detector`**: For documentation AND commit message quality analysis
- **`scribe:doc-generator`**: For PR description writing guidelines (slop-free)

## Slop Detection Integration

### Documentation Review
For all changed `.md` files, invoke `Skill(scribe:slop-detector)`:
- Score ≥ 3.0: Flag as IN-SCOPE (should remediate)
- Score ≥ 5.0: Flag as BLOCKING if `--strict` mode

### Commit Message Review
Scan all PR commit messages for slop markers:
```bash
gh pr view <number> --json commits --jq '.commits[].messageBody' | \
  grep -iE 'leverage|seamless|comprehensive|delve|robust|utilize|facilitate'
```
If slop found in commits: Add to SUGGESTION category with remediation guidance.

### PR Description Review
Apply `scribe:slop-detector` to PR body:
- Tier 1 words in description → SUGGESTION to rephrase
- Marketing phrases ("unlock potential") → Flag for removal

## Exit Criteria

- Scope baseline established
- All changes reviewed against scope
- Findings classified correctly
- Backlog items tracked as issues
- Clear recommendation provided

## Supporting Modules

- [GitHub PR comment patterns](modules/github-comments.md) - `gh api` patterns for inline and summary PR comments

## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
