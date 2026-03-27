# PR/MR Review: Workflow Phases 5-6

Phase 5 (test plan generation) and Phase 6 (PR description update)
of the review workflow.

> **See Also**:
> [Main Command](../../pr-review.md) |
> [Workflow Index](review-workflow.md) |
> [Phases 1-4](review-workflow-phases-1-4.md) |
> [Enforcement](review-workflow-enforcement.md) |
> [Framework](review-framework.md) |
> [Configuration](review-configuration.md)

### Phase 5: Test Plan Generation (MANDATORY)

**⚠️ ENFORCEMENT CHECK: This phase MUST complete with a `gh pr comment` call.**
**If you skip this phase, the workflow is INCOMPLETE.**

After documenting review threads, generate a detailed test plan that `/fix-pr` can execute to verify fixes.

**CRITICAL REQUIREMENT:**
- The test plan MUST be posted as a **separate PR comment** using `gh pr comment`
- Do NOT just include the test plan in your conversational output
- Do NOT just include the test plan in the review summary
- The test plan comment enables `/fix-pr` to find and execute verification steps

13. **Generate Test Plan Document**

    Create a structured test plan covering all blocking and in-scope issues:

    ```markdown
    ## Test Plan for PR #42

    Generated from `/pr-review` on YYYY-MM-DD

    ### Prerequisites
    - [ ] All blocking issues (B1-BN) have been addressed
    - [ ] All in-scope issues (S1-SN) have been addressed
    - [ ] Code compiles without errors

    ---

    ### Blocking Issues Verification

    #### B1: Missing token validation
    **File:** `middleware/auth.py:45`
    **Issue:** Always returns True, validation not implemented

    **Verification Steps:**
    1. [ ] Review the fix at `middleware/auth.py:45`
    2. [ ] Run: `pytest tests/test_auth.py -k "token_validation" -v`
    3. [ ] Manual check: Attempt login with invalid token, verify rejection
    4. [ ] Verify error response includes appropriate message

    **Expected Outcome:**
    - Tests pass
    - Invalid tokens return 401 Unauthorized
    - No security regression

    ---

    #### B2: SQL injection vulnerability
    **File:** `models/user.py:123`
    **Issue:** String interpolation in query

    **Verification Steps:**
    1. [ ] Review the fix at `models/user.py:123`
    2. [ ] Run: `bandit -r models/ -ll`
    3. [ ] Run: `pytest tests/test_models.py -k "sql" -v`
    4. [ ] Manual check: Verify parameterized queries used

    **Expected Outcome:**
    - Bandit reports no high-severity SQL issues
    - All SQL queries use parameterized format
    - Tests pass

    ---

    ### In-Scope Issues Verification

    #### S1: Password reset flow missing
    **Requirement:** Users must be able to reset passwords

    **Verification Steps:**
    1. [ ] Verify endpoint exists: `grep -r "password.*reset" routes/`
    2. [ ] Run: `pytest tests/test_auth.py -k "password_reset" -v`
    3. [ ] Manual check: Test password reset email flow

    **Expected Outcome:**
    - Password reset endpoint implemented
    - Email sending functionality works
    - Tests cover happy path and error cases

    ---

    ### Build & Quality Gates

    **Run these commands to verify overall quality:**

    ```bash
    # Full test suite
    make test

    # Linting and formatting
    make lint

    # Security scan
    make security-check

    # Build verification
    make build
    ```

    **All must pass before PR approval.**

    ---

    ### Summary Checklist

    | Issue ID | File | Verified | Notes |
    |----------|------|----------|-------|
    | B1 | middleware/auth.py:45 | [ ] | |
    | B2 | models/user.py:123 | [ ] | |
    | S1 | routes/auth.py | [ ] | |
    | S2 | auth.py:78 | [ ] | |

    **Ready for merge when all boxes checked.**
    ```

