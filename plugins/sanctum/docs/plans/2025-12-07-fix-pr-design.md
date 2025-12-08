# Fix PR Command Design

**Date:** 2025-12-07
**Status:** Approved
**Command:** `/fix-pr`

## Overview

A slash command to address PR review comments by fetching feedback, triaging actionable items, implementing fixes, and resolving comments on GitHub.

## Command Interface

```
/fix-pr [<pr-number> | <pr-url>]
```

- No argument: Uses PR for current branch
- PR number: `/fix-pr 123`
- PR URL: `/fix-pr https://github.com/owner/repo/pull/123`

### Error Cases

- No PR for current branch → prompt to specify PR
- Invalid PR number/URL → report not found
- No review comments → report nothing to address

## Workflow

### Step 1: Fetch Comments

```bash
# Line-specific review comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments

# General PR comments
gh api repos/{owner}/{repo}/issues/{pr}/comments
```

### Step 2: Classify Comments

Each comment assessed as:
- **Actionable** - Clear change request
- **Informational** - No change needed
- **Ambiguous** - Unclear, needs user input

### Step 3: Triage Presentation

Compact table showing all comments with assessments:

```
PR #123: 5 review comments found

| # | File:Line | Comment | Assessment | Proposed Fix |
|---|-----------|---------|------------|--------------|
| 1 | api.py:42 | "Add error handling" | Actionable | Add try/except |
| 2 | api.py:87 | "Why dataclass?" | Informational | (skip) |

Ambiguous items:
→ #3: "Consider renaming" - Rename? [y/n/custom]

Proceed with actionable items? [y/n/modify]
```

### Step 4: Execute Fixes

For each approved fix:

1. **Gather context (adaptive)**
   - Diff hunk + 20 lines surrounding
   - Expand if comment references other files/usages

2. **Apply change** via Edit tool

3. **Track progress**
   - Show: `[2/5] Fixed: api.py:42 - Added try/except`

### Step 5: Commit Strategy

After fixes applied, prompt:
```
1. Single commit: "Address PR review feedback"
2. Separate commits per fix
3. Leave staged for manual review
```

### Step 6: Resolve on GitHub

For each fixed comment:
- Reply with concise description (e.g., "Fixed: added try/except")
- Resolve the review thread

Report unresolved items:
```
Unresolved (manual action needed):
- api.py:87 - "Why dataclass?" → Reply explaining your reasoning
```

## Dependencies

- `gh` CLI (authenticated)
- `sanctum:git-workspace-review` for workspace state

## Files

- `commands/fix-pr.md` - Slash command definition
