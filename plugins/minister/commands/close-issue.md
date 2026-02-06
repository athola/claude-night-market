---
name: close-issue
description: Analyze if GitHub issues can be closed based on commits
usage: /close-issue <issue-ref>... [--dry-run]
---

# Close Issue Analysis

Researches commits and codebase to determine if linked GitHub issues can be closed based on existing changes. For incomplete issues, reports gaps with specific tasks and offers to work on them immediately.

## When To Use

Use this command when you need to:
- Determining if issues are complete based on commits
- Finding remaining work for incomplete issues

## Arguments

- `<issue-ref>` - One or more issue references:
  - Issue number: `21`
  - Full URL: `https://github.com/owner/repo/issues/21`
  - Short reference: `owner/repo#21`
- `--dry-run` - Analyze only, skip interactive prompts

## Workflow

### Phase 1: Parse & Group Issues

1. **Parse Issue References**

   For each argument, determine the format and extract `(owner, repo, number)`:

   ```bash
   # Get current repo context for bare numbers
   gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
   ```

   **Parsing Rules:**
   - Bare number (`21`) → Use current repo
   - Full URL → Extract from path
   - Short ref (`owner/repo#21`) → Parse directly

2. **Group by Repository**

   Group issues by `owner/repo` for efficient batch analysis. Issues in the same repo share commit history analysis.

3. **Validate Issues Exist**

   ```bash
   # For each issue
   gh issue view <number> --repo <owner/repo> --json number,title,body,state,labels
   ```

   If issue doesn't exist or is already closed, report and skip.

### Phase 2: Gather Evidence (Per Repo Group)

For each repository group, gather evidence in parallel where possible.

#### 2a. Commit Analysis

Search for commits that reference the issue:

```bash
# Search by issue number patterns
git log --all --oneline --grep="#<number>" -i
git log --all --oneline --grep="issue <number>" -i
git log --all --oneline --grep="<owner>/<repo>/issues/<number>"
git log --all --oneline --grep="closes <number>" -i
git log --all --oneline --grep="fixes <number>" -i

# For each found commit, get details
git show <sha> --stat --format="%H %s"
```

Record:
- Commit SHA and message
- Files changed
- Whether commit explicitly closes/fixes the issue

#### 2b. Codebase Analysis

Use an Explore agent to search the codebase for implementations related to the issue:

```
Spawn an Explore agent with the following task:

Analyze issue #<number> from <owner>/<repo>:

Title: <issue_title>
Body: <issue_body>

Extract acceptance criteria from the issue body (look for checkboxes, "should", "must", numbered lists).

Search the codebase for evidence that each criterion is implemented:
- Look for related function/class names
- Search for comments referencing the issue
- Check test files for related test cases
- Examine recently modified files

Return structured findings:
{
  "criteria": [
    {
      "description": "Track skills used together",
      "status": "met|partial|missing",
      "evidence": ["file:line - description", ...]
    }
  ],
  "related_files": ["path/to/file.py", ...],
  "confidence": "high|medium|low"
}
```

For multiple repo groups, spawn Explore agents in parallel using the Task tool.

### Phase 3: Verdict Determination

For each issue, synthesize commit and codebase evidence into a verdict:

| Verdict | Criteria |
|---------|----------|
| **READY TO CLOSE** | All acceptance criteria met with evidence |
| **PARTIALLY DONE** | Some criteria met, clear gaps identified |
| **NOT STARTED** | No commits or code evidence found |
| **UNCLEAR** | Issue lacks clear acceptance criteria |

**Verdict Logic:**
```
if all criteria have status "met":
    verdict = "READY TO CLOSE"
elif any criteria have status "met":
    verdict = "PARTIALLY DONE"
elif no evidence found:
    verdict = "NOT STARTED"
else:
    verdict = "UNCLEAR"
```

### Phase 4: Generate Report

Present findings in a consolidated report with per-issue sections.

#### Report Template