14. **Post Test Plan to PR (MANDATORY)**

    The test plan MUST be posted as a PR comment so `/fix-pr` can reference it:

    ```bash
    gh pr comment $PR_NUMBER --body "$(cat <<'EOF'
    ## Test Plan for PR #$PR_NUMBER

    Generated from `/pr-review` on $(date +%Y-%m-%d)

    ### Prerequisites
    - [ ] All blocking issues (B1-BN) have been addressed
    - [ ] All in-scope issues (S1-SN) have been addressed
    - [ ] Code compiles without errors

    ---

    ### Blocking Issues Verification

    #### B1: [Issue title]
    **File:** \`path/to/file.py:line\`
    **Issue:** [Description]

    **Verification Steps:**
    1. [ ] Review the fix at \`path/to/file.py:line\`
    2. [ ] Run: \`[specific test command]\`
    3. [ ] Manual check: [verification procedure]

    **Expected Outcome:**
    - [What success looks like]

    ---

    [Repeat for each blocking and in-scope issue]

    ---

    ### Build & Quality Gates

    **Run these commands to verify overall quality:**

    \`\`\`bash
    # Project-specific commands (detect from Makefile/pyproject.toml)
    make test && make lint && make build
    # OR
    uv run pytest && uv run ruff check . && uv run mypy src/
    \`\`\`

    **All must pass before PR approval.**

    ---

    ### Summary Checklist

    | Issue ID | File | Verified | Notes |
    |----------|------|----------|-------|
    | B1 | path/to/file.py:line | [ ] | |
    | B2 | path/to/file.py:line | [ ] | |
    | S1 | path/to/file.py:line | [ ] | |

    **Ready for merge when all boxes checked.**

    ---
    *Test plan generated by /pr-review - execute with /fix-pr*
    EOF
    )"
    ```

    **Test Plan Posting Rules:**
    - MUST be posted as a separate PR comment (not part of the review body)
    - MUST include all blocking and in-scope issues
    - MUST have specific verification commands for each issue
    - SHOULD detect project's test/lint/build commands from Makefile or pyproject.toml
    - Posted AFTER the review summary comment

15. **Confirm Test Plan Posted**

    After posting, verify the comment was created:

    ```bash
    # Verify test plan comment exists
    gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
      --jq '.[] | select(.body | contains("Test Plan for PR")) | .id' | head -1

    # If successful, output confirmation
    echo "✅ Test plan posted to PR #$PR_NUMBER"
    ```

    **If posting fails:**
    - Save test plan locally to `.pr-review/test-plan-{pr_number}.md`
    - Output warning: "⚠️ Failed to post test plan to PR. Saved locally."

**Test Plan Generation Rules:**

| Finding Type | Include in Test Plan | Verification Depth |
|--------------|---------------------|-------------------|
| Blocking | Always | Full: code review + tests + manual |
| In-Scope | Always | Standard: code review + tests |
| Suggestion | If addressed | Light: code review only |
| Backlog | Never | N/A (tracked in issues) |

**Test Plan Section Requirements:**
- Each issue must have numbered verification steps
- Include specific commands to run
- Define expected outcomes clearly
- Provide manual check procedures where automated tests insufficient
- Include overall quality gate commands
- Format as checkboxes for `/fix-pr` execution

### Phase 5 Completion Checklist

Before proceeding, verify ALL items are complete:

- [ ] Test plan generated with all blocking/in-scope issues
- [ ] `gh pr comment $PR_NUMBER --body "## Test Plan..."` executed
- [ ] Confirmation output: "✅ Test plan posted to PR #$PR_NUMBER"
- [ ] If posting failed: Test plan saved locally + warning issued

**If any item above is unchecked, GO BACK and complete Phase 5.**

### Phase 6: PR Description Update (MANDATORY)

**⚠️ ENFORCEMENT CHECK: This phase MUST complete with a `gh api` call to update PR body.**
**If you skip this phase, the workflow is INCOMPLETE.**

After posting the test plan, update the PR description with a summary of the review findings.

16. **Extract Review Summary**

    From the review findings, extract key metrics:
    - Critical issues count
    - Important issues count
    - Suggestions count
    - Verdict (Ready to Merge / Needs Changes)

17. **Generate PR Description Update**

    Apply `scribe:doc-generator` principles when drafting PR descriptions:
    - Ground claims with specifics (commit hashes, file counts, test results)
    - Use direct language, avoid marketing terms
    - No tier-1 slop words: delve, comprehensive, leverage, seamless
    - Active voice preferred

    ```markdown
    ## Summary

    [Extract from PR title/commits or scope artifacts]

    ### Changes

    - [Extracted from commit messages]

    ### Code Review Summary

    | Category | Count |
    |----------|-------|
    | Critical | X |
    | Important | X |
    | Suggestions | X |

    **Verdict**: [Ready to merge | Needs changes] after addressing X issues.

    [View full review](link_to_review_comment)

    ---

    ### Closes
    - Closes #XX (from commit messages or scope artifacts)
    ```

