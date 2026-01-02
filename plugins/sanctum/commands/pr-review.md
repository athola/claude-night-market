---
name: pr-review
description: |
  Comprehensive PR review with scope validation, code analysis, and version checks via GitHub.

  Triggers: PR review, code review, pull request, pre-merge
  Use when: reviewing feature PRs or enforcing quality gates
usage: /pr-review [<pr-number> | <pr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--create-backlog-issues] [--dry-run] [--no-line-comments] [--skip-version-check]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Review

Integrates Sanctum's disciplined scope validation with superpowers:receiving-code-review's detailed analysis to provide thorough, balanced PR reviews that prevent scope creep while ensuring code quality.

## Core Philosophy

**Scope-Aware Quality Validation**
- Validate implementation against stated requirements
- Prevent overengineering through scope discipline
- validate code quality without blocking valid implementations
- Route out-of-scope improvements to backlog

## Key Enhancements

### Sanctum Contributions
- **Scope Baseline Establishment**: Analyzes plan/spec artifacts
- **Requirements Compliance Checking**: Validates against original specs
- **Backlog Triage**: Creates GitHub issues for out-of-scope items
- **Structured Reporting**: Clear classification of findings

### Superpowers Contributions
- **Automated Code Analysis**: Deep review of implementation quality
- **Best Practice Validation**: Industry-standard checks
- **Security Scanning**: Vulnerability detection
- **Performance Impact Assessment**: Efficiency considerations

## When to Use

- Reviewing feature branch PRs
- Validating implementation against requirements
- Pre-merge quality gates
- Generating actionable review feedback
- Creating improvement backlog

## Workflow

### Phase 1: Scope Establishment (Sanctum)

1. **Discover Scope Artifacts**
   ```bash
   # Search in priority order:
   1. docs/plans/*-<branch-name>*.md
   2. plan.md or spec.md
   3. tasks.md with completed items
   4. PR description and commit history
   ```

2. **Check Existing Backlog for Context**
   ```bash
   # Check for existing backlog files to avoid duplicate issue creation
   ls docs/backlog/*.md 2>/dev/null
   # Key files to check:
   # - docs/backlog/queue.md - Active backlog items with worthiness scores
   # - docs/backlog/technical-debt.md - Known technical debt items
   ```

   If these files exist:
   - Cross-reference out-of-scope items against existing entries
   - Avoid creating duplicate GitHub issues for items already tracked
   - Link new issues to related existing items when appropriate

3. **Establish Requirements Baseline**
   ```markdown
   This PR aims to: [extracted from artifacts]

   Requirements:
   1. [Requirement from plan]
   2. [Requirement from spec]
   3. [Requirement from tasks]
   ```

### Phase 1.5: Version Validation (MANDATORY)

**CRITICAL: This phase is MANDATORY for all PR reviews unless explicitly bypassed.**

Before proceeding to code analysis, validate version consistency across all version-bearing files.

**Bypass Conditions (any of):**
- CLI flag: `--skip-version-check` provided
- GitHub label: PR has `skip-version-check` label
- PR description: Contains `[skip-version-check]` marker

**Validation Process:**

1. **Check if bypass requested**
   ```bash
   # Check CLI flag (handled by command parsing)
   SKIP_VERSION_CHECK=false

   # Check PR label
   if gh pr view $PR_NUMBER --json labels --jq '.labels[].name' | grep -q "skip-version-check"; then
     SKIP_VERSION_CHECK=true
     echo "⚠️ Version validation bypassed via GitHub label"
   fi

   # Check PR description
   if gh pr view $PR_NUMBER --json body --jq '.body' | grep -q "\[skip-version-check\]"; then
     SKIP_VERSION_CHECK=true
     echo "⚠️ Version validation bypassed via PR description marker"
   fi
   ```

