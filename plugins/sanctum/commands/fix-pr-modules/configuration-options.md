# Fix PR: Configuration & Options

Command options, configuration, and best practices.

> **See Also**: [Main Command](../fix-pr.md) | [Workflow Steps](workflow-steps.md) | [Troubleshooting](troubleshooting-fixes.md)

## Options Reference

| Option | Description |
|--------|-------------|
| `--dry-run` | Analyze and show planned fixes without applying |
| `--from <step>` | Start at specific step (analyze, triage, plan, fix, validate, complete) |
| `--to <step>` | Stop after specific step |
| `--scope <level>` | Set scope level (auto, minor, medium, major) |
| `--commit-strategy` | Choose commit approach (single, separate, manual) |
| `--skip-issue-linkage` | Skip issue analysis in Step 6 |
| `--close-issues` | Automatically close fully addressed issues |
| `--continue` | Resume from last incomplete phase (see Session Resumption) |
| `pr-number`/`pr-url` | Target specific PR (default: current branch)

## Enhanced Features

### 1. Smart Fix Generation

uses superpowers to understand context:

```javascript
// Comment: "Add error handling for null values"
// Superpowers analyzes:
// - Current function signature
// - Error handling patterns in codebase
// - Testing requirements
// - Performance implications

// Generated fix:
function processData(data) {
  if (!data) {
    throw new Error('Data cannot be null or undefined');
  }
  // ... rest of function
}
```

### 2. Batch Fix Operations

Groups related fixes for efficiency:

```bash
# Detects patterns:
- 5 comments about missing tests
- 3 comments about error handling
- 2 comments about documentation

# Applies fixes by batch:
1. Add all missing tests
2. Implement error handling
3. Update documentation
```

### 3. Backlog Triage

Creates GitHub issues for out-of-scope items:

```bash
gh issue create \
  --title "[Enhancement] Add caching layer" \
  --body="Identified during PR #123 review
  Consider implementing Redis caching for API responses
  Priority: Medium
  Estimated effort: 2-3 days" \
  --label="enhancement,backlog"
```

## Example Execution

```bash
# Run with default settings
/fix-pr

# Dry run to see planned changes
/fix-pr --dry-run

# Specific PR with separate commits
/fix-pr 42 --commit-strategy separate
```

### Sample Output

```markdown
PR #42: Found 12 review comments

### Triage Results
| Critical | In-Scope | Suggestions | Out-of-Scope | Informational |
|----------|----------|-------------|--------------|---------------|
| 2        | 5        | 3           | 1            | 1             |

### Fix Plan
**Critical Issues (2)**
1. [C1] api.py:45 - Add null check for user input
2. [C2] utils.py:87 - Fix SQL injection vulnerability

**In-Scope Issues (5)**
1. [S1] models.py:23 - Add validation for email format
2. [S2] views.py:156 - Handle edge case for empty lists
...

**Out-of-Scope → Creating GitHub Issues (2)**
Creating issue for: "Add detailed logging system"...
[OK] Created issue #234: feat(logging): Add detailed logging system

Creating issue for: "Add tests for feature-review skill"...
[OK] Created issue #235: test(imbue): Add detailed tests for feature-review skill

Proceed with 7 fixes? [y/n/select]
```

### Issue Linkage Output

After thread resolution, issue analysis runs:

```markdown
PR #42: Analyzing 8 open issues...

### Issue Analysis Results

**#15 - Add input validation for API endpoints**
Status: FULLY ADDRESSED
Evidence:
  - Added validation in api/validators.py (lines 45-89)
  - Tests added in tests/test_validators.py
  - All acceptance criteria met
Action: Commented and closed issue #15

**#18 - Improve error messages**
Status: PARTIALLY ADDRESSED
Evidence:
  - Updated error messages in auth module
  - Database errors still use generic messages
Remaining work:
  - [ ] Update database error messages in db/errors.py
  - [ ] Add user-friendly messages for validation failures
Action: Commented with follow-up tasks

**#22 - Refactor payment module**
Status: NOT RELATED
Evidence: No changes to payment/* files
Action: Skipped
```

### Thread Resolution Output

After fixes are applied and committed:

```markdown
### Thread Resolution Status

| Thread ID | File | Status | Action |
|-----------|------|--------|--------|
| PRRT_abc123 | api.py:45 | Replied + Resolved | "Fixed in a1b2c3d" |
| PRRT_def456 | utils.py:87 | Replied + Resolved | "Fixed in a1b2c3d" |
| PRRT_ghi789 | models.py:23 | Replied + Resolved | "Fixed in a1b2c3d" |
| PRRT_jkl012 | views.py:156 | Skipped (suggestion) | Author discretion |
| PRRT_mno345 | config.py:10 | Issue #234 created | Out of scope |
| PRRT_pqr678 | tests/ | Issue #235 created | Out of scope |

**Summary:**
- 3 threads replied to and resolved
- 1 thread skipped (optional suggestion)
- 2 out-of-scope items → GitHub issues created (#234, #235)
- 0 unresolved threads remaining
```