17.5. **Inject Test Plan into PR Description**

    > **Module**: [test-plan-injection](../../shared/test-plan-injection.md)

    Before sending `$NEW_BODY` to the API, check whether
    it contains a detailed test plan section. If missing,
    generate one from the Phase 5 test plan data and
    inject it into the body.

    ```bash
    # --- Detection ---
    # Match recognized test plan headings
    TEST_PLAN_HEADING='##+ (Test [Pp]lan|Manual Test|Verification Steps)'

    HAS_HEADING=$(echo "$NEW_BODY" | grep -ciE "$TEST_PLAN_HEADING" || true)
    CHECKBOX_COUNT=$(echo "$NEW_BODY" | grep -c '- \[[ x]\]' || true)

    if [[ "$HAS_HEADING" -gt 0 ]] && [[ "$CHECKBOX_COUNT" -ge 3 ]]; then
      echo "Test plan already present in PR description, skipping injection"
    else
      echo "No detailed test plan found, injecting..."

      # --- Generation ---
      # Build condensed test plan from Phase 5 data
      # (blocking/in-scope issues already in context from step 13)

      TEST_PLAN="## Test Plan

    ### Prerequisites
    - [ ] Branch is up to date with base branch
    - [ ] Dependencies installed (\`uv sync\` or \`npm install\`)

    ### Verification Steps
    "
      # Append per-area steps from blocking/in-scope issues
      AREA_NUM=1
      for ISSUE in "${BLOCKING_ISSUES[@]}" "${IN_SCOPE_ISSUES[@]}"; do
        ISSUE_ID=$(echo "$ISSUE" | cut -d'|' -f1)
        ISSUE_FILE=$(echo "$ISSUE" | cut -d'|' -f2)
        ISSUE_DESC=$(echo "$ISSUE" | cut -d'|' -f3)

        TEST_PLAN+="
    #### $AREA_NUM. $ISSUE_ID: $ISSUE_DESC
    **Files:** \`$ISSUE_FILE\`

    1. [ ] Review the fix at \`$ISSUE_FILE\`
    2. [ ] Run relevant tests for this area
    3. [ ] Expected: issue resolved, no regression
    "
        AREA_NUM=$((AREA_NUM + 1))
      done

      # Add build and quality gates
      TEST_PLAN+="
    ### Build & Quality Gates
    \`\`\`bash
    make test && make lint
    \`\`\`

    ### Summary
    | Area | Steps | Verified |
    |------|-------|----------|"

      for ISSUE in "${BLOCKING_ISSUES[@]}" "${IN_SCOPE_ISSUES[@]}"; do
        ISSUE_ID=$(echo "$ISSUE" | cut -d'|' -f1)
        TEST_PLAN+="
    | $ISSUE_ID | 3 | [ ] |"
      done

      # --- Injection ---
      # Insert before Code Review Summary if it exists
      if echo "$NEW_BODY" | grep -q '### Code Review Summary'; then
        # Insert test plan before the review summary
        NEW_BODY=$(echo "$NEW_BODY" | sed "/### Code Review Summary/i\\
\\
${TEST_PLAN}\\
\\
---\\
")
      else
        # Append after existing content
        NEW_BODY="${NEW_BODY}

    ---

    ${TEST_PLAN}"
      fi

      echo "Test plan injected into PR description"
    fi
    ```

    **For the prepend flow** (existing description case):
    also check the combined `$NEW_BODY` after prepending
    the review summary. If the original body lacked a test
    plan, the injection adds one between the changes
    section and the review summary.

    **Test plan content sources:**
    - Blocking issues (B1, B2, ...) from Phase 3 triage
    - In-scope issues (S1, S2, ...) from Phase 3 triage
    - Build commands detected from `Makefile` or
      `pyproject.toml`