2. **Detect version changes in PR diff**
   ```bash
   # Key version files to check
   VERSION_FILES=(
     ".claude-plugin/marketplace.json"
     "CHANGELOG.md"
     "CHANGELOG"
     "package.json"
     "pyproject.toml"
     "Cargo.toml"
     "setup.py"
     "VERSION"
   )

   VERSION_CHANGED=false
   for file in "${VERSION_FILES[@]}"; do
     if gh pr diff $PR_NUMBER --name-only | grep -qF "$file"; then
       # Check if version-related lines changed
       if gh pr diff $PR_NUMBER | grep -qE "^\+.*version|^\+.*## \["; then
         VERSION_CHANGED=true
         echo "Version change detected in $file"
         break
       fi
     fi
   done

   # If no version changed and not a release PR, skip validation
   if [[ "$VERSION_CHANGED" == "false" ]]; then
     echo "✅ Version validation: N/A (no version files changed)"
     # Skip to Phase 2
   fi
   ```

3. **Run detailed version validation**

   If version files changed, invoke the version validation module:

   ```bash
   # Load module
   # See: plugins/sanctum/skills/pr-review/modules/version-validation.md

   # Project type detection
   PROJECT_TYPE=""
   if [[ -f ".claude-plugin/marketplace.json" ]]; then
     PROJECT_TYPE="claude-marketplace"
   elif [[ -f "pyproject.toml" ]]; then
     PROJECT_TYPE="python"
   elif [[ -f "package.json" ]]; then
     PROJECT_TYPE="node"
   elif [[ -f "Cargo.toml" ]]; then
     PROJECT_TYPE="rust"
   fi

   # Run validations based on project type
   ```

4. **For Claude Marketplace Projects**

   ```bash
   if [[ "$PROJECT_TYPE" == "claude-marketplace" ]]; then
     echo "### Version Validation: Claude Marketplace"

     # Get ecosystem version
     ECOSYSTEM_VERSION=$(jq -r '.metadata.version' .claude-plugin/marketplace.json)
     echo "Ecosystem version: $ECOSYSTEM_VERSION"

     # Check each plugin in marketplace matches actual plugin.json
     MISMATCHES=()
     jq -r '.plugins[] | "\(.name):\(.version)"' .claude-plugin/marketplace.json | while IFS=: read -r name version; do
       if [[ -f "plugins/$name/.claude-plugin/plugin.json" ]]; then
         ACTUAL_VERSION=$(jq -r '.version' "plugins/$name/.claude-plugin/plugin.json")

         if [[ "$version" != "$ACTUAL_VERSION" ]]; then
           MISMATCHES+=("$name: marketplace=$version, actual=$ACTUAL_VERSION")
           echo "[B-VERSION] Version mismatch for $name"
           echo "  Marketplace (.claude-plugin/marketplace.json): $version"
           echo "  Actual (plugins/$name/.claude-plugin/plugin.json): $ACTUAL_VERSION"
           echo "  Fix: Update marketplace.json to match actual version"
         else
           echo "  ✓ $name: $version"
         fi
       fi
     done

     # Check CHANGELOG has entry for new version
     if [[ -f "CHANGELOG.md" ]]; then
       if ! grep -q "\[$ECOSYSTEM_VERSION\]" CHANGELOG.md; then
         echo "[B-VERSION] CHANGELOG.md missing entry for version $ECOSYSTEM_VERSION"
         echo "  Fix: Add release entry to CHANGELOG.md"
       else
         echo "  ✓ CHANGELOG.md has entry for $ECOSYSTEM_VERSION"

         # Check if marked as Unreleased
         if grep -q "\[$ECOSYSTEM_VERSION\] - Unreleased" CHANGELOG.md; then
           echo "[G-VERSION] CHANGELOG shows $ECOSYSTEM_VERSION as Unreleased"
           echo "  Suggestion: Update release date before merge"
         fi
       fi
     fi

     # Add to blocking issues if any mismatches found
     if [[ ${#MISMATCHES[@]} -gt 0 ]]; then
       echo ""
       echo "❌ Version validation FAILED - ${#MISMATCHES[@]} issues found"
       # These will be added to blocking issues in Phase 3
     else
       echo ""
       echo "✅ Version validation PASSED"
     fi
   fi
   ```

