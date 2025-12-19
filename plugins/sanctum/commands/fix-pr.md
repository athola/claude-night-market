---
name: fix-pr
description: Enhanced PR fix workflow that combines superpowers:receiving-code-review analysis with Sanctum's GitHub integration for systematic review comment resolution
usage: /fix-pr [<pr-number> | <pr-url>] [--dry-run] [--commit-strategy single|separate|manual]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Fix

Integrates superpowers:receiving-code-review analysis capabilities with Sanctum's robust GitHub integration to systematically address PR review comments and automate resolution workflows.

## Key Enhancements Over Base Commands

- **Intelligent Comment Triage**: Uses code review analysis to classify feedback
- **Automated Fix Suggestions**: Leverages superpowers for generating fixes
- **GitHub Thread Resolution**: Automatically resolves threads when fixes are applied
- **Commit Strategy Options**: Flexible commit approaches for different workflows
- **Backlog Item Creation**: Routes out-of-scope feedback to GitHub issues

## When to Use

- Addressing PR review comments systematically
- Automating repetitive review feedback resolution
- Managing large PRs with many review comments
- Ensuring all feedback is properly categorized and addressed

## Workflow

### Phase 1: Discovery & Analysis

1. **Identify Target PR**
   ```bash
   # Current branch or specified PR
   gh pr view --json number,url,headRefName
   ```

2. **Fetch Review Context**
   ```bash
   # Get unresolved review threads (GraphQL)
   gh api graphql -f query='...'
   # Get general issue comments
   gh api repos/{owner}/{repo}/issues/{pr_number}/comments
   ```

3. **Analyze with Superpowers**
   ```bash
   Skill(superpowers:receiving-code-review)
   ```
   - Analyzes code context for each comment
   - Suggests specific fixes
   - Classifies feedback by impact and scope

### Phase 2: Intelligent Triage

4. **Classify Comments**

   | Type | Description | Action |
   |------|-------------|--------|
   | **Critical** | Bugs, security issues | Fix immediately |
   | **In-Scope** | Requirements-related | Address in this PR |
   | **Suggestion** | Improvements | Author's discretion |
   | **Out-of-Scope** | Future work | Create GitHub issue |
   | **Informational** | Questions, praise | Reply only |

5. **Generate Fix Strategies**
   - For each actionable comment, superpowers analyzes:
     - Code context around comment location
     - Best practices for the suggested change
     - Impact on related code
     - Test implications

### Phase 3: Execution

6. **Apply Fixes Systematically**
   ```bash
   # For each approved fix:
   1. Read code context (±20 lines)
   2. Apply fix with Edit tool
   3. Verify no new issues introduced
   4. Mark as completed
   ```

7. **Commit with Strategy**
   - **Single**: "Address PR review feedback"
   - **Separate**: One commit per fix category
   - **Manual**: Stage changes, user commits

### Phase 4: Thread Resolution (MANDATORY)

**CRITICAL: You MUST reply to and resolve each review thread after fixing. This is not optional.**

> **Important:** Thread IDs (format: `PRRT_*`) are different from comment IDs. You need thread IDs for both replies and resolution.

8. **Get All Review Threads**
   ```bash
   # Fetch all review threads with their IDs and resolution status
   # Note: Use literal owner/repo/pr values - do NOT use $() substitution inside gh commands
   gh api graphql -f query='
   query {
     repository(owner: "OWNER", name: "REPO") {
       pullRequest(number: PR_NUMBER) {
         reviewThreads(first: 100) {
           nodes {
             id
             isResolved
             path
             line
             comments(first: 1) {
               nodes {
                 body
                 author { login }
               }
             }
           }
         }
       }
     }
   }'
   ```

   Replace `OWNER`, `REPO`, and `PR_NUMBER` with actual values. The thread `id` field returns the `PRRT_*` ID needed for replies and resolution.

9. **Reply to Each Thread with Fix Description**
   For EACH review comment that was addressed, use the GraphQL mutation (NOT REST API):
   ```bash
   # Reply using addPullRequestReviewThreadReply mutation
   # The pullRequestReviewThreadId is the PRRT_* ID from step 8
   gh api graphql -f query='
   mutation {
     addPullRequestReviewThreadReply(input: {
       pullRequestReviewThreadId: "PRRT_kwDOxxxxxx"
       body: "Fixed - added input validation for slug parameter. Rejects injection characters."
     }) {
       comment { id }
     }
   }'
   ```

   **Reply format requirements:**
   - Use "Fixed" prefix for fixed items
   - Briefly describe what was changed
   - Reference the file/line if helpful
   - Keep it concise (1-2 sentences)

   **Common mistakes to avoid:**
   - Do NOT use `addPullRequestReviewComment` - it lacks thread support
   - Do NOT use REST API `/comments/{id}/replies` - it doesn't work for review threads
   - Use `addPullRequestReviewThreadReply` with the `PRRT_*` thread ID

