# Test Plan Injection (Shared Module)

Shared detection, generation, and injection logic for
ensuring PR descriptions contain step-by-step manual
testing instructions.

> **Referenced by**:
> [pr-review Phase 6](../pr-review/modules/review-workflow-phases-5-6.md)
> | [fix-pr Step 6.5b](../fix-pr-modules/steps/6-complete/summary.md)

---

## Detection Logic

Check whether the PR body already contains a detailed
test plan section. A valid test plan has a recognized
heading AND at least 3 checkbox steps.

### Detection Patterns

Match any of these headings (case-insensitive):

```
## Test Plan
## Manual Testing
## Verification Steps
## Test plan
## Manual Test Plan
### Test Plan
### Manual Testing
### Verification Steps
```

**Regex pattern:**
```bash
TEST_PLAN_HEADING='## [Tt]est [Pp]lan|## [Mm]anual [Tt]est|## [Vv]erification [Ss]teps|### [Tt]est [Pp]lan|### [Mm]anual [Tt]est|### [Vv]erification [Ss]teps'
```

### Validation Criteria

A heading alone is not sufficient. The section must
also contain at least 3 checkbox items:

```bash
has_test_plan() {
  local BODY="$1"

  # Check for recognized heading
  if ! echo "$BODY" | grep -qiE \
    '##+ (Test [Pp]lan|Manual Test|Verification Steps)'; then
    return 1
  fi

  # Count checkbox steps after the heading
  CHECKBOX_COUNT=$(echo "$BODY" | \
    grep -c '- \[[ x]\]' || true)

  if [[ "$CHECKBOX_COUNT" -ge 3 ]]; then
    return 0  # Valid test plan exists
  fi

  return 1  # Heading found but insufficient steps
}
```

---

## Generation Template

Generate a test plan section from changed files and
review findings. The template adapts to the data
available in each workflow context.

### Template Structure

```markdown
## Test Plan

### Prerequisites
- [ ] Branch is up to date with base branch
- [ ] Dependencies installed (`uv sync` or `npm install`)

### Verification Steps

#### 1. [Area name]
**Files:** `path/to/file.py`

1. [ ] [Specific action or command to run]
2. [ ] [What to check or verify]
3. [ ] Expected: [what success looks like]

#### 2. [Another area]
**Files:** `path/to/other.py`

1. [ ] [Action]
2. [ ] [Verification]
3. [ ] Expected: [outcome]

### Build & Quality Gates
```bash
make test && make lint
```

### Summary
| Area | Steps | Verified |
|------|-------|----------|
| [area] | N | [ ] |
```

### Generation from pr-review (Phase 6)

Use Phase 5 test plan data already in context:

1. Extract verification areas from blocking/in-scope
   issues (B1, B2, S1, etc.)
2. Group by file or module
3. Include specific test commands from each issue
4. Add build and quality gate commands detected from
   `Makefile` or `pyproject.toml`
5. Condense into the template above (shorter than the
   full Phase 5 comment)

### Generation from fix-pr (Step 6.5b)

Use triage data available in the fix-pr context:

1. Extract fixed items from the triage table
2. Group changed files by functional area
3. Include quality gate commands from the project
4. Generate verification steps per area

---

## Injection Logic

### Insertion Point in PR Body

Insert the test plan section in this priority order:

1. **After `### Changes`** and **before
   `### Code Review Summary`** (if both exist)
2. **After the last `---` separator** before
   `### Code Review Summary` (if changes heading
   is absent)
3. **Appended at the end** of the body (fallback)

### Injection Procedure

```bash
inject_test_plan() {
  local CURRENT_BODY="$1"
  local TEST_PLAN="$2"

  # Check if test plan already exists
  if has_test_plan "$CURRENT_BODY"; then
    echo "Test plan already present, skipping injection"
    return 0
  fi

  # Try insertion after ### Changes, before
  # ### Code Review Summary
  if echo "$CURRENT_BODY" | \
    grep -q '### Code Review Summary'; then
    # Insert before Code Review Summary
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

  echo "$NEW_BODY"
}
```

### API Update

After injection, update the PR body:

```bash
gh api "repos/{owner}/{repo}/pulls/$PR_NUMBER" \
  -X PATCH -f body="$NEW_BODY"
```

If the API call fails (token scope issues), fall back
to posting the test plan as a PR comment:

```bash
gh pr comment $PR_NUMBER --body "$TEST_PLAN"
echo "Posted test plan as comment (body update failed)"
```

---

## Notes

- The injected test plan is a **condensed version** of
  the full Phase 5 test plan comment. It provides a
  quick checklist in the PR description while the
  detailed version remains as a separate comment.
- Detection runs before injection to avoid duplicates.
- Both workflows share the same heading patterns and
  validation criteria for consistency.
