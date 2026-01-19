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
| `find .` | `find . -name "*.py" \| head -10` |
| `pytest` | `pytest --quiet` |

## Discovery Strategy

1. **LSP first** (if enabled) - semantic queries in ~50ms
2. **Targeted reads** - based on initial findings
3. **Grep tool** - ripgrep for text search (not bash grep)

## Retries & Self-Reflection

If a command fails 3+ times:
1. Check for simpler approach
2. Verify assumptions about codebase
3. Consider token cost of retries vs. asking for clarification