10. **Resolve the Thread**
    After replying, resolve the thread:
    ```bash
    # Resolve the review thread via GraphQL mutation
    gh api graphql -f query='
    mutation {
      resolveReviewThread(input: {threadId: "PRRT_kwDOxxxxxx"}) {
        thread { isResolved }
      }
    }'
    ```

    **Batch resolution pattern:**
    ```bash
    # Resolve multiple threads in a loop
    for thread_id in PRRT_abc123 PRRT_def456 PRRT_ghi789; do
      gh api graphql -f query="
    mutation {
      resolveReviewThread(input: {threadId: \"$thread_id\"}) {
        thread { isResolved }
      }
    }"
    done
    ```

11. **Verify All Threads Resolved**
    ```bash
    # Count unresolved threads - should return 0
    gh api graphql -f query='
    query {
      repository(owner: "OWNER", name: "REPO") {
        pullRequest(number: PR_NUMBER) {
          reviewThreads(first: 100) {
            nodes {
              isResolved
              path
            }
          }
        }
      }
    }' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
    ```

**Thread Resolution Checklist:**
- [ ] Retrieved all review thread IDs (format: `PRRT_*`)
- [ ] Replied to each addressed thread using `addPullRequestReviewThreadReply`
- [ ] Resolved each thread via `resolveReviewThread` mutation
- [ ] Verified no unresolved threads remain (or documented why)

### Phase 5: Issue Linkage & Closure

After resolving review threads, analyze whether this PR addresses any open issues.

12. **Fetch Open Issues**
    ```bash
    # Get all open issues for the repository
    gh issue list --state open --json number,title,body,labels --limit 50
    ```

13. **Analyze Issue Coverage**

    For each open issue, analyze whether the PR's changes address it:

    ```bash
    # Get PR changed files and commit messages
    gh pr view --json files,commits -q '{files: .files[].path, commits: .commits[].messageHeadline}'

    # Compare against issue requirements:
    # - Extract acceptance criteria from issue body
    # - Check if changed files relate to issue scope
    # - Review commit messages for issue references
    ```

    **Classification:**
    | Status | Criteria | Action |
    |--------|----------|--------|
    | **Fully Addressed** | All acceptance criteria met, all required changes made | Comment + Close |
    | **Partially Addressed** | Some criteria met, some work remaining | Comment with follow-up details |
    | **Not Related** | PR doesn't touch issue scope | Skip |

14. **Comment on Fully Addressed Issues**
    ```bash
    gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
    ## Addressed in PR #PR_NUMBER

    This issue has been fully addressed by the linked pull request.

    **Changes made:**
    - [List specific changes that address the issue]

    **Files modified:**
    - `path/to/file.py`
    - `path/to/another.py`

    Closing this issue. The fix will be available after PR merge.
    EOF
    )"

    # Close the issue
    gh issue close ISSUE_NUMBER --reason completed
    ```

15. **Comment on Partially Addressed Issues**
    ```bash
    gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
    ## Partially Addressed in PR #PR_NUMBER

    This PR addresses some aspects of this issue but additional work is needed.

    **What was addressed:**
    - [List completed items]

    **What still needs to be done (follow-up PR):**
    - [ ] [Remaining task 1]
    - [ ] [Remaining task 2]
    - [ ] [Remaining task 3]

    **Suggested next steps:**
    1. Create follow-up branch from main after this PR merges
    2. Address remaining items listed above
    3. Reference this issue in the follow-up PR

    Keeping this issue open until fully resolved.
    EOF
    )"
    ```

16. **Generate Issue Linkage Report**
    ```markdown
    ### Issue Linkage Summary

    | Issue | Title | Status | Action Taken |
    |-------|-------|--------|--------------|
    | #42 | Add user authentication | Fully Addressed | Commented + Closed |
    | #43 | Fix validation bugs | Partially Addressed | Commented (3 items remaining) |
    | #44 | Improve performance | Not Related | Skipped |

    **Closed Issues:** 1
    **Partially Addressed:** 1 (follow-up items documented)
    **Not Related:** 1
    ```

**Issue Linkage Checklist:**
- [ ] Fetched all open issues for the repository
- [ ] Analyzed PR changes against each issue's requirements
- [ ] Commented on and closed fully addressed issues
- [ ] Documented remaining work for partially addressed issues
- [ ] Generated linkage summary report

