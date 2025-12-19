# Phase 1: Issue Discovery

Parse input arguments and retrieve issue content from GitHub.

## Input Formats

The command accepts flexible input:

```bash
# Single issue number
/fix-issue 42

# GitHub issue URL
/fix-issue https://github.com/owner/repo/issues/42

# Multiple issues (space-delimited)
/fix-issue 42 43 44

# Mixed formats
/fix-issue 42 https://github.com/owner/repo/issues/43
```

## Retrieve Issue Content

For each issue, fetch the full content:

```bash
# By number (uses current repo)
gh issue view 42 --json title,body,labels,assignees,comments

# By URL (extracts owner/repo/number)
gh issue view https://github.com/owner/repo/issues/42 --json title,body,labels,assignees,comments
```

## Extract Requirements

From each issue body, identify:

| Category | Look For |
|----------|----------|
| **Acceptance Criteria** | Checkboxes, "should", "must" statements |
| **Technical Requirements** | Code references, API specs, constraints |
| **Test Expectations** | Expected behavior, edge cases |
| **Dependencies** | Related issues, blocking items |

## Example Output

```
Fetching issue #42...
Title: Add user authentication
Requirements identified: 4
  - Acceptance Criteria: 2
  - Technical Requirements: 1
  - Test Expectations: 1
Tasks will be generated: 3
```

## Next Phase

After discovery, proceed to [task-planning.md](task-planning.md) for dependency analysis and task breakdown.
