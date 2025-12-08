---
description: Address PR review comments by triaging feedback, implementing fixes, and resolving threads on GitHub
usage: /fix-pr [<pr-number> | <pr-url>]
---

# Fix PR Review Comments

Address review feedback on a pull request. Fetches all comments, triages them for actionability, implements approved fixes, and resolves threads on GitHub.

## Arguments

- No argument: Uses the PR associated with the current branch
- `<pr-number>`: Target a specific PR by number (e.g., `/fix-pr 123`)
- `<pr-url>`: Target a PR by URL (e.g., `/fix-pr https://github.com/owner/repo/pull/123`)

## Workflow

### 1. Identify the PR

```bash
# If no argument, get PR for current branch
gh pr view --json number,url,headRefName

# If argument provided, use it directly
gh pr view <argument> --json number,url,headRefName
```

If no PR found, report: "No open PR found for this branch. Specify a PR number or URL."

### 2. Extract Repository Info

```bash
# Get owner/repo from git remote
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'
```

### 3. Fetch UNRESOLVED Review Threads (GraphQL)

**IMPORTANT**: Use GraphQL to fetch threads with resolution status. REST API doesn't expose thread resolution and may miss pending review comments.

```bash
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr_number}) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 5) {
            nodes {
              id
              databaseId
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

Filter to only `isResolved: false` threads. Already-resolved threads have been addressed.

Also fetch general PR comments (not in review threads):
```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments
```

If no unresolved threads and no issue comments, report: "PR #{number} has no unresolved review comments."

### 4. Classify Each Unresolved Thread

For each unresolved thread, determine:

- **Actionable**: Clear request for a code change ("rename this", "add error handling", "remove unused import")
- **Informational**: Observation, praise, or question not requiring code change ("looks good", "why did you choose X?", "interesting approach")
- **Ambiguous**: Unclear whether action is needed ("I'm not sure about this", "consider whether...", "might want to think about")

### 5. Present Triage Table

Show a compact summary:

```
PR #123: Found X review comments

| # | Location | Comment (truncated) | Assessment | Proposed Action |
|---|----------|---------------------|------------|-----------------|
| 1 | file:line | "..." | Actionable | [what you'll do] |
| 2 | file:line | "..." | Informational | (skip) |
| 3 | general | "..." | Ambiguous | ? |
```

For **ambiguous** items, ask the user directly:
- Quote the full comment
- Ask: "Should I take action on this? [y/n] If yes, what should I do?"

Then ask: "Proceed with N actionable items? [y/n/modify]"

### 6. Execute Fixes

For each approved fix:

1. **Read context**: Start with the file at the commented line, plus ~20 lines of surrounding context
2. **Expand if needed**: If the comment mentions "callers", "usages", or other files, search the codebase
3. **Apply the fix**: Use Edit tool to make the change
4. **Report progress**: `[2/5] Fixed: file.py:42 - Added error handling`

If a fix is unclear during implementation, pause and ask the user.

### 7. Commit Strategy

After all fixes are applied, show changed files and ask:

```
All fixes applied. Changed files:
  M api.py (2 changes)
  M utils.py (1 change)

How would you like to commit?
1. Single commit: "Address PR review feedback"
2. Separate commits per fix
3. Leave staged for manual review
```

Execute the chosen strategy.

### 8. Resolve Threads on GitHub

**Use GraphQL for all thread operations.** The REST API `/pulls/comments/{id}/replies` often returns 404 for pending review comments.

For each fixed thread:

```bash
# Step 1: Resolve the thread (this usually works)
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "{thread_id}"}) {
      thread { isResolved }
    }
  }
'
```

**Replying is optional and often fails due to permissions.** If you need to reply:

```bash
# Attempt reply via GraphQL (may fail with FORBIDDEN)
gh api graphql -f query='
  mutation {
    addPullRequestReviewComment(input: {
      inReplyTo: "{comment_node_id}",
      body: "Fixed: [brief description]"
    }) {
      comment { id }
    }
  }
'
```

If reply fails with permissions error, just resolve the thread without replying. The fix is visible in the code diff.

Keep replies terse: "Fixed: added try/except" not "I've addressed your feedback by..."

### 9. Final Report

```
Resolved:
  - file.py:42 - Added error handling (replied & resolved)
  - utils.py:15 - Renamed function (replied & resolved)

Unresolved (manual action needed):
  - file.py:87 - "Why not use dataclass?"
    Marked informational, no code change. Consider replying to explain your reasoning.
```

## Error Handling

- **No `gh` CLI**: "GitHub CLI (gh) is required. Install from https://cli.github.com"
- **Not authenticated**: "Run `gh auth login` to authenticate"
- **API rate limit**: Continue with local fixes, report "Could not resolve comments on GitHub"
- **REST 404 on comment**: Comment may be in a pending review. Use GraphQL with the thread ID from step 3 instead
- **GraphQL FORBIDDEN on reply**: Token lacks `addPullRequestReviewComment` permission. Skip the reply, resolve the thread only
- **Permission denied**: Report which operations failed, continue with others

## Notes

- Always verify workspace is clean before starting (`git status`)
- Fixes are applied to the working directory, not automatically pushed
- User controls when/how to commit changes
- GitHub resolution happens after local changes are made
- **Use thread IDs from step 3 GraphQL query** - don't make additional API calls to rediscover them
- The GraphQL query returns both `id` (node ID for mutations) and `databaseId` (numeric ID) - use the node ID for GraphQL mutations
