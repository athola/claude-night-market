# Plugin Dependencies

This document maps inter-plugin dependencies in the
night-market ecosystem.

## Dependency Graph

```
conjure ──(optional)──> leyline
```

All other plugins are independent. No plugin requires
another to function, though some provide enhanced
capabilities when paired.

## Direct Dependencies

### conjure → leyline (optional)

**Declared in:** `plugins/conjure/pyproject.toml`
(optional dependency)

**Modules using leyline:**

- `scripts/quota_tracker.py` — token estimation via
  `leyline.tokens.estimate_tokens`
- `scripts/delegation_executor.py` — quota tracking via
  `leyline.quota_tracker.QuotaTracker`

**Fallback behavior:** Both modules use `try/except
ImportError` to degrade gracefully when leyline is not
installed. Quota tracking is skipped and token estimates
use a built-in heuristic.

## Shared Patterns

Several plugins follow patterns defined in leyline's
skills without importing leyline as a Python dependency:

| Plugin | Leyline Pattern Used |
|--------|---------------------|
| abstract | error-patterns, testing-quality-standards |
| conserve | context-optimization (MECW thresholds) |
| sanctum | git-platform, markdown-formatting |
| pensive | evaluation-framework |

These are skill-level references (markdown), not runtime
Python imports.

## Adding New Dependencies

When adding a cross-plugin Python dependency:

1. Declare it in `pyproject.toml` under
   `[project.optional-dependencies]`
2. Use `try/except ImportError` for graceful fallback
3. Document the dependency in this file
4. Update the plugin's README with a "Dependencies"
   section
