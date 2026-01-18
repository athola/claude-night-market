# Step 2: Triage (Classification)

> **Navigation**: [← Step 1: Analyze](1-analyze.md) | [Main Workflow](../workflow-steps.md) | [Step 3: Plan →](3-plan.md)

**Purpose**: Classify comments by type and priority to determine what to fix now vs. later.

**Skip when**: Single simple fix with obvious resolution.

## 2.0 Triage Output Format

Present triage results in this actionable format:

```markdown
### Triage Results

#### 🔴 Fix Now (2 items)
| ID | Issue | File | Why Critical |
|----|-------|------|--------------|
| C1 | Path traversal vulnerability | intelligence.rs:490 | Security |
| C2 | SQL injection risk | github_search.rs:143 | Security |

#### 🟡 This PR (4 items)
| ID | Issue | File |
|----|-------|------|
| S1 | Missing error logging | intelligence.rs:82 |
| S2 | Incomplete validation | parser.py:45 |
| S3 | Missing docstring | utils.py:120 |
| S4 | Inconsistent naming | models.py:67 |

#### 📋 Backlog → Issues (7 items)
| ID | Issue | Suggested Title |
|----|-------|-----------------|
| B1 | Low test coverage | test(intelligence): add integration tests |
| B2 | Performance optimization | perf(parser): optimize regex compilation |
| B3 | API documentation | docs(api): add endpoint documentation |

#### ⏭️ Skip (2 items)
- Informational comment about architecture
- Praise for clean code structure
```

**Category definitions:**
- **Fix Now**: Security issues, correctness bugs, blocking problems
- **This PR**: In-scope improvements that should be addressed
- **Backlog**: Out-of-scope items → will become GitHub issues in Step 6
- **Skip**: Informational, praise, or items not requiring action

## 2.1 Check Existing Backlog Context (Optional but Recommended)

   Before classifying comments, check if relevant backlog documentation exists:
   ```bash
   # Check for existing backlog files that may provide context
   ls docs/backlog/*.md 2>/dev/null
   # Key files to check:
   # - docs/backlog/queue.md - Active backlog items with worthiness scores
   # - docs/backlog/technical-debt.md - Known technical debt items
   ```

If these files exist:
- Cross-reference out-of-scope items against existing backlog entries
- Avoid creating duplicate GitHub issues for items already tracked
- Link new issues to related existing items when appropriate

## 2.2 Classify Comments

| Type | Description | Action |
|------|-------------|--------|
| **Critical** | Bugs, security issues | Fix immediately |
| **In-Scope** | Requirements-related | Address in this PR |
| **Suggestion** | Improvements | **Create GitHub issue (Step 6)** |
| **Deferred** | Medium priority, future work, out-of-scope | **Create GitHub issue (Step 6)** |
| **Informational** | Questions, praise | Reply only |

> **Note**: If you classify ANY item as "deferred", "out-of-scope", "suggestion", or "future work", Step 6 will create GitHub issues for them.

**Step 2 Output**: Classified comment list with types and priorities

---

> **Next**: [Step 3: Plan (Fix Strategy) →](3-plan.md)
