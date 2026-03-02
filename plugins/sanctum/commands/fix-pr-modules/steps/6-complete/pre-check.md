# Step 6 Pre-Check: Thread & Review Validation

> **Navigation**: [Step 6 Hub](../6-complete.md) | [Next: Reconciliation ->](reconciliation.md)

**Purpose**: Validate that all reviews are submitted and all threads are resolved before Step 6 proceeds.

---

## Mandatory Pre-Check Script

Run this BEFORE anything else in Step 6. The script exits with code 1 if any threads are unresolved or if reviews are still PENDING (not yet submitted).

```bash
# This command will EXIT WITH ERROR CODE 1 if any threads are unresolved
# OR if reviews are still PENDING (not yet submitted)
# Run this FIRST, before doing anything else in Step 6

REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=$(echo "$REPO_FULL" | cut -d'/' -f1)
REPO=$(echo "$REPO_FULL" | cut -d'/' -f2)
PR_NUM=$(gh pr view --json number -q .number)

echo "=== MANDATORY THREAD RESOLUTION CHECK ==="
echo "PR: $OWNER/$REPO #$PR_NUM"

# STEP 0: Check for PENDING reviews (reviews not yet submitted)
echo ""
echo "Checking review states..."
PENDING_REVIEWS=$(gh pr view $PR_NUM --json reviews -q '[.reviews[] | select(.state == "PENDING")] | length')

if [[ "$PENDING_REVIEWS" -gt 0 ]]; then
  echo ""
  echo "PENDING REVIEW DETECTED"
  echo ""
  echo "There are $PENDING_REVIEWS review(s) in PENDING state."
  echo "Pending reviews have NOT been submitted yet - their threads cannot be resolved."
  echo ""
  echo "This typically means:"
  echo "  - The reviewer started a review but hasn't clicked 'Submit review'"
  echo "  - OR you are the reviewer and have a draft review in progress"
  echo ""
  echo "REQUIRED ACTIONS:"
  echo "  1. If you are the reviewer: Submit or discard your pending review"
  echo "  2. If waiting on reviewer: Ask them to submit their review"
  echo "  3. Once review is submitted, re-run: /fix-pr"
  echo ""
  echo "Pending review details:"
  gh pr view $PR_NUM --json reviews -q '.reviews[] | select(.state == "PENDING") | "  Author: \(.author.login) | State: \(.state)"'
  echo ""
  echo "CANNOT RESOLVE THREADS UNTIL REVIEWS ARE SUBMITTED"
  echo ""
  exit 1
fi

echo "No pending reviews - proceeding to thread check"

CHECK_OUTPUT=$(gh api graphql -f query="
query {
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $PR_NUM) {
      reviewThreads(first: 100) {
        totalCount
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

UNRESOLVED_COUNT=$(echo "$CHECK_OUTPUT" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length')

echo ""
echo "Unresolved review threads: $UNRESOLVED_COUNT"

if [[ "$UNRESOLVED_COUNT" -gt 0 ]]; then
  echo ""
  echo "WORKFLOW HALT: You have $UNRESOLVED_COUNT unresolved review threads"
  echo ""
  echo "You CANNOT proceed until these threads are resolved:"
  echo "$CHECK_OUTPUT" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | "  Thread \(.id): \(.path):\(.line)\n    Comment: \(.comments.nodes[0].body[0:80])..."'
  echo ""
  echo "REQUIRED ACTIONS (in order):"
  echo "  1. Extract thread IDs (format: PRRT_*) from the list above"
  echo "  2. Reply to each thread using: addPullRequestReviewThreadReply"
  echo "  3. Resolve each thread using: resolveReviewThread"
  echo "  4. Re-run this pre-check to verify"
  echo ""
  echo "DO NOT POST REGULAR PR COMMENTS - They don't resolve threads!"
  echo "DO NOT SKIP THIS STEP - It is MANDATORY for PR authors"
  echo ""
  exit 1
else
  echo "All threads resolved - you may proceed to Step 6.0"
fi
```

---

## Common Failure Modes

Read this table before proceeding. These are the most frequent mistakes that cause threads to remain unresolved.

| What You Did | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Posted regular PR comment with `gh pr comment` | Comment not in thread context, thread remains unresolved | Use `addPullRequestReviewThreadReply` GraphQL mutation |
| Tried to use REST API `/comments/{id}/replies` | REST API doesn't support thread replies | Use GraphQL `addPullRequestReviewThreadReply` |
| Used comment ID instead of thread ID | Comment IDs can't resolve threads | Use thread ID (format: `PRRT_*`) |
| Skipped because "fixes are obvious" | Reviewer not notified, thread remains open | ALWAYS reply + resolve, even for "obvious" fixes |
| Assumed someone else will handle it | YOU are the PR author, it's YOUR responsibility | Complete the workflow yourself |
| **Review is in PENDING state** | Threads from pending reviews cannot be resolved until review is submitted | Submit the review first (or ask reviewer to submit), then re-run `/fix-pr` |

---

> **Next**: [Reconciliation](reconciliation.md)
