---
description: Token and context conservation patterns (MECW principles)
alwaysApply: true
---

# Conservation Principles

## MECW (Maximum Effective Context Window)

Keep context pressure under 50% for quality responses.

| Threshold | Level | Action |
|-----------|-------|--------|
| < 30% | LOW | Normal operations |
| 30-50% | MODERATE | Consider consolidation |
| > 50% | CRITICAL | Immediate cleanup needed |

## Command Verbosity Control

| Avoid | Use Instead |
|-------|-------------|
| `npm install` | `npm install --silent` |
| `pip install pkg` | `pip install --quiet pkg` |
| `git log` | `git log --oneline -10` |
| `git diff` | `git diff --stat` |
| `ls -la` | `ls -1 \| head -20` |
| `find .` | `find . -name "*.py" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -not -path "*/node_modules/*" -not -path "*/.git/*" \| head -10` |
| `pytest` | `pytest --quiet` |

## Discovery Strategy

1. **LSP first** (if enabled) - semantic queries in ~50ms
2. **Targeted reads** - based on initial findings
3. **Grep tool** - ripgrep for text search (not bash grep)

## Read Budget

Hard caps on file reads before implementation.
Exceeding these requires **explicit user approval**.

| Task | Max Reads | Budget |
|------|-----------|--------|
| From spec | 8 files | ~10k tokens |
| Bug fix | 5 files | ~5k tokens |
| Refactor | 1 per changed file | ~8k tokens |
| Exploration | 15 files | ~15k tokens |

Free operations (don't count): `Glob`, `Grep` in
`files_with_matches` mode, `Read` with <50 line slices.

When budget is spent: **ask the user**, don't read more.
Self-authorized overrides are prohibited.

**User override phrases** (unlocks unlimited reads):
"ultrathink", "explore deeply", "deep dive",
"read more files", "read the whole module",
"take your time and understand the full context".

## Retries & Self-Reflection

If a command fails 3+ times:
1. Check for simpler approach
2. Verify assumptions about codebase
3. Consider token cost of retries vs. asking for clarification