5. **Classification of version issues**

   All version validation findings are classified as:

   | Issue Type | Severity | Example |
   |------------|----------|---------|
   | Version mismatch between files | **BLOCKING** | marketplace.json says 1.1.1, plugin.json says 1.2.0 |
   | Missing CHANGELOG entry | **BLOCKING** | Version bumped but no CHANGELOG entry |
   | CHANGELOG marked Unreleased | **SUGGESTION** | Release date not set |
   | README references old version | **IN-SCOPE** | Documentation accuracy issue |
   | __version__ mismatch | **BLOCKING** | Python: pyproject.toml vs __init__.py |

6. **If bypass enabled**

   ```bash
   if [[ "$SKIP_VERSION_CHECK" == "true" ]]; then
     # Still run validation but classify as WAIVED instead of BLOCKING
     echo ""
     echo "⚠️ Version validation issues WAIVED by maintainer"
     echo "Issues found will be marked as [WAIVED] instead of [BLOCKING]"

     # Convert all [B-VERSION] to [WAIVED-VERSION] in findings
   fi
   ```

**Output from this phase:**

A version validation section that will be included in the final PR review:

```markdown
### Version Validation

**Status:** ✅ PASSED | ⚠️ WAIVED | ❌ FAILED

**Ecosystem Version:** 1.1.0 → 1.1.1

**Validation Results:**
- [x] Marketplace version: 1.1.1 ✓
- [x] Plugin versions: 11 plugins at 1.1.1 ✓
- [ ] memory-palace: Marketplace=1.1.1, Actual=1.2.0 ❌ MISMATCH
- [x] CHANGELOG.md: Entry for 1.1.1 ✓
- [x] README.md: Version references current ✓

**Blocking Issues:**
- [B-VERSION-1] Version mismatch for memory-palace (see details above)

**Suggestions:**
- [G-VERSION-1] CHANGELOG release date shows "Unreleased" - update before merge
```

**This section is PREPENDED to the review summary** so version issues are the first thing reviewers see.

### Phase 2: Code Analysis (Superpowers)

4. **detailed Code Review**
   ```bash
   Skill(superpowers:receiving-code-review)
   ```
   - Analyzes all changed files
   - Checks against best practices
   - Identifies potential issues
   - Suggests improvements

5. **Quality Classification**
   - Security vulnerabilities
   - Performance issues
   - Maintainability concerns
   - Test coverage gaps

### Phase 3: Synthesis & Validation

6. **Scope-Aware Triage**
   Each finding evaluated against scope:

   | Finding Type | In Scope? | Action |
   |--------------|-----------|--------|
   | Bug introduced by change | Always | Block |
   | Missing requirement | Yes | Block |
   | Security issue | Always | Block |
   | Refactoring suggestion | No | Backlog |
   | Style improvement | No | Ignore |
   | Performance optimization | No | Backlog |

7. **Generate Structured Report**
   Combines scope validation with code analysis

### Phase 4: GitHub Review Submission (MANDATORY)

After generating findings, you MUST post them to GitHub as PR review comments.

8. **Determine PR Number and Check Authorship**
   ```bash
   # Get PR number if not provided
   PR_NUMBER=$(gh pr view --json number -q '.number')

   # CRITICAL: Check if reviewing own PR (approval will fail)
   PR_AUTHOR=$(gh pr view $PR_NUMBER --json author -q '.author.login')
   CURRENT_USER=$(gh api user -q '.login')
   IS_OWN_PR=$([[ "$PR_AUTHOR" == "$CURRENT_USER" ]] && echo "true" || echo "false")

   # If own PR, can only use COMMENT event (not APPROVE/REQUEST_CHANGES)
   if [[ "$IS_OWN_PR" == "true" ]]; then
     echo "Note: Reviewing own PR - will use COMMENT event"
   fi
   ```

9. **Get PR Diff and Head Commit**
   ```bash
   # Get head commit (required for review API)
   COMMIT_ID=$(gh pr view $PR_NUMBER --json headRefOid -q '.headRefOid')

   # Get the diff to identify which lines are reviewable
   gh pr diff $PR_NUMBER > /tmp/pr_diff.txt
   ```

