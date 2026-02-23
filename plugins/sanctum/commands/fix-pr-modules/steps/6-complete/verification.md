# Step 6.6: Final Verification & Workflow Gate

> **Navigation**: [<- Summary](summary.md) | [Step 6 Hub](../6-complete.md) | [Main Workflow](../../workflow-steps.md)

**Purpose**: Run final verification and ensure all workflow gates pass before reporting complete.

---

## 6.6 Final Thread Verification (AUTOMATIC)

This phase runs automatically at the end of /fix-pr.

```bash
Skill(sanctum:resolve-threads)
```

This validates any threads missed during Step 6.3 are resolved via batch operation.

**Step 6 Output**: All threads resolved, issues created, summary posted

---

## FINAL WORKFLOW GATE (Run Before Reporting Complete)

**ALL THREE conditions must be true:**

```bash
# === GATE 1: Thread Resolution ===
UNRESOLVED=$(gh api graphql -f query="..." --jq '...' )
[[ "$UNRESOLVED" -eq 0 ]] && echo "Gate 1: Threads" || echo "Gate 1 FAILED"

# === GATE 2: Reconciliation Complete ===
# Verify reconciliation table has no UNACCOUNTED items
# This is a manual check - review your reconciliation table above
echo "Gate 2: Verify UNACCOUNTED = 0 in reconciliation table"

# === GATE 3: Issues Created ===
# Count issues created that reference this PR
ISSUES=$(gh issue list --search "PR #$PR_NUM in:body created:>=today" --json number --jq 'length')
echo "Issues created today referencing PR: $ISSUES"
# Compare against Suggestion + Deferred count from triage
```

**Workflow completion checklist:**
- [ ] Gate 1: 0 unresolved threads
- [ ] Gate 2: Reconciliation table complete, UNACCOUNTED = 0
- [ ] Gate 3: Issues created match Suggestion + Deferred count (or all were fixed)
- [ ] Summary comment posted with all evidence

**DO NOT report "/fix-pr complete" until all gates pass.**

---

> **Back to**: [Step 6 Hub](../6-complete.md) | [Main Workflow](../../workflow-steps.md)
