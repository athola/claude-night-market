# Step 6.3: Thread Resolution

> **Navigation**: [<- Issue Creation](issue-creation.md) | [Step 6 Hub](../6-complete.md) | [Next: Issue Linkage ->](issue-linkage.md)

**Purpose**: Reply to and resolve every review thread. This is MANDATORY for PR authors.

---

## 6.3 Thread Resolution (MANDATORY)

**CRITICAL: You MUST reply to and resolve each review thread after fixing. This is not optional.**

### Review Feedback Types

GitHub has TWO types of review feedback - this workflow handles BOTH:

| Type | Source | Resolution Method |
|------|--------|-------------------|
| **Review Threads** | Line-level comments from "Start a review" | GraphQL `resolveReviewThread` |
| **PR Comments** | Conversation tab comments | Reply via `gh pr comment` |

**Detection Logic:**
```bash
# Check for review threads (line-level)
THREADS=$(gh api graphql -f query="..." --jq '[...reviewThreads...] | length')

# Check for PR comments containing review feedback
COMMENTS=$(gh pr view --json comments --jq '[.comments[] | select(.body | test("review|fix|change|improve|consider"; "i"))] | length')

if [[ "$THREADS" -eq 0 && "$COMMENTS" -gt 0 ]]; then
  echo "Review feedback is in PR comments (not threads)"
  echo "Reply to comments using: gh pr comment --body 'Addressed in commit abc123'"
fi
```

**If review feedback is in PR comments (not threads):**
1. Reply to the comment thread acknowledging fixes
2. Reference commit SHAs for each addressed item
3. No GraphQL resolution needed (comments don't have resolve state)

---

## MANDATORY WORKFLOW CHECKPOINTS

**Create TodoWrite items BEFORE starting:**
```markdown
## Thread Resolution (MANDATORY for PR Authors)
- [ ] fix-pr:thread-preflight - Run pre-check script (must pass to continue)
- [ ] fix-pr:thread-extract - Extract thread IDs (PRRT_*) from GraphQL API
- [ ] fix-pr:thread-reply-count - Reply to EACH unresolved thread (count: N)
- [ ] fix-pr:thread-resolve-count - Resolve EACH thread (count: N)
- [ ] fix-pr:thread-validate - Run validation checkpoint (must pass to proceed)
- [ ] fix-pr:thread-verify-all - Confirm ZERO unresolved threads remain

IF ANY CHECKPOINT FAILS, STOP AND FIX BEFORE PROCEEDING
```

**Checkpoint Enforcement Rules:**
1. **Pre-check must pass** (exit code 0) before any thread operations
2. **Extract ALL thread IDs** before replying to any
3. **Reply to ALL threads** before resolving any
4. **Resolve ALL threads** before running validation
5. **Validation must pass** (0 unresolved) before marking TodoWrite items complete
6. **NEVER mark TodoWrite complete** if validation fails

> **Important:** Thread IDs (format: `PRRT_*`) are different from comment IDs. You need thread IDs for both replies and resolution.

---

## Pre-Flight Check - Verify Threads Exist

Before attempting resolution, confirm there are review threads to process:
```bash
# Get repository info first (MANDATORY)
REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=$(echo "$REPO_FULL" | cut -d'/' -f1)
REPO=$(echo "$REPO_FULL" | cut -d'/' -f2)
PR_NUM=$(gh pr view --json number -q .number)

echo "Repository: $OWNER/$REPO"
echo "PR: #$PR_NUM"

# Fetch all review threads with their IDs and resolution status
THREADS_JSON=$(gh api graphql -f query="
query {
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $PR_NUM) {
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
}")

# Count unresolved threads
UNRESOLVED_COUNT=$(echo "$THREADS_JSON" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length')

echo "Unresolved threads: $UNRESOLVED_COUNT"

if [[ "$UNRESOLVED_COUNT" -eq 0 ]]; then
  echo "No unresolved threads to process - skipping thread resolution"
  # Skip to Step 6.4
fi
```

**If threads exist, proceed with resolution. If none exist, skip to Step 6.4.**

---

## Reply to Each Thread with Fix Description

For EACH review comment that was addressed, use the GraphQL mutation (NOT REST API):
```bash
# Reply using addPullRequestReviewThreadReply mutation
# The pullRequestReviewThreadId is the PRRT_* ID from pre-flight
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

---

## Resolve the Thread

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

---

## VALIDATION CHECKPOINT - Verify All Threads Resolved

After replying to and resolving all threads, you MUST verify the resolution was successful:
```bash
# Re-use variables from pre-flight check
VERIFICATION=$(gh api graphql -f query="
query {
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $PR_NUM) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          path
          line
        }
      }
    }
  }
}")

# Count remaining unresolved threads
REMAINING=$(echo "$VERIFICATION" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length')

echo "Verification: $REMAINING unresolved threads remaining"

if [[ "$REMAINING" -eq 0 ]]; then
  echo "SUCCESS: All review threads are now resolved"
else
  echo "FAILED: $REMAINING threads still unresolved"
  # Show which threads are still unresolved
  echo "$VERIFICATION" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | "  - \(.path):\(.line)"'
  echo ""
  echo "RESOLUTION REQUIRED:"
  echo "1. Review the above threads and determine why they weren't resolved"
  echo "2. Manually resolve them using the GraphQL mutations above"
  echo "3. Or run: /resolve-threads $PR_NUM"
  echo ""
  echo "DO NOT PROCEED TO STEP 6.4 UNTIL ALL THREADS ARE RESOLVED"
  exit 1
fi
```

---

## FINAL ENFORCEMENT CHECKPOINT

**You MAY NOT mark the TodoWrite items as complete until:**
- All unresolved threads count is 0
- Verification query shows `isResolved: true` for all threads
- No threads appear in "unresolved" list
- Exit code 0 from validation script

**If validation fails, you MUST:**
1. Identify which threads weren't resolved
2. Run the reply mutation again for those threads
3. Run the resolve mutation again for those threads
4. Re-run the validation checkpoint
5. Repeat until validation passes

**There is NO scenario where it is acceptable to:**
- Post a regular PR comment instead of thread replies
- Mark threads as "resolved" without actually resolving them
- Skip thread resolution because "it's too hard"
- Assume someone else will handle it
- Defer thread resolution to "later"

**WORKFLOW CANNOT BE MARKED COMPLETE UNTIL ALL THREADS ARE RESOLVED**

This checkpoint prevents proceeding until ALL threads are resolved. No exceptions.

---

> **Next**: [Issue Linkage](issue-linkage.md)