## Integration Benefits

### Superpowers Contributions
- **Contextual Understanding**: Analyzes code implications of each comment
- **Best Practice Application**: Suggests industry-standard solutions
- **Impact Analysis**: Identifies side effects of proposed changes
- **Test Generation**: Creates tests for new/modified code

### Sanctum Enhancements
- **GitHub Integration**: Direct thread resolution
- **Workflow Automation**: Batch operations and commit strategies
- **Backlog Management**: Systematic triage and issue creation
- **Progress Tracking**: Clear reporting of actions taken

## Error Handling

### Permission Issues
```bash
Warning: Cannot resolve threads (permission denied)
Fixes applied locally. Please resolve threads manually.
```

### Thread Resolution Failures
```bash
# If thread reply fails
Error: Failed to reply to thread {thread_id}
Fallback: Post a general PR comment referencing the fix

# If thread resolution fails
Error: Failed to resolve thread {thread_id}
Action: Document the thread ID for manual resolution
```

### Missing Thread IDs
```bash
# If GraphQL returns empty thread list
Warning: No review threads found via GraphQL
Fallback: Use REST API to fetch review comments
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments
```

### Complex Fixes
```bash
Error: Fix for comment #5 requires architectural decision
Manual intervention needed:
"Consider whether we should use factory pattern here"
```

### Conflicts
```bash
Warning: Fixes for comments 3 and 4 conflict
Comment 3: "Make function async"
Comment 4: "Remove async from function"
Manual resolution required.
```

## Configuration

```yaml
fix_pr:
  default_commit_strategy: "single"
  auto_resolve_threads: true
  create_backlog_issues: true
  batch_operations: true
  dry_run_default: false

  # Issue linkage settings
  issue_linkage:
    enabled: true                    # Enable Phase 5 issue analysis
    auto_close_issues: false         # Prompt before closing (true = auto-close)
    max_issues_to_analyze: 50        # Limit for performance
    skip_labels: ["wontfix", "duplicate"]  # Ignore issues with these labels
    require_explicit_reference: false  # If true, only match issues referenced in commits

  # Superpowers integration
  code_review_context:
    include_test_suggestions: true
    analyze_performance_impact: true
    check_security_implications: true

  # Context budget settings (new)
  context_budget:
    warn_threshold: 0.50        # Warn at 50% context usage
    checkpoint_threshold: 0.70  # Suggest checkpoint at 70%
    mandatory_phases: ["3.5", "4", "6"]  # Never skip these
```

## Context Management

### Budget Awareness

The `/fix-pr` workflow can exhaust context when:
- Many files need to be read for fixes
- Test output is verbose
- Review has many findings to address

**Context Usage Thresholds:**

| Threshold | Action |
|-----------|--------|
| 50% | Warning: "Context usage at 50%. Consider completing current phase before continuing." |
| 70% | Checkpoint: "Context usage at 70%. Recommend committing changes and using `--continue`." |
| 90% | Critical: "Context nearly exhausted. Complete current phase and resume with `/fix-pr --continue`." |

### Checkpoint/Resume Pattern

If context usage approaches 50%:
1. Complete current phase fully
2. Commit and push changes
3. Document remaining phases in a PR comment
4. Use `/clear` + `/fix-pr --continue` to resume

**Mandatory phases that MUST NOT be skipped:**
- **Phase 3.5**: Create backlog issues (deferred items must be tracked)
- **Phase 4**: Thread resolution (reviewer expects responses)
- **Phase 6**: Summary comment (documents what was done)

### Session Resumption (`--continue`)

The `--continue` flag detects previous `/fix-pr` execution and resumes from the first incomplete phase.

**Resume Detection Logic:**

```bash
# Check for completion markers in PR comments
PHASE_6_DONE=$(gh pr view $PR --json comments --jq '.comments[].body | contains("PR Review Feedback Addressed")')
PHASE_3_5_DONE=$(gh pr view $PR --json comments --jq '.comments[].body | contains("Backlog → Issues") or contains("Deferred Items Created")')

# Resume from first incomplete phase
if [ "$PHASE_6_DONE" = "false" ]; then
  if [ "$PHASE_3_5_DONE" = "false" ]; then
    echo "Resuming from Phase 3.5 (backlog issue creation)"
  else
    echo "Resuming from Phase 6 (summary comment)"
  fi
fi
```

**Phase Completion Markers:**

| Phase | Marker in PR Comments |
|-------|----------------------|
| Phase 3.5 | "Backlog → Issues" or "Deferred Items Created" |
| Phase 4 | "Thread Resolution Status" or all threads resolved |
| Phase 6 | "PR Review Feedback Addressed" |

**Example Resume Scenarios:**

```bash
# Context exhausted after Phase 3
/clear
/fix-pr 123 --continue
# Detects: Phase 3.5 not done, resumes there

# Session timeout after Phase 4
/fix-pr 123 --continue
# Detects: Phase 6 not done, resumes there

# Interrupted during fixes
/fix-pr 123 --continue
# Detects: No phases marked complete, re-runs from analyze
```