10. **Post Line-Specific Comments via Reviews API**

   **IMPORTANT:** Use the reviews endpoint with a comments array. The individual comments endpoint does NOT support `line`/`side` parameters reliably.

   For findings on lines IN THE DIFF:
   ```bash
   # Use the reviews API with comments array
   # Note: -F for integers, -f for strings
   gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
     --method POST \
     -f event="COMMENT" \
     -f body="Inline comments attached." \
     -f 'comments[][path]=middleware/auth.py' \
     -F 'comments[][line]=45' \
     -f 'comments[][body]=**[B1] Missing token validation**

   Issue: Always returns True, validation not implemented
   Severity: BLOCKING

   **Fix:** Implement JWT signature verification'
   ```

   **For multiple inline comments in one review:**
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
     --method POST \
     -f event="COMMENT" \
     -f body="Review with inline comments" \
     -f 'comments[0][path]=middleware/auth.py' \
     -F 'comments[0][line]=45' \
     -f 'comments[0][body]=**[B1] Issue description**' \
     -f 'comments[1][path]=models/user.py' \
     -F 'comments[1][line]=123' \
     -f 'comments[1][body]=**[B2] Another issue**'
   ```

   **For findings on lines NOT in the diff** (suggestions on unchanged code):
   ```bash
   # Fall back to PR comment (not inline)
   gh pr comment $PR_NUMBER --body "**[G2] Suggestion for unchanged code**

   Location: app.rs:1933 (not in PR diff - general observation)

   Consider further modularization as this file approaches size thresholds.

   **Suggestion:** Extract SkillCache to its own module."
   ```

11. **Submit Review with Summary**
    ```bash
    # Determine review event based on findings AND authorship
    if [[ "$IS_OWN_PR" == "true" ]]; then
      # Can only comment on own PRs
      EVENT="COMMENT"
    elif [[ $BLOCKING_COUNT -gt 0 ]]; then
      EVENT="REQUEST_CHANGES"
    elif [[ $IN_SCOPE_COUNT -gt 0 ]]; then
      EVENT="COMMENT"
    else
      EVENT="APPROVE"
    fi

    gh pr review $PR_NUMBER \
      --event $EVENT \
      --body "$(cat <<'EOF'
    ## PR Review Summary

    ### Blocking Issues (2)
    - [B1] Missing token validation (middleware/auth.py:45)
    - [B2] SQL injection vulnerability (models/user.py:123)

    ### In-Scope Issues (3)
    - [S1] Password reset flow missing
    - [S2] Error handling incomplete

    ### Suggestions (4)
    - See inline comments for details

    **Action Required:** Address blocking issues B1-B2 before merge.

    ---
    *Review generated by Claude Code PR Review*
    EOF
    )"
    ```

**Review Event Selection:**
| Condition | Own PR? | Event |
|-----------|---------|-------|
| Any findings | Yes | `COMMENT` (approval blocked by GitHub) |
| No blocking issues, no in-scope issues | No | `APPROVE` |
| No blocking issues, has in-scope issues | No | `COMMENT` |
| Has blocking issues | No | `REQUEST_CHANGES` |

**Comment Format for Line Comments:**
```markdown
**[ID] Title**

Issue: <description>
Severity: BLOCKING | IN_SCOPE | SUGGESTION

