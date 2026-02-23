# Step 6.0: Reconciliation & Enforcement

> **Navigation**: [<- Step 6 Hub](../6-complete.md) | [Next: Issue Creation ->](issue-creation.md)

**Purpose**: Reconcile ALL items from the review before creating issues. Ensures nothing is missed.

---

## 6.0 Reconcile ALL Unworked Items (MANDATORY)

**Before creating issues, reconcile ALL items from the review.** This captures items identified DURING review but not formally triaged (test gaps, doc suggestions, security concerns, performance hints, etc.).

**Quick Checklist:**
- [ ] Review: Did ALL "Fix Now" / "This PR" items get addressed? Create issues for incomplete ones.
- [ ] Re-read ALL review comments - find suggestions not captured at triage time.
- [ ] Ensure EVERY non-worked-on item has a GitHub issue created in 6.1/6.2.

**MANDATORY OUTPUT FORMAT (Machine-Checkable):**

You MUST produce this reconciliation table. Empty tables or missing rows = workflow failure.

```markdown
## Reconciliation Table

| ID | Category | Description | Disposition | Evidence |
|----|----------|-------------|-------------|----------|
| C1 | Critical | [from triage] | Fixed | commit SHA |
| C2 | Critical | [from triage] | Fixed | commit SHA |
| S1 | In-Scope | [from triage] | Fixed | commit SHA |
| S2 | Suggestion | [from triage] | Issue #NN | link |
| S3 | Suggestion | [discovered in review] | Fixed | commit SHA |
| D1 | Deferred | [from triage] | Issue #NN | link |
| I1 | Informational | [praise/question] | Skipped | N/A |

### Summary
- **Fixed**: N items (commit refs: abc123, def456)
- **Issues Created**: N items (issue refs: #45, #46, #47)
- **Skipped**: N items (informational only)
- **UNACCOUNTED**: 0 items <- MUST BE ZERO

If UNACCOUNTED > 0, STOP and address before proceeding.
```

**Disposition values (ONLY these are valid):**
- `Fixed` - Code change applied, requires commit SHA
- `Issue #NN` - GitHub issue created, requires issue number
- `Skipped` - Informational/praise only, no action needed

**VALIDATION RULE**: Every row from Step 2 triage MUST appear here. Missing rows = incomplete reconciliation.

---

## 6.0.1 Issue Creation Enforcement (AUTOMATIC - BEFORE 6.1)

**CRITICAL: Issues MUST be created IMMEDIATELY after reconciliation, not deferred.**

When the reconciliation table contains items with disposition "Issue #NN" or category "Suggestion"/"Deferred":

1. **STOP** - Do not proceed to 6.1 documentation
2. **CREATE** the issues NOW using the templates in 6.1/6.2
3. **UPDATE** the reconciliation table with actual issue numbers
4. **VERIFY** issues exist before continuing

```bash
# Enforcement check - count items needing issues
NEEDS_ISSUES=$(grep -c "Suggestion\|Deferred" reconciliation_table.md || echo 0)
ISSUES_CREATED=$(gh issue list --search "PR #$PR_NUM in:body created:>=today" --json number --jq 'length')

if [[ "$NEEDS_ISSUES" -gt "$ISSUES_CREATED" ]]; then
  echo "ENFORCEMENT FAILED: $NEEDS_ISSUES items need issues, only $ISSUES_CREATED created"
  echo "CREATE ISSUES NOW before proceeding"
  exit 1
fi
```

**Anti-Pattern Detection:**
| What You Wrote | Problem | Correct Action |
|----------------|---------|----------------|
| "Issue: Create follow-up" | Intent, not execution | Run `gh issue create` NOW |
| "Will create issue later" | Deferring the deferral | Create issue IMMEDIATELY |
| "S3: Deferred" without #NN | Missing issue number | Issue not created yet |

**The reconciliation table is NOT complete until all Issue dispositions have real issue numbers (e.g., `Issue #184`).**

---

> **Next**: [Issue Creation](issue-creation.md)
