# PR/MR Review: Workflow Phases 1-4

Phases 1 through 4 of the review workflow: scope establishment,
version validation, slop detection, code analysis, and review output.

> **See Also**:
> [Main Command](../../pr-review.md) |
> [Workflow Index](review-workflow.md) |
> [Phases 5-6](review-workflow-phases-5-6.md) |
> [Enforcement](review-workflow-enforcement.md) |
> [Framework](review-framework.md) |
> [Configuration](review-configuration.md)

**Platform Note**: Commands below show GitHub (`gh`) examples.
Check session context for `git_platform:` and consult
`Skill(leyline:git-platform)` for GitLab (`glab`) / Bitbucket
equivalents.

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

### Phase 4: Review Output (MANDATORY)

After generating findings, output the review. By default this posts
to the PR via GitHub/GitLab API. With `--local`, write the full
report (review summary, test plan, and backlog items) to a local
`.md` file instead.

#### Local Output Mode (`--local`)

When `--local` is passed, skip all API calls and write the report:

```bash
# Default path: .pr-review/pr-<number>-review.md
# Custom path:  whatever the user supplied after --local
LOCAL_PATH="${LOCAL_ARG:-.pr-review/pr-${PR_NUMBER}-review.md}"
mkdir -p "$(dirname "$LOCAL_PATH")"
```

Write the file with all review sections concatenated:

```markdown
# PR Review: #<number> - <title>

Generated: YYYY-MM-DD
Mode: local (not posted to PR)

---

## Scope Compliance
...

## Blocking Issues (N)
...

## In-Scope Issues (N)
...

## Suggestions (N)
...

## Backlog Items (N)
...

---

## Test Plan
...

---

## Recommendation
...
```

After writing, confirm the path to the user:
```
Review written to: <LOCAL_PATH>
```

**Important:** `--local` skips PR description updates, inline
comments, issue creation, and test plan posting. The report
contains everything that would have been posted. Knowledge
capture (Phase 7) still runs.

When `--local` is NOT set, proceed with the default posting
workflow below.

#### Default: Post to PR

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


> **Next**: [Phases 5-6](review-workflow-phases-5-6.md) — test plan generation and PR description update.