**Fix:** <recommended action>
```

**Key API Differences:**
| Endpoint | Use Case | Notes |
|----------|----------|-------|
| `gh api .../pulls/{n}/reviews` | Inline comments on diff lines | Use `-F` for line numbers (integers) |
| `gh pr comment` | General comments, lines not in diff | Simple, always works |
| `gh pr review` | Summary submission | Use after inline comments |

12. **Document Created Threads for `/fix-pr`**
    After posting all comments, output a summary that can be used by `/fix-pr`:
    ```markdown
    ### Review Threads Created

    | Issue ID | Comment ID | File:Line | Severity | Description |
    |----------|------------|-----------|----------|-------------|
    | B1 | 12345678 | middleware/auth.py:45 | BLOCKING | Missing token validation |
    | B2 | 12345679 | models/user.py:123 | BLOCKING | SQL injection vulnerability |
    | S1 | 12345680 | routes/auth.py:78 | IN_SCOPE | Missing error handling |

    **To resolve these threads after fixing, run:** `/fix-pr {pr_number}`
    ```

    This enables `/fix-pr` to:
    - Reply to each thread with the fix description
    - Resolve the threads via GraphQL
    - Verify all issues have been addressed

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

## Options

- `--scope-mode`: Set strictness level (default: standard)
  - `strict`: All requirements must be complete
  - `standard`: Core requirements required
  - `flexible`: MVP implementation acceptable
- `--auto-approve-safe-prs`: Auto-approve PRs with no issues
- `--create-backlog-issues`: Create GitHub issues for improvements
- `--dry-run`: Generate report locally without posting to GitHub
- `--no-line-comments`: Skip individual line comments, only submit summary review
- `--skip-version-check`: **BYPASS version validation** (maintainer override)
  - Use when: intentional version skew, non-release PR touching version files
  - Alternative: Add `skip-version-check` label to PR or `[skip-version-check]` in PR description
  - **Still runs validation** but marks issues as [WAIVED] instead of [BLOCKING]
- `pr-number`/`pr-url`: Target specific PR (default: current branch)

## Review Classification Framework

### Blocking Issues
Must fix before merge:
- **Version mismatches** (marketplace vs actual, CHANGELOG missing, etc.)
- Bugs introduced by this change
- Security vulnerabilities
- Breaking changes without migration
- Missing core requirements
- Test failures in new code

### In-Scope Issues
Should address in this PR:
- Incomplete requirement implementation
- Missing error handling specified in requirements
- Performance issues affecting feature
- Edge cases not covered

### Suggestions (Author's Discretion)
Nice improvements:
- Better variable names
- Minor optimizations
- Additional test cases
- Documentation improvements

### Backlog Items
Create GitHub issues (primary storage):
- Refactoring opportunities
- "While we're here" improvements
- Feature expansions
- Technical debt in adjacent code

**Important**: GitHub issues are the source of truth for backlog items. Reference existing `docs/backlog/*.md` files for context (e.g., `docs/backlog/queue.md`, `docs/backlog/technical-debt.md`) to avoid duplicates.

## Enhanced Example

```bash
/pr-review 42 --scope-mode standard --create-backlog-issues
```

### Sample Output

```markdown
## PR #42: Add user authentication system

### Scope Compliance Analysis
**Source:** docs/plans/2025-12-01-auth-design.md

**Requirements:**
1. [x] JWT token generation - Implemented in auth.py
2. [x] Password hashing with bcrypt - Implemented in utils.py
3. [x] Login endpoint - Implemented in routes/auth.py
4. [x] Token validation middleware - Partially implemented
5. [ ] Password reset flow - **Missing**

### Superpowers Code Analysis
**Files Changed:** 12 files, +542/-89 lines
**Coverage:** New code 85% covered

### Blocking Issues (2)
> Must fix before merge

1. **[B1] Missing token validation**
   - Location: middleware/auth.py:45
   - Issue: Always returns True, validation not implemented
   - Superpowers finding: Critical security gap
   - Fix: Implement JWT signature verification

2. **[B2] SQL injection vulnerability**
   - Location: models/user.py:123
   - Issue: String interpolation in query
   - Superpowers finding: High severity security issue
   - Fix: Use parameterized queries

### In-Scope Issues (3)
> Related to requirements

1. **[S1] Password reset flow missing**
   - Requirement: "Users must be able to reset passwords"
   - Status: Not implemented
   - Fix: Add password reset endpoints and email handling

2. **[S2] Error handling incomplete**
   - Location: auth.py:78
   - Issue: No error handling for invalid tokens
   - Fix: Add try/catch with proper error responses

### Suggestions (4)
> Author's discretion

1. **[G1] Add rate limiting to login endpoint**
   - Superpowers recommendation: Prevent brute force attacks
   - Location: routes/auth.py:23

2. **[G2] Consider using refresh tokens**
   - Superpowers finding: Better security pattern
   - Location: auth.py:45

### Backlog → GitHub Issues Created (5)
> Out of scope for this PR

1. #247 - Add two-factor authentication support
2. #248 - Implement user roles and permissions
3. #249 - Add audit logging for authentication events
4. #250 - Social login integration (OAuth2)
5. #251 - Session management dashboard

### Recommendation
**REQUEST CHANGES**
Address blocking issues B1-B2 and in-scope issue S1 before merge.
Implementation looks promising once core requirements are complete.
```

## Scope Mode Details

### Strict Mode
All requirements must be fully implemented:
- No missing features
- Complete error handling
- Full test coverage
- Documentation complete

### Standard Mode (Default)
Core functionality required:
- Main features working
- Basic error handling
- Critical tests passing
- Essential documentation

### Flexible Mode
MVP acceptable:
- Basic functionality works
- Critical path tested
- Security requirements met
- Future work tracked

## Advanced Features

### 1. Automated Issue Creation
```bash
# For each backlog item:
gh issue create \
  --title "[Enhancement] <title>" \
  --body="## Context
Identified during PR #<number> review

## Details
<finding details>

## Suggested Approach
<implementation notes>

## Priority
Medium - Improvement opportunity

---
*Auto-created by pr-review*" \
  --label="enhancement,backlog"
```

### 2. Quality Metrics Integration
```markdown
### Quality Metrics
- **Code Coverage**: 85% (target: 80%) PASS
- **Complexity**: Low (new functions < 10 cyclomatic) PASS
- **Duplication**: 2% (target: <5%) PASS
- **Security**: 0 high-severity issues PASS
```

### 3. Reviewer Guidance
```markdown
### Review Focus Areas
Based on scope and analysis:
1. Verify JWT implementation (security)
2. Check password hashing (security)
3. Validate error handling (robustness)
4. Review test coverage (quality)
```

## Integration Benefits

### For Reviewers
- Clear understanding of PR scope
- Prioritized feedback (blocking vs suggestions)
- Context-aware recommendations
- Reduced review time through automation

### For Authors
- Specific, actionable feedback
- Clear path to approval
- Backlog items automatically created
- Quality metrics provided

### For Teams
- Consistent review standards
- Scope discipline enforced
- Technical debt tracked
- Quality gates automated

## Error Handling

### No Scope Artifacts Found
```markdown
Warning: No plan/spec found for this PR
Using PR description as scope baseline
Recommendation: Create plan.md for future PRs
```

### Analysis Failures
```bash
Error: Superpowers code review failed
Falling back to manual review mode
```

### GitHub API Issues
```bash
Warning: Cannot create backlog issues (rate limit)
Please create manually from backlog section
```

### GitHub Review Submission Errors

**No PR Found:**
```bash
# If no PR exists for current branch
gh pr view --json number -q '.number'
# Returns empty - skip GitHub submission
Warning: No PR found for current branch. Review saved locally only.
```

**Cannot Approve Own PR:**
```bash
# Error: "Review Can not approve your own pull request"
# This occurs when using --approve or REQUEST_CHANGES on your own PR

# SOLUTION: Check authorship first, use COMMENT event for own PRs
PR_AUTHOR=$(gh pr view $PR_NUMBER --json author -q '.author.login')
CURRENT_USER=$(gh api user -q '.login')
if [[ "$PR_AUTHOR" == "$CURRENT_USER" ]]; then
  # Use COMMENT instead of APPROVE/REQUEST_CHANGES
  gh pr review $PR_NUMBER --comment --body "Review summary..."
fi
```

**Line Comment API Errors:**
```bash
# Error: "line is not a permitted key" or "No subschema in oneOf matched"
# This happens when using the comments endpoint with line/side parameters

# WRONG - Individual comments endpoint doesn't support line/side:
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f body="..." -f path="file.rs" -f line=45 -f side="RIGHT"  # FAILS

# CORRECT - Use the reviews endpoint with comments array:
gh api repos/{owner}/{repo}/pulls/{pr}/reviews \
  --method POST \
  -f event="COMMENT" \
  -f body="" \
  -f 'comments[][path]=file.rs' \
  -F 'comments[][line]=45' \              # Note: -F for integer
  -f 'comments[][body]=Comment text'
```

**Line Not In Diff (422 Unprocessable Entity):**
```bash
# Error: "Line could not be resolved"
# This occurs when the line number isn't part of the PR diff

# SOLUTION: Post as a general PR comment instead
gh pr comment $PR_NUMBER --body "**[G2] Suggestion**

Location: app.rs:1933 (not in PR diff - general observation)
Issue: File approaching size threshold

**Suggestion:** Consider modularization."
```

**Integer vs String Parameters:**
```bash
# Error: "128 is not an integer" (when passed as string)

# WRONG - Using -f passes as string:
-f 'comments[][line]=128'

# CORRECT - Using -F passes as raw/integer:
-F 'comments[][line]=128'
```

**Pending Review Already Exists:**
```bash
# Check for existing pending review
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --jq '.[] | select(.state == "PENDING")'

# If pending review exists, add comments to it instead of creating new
# Use the existing review_id for subsequent comments
```

**Authentication Issues:**
```bash
# Verify gh is authenticated
gh auth status
# If not authenticated, proceed with dry-run mode
Warning: GitHub CLI not authenticated. Running in dry-run mode.
```

## Configuration

```yaml
pr_review:
  default_scope_mode: "standard"
  auto_approve_threshold: 0  # No blocking issues
  create_backlog_issues: true
  require_test_coverage: true
  min_coverage_percent: 80

  quality_gates:
    max_complexity: 10
    max_duplication: 5
    require_documentation: true

  backlog_settings:
    auto_create: true
    default_priority: "medium"
    assign_to_author: false
```

## Best Practices

### Before Review
1. validate PR description is clear
2. Verify CI pipeline passed
3. Check for scope artifacts
4. Confirm tests are running

### During Review
1. Establish scope baseline first
2. Classify findings consistently
3. Provide actionable feedback
4. Create issues for improvements

### After Review
1. Verify all issues are tracked
2. Check recommendation accuracy
3. Update scope artifacts if needed
4. Follow up on backlog items

## Migration Notes

- `/pr-review` now includes the enhanced superpowers-driven workflow (formerly `/pr-review-wrapper`).
- Options like `--scope-mode` and `--create-backlog-issues` remain unchanged.

## Notes

- Maintains full backward compatibility with /pr-review
- Requires superpowers plugin for enhanced analysis
- GitHub CLI (`gh`) required for review submission and issue creation
- All Sanctum scope validation preserved
- Adds detailed code quality checks
- **Automatically posts findings as GitHub PR review comments**
- **⚠️ MUST post test plan as a SEPARATE PR comment** (for `/fix-pr` integration)
  - This is NOT optional - test plan must be a distinct `gh pr comment` call
  - Do NOT just include in review summary or conversational output
  - `/fix-pr` searches for "Test Plan for PR" to find verification steps
- Use `--dry-run` to generate report without posting to GitHub
- Use `--no-line-comments` to only submit summary without inline comments
- Test plan includes verification steps for all blocking and in-scope issues

### Version Validation Enforcement (NEW)

**MANDATORY on every PR** unless explicitly bypassed:
- Runs in Phase 1.5 (after scope, before code analysis)
- Checks version consistency across:
  - Claude marketplace: marketplace.json ↔ plugin.json files
  - Python: pyproject.toml ↔ __version__ in code
  - Node: package.json ↔ package-lock.json
  - Rust: Cargo.toml ↔ Cargo.lock
  - CHANGELOG: Has entry for new version
- **All version mismatches are BLOCKING** (unless waived)
- Bypass with: `--skip-version-check`, `skip-version-check` label, or `[skip-version-check]` in PR description
- See `modules/version-validation.md` for complete validation procedures

## See Also

- `/fix-pr` - Address PR review comments and resolve threads
- `/resolve-threads` - Batch-resolve unresolved review threads
- `/pr` - Prepare a PR for submission
