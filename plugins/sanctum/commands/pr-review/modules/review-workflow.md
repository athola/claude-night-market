# PR/MR Review: Workflow Details

Detailed workflow phases, examples, and advanced features.

> **See Also**: [Main Command](../../pr-review.md) | [Framework](review-framework.md) | [Configuration](review-configuration.md)

**Platform Note**: Commands below show GitHub (`gh`) examples. Check session context for `git_platform:` and consult `Skill(leyline:git-platform)` for GitLab (`glab`) / Bitbucket equivalents.

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

     # Get ecosystem version from pyproject.toml (source of truth)
     ECOSYSTEM_VERSION=$(grep -E '^version\s*=' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')
     echo "Ecosystem version (pyproject.toml): $ECOSYSTEM_VERSION"

     # Check CHANGELOG has entry for new version
     if [[ -f "CHANGELOG.md" ]]; then
       if ! grep -q "\[$ECOSYSTEM_VERSION\]" CHANGELOG.md; then
         echo "[B-VERSION] CHANGELOG.md missing entry for version $ECOSYSTEM_VERSION"
         echo "  Fix: Add release entry to CHANGELOG.md"
       else
         echo "  ✓ CHANGELOG.md has entry for $ECOSYSTEM_VERSION"
       fi
     fi

     # Check pyproject.toml versions across all plugins
     PYPROJECT_MISMATCHES=()
     for pyproject in plugins/*/pyproject.toml; do
       PLUGIN_NAME=$(dirname "$pyproject" | xargs basename)
       PLUGIN_VERSION=$(grep -E '^version\s*=' "$pyproject" | head -1 | sed 's/.*"\(.*\)".*/\1/')

       if [[ "$PLUGIN_VERSION" != "$ECOSYSTEM_VERSION" ]]; then
         PYPROJECT_MISMATCHES+=("$PLUGIN_NAME: pyproject=$PLUGIN_VERSION, expected=$ECOSYSTEM_VERSION")
         echo "[B-VERSION] pyproject.toml version mismatch for $PLUGIN_NAME"
         echo "  Expected: $ECOSYSTEM_VERSION"
         echo "  Actual (plugins/$PLUGIN_NAME/pyproject.toml): $PLUGIN_VERSION"
         echo "  Fix: Update plugin pyproject.toml to match ecosystem version"
       fi
     done

     # Check plugin.json versions match pyproject.toml (BLOCKING)
     PLUGIN_JSON_MISMATCHES=()
     for plugin_json in plugins/*/.claude-plugin/plugin.json; do
       PLUGIN_NAME=$(dirname "$(dirname "$plugin_json")" | xargs basename)
       JSON_VERSION=$(jq -r '.version' "$plugin_json")
       PYPROJECT_VERSION=$(grep -E '^version\s*=' "plugins/$PLUGIN_NAME/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')

       if [[ "$JSON_VERSION" != "$PYPROJECT_VERSION" ]]; then
         PLUGIN_JSON_MISMATCHES+=("$PLUGIN_NAME: plugin.json=$JSON_VERSION, pyproject.toml=$PYPROJECT_VERSION")
         echo "[B-VERSION] plugin.json version mismatch for $PLUGIN_NAME"
         echo "  plugin.json: $JSON_VERSION"
         echo "  pyproject.toml: $PYPROJECT_VERSION (source of truth)"
         echo "  Fix: Update plugin.json to match pyproject.toml version"
       else
         echo "  ✓ $PLUGIN_NAME: $JSON_VERSION"
       fi
     done

     # Legacy: Check marketplace.json if it exists
     if [[ -f ".claude-plugin/marketplace.json" ]]; then
       jq -r '.plugins[] | "\(.name):\(.version)"' .claude-plugin/marketplace.json | while IFS=: read -r name version; do
         if [[ -f "plugins/$name/.claude-plugin/plugin.json" ]]; then
           ACTUAL_VERSION=$(jq -r '.version' "plugins/$name/.claude-plugin/plugin.json")

           if [[ "$version" != "$ACTUAL_VERSION" ]]; then
             echo "[B-VERSION] Marketplace version mismatch for $name"
             echo "  Marketplace (.claude-plugin/marketplace.json): $version"
             echo "  Actual (plugins/$name/.claude-plugin/plugin.json): $ACTUAL_VERSION"
             echo "  Fix: Update marketplace.json to match actual version"
           fi
         fi
       done
     fi

     # Summary: Report all mismatches found
     TOTAL_MISMATCHES=$((${#PYPROJECT_MISMATCHES[@]} + ${#PLUGIN_JSON_MISMATCHES[@]}))
     if [[ $TOTAL_MISMATCHES -gt 0 ]]; then
       echo ""
       echo "❌ Version validation FAILED - $TOTAL_MISMATCHES issues found"
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
   | Branch name version ≠ project version | **BLOCKING** | Branch `skills-improvements-1.2.2` but pyproject.toml shows 1.2.1 |
   | pyproject.toml version mismatch | **BLOCKING** | Root pyproject.toml says 1.2.9, plugin says 1.2.6 |
   | plugin.json ≠ pyproject.toml | **BLOCKING** | plugin.json says 1.2.6, pyproject.toml says 1.2.9 |
   | marketplace.json ≠ plugin.json | **BLOCKING** | marketplace.json says 1.1.1, plugin.json says 1.2.0 |
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

**Branch Name:** skills-improvements-1.2.2
**Ecosystem Version:** 1.1.0 → 1.2.1

**Validation Results:**
- [ ] Branch name version: 1.2.2 ≠ Marketplace version: 1.2.1 ❌ MISMATCH
- [x] Marketplace version: 1.2.1 ✓
- [x] Plugin versions: 11 plugins at 1.2.1 ✓
- [ ] memory-palace: Marketplace=1.2.1, Actual=1.2.0 ❌ MISMATCH
- [x] CHANGELOG.md: Entry for 1.2.1 ✓
- [x] README.md: Version references current ✓

**Blocking Issues:**
- [B-VERSION-1] Branch name suggests version 1.2.2, but marketplace version is 1.2.1
  - Fix: Update marketplace.json to 1.2.2 OR rename branch to match 1.2.1
- [B-VERSION-2] Version mismatch for memory-palace (see details above)

**Suggestions:**
- [G-VERSION-1] CHANGELOG release date shows "Unreleased" - update before merge
```

**This section is PREPENDED to the review summary** so version issues are the first thing reviewers see.

### Phase 1.7: Slop Detection (MANDATORY)

**Run AI slop detection on documentation and commit messages BEFORE code review.**

This phase uses `Skill(scribe:slop-detector)` to identify AI-generated content markers.

1. **Scan Changed Documentation**
   ```bash
   # Get all changed .md files
   MD_FILES=$(gh pr diff $PR_NUMBER --name-only | grep -E '\.md$')

   for file in $MD_FILES; do
     # Invoke slop detection
     echo "Scanning $file for AI slop..."
     # Apply scribe:slop-detector patterns
   done
   ```

2. **Scan Commit Messages**
   ```bash
   # Extract all commit messages
   gh pr view $PR_NUMBER --json commits --jq '.commits[] | .messageHeadline + "\n" + .messageBody' > /tmp/commits.txt

   # Check for tier-1 slop words
   SLOP_WORDS="leverage|seamless|comprehensive|delve|robust|utilize|facilitate|streamline|multifaceted|pivotal|intricate|nuanced"
   SLOP_FOUND=$(grep -iE "$SLOP_WORDS" /tmp/commits.txt || true)

   if [[ -n "$SLOP_FOUND" ]]; then
     echo "⚠️ AI slop detected in commit messages:"
     echo "$SLOP_FOUND"
   fi
   ```

3. **Scan PR Description**
   ```bash
   gh pr view $PR_NUMBER --json body --jq '.body' | \
     grep -iE 'leverage|seamless|comprehensive|delve|robust|utilize' && \
     echo "⚠️ Slop markers in PR description"
   ```

4. **Classification of Slop Findings**

   | Location | Score | Severity | Action |
   |----------|-------|----------|--------|
   | Documentation | ≥5.0 | BLOCKING (if --strict) | Must remediate |
   | Documentation | 3.0-4.9 | IN-SCOPE | Should remediate |
   | Documentation | <3.0 | SUGGESTION | Optional cleanup |
   | Commit messages | Any tier-1 | SUGGESTION | Note for future |
   | PR description | Any tier-1 | SUGGESTION | Recommend rephrase |

**Output from this phase:**

```markdown
### Slop Detection Results

**Documentation Scanned**: 3 files
**Overall Score**: 2.8/10 (Light)

| File | Score | Top Issues |
|------|-------|------------|
| README.md | 1.2 | Clean |
| docs/guide.md | 4.1 | "comprehensive", "leverage" |
| CHANGELOG.md | 0.5 | Clean |

**Commit Messages**: 1 slop marker found
- "feat: leverage new API" → suggest: "feat: use new API"

**Recommendations**:
- Run `/doc-polish docs/guide.md` to remediate
- Consider rewording commit message for clarity
```

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

### Phase 2.5: Code Quality Analysis (MANDATORY)

**CRITICAL: This phase is MANDATORY for all PR reviews. There is NO bypass mechanism.**

**⚠️ ENFORCEMENT CHECK: This phase MUST complete with duplication and redundancy findings documented.**
**If you skip this phase, the workflow is INCOMPLETE.**

Invokes `pensive:code-refinement` patterns:

6. **Duplication & Redundancy Scan**
   ```bash
   # Analyze only changed files for duplication
   CHANGED_FILES=$(gh pr diff $PR_NUMBER --name-only | grep -E '\.(py|ts|js|rs|go)$')

   # Run targeted quality analysis
   # See: pensive:code-refinement
   ```

   **Invoke the full skill:**
   ```
   Skill(pensive:code-refinement)
   ```

   Analysis dimensions (from `pensive:code-refinement`):
   - **Duplication & Redundancy**: Hash-based detection, similar functions, copy-paste
   - **Algorithmic Efficiency**: Time/space complexity, O(n^2) where O(n) works, unnecessary iterations
   - **Clean Code Violations**: Long methods, deep nesting, poor naming, magic values
   - **Architectural Fit**: Coupling violations, paradigm mismatches, leaky abstractions
   - **Anti-Slop Patterns**: Premature abstraction, enterprise cosplay, hollow patterns
   - **Error Handling**: Bare excepts, swallowed errors, happy-path-only code

7. **Quality Findings Classification**

   | Finding | Severity | Action |
   |---------|----------|--------|
   | Exact duplication >10 lines | BLOCKING | Must consolidate |
   | Similar functions 3+ occurrences | IN-SCOPE | Should refactor |
   | Repeated patterns | SUGGESTION | Author discretion |
   | Minor redundancy | SUGGESTION | Optional cleanup |

**Output**: Code quality findings added to review report with consolidation strategies.

### Phase 2.5 Completion Checklist

Before proceeding to Phase 3, verify ALL items are complete:

- [ ] Duplication scan executed on all changed files
- [ ] Redundancy patterns analyzed
- [ ] Findings classified (BLOCKING/IN-SCOPE/SUGGESTION)
- [ ] Consolidation strategies documented for each finding

**If any item above is unchecked, GO BACK and complete Phase 2.5.**

**This phase is NON-NEGOTIABLE. Skipping code quality analysis = incomplete review.**

### Phase 3: Synthesis & Validation

6. **Scope-Aware Triage**
   Each finding evaluated against scope:

   | Finding Type | In Scope? | Action |
   |--------------|-----------|--------|
   | Bug introduced by change | Always | Block |
   | Missing requirement | Yes | Block |
   | Security issue | Always | Block |
   | Refactoring suggestion | No | Backlog → Auto-create issue |
   | Style improvement | No | Ignore |
   | Performance optimization | No | Backlog → Auto-create issue |

7. **Generate Structured Report**
   Combines scope validation with code analysis

8. **Auto-Create Issues for Backlog Items (AUTOMATIC)**

   > **Module Reference**: Auto-issue creation is handled inline by the workflow monitor.

   Items classified as "Backlog" or "Out-of-Scope" are automatically logged to GitHub:

   ```bash
   # For each backlog item
   for item in "${BACKLOG_ITEMS[@]}"; do
     # Check for duplicates first
     EXISTING=$(gh issue list --search "$ITEM_TITLE in:title is:open" --json number --jq '.[0].number // empty')

     if [[ -z "$EXISTING" ]]; then
       # Create issue with appropriate labels
       ISSUE_URL=$(gh issue create \
         --title "[Suggestion] $ITEM_TITLE" \
         --body "## Context
   Identified during PR #$PR_NUMBER review as out-of-scope improvement.

   **Location:** \`$FILE_PATH\`

   ## Description
   $ITEM_DESCRIPTION

   ---
   *Auto-created by /pr-review*" \
         --label "enhancement,low-priority")

       CREATED_ISSUES+=("$ISSUE_URL")
     else
       SKIPPED_ISSUES+=("$ITEM_TITLE (duplicate of #$EXISTING)")
     fi
   done
   ```

   **Report created issues in review summary:**
   ```markdown
   ### Issues Created (Automatic)

   | Title | Issue | Labels |
   |-------|-------|--------|
   | Improve error messages | #115 | enhancement, low-priority |
   | Add rate limiting | #116 | enhancement, low-priority |

   **Skipped (duplicates):** 1
   ```

   **To skip**: Use `--no-auto-issues` flag

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

   **For multiple inline comments in one review (use JSON input):**
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
     --method POST \
     --input - <<'EOF'
   {
     "event": "COMMENT",
     "body": "Review with inline comments",
     "comments": [
       {
         "path": "middleware/auth.py",
         "line": 45,
         "side": "RIGHT",
         "body": "**[B1] Issue description**"
       },
       {
         "path": "models/user.py",
         "line": 123,
         "side": "RIGHT",
         "body": "**[B2] Another issue**"
       }
     ]
   }
   EOF
   ```

   **Note:** The indexed array syntax (`comments[0][path]`) does NOT work - always use JSON input for multiple comments.

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

---

## Mandatory Outputs Enforcement

**CRITICAL: The /pr-review command is NOT complete unless ALL of these outputs exist:**

| Output | Phase | Verification |
|--------|-------|--------------|
| Review comment | Phase 4 | `gh pr view --json comments` contains "PR Review" |
| Test plan comment | Phase 5 | `gh pr view --json comments` contains "Test Plan" |
| PR description | Phase 6 | `gh pr view --json body` is non-empty and contains "Review Summary" |

**Enforcement Check (run at end of review):**

```bash
# Validate all mandatory outputs
PR_NUMBER=${1:-$(gh pr view --json number -q '.number')}

REVIEW_EXISTS=$(gh pr view $PR_NUMBER --json comments --jq '[.comments[].body | contains("PR Review")] | any')
TEST_PLAN_EXISTS=$(gh pr view $PR_NUMBER --json comments --jq '[.comments[].body | ascii_downcase | contains("test plan")] | any')
DESCRIPTION_EXISTS=$(gh pr view $PR_NUMBER --json body --jq '.body | length > 0')

echo "=== Mandatory Output Verification ==="
echo "Review comment:  $( [[ $REVIEW_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"
echo "Test plan:       $( [[ $TEST_PLAN_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"
echo "PR description:  $( [[ $DESCRIPTION_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"

if [[ $REVIEW_EXISTS != "true" ]] || [[ $TEST_PLAN_EXISTS != "true" ]] || [[ $DESCRIPTION_EXISTS != "true" ]]; then
  echo ""
  echo "⚠️  PR review INCOMPLETE - mandatory outputs missing"
  echo "Run /pr-review-enforcer $PR_NUMBER to fix"
  exit 1
fi

echo ""
echo "✅ All mandatory outputs verified for PR #$PR_NUMBER"
```

**If verification fails, the review is INCOMPLETE. Go back and complete missing phases.**

## Options

- `--scope-mode`: Set strictness level (default: standard)
  - `strict`: All requirements must be complete
  - `standard`: Core requirements required
  - `flexible`: MVP implementation acceptable
- `--auto-approve-safe-prs`: Auto-approve PRs with no issues
- `--no-auto-issues`: **Skip automatic issue creation** for out-of-scope items (issues are created by default)
- `--dry-run`: Generate report locally without posting to GitHub
- `--no-line-comments`: Skip individual line comments, only submit summary review
- `--skip-version-check`: **BYPASS version validation** (maintainer override)
  - Use when: intentional version skew, non-release PR touching version files
  - Alternative: Add `skip-version-check` label to PR or `[skip-version-check]` in PR description
  - **Still runs validation** but marks issues as [WAIVED] instead of [BLOCKING]
- `pr-number`/`pr-url`: Target specific PR (default: current branch)