## Options

- `--dry-run`: Analyze and show planned fixes without applying
- `--commit-strategy`: Choose commit approach (default: single)
- `--skip-issue-linkage`: Skip Phase 5 issue analysis (faster execution)
- `--close-issues`: Automatically close fully addressed issues (default: prompt)
- `pr-number`/`pr-url`: Target specific PR (default: current branch)

## Enhanced Features

### 1. Smart Fix Generation

Leverages superpowers to understand context:

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

**Out-of-Scope → GitHub Issues (1)**
1. #234 - Add comprehensive logging system

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
| PRRT_mno345 | config.py:10 | Created Issue #234 | Out of scope |

**Summary:**
- 3 threads replied to and resolved
- 1 thread skipped (optional suggestion)
- 1 thread triaged to backlog issue
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
```

## Best Practices

### Before Running
1. Ensure clean working directory
2. Pull latest changes from remote
3. Confirm PR is still open
4. Check for merge conflicts

### During Execution
1. Review proposed fixes before applying
2. Monitor for unexpected side effects
3. Keep detailed logs of changes made
4. Verify tests still pass after each batch

### After Completion
1. Push changes to remote
2. **VERIFY all threads have replies** - each addressed comment must have a response
3. **VERIFY all threads are resolved** - run the verification query from Phase 4
4. Check CI pipeline status
5. Notify reviewers of updates
6. If any threads couldn't be resolved, document them in a PR comment

## Troubleshooting

### GitHub API Limits
```bash
Error: GitHub API rate limit exceeded
Solution: Wait and retry, or use --dry-run mode
```

### Complex Review Comments
```bash
Warning: Unable to auto-generate fix for comment
Manual review required: "Consider broader architectural implications"
```

### Merge Conflicts
```bash
Error: Fix conflicts with recent changes
Solution: Pull latest, resolve conflicts, re-run the command
```

## Known Issues and Workarounds

### Bash Command Substitution in gh Commands

**Problem:** Using `$()` substitution inside `gh api` commands causes shell syntax errors.

```bash
# WRONG - This FAILS with syntax errors
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api repos/$REPO/pulls/40/comments  # Breaks due to escaping issues
```

**Solution:** Get repo info separately, then use literal values:

```bash
# CORRECT - get info first, then use literals
gh repo view --json nameWithOwner -q .nameWithOwner
# Returns: owner/repo

# Then use the actual values directly in the query
gh api repos/owner/repo/pulls/40/comments
```

### Wrong Mutation for Thread Replies

**Problem:** `addPullRequestReviewComment` mutation doesn't accept `pullRequestReviewThreadId`.

```bash
# WRONG - This FAILS
gh api graphql -f query='
mutation {
  addPullRequestReviewComment(input: {
    pullRequestReviewThreadId: "PRRT_xxx"  # Not a valid field!
    body: "Fixed"
  }) { comment { id } }
}'
```

**Solution:** Use `addPullRequestReviewThreadReply` instead:

```bash
# CORRECT - This works
gh api graphql -f query='
mutation {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: "PRRT_xxx"
    body: "Fixed"
  }) { comment { id } }
}'
```

### REST API for Review Thread Replies

**Problem:** REST API endpoint for comment replies doesn't work for review threads.

**Solution:** Always use GraphQL `addPullRequestReviewThreadReply` for review threads.

### Thread ID vs Comment ID Confusion

**Problem:** Review comments have both comment IDs (numeric) and thread IDs (`PRRT_*`). Resolution requires thread IDs.

**Solution:** When fetching review threads, extract the `id` field which contains the `PRRT_*` thread ID:

```bash
# The 'id' field in reviewThreads.nodes is the PRRT_* thread ID
gh api graphql -f query='...' | jq '.data.repository.pullRequest.reviewThreads.nodes[].id'
# Returns: PRRT_kwDOQcL40c5l9_nO
```

## Migration Notes

- `/fix-pr` now includes the enhanced superpowers-driven workflow (formerly `/fix-pr-wrapper`).
- Use `--dry-run` to preview the planned fixes before applying changes.

## Notes

- Requires GitHub CLI authentication
- Works best with superpowers code review analysis
- Maintains full backward compatibility
- Preserves all original Sanctum GitHub integrations
- Adds intelligent fix generation and contextual understanding
- **Thread resolution is MANDATORY** - every addressed comment MUST receive a reply and be resolved
- If thread resolution fails, document the failure and attempt manual resolution
- **Issue linkage** automatically analyzes open issues and closes/comments on addressed ones
- Use `--skip-issue-linkage` for faster execution when issue analysis is not needed
