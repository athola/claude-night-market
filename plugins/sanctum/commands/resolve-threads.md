---
name: resolve-threads
description: Batch-resolve all unresolved PR review threads via GitHub GraphQL API
usage: /resolve-threads [<pr-number> | <pr-url>]
---

# Resolve PR Review Threads

Quickly resolve all unresolved review threads on a PR after fixes have been addressed.

## When To Use

- **Runs automatically** at the end of `/fix-pr` (Phase 7)
- After manually addressing PR review comments outside `/fix-pr`
- To clean up resolved conversations before merge
- As a standalone verification command

## When NOT To Use

- Simple changes that don't need the full workflow
- Work already completed through another sanctum command

## Workflow

### Step 1: Identify Target PR

```bash
# If no PR specified, use current branch
gh pr view --json number,url -q '.number'
```

### Step 2: Fetch Unresolved Threads

```bash
# Replace OWNER, REPO, PR_NUMBER with actual values
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
            nodes { body }
          }
        }
      }
    }
  }
}'
```

### Step 3: Resolve Each Thread

For each unresolved thread:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "PRRT_xxx"}) {
    thread { isResolved }
  }
}'
```

### Step 4: Verify Resolution

```bash
# Should return 0
gh api graphql -f query='...' \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

## Output

```markdown
### Thread Resolution Summary

| Status | Count |
|--------|-------|
| Resolved | 15 |
| Already resolved | 3 |
| Failed | 0 |

All 18 review threads are now resolved.
```

## Notes

- Requires GitHub CLI with GraphQL access
- Does NOT reply to threads - use `/fix-pr` for reply + resolve
- Safe to run multiple times (idempotent)

## See Also

- `/fix-pr` - Full workflow for addressing PR comments (reply + resolve)
- `/pr-review` - Review a PR and post findings as GitHub comments
