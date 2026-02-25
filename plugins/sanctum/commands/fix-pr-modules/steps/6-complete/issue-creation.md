# Step 6.1-6.2: Issue Creation

> **Navigation**: [<- Reconciliation](reconciliation.md) | [Step 6 Hub](../6-complete.md) | [Next: Thread Resolution ->](thread-resolution.md)

**Purpose**: Create GitHub issues for all suggestion and deferred items identified during triage and reconciliation.

---

## 6.1 Create Issues for Suggestions/Deferred Items (AUTOMATIC)

**CRITICAL: GitHub issues are created AUTOMATICALLY for ALL suggestion and deferred items identified in Step 6.0.**

> **Module Reference**: Auto-issue creation is handled inline by the workflow monitor.

**This step is automatic** - no flag required. When items are classified as "Suggestion" or "Deferred" during triage (Step 2) OR identified during reconciliation (Step 6.0), issues are created.

**To skip automatic creation**: Use `--no-auto-issues` flag.

**Duplicate Detection**: Before creating, search for existing issues with similar titles to avoid duplicates.

For each comment classified as **Suggestion** during triage or reconciliation, create a GitHub issue:
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
### Suggestions -> GitHub Issues

| Review Item | Issue Created | Description |
|-------------|---------------|-------------|
| S1 | #43 | Clarify ruff-format comment |
| S2 | #44 | Improve test output verbosity |
```

---

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

---

> **Next**: [Thread Resolution](thread-resolution.md)
