# Step 6.4: Issue Linkage & Closure

> **Navigation**: [<- Thread Resolution](thread-resolution.md) | [Step 6 Hub](../6-complete.md) | [Next: Summary ->](summary.md)

**Purpose**: Analyze whether this PR addresses any open issues and close/comment on them accordingly.

---

## 6.4 Issue Linkage & Closure

**Analyze whether this PR addresses any open issues and close/comment on them accordingly.**

**Fetch Open Issues:**
```bash
# Get all open issues for the repository
gh issue list --state open --json number,title,body,labels --limit 50
```

**Analyze Issue Coverage:**

For each open issue, analyze whether the PR's changes address it:

```bash
# Get PR changed files and commit messages
gh pr view --json files,commits -q '{files: .files[].path, commits: .commits[].messageHeadline}'

# Compare against issue requirements:
# - Extract acceptance criteria from issue body
# - Check if changed files relate to issue scope
# - Review commit messages for issue references
```

**Classification:**
| Status | Criteria | Action |
|--------|----------|--------|
| **Fully Addressed** | All acceptance criteria met, all required changes made | Comment + Close |
| **Partially Addressed** | Some criteria met, some work remaining | Comment with follow-up details |
| **Not Related** | PR doesn't touch issue scope | Skip |

---

### Comment on Fully Addressed Issues

```bash
gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
## Addressed in PR #PR_NUMBER

This issue has been fully addressed by the linked pull request.

**Changes made:**
- [List specific changes that address the issue]

**Files modified:**
- `path/to/file.py`
- `path/to/another.py`

Closing this issue. The fix will be available after PR merge.
EOF
)"

# Close the issue
gh issue close ISSUE_NUMBER --reason completed
```

---

### Comment on Partially Addressed Issues

```bash
gh issue comment ISSUE_NUMBER --body "$(cat <<'EOF'
## Partially Addressed in PR #PR_NUMBER

This PR addresses some aspects of this issue but additional work is needed.

**What was addressed:**
- [List completed items]

**What still needs to be done (follow-up PR):**
- [ ] [Remaining task 1]
- [ ] [Remaining task 2]
- [ ] [Remaining task 3]

**Suggested next steps:**
1. Create follow-up branch from main after this PR merges
2. Address remaining items listed above
3. Reference this issue in the follow-up PR

Keeping this issue open until fully resolved.
EOF
)"
```

---

> **Next**: [Summary](summary.md)
