# Step 6: Complete (Threads, Issues, Summary)

> **Navigation**: [← Step 5: Validate](5-validate.md) | [Main Workflow](../workflow-steps.md)

**Purpose**: Resolve threads, create issues for deferred items, and post summary.

**⚠️ CRITICAL WORKFLOW GUARDRAIL ⚠️**

**NEVER skip this step unless you are NOT the PR author. If you are the PR author and received review comments, you MUST complete this step. There are NO exceptions.**

**MANDATORY PRE-CHECK (Run BEFORE anything else in this step):**
```bash
# This command will EXIT WITH ERROR CODE 1 if any threads are unresolved
# Run this FIRST, before doing anything else in Step 6

REPO_FULL=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=$(echo "$REPO_FULL" | cut -d'/' -f1)
REPO=$(echo "$REPO_FULL" | cut -d'/' -f2)
PR_NUM=$(gh pr view --json number -q .number)

echo "=== MANDATORY THREAD RESOLUTION CHECK ==="
echo "PR: $OWNER/$REPO #$PR_NUM"

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
  echo "❌ WORKFLOW HALT: You have $UNRESOLVED_COUNT unresolved review threads"
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
  echo "⛔ DO NOT POST REGULAR PR COMMENTS - They don't resolve threads!"
  echo "⛔ DO NOT SKIP THIS STEP - It is MANDATORY for PR authors"
  echo ""
  exit 1
else
  echo "✓ All threads resolved - you may proceed to Step 6.1"
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

**If you are NOT the PR author**, you may skip to Step 6.4. Otherwise, continue below.

## 6.1 Create Issues for Suggestions/Deferred Items (AUTOMATIC)

**CRITICAL: GitHub issues are created AUTOMATICALLY for ALL suggestion and deferred items.**

> **Module Reference**: See `plugins/sanctum/skills/shared/modules/auto-issue-creation.md` for the full pattern.

**This step is automatic** - no flag required. When items are classified as "Suggestion" or "Deferred" during triage (Step 2), issues are created at the end of this step.

**To skip automatic creation**: Use `--no-auto-issues` flag.

**Duplicate Detection**: Before creating, search for existing issues with similar titles to avoid duplicates.

For each comment classified as **Suggestion** during triage, create a GitHub issue:
   ```bash
   gh issue create \
     --title "[Suggestion] <description from review comment>" \
     --body "$(cat <<'EOF'
   ## Background

   Identified during PR #PR_NUMBER review as a suggestion for improvement.

   **Original Review Comment:**
   > [Quote the review comment here]

   **Location:** `file/path.py:line` (if applicable)

   ## Suggested Improvement

   [Describe the suggested improvement based on the review feedback]

   ## Value

   [Explain why this improvement would be valuable - performance, UX, maintainability, etc.]

   ## Acceptance Criteria

   - [ ] [Specific criteria based on the suggestion]
   - [ ] Tests added/updated (if applicable)
   - [ ] Documentation updated (if applicable)

   ## References

   - PR #PR_NUMBER: [PR URL]
   - Original review comment: [Link if available]

   ---
   *Created from PR #PR_NUMBER review triage*
   EOF
   )" \
     --label "suggestion" \
     --label "enhancement"
   ```

   **Suggestion Issue Rules:**
   - Prefix title with "[Suggestion]" for easy identification
   - Always use the "suggestion" label (required for tracking)
   - Add additional labels as appropriate (enhancement, docs, testing, etc.)
   - Include the original review comment verbatim
   - Explain the value/improvement rationale
   - Reference the source PR
   - Define clear acceptance criteria

**Track Created Suggestion Issues:**
After creating issues, document them in the PR comment:
```markdown
### Suggestions → GitHub Issues

| Review Item | Issue Created | Description |
|-------------|---------------|-------------|
| S1 | #43 | Clarify ruff-format comment |
| S2 | #44 | Improve test output verbosity |
```

## 6.2 Create Issues for Deferred/Out-of-Scope Items

For each comment classified as **Deferred** (including "out-of-scope", "medium priority", "future work") during triage, create a GitHub issue:
   ```bash
   gh issue create \
     --title "<type>(<scope>): <description from review comment>" \
     --body "$(cat <<'EOF'
   ## Background

   Identified during PR #PR_NUMBER review as out-of-scope.

   **Original Review Comment:**
   > [Quote the review comment here]

   **Location:** `file/path.py:line` (if applicable)

   ## Scope

   [Describe what needs to be done based on the review feedback]

   ## Suggested Implementation

   [Any suggestions from the review or analysis]

   ## Acceptance Criteria

   - [ ] [Specific criteria based on the feedback]
   - [ ] Tests added/updated
   - [ ] Documentation updated (if applicable)

   ## References

   - PR #PR_NUMBER: [PR URL]
   - Original review comment: [Link if available]

   ---
   *Created from PR #PR_NUMBER review triage*
   EOF
   )" \
     --label "enhancement"
   ```

**Issue Creation Rules:**
- Use conventional commit format for title: `type(scope): description`
- Common types: `feat`, `fix`, `test`, `docs`, `perf`, `refactor`
- Include the original review comment in the body
- Add relevant labels (enhancement, bug, docs, etc.)
- Reference the source PR
- Define clear acceptance criteria

## 6.3 Thread Resolution (MANDATORY)

**CRITICAL: You MUST reply to and resolve each review thread after fixing. This is not optional.**

**MANDATORY WORKFLOW CHECKPOINTS - Create TodoWrite items BEFORE starting:**
```markdown
## Thread Resolution (MANDATORY for PR Authors)
- [ ] fix-pr:thread-preflight - Run pre-check script (must pass to continue)
- [ ] fix-pr:thread-extract - Extract thread IDs (PRRT_*) from GraphQL API
- [ ] fix-pr:thread-reply-count - Reply to EACH unresolved thread (count: N)
- [ ] fix-pr:thread-resolve-count - Resolve EACH thread (count: N)
- [ ] fix-pr:thread-validate - Run validation checkpoint (must pass to proceed)
- [ ] fix-pr:thread-verify-all - Confirm ZERO unresolved threads remain