18. **Update PR Description via API**

    ```bash
    # Get current body
    CURRENT_BODY=$(gh pr view $PR_NUMBER --json body --jq '.body // empty')

    # Check if body is empty or just whitespace
    if [[ -z "${CURRENT_BODY// /}" ]]; then
      echo "PR description is empty - generating from scratch"
      IS_EMPTY=true
    else
      echo "PR description exists - prepending review summary"
      IS_EMPTY=false
    fi

    # Build review summary section
    REVIEW_SUMMARY="### Code Review Summary

    | Category | Count |
    |----------|-------|
    | Critical | $CRITICAL_COUNT |
    | Important | $IMPORTANT_COUNT |
    | Suggestions | $SUGGESTION_COUNT |

    **Verdict**: [Ready to merge | Needs changes] after addressing $BLOCKING_COUNT issues.

    [View full review]($REVIEW_COMMENT_URL)"

    # Generate PR body based on whether it's empty
    if [[ "$IS_EMPTY" == "true" ]]; then
      # Generate full description from scope artifacts

      # Extract summary from commits or scope artifacts
      COMMIT_SUMMARY=$(git log --oneline $(git merge-base HEAD origin/main)..HEAD | head -5 | sed 's/^[a-f0-9]* /- /')

      # Try to extract from plan/spec files
      PLAN_SUMMARY=""
      if [[ -f "docs/plans/plan-$(git branch --show-current).md" ]]; then
        PLAN_SUMMARY=$(head -20 "docs/plans/plan-$(git branch --show-current).md" | grep -E "^## |^- " | head -10)
      elif [[ -f "plan.md" ]]; then
        PLAN_SUMMARY=$(head -20 "plan.md" | grep -E "^## |^- " | head -10)
      fi

      # Build full description
      NEW_BODY="## Summary

$(if [[ -n "$PLAN_SUMMARY" ]]; then echo "$PLAN_SUMMARY"; else echo "This PR includes the following changes:"; fi)

### Changes

$COMMIT_SUMMARY

---

$REVIEW_SUMMARY"
    else
      # Prepend review summary to existing body
      NEW_BODY="$REVIEW_SUMMARY

---

$CURRENT_BODY"
    fi

    # Update via API with fallback for token scope issues
    # gh pr edit requires read:org scope which may not be granted
    # gh api PATCH to pulls endpoint only requires repo scope

    # Try direct API first (most reliable, only needs repo scope)
    if gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER" -X PATCH -f body="$NEW_BODY" 2>/dev/null; then
      echo "✅ PR description updated for PR #$PR_NUMBER"
    else
      # Fallback: post description as comment if API fails
      echo "⚠️ Could not update PR description (token may lack required scope)"
      echo "Posting summary as comment instead..."

      gh pr comment $PR_NUMBER --body "## PR Summary (Auto-generated)

$NEW_BODY

---
*Note: Could not update PR description due to token permissions. This summary is posted as a comment instead.*"

      echo "✅ PR summary posted as comment to PR #$PR_NUMBER"
    fi
    ```

    **Token Scope Handling:**

    The `gh pr edit` command may fail with GraphQL errors like:
    ```
    Your token has not been granted the required scopes to execute this query.
    The 'login' field requires one of the following scopes: ['read:org']
    ```

    This happens because `gh pr edit` uses GraphQL which queries organization data.
    The workflow handles this by:
    1. Using `gh api` PATCH endpoint first (only needs `repo` scope)
    2. Falling back to posting as a comment if API fails
    3. Never failing the review due to permission issues

    **Empty Description Handling:**

    When PR description is empty, the command:
    1. **Detects** empty body (null, empty string, or whitespace-only)
    2. **Extracts** summary from:
       - Scope artifacts (`docs/plans/`, `plan.md`, `spec.md`)
       - Recent commit messages (last 5 commits)
    3. **Generates** full description with:
       - Summary section (from scope or commits)
       - Changes section (commit list)
       - Review summary (issue counts, verdict)
    4. **Creates** complete PR description from scratch

    **Existing Description Handling:**

    When PR description exists:
    1. **Preserves** existing content unchanged
    2. **Prepends** review summary at top
    3. **Separates** with horizontal rule (`---`)

    **Example Generated Description (empty case):**

    ```markdown
    ## Summary

    This PR implements continuous improvement features:
    - Phase 2 improvement analysis in /update-plugins
    - Iron Law TDD enforcement
    - Agent-aware hooks for context optimization

    ### Changes

    - feat: release version 1.2.5 with continuous improvement and Iron Law TDD
    - feat: add agent-aware hooks and integrate proof-of-work enforcement
    - feat(sanctum): add /update-plugins command and enhance doc-updates workflow
    - fix(plugins): register missing commands and skills in plugin.json files
    - docs: sync capabilities-reference with 1.2.4 features

    ---

    ### Code Review Summary

    | Category | Count |
    |----------|-------|
    | Critical | 0 |
    | Important | 0 |
    | Suggestions | 9 |

    **Verdict**: Ready to merge after addressing 0 issues.

    [View full review](https://github.com/owner/repo/pull/100#issuecomment-123456)
    ```

19. **Confirm PR Description Updated**

    ```bash
    # Verify description was updated
    gh pr view $PR_NUMBER --json body --jq '.body | length > 0'

    # Check for review summary marker
    gh pr view $PR_NUMBER --json body --jq '.body | contains("Code Review Summary")'
    ```

### Phase 6 Completion Checklist

Before completing the review, verify ALL items are complete:

- [ ] Review summary extracted with issue counts
- [ ] PR description updated with summary table
- [ ] `gh api repos/.../pulls/$PR_NUMBER -X PATCH` executed
- [ ] Confirmation output: "✅ PR description updated for PR #$PR_NUMBER"

**If any item above is unchecked, GO BACK and complete Phase 6.**


> **Next**: [Enforcement](review-workflow-enforcement.md) — mandatory output verification and options.
