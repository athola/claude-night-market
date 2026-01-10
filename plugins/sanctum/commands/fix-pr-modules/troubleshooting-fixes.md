# Fix PR: Troubleshooting & Known Issues

Error handling, troubleshooting guide, and known issues.

> **See Also**: [Main Command](../fix-pr.md) | [Workflow Steps](workflow-steps.md) | [Configuration](configuration-options.md)

## Best Practices

### Before Running
1. validate clean working directory
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
3. **Threads auto-resolved via Phase 7** - `/resolve-threads` runs automatically
4. **POST SUMMARY COMMENT (MANDATORY)** - See Phase 6. This step is NOT optional.
5. Check CI pipeline status
6. Notify reviewers of updates
7. If any threads couldn't be resolved, document them in a PR comment

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
- **Threads auto-resolved** - `/resolve-threads` runs automatically as Phase 7 for final cleanup
- **Version validation verification** (Phase 3.5) re-checks version consistency after fixes are applied
  - Ensures B-VERSION issues from `/pr-review` were actually fixed
  - Blocks proceeding to test plan execution if version mismatches remain
  - Supports: pyproject.toml, package.json, Cargo.toml, marketplace.json, CHANGELOG.md

## Integration with Attune Workflow

This command follows the attune-style progressive workflow pattern:

```
Attune Workflow        | /fix-pr Equivalent
-----------------------|-------------------
/attune:brainstorm     | (PR review received)
/attune:arch-init      | --
/attune:specify        | Step 1: Analyze
/attune:plan           | Step 2-3: Triage + Plan
/attune:init           | --
/attune:execute        | Step 4-5: Fix + Validate
/attune:validate       | (included in Step 5)
/attune:upgrade        | (optional: /attune:upgrade --component workflows)
```

## See Also

- `/fix-issue` - Fix GitHub issues using same progressive workflow
- `/resolve-threads` - Batch-resolve review threads (runs automatically in Step 6)
- `/pr-review` - Review a PR and post findings as GitHub comments (generates test plan)
- `/pr` - Prepare a PR for submission
- `/attune:validate` - Validate project structure (can be used as additional check)