```markdown
# Issue Analysis Report

## Summary

| Issue | Title | Verdict |
|-------|-------|---------|
| #21 | Enhance MCP analytics | READY TO CLOSE |
| #22 | Fix validation bug | PARTIALLY DONE |

---

## #21: Enhance MCP analytics

**Repo:** athola/skrills
**Verdict:** READY TO CLOSE

### Commits (3)
- `a1b2c3d` feat(mcp): add skill co-occurrence tracking
- `e4f5g6h` feat(mcp): implement recommend-skills tool
- `i7j8k9l` feat(mcp): add metrics endpoint

### Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Track skills used together | Met | `src/mcp/analytics.py:45-89` |
| Provide recommend-skills tool | Met | `src/mcp/tools/recommend.py` |
| Add metrics endpoint | Met | `src/mcp/api/metrics.py` |

---

## #22: Fix validation bug

**Repo:** athola/skrills
**Verdict:** PARTIALLY DONE (1/3 criteria)

### Commits (1)
- `x1y2z3a` fix: add null check for user input

### Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Validate user input | Met | `src/api/validators.py:23` |
| Add error messages | Missing | - |
| Add unit tests | Missing | - |

### Remaining Tasks

1. **Add user-friendly error messages**
   - Update `src/api/validators.py` to return descriptive errors
   - Follow error message patterns in `src/api/errors.py`

2. **Add unit tests for validation**
   - Create tests in `tests/test_validators.py`
   - Cover null, empty, and invalid format cases
```

### Phase 5: Interactive Prompt

After presenting the report, prompt the user based on verdicts found.

#### If any issues are READY TO CLOSE:

```
Use the AskUserQuestion tool:

Question: "Close these issues?"
Options:
- "Yes, close all ready issues (Recommended)" - Close via gh issue close
- "Review individually" - Prompt per issue
- "No, just report" - End without closing
```

If user chooses to close:
```bash
gh issue close <number> --repo <owner/repo> --reason completed --comment "Closed via /close-issue analysis. All acceptance criteria verified as met."
```

#### If any issues are PARTIALLY DONE or NOT STARTED:

```
Use the AskUserQuestion tool:

Question: "Work on remaining tasks now?"
Options:
- "Yes, fix now (Recommended)" - Create TodoWrite items and begin work
- "Defer to later" - End with report only
```

If user chooses "fix now":
1. Create TodoWrite items for each remaining task
2. Begin working through them systematically
3. After completion, re-run analysis to verify

## Options

- `--dry-run`: Skip interactive prompts, only output the report

## Error Handling

### Issue Not Found
```markdown
Warning: Issue #99 not found in athola/skrills
Skipping this issue.
```

### Issue Already Closed
```markdown
Info: Issue #21 is already closed (completed on 2025-12-15)
Skipping analysis.
```

### No Acceptance Criteria Found
```markdown
## #21: Vague feature request

**Verdict:** UNCLEAR

The issue body doesn't contain clear acceptance criteria.
Consider updating the issue with specific requirements before analysis.

Suggested criteria based on title:
- [ ] [Inferred criterion 1]
- [ ] [Inferred criterion 2]
```

### Cross-Repo Without Access
```markdown
Error: Cannot access other-org/private-repo
validate you have read access to analyze issues from this repository.
```

## Examples

### Single Issue - Ready to Close
```bash
$ /close-issue 21

# Issue Analysis Report

## #21: Add user authentication

**Verdict:** READY TO CLOSE

All 4 acceptance criteria met with commit evidence.

**Close this issue?** [y/n]
> y

Closed issue #21 with comment.
```

### Multiple Issues - Mixed Verdicts
```bash
$ /close-issue 21 22 23

# Issue Analysis Report

| Issue | Verdict |
|-------|---------|
| #21 | READY TO CLOSE |
| #22 | PARTIALLY DONE |
| #23 | NOT STARTED |

[Detailed sections follow...]

**Close #21?** [y/n] > y
**Work on #22 tasks now?** [fix/defer] > fix

Creating tasks for #22...
[TodoWrite items created, work begins]
```

### Dry Run
```bash
$ /close-issue 21 22 --dry-run

# Issue Analysis Report
[Full report without prompts]
```

## Integration Notes

### Relationship to /fix-pr

| Command | Scope | Question |
|---------|-------|----------|
| `/fix-pr` Phase 5 | PR-centric | "What issues does this PR close?" |
| `/close-issue` | Issue-centric | "Is this specific issue done?" |

Use `/fix-pr` when finishing a PR. Use `/close-issue` for ad-hoc issue status checks.

### Subagent Parallelization

For multi-repo issue sets, the command spawns Explore agents in parallel:
- One agent per repository group
- Main thread coordinates and merges results
- Improves performance for cross-repo analysis

## See Also

- `/fix-pr` - PR workflow with issue linkage (Phase 5)
- `minister:github-initiative-pulse` - Initiative status snapshots
- `minister:release-health-gates` - Release readiness checks
