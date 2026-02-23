# Step 6.5: Post Summary Comment

> **Navigation**: [<- Issue Linkage](issue-linkage.md) | [Step 6 Hub](../6-complete.md) | [Next: Verification ->](verification.md)

**Purpose**: Post a comprehensive summary comment to the PR documenting all actions taken.

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

> **Next**: [Verification](verification.md)
