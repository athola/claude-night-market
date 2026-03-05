# Step 6.5: Post Summary Comment

> **Navigation**: [<- Issue Linkage](issue-linkage.md) | [Step 6 Hub](../6-complete.md) | [Next: Verification ->](verification.md)

**Purpose**: Post a summary comment to the PR documenting all actions taken.

---

## 6.5 Post Summary Comment (MANDATORY)

### Issue Linkage Summary

Include this table in the summary:
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

---

### Post Summary Comment

After completing all fixes, thread resolutions, and issue linkage, post a detailed summary comment to the PR.

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

---

## 6.5b Ensure PR Description Has Test Plan (MANDATORY)

> **Module**: [test-plan-injection](../../../shared/test-plan-injection.md)

After posting the summary comment, check whether the PR
description body contains a detailed test plan section.
If missing, generate one from the triage data and inject
it into the body.

### Detection

```bash
# Fetch current PR body
CURRENT_BODY=$(gh pr view $PR_NUMBER --json body \
  --jq '.body // empty')

# Check for recognized test plan headings
TEST_PLAN_HEADING='##+ (Test [Pp]lan|Manual Test|Verification Steps)'
HAS_HEADING=$(echo "$CURRENT_BODY" | \
  grep -ciE "$TEST_PLAN_HEADING" || true)
CHECKBOX_COUNT=$(echo "$CURRENT_BODY" | \
  grep -c '- \[[ x]\]' || true)

if [[ "$HAS_HEADING" -gt 0 ]] && \
   [[ "$CHECKBOX_COUNT" -ge 3 ]]; then
  echo "Test plan already present in PR description"
  # Skip injection
else
  echo "No detailed test plan found, generating..."
  # Proceed to generation
fi
```

### Generation

Build a test plan from the fix-pr triage data (fixed
items, changed files, quality gate commands):

```bash
# Collect changed files grouped by area
CHANGED_FILES=$(git diff --name-only \
  origin/$BASE_BRANCH...HEAD)

# Build test plan from fixed items
TEST_PLAN="## Test Plan

### Prerequisites
- [ ] Branch is up to date with base branch
- [ ] Dependencies installed (\`uv sync\` or \`npm install\`)

### Verification Steps
"

# For each fixed blocking/in-scope item from triage
AREA_NUM=1
for ITEM in "${FIXED_ITEMS[@]}"; do
  ITEM_ID=$(echo "$ITEM" | cut -d'|' -f1)
  ITEM_FILE=$(echo "$ITEM" | cut -d'|' -f2)
  ITEM_DESC=$(echo "$ITEM" | cut -d'|' -f3)

  TEST_PLAN+="
#### $AREA_NUM. $ITEM_ID: $ITEM_DESC
**Files:** \`$ITEM_FILE\`

1. [ ] Review the fix at \`$ITEM_FILE\`
2. [ ] Run relevant tests for this area
3. [ ] Expected: issue resolved, no regression
"
  AREA_NUM=$((AREA_NUM + 1))
done

TEST_PLAN+="
### Build & Quality Gates
\`\`\`bash
make test && make lint
\`\`\`

### Summary
| Area | Steps | Verified |
|------|-------|----------|"

for ITEM in "${FIXED_ITEMS[@]}"; do
  ITEM_ID=$(echo "$ITEM" | cut -d'|' -f1)
  TEST_PLAN+="
| $ITEM_ID | 3 | [ ] |"
done
```

### Injection

```bash
# Insert before Code Review Summary if present
if echo "$CURRENT_BODY" | \
  grep -q '### Code Review Summary'; then
  NEW_BODY=$(echo "$CURRENT_BODY" | \
    sed "/### Code Review Summary/i\\
\\
${TEST_PLAN}\\
\\
---\\
")
else
  # Append at end
  NEW_BODY="${CURRENT_BODY}

---

${TEST_PLAN}"
fi

# Update PR body via API
if gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER" \
  -X PATCH -f body="$NEW_BODY" 2>/dev/null; then
  echo "✅ Test plan injected into PR #$PR_NUMBER description"
else
  # Fallback: post as comment
  gh pr comment $PR_NUMBER --body "$TEST_PLAN"
  echo "⚠️ Posted test plan as comment (body update failed)"
fi
```

**Test plan sources for fix-pr:**
- Fixed blocking issues (from triage table)
- Fixed in-scope issues (from triage table)
- Changed files (from `git diff`)
- Build commands (from `Makefile` or `pyproject.toml`)

---

> **Next**: [Verification](verification.md)