⚠️ IF ANY CHECKPOINT FAILS, STOP AND FIX BEFORE PROCEEDING
```

**Checkpoint Enforcement Rules:**
1. **Pre-check must pass** (exit code 0) before any thread operations
2. **Extract ALL thread IDs** before replying to any
3. **Reply to ALL threads** before resolving any
4. **Resolve ALL threads** before running validation
5. **Validation must pass** (0 unresolved) before marking TodoWrite items complete
6. **NEVER mark TodoWrite complete** if validation fails

> **Important:** Thread IDs (format: `PRRT_*`) are different from comment IDs. You need thread IDs for both replies and resolution.

**Pre-Flight Check - Verify Threads Exist:**
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
     echo "✓ No unresolved threads to process - skipping thread resolution"
     # Skip to Step 6.4
   fi
   ```

   **If threads exist, proceed with resolution. If none exist, skip to Step 6.4.**

**Reply to Each Thread with Fix Description:**
   For EACH review comment that was addressed, use the GraphQL mutation (NOT REST API):
   ```bash
   # Reply using addPullRequestReviewThreadReply mutation
   # The pullRequestReviewThreadId is the PRRT_* ID from step 19
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

**Resolve the Thread:**
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

**VALIDATION CHECKPOINT - Verify All Threads Resolved:**
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
      echo "✓ SUCCESS: All review threads are now resolved"
    else
      echo "❌ FAILED: $REMAINING threads still unresolved"
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

**⛔ FINAL ENFORCEMENT CHECKPOINT ⛔**

**You MAY NOT mark the TodoWrite items as complete until:**
- ✅ All unresolved threads count is 0
- ✅ Verification query shows `isResolved: true` for all threads
- ✅ No threads appear in "unresolved" list
- ✅ Exit code 0 from validation script

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

**⛔ WORKFLOW CANNOT BE MARKED COMPLETE UNTIL ALL THREADS ARE RESOLVED ⛔**

    **This checkpoint prevents proceeding until ALL threads are resolved. No exceptions.**

## 6.4 Issue Linkage & Closure

**Analyze whether this PR addresses any open issues and close/comment on them accordingly.**

**Fetch Open Issues:**
```bash
# Get all open issues for the repository
gh issue list --state open --json number,title,body,labels --limit 50
```

**Analyze Issue Coverage:**

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

**Comment on Fully Addressed Issues:**
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

**Comment on Partially Addressed Issues:**
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

## 6.5 Post Summary Comment (MANDATORY)
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

After completing all fixes, thread resolutions, and issue linkage, post a detailed summary comment to the PR.

**Post Summary Comment:**
    ```bash
    gh pr comment PR_NUMBER --body "$(cat <<'EOF'
    ## PR Review Feedback Addressed

    All issues from the code review have been fixed in commit `COMMIT_SHA`.

    ### Blocking Issues (N) [FIXED]

    | ID | Issue | Resolution |
    |----|-------|------------|
    | **B1** | [Description] | [How it was fixed] |

    ### In-Scope Issues (N) [FIXED]

    | ID | Issue | Resolution |
    |----|-------|------------|
    | **S1** | [Description] | [How it was fixed] |

    ### Suggestions Created (N)

    | Review Item | Issue Created | Description |
    |-------------|---------------|-------------|
    | S2 | #43 | [Description] |
    | S3 | #44 | [Description] |

    Or: **None** - All suggestions were addressed directly in this PR.

    ### Deferred Items Created (N)

    | Review Item | Issue Created | Description |
    |-------------|---------------|-------------|
    | C2 | #41 | [Description] |

    Or: **None** - No deferred/out-of-scope items identified.

    ---

    Ready for re-review. All pre-commit hooks pass.
    EOF
    )"
    ```

    **Summary Comment Requirements:**
    - Include commit SHA for reference
    - Group fixes by category (Blocking, In-Scope)
    - List suggestions that were fixed directly vs. suggestions that created issues
    - List deferred items that created issues
    - Use tables for clarity
    - End with clear status ("Ready for re-review")

## 6.6 Final Thread Verification (AUTOMATIC)

This phase runs automatically at the end of /fix-pr.

```bash
Skill(sanctum:resolve-threads)
```

This validates any threads missed during Step 6.3 are resolved via batch operation.

**Step 6 Output**: All threads resolved, issues created, summary posted

---

> **Back to**: [Main Workflow](../workflow-steps.md)
