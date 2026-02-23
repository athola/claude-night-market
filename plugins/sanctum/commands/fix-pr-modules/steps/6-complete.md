# Step 6: Complete (Threads, Issues, Summary)

> **Navigation**: [<- Step 5: Validate](5-validate.md) | [Main Workflow](../workflow-steps.md)

**Purpose**: Resolve threads, create issues for deferred items, and post summary.

**Platform Note**: Commands below show GitHub (`gh`) examples. Check session context for `git_platform:` and consult `Skill(leyline:git-platform)` for GitLab (`glab`) / Bitbucket equivalents. GitLab uses "merge request" terminology and `glab api graphql` for thread resolution.

**CRITICAL WORKFLOW GUARDRAIL**

**NEVER skip this step unless you are NOT the PR author. If you are the PR author and received review comments, you MUST complete this step. There are NO exceptions.**

**MANDATORY PRE-CHECK (Run BEFORE anything else in this step):**
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

**COMMON FAILURE MODES (READ BEFORE PROCEEDING):**

| What You Did | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Posted regular PR comment with `gh pr comment` | Comment not in thread context, thread remains unresolved | Use `addPullRequestReviewThreadReply` GraphQL mutation |
| Tried to use REST API `/comments/{id}/replies` | REST API doesn't support thread replies | Use GraphQL `addPullRequestReviewThreadReply` |
| Used comment ID instead of thread ID | Comment IDs can't resolve threads | Use thread ID (format: `PRRT_*`) |
| Skipped because "fixes are obvious" | Reviewer not notified, thread remains open | ALWAYS reply + resolve, even for "obvious" fixes |
| Assumed someone else will handle it | YOU are the PR author, it's YOUR responsibility | Complete the workflow yourself |
| **Review is in PENDING state** | Threads from pending reviews cannot be resolved until review is submitted | Submit the review first (or ask reviewer to submit), then re-run `/fix-pr` |

**If you are NOT the PR author**, you may skip to Step 6.4. Otherwise, continue below.

---

## Sub-Module Navigation

Step 6 is organized into sub-modules. Execute them in order:

| Sub-Step | Module | Purpose |
|----------|--------|---------|
| **6.0** | [Reconciliation](6-complete/reconciliation.md) | Reconcile ALL unworked items + enforcement |
| **6.1-6.2** | [Issue Creation](6-complete/issue-creation.md) | Create issues for suggestions and deferred items |
| **6.3** | [Thread Resolution](6-complete/thread-resolution.md) | Reply to and resolve every review thread |
| **6.4** | [Issue Linkage](6-complete/issue-linkage.md) | Link/close related issues |
| **6.5** | [Summary](6-complete/summary.md) | Post summary comment to PR |
| **6.6** | [Verification](6-complete/verification.md) | Final verification and workflow gate |

---

> **Back to**: [Main Workflow](../workflow-steps.md)
