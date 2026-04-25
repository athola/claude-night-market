---
name: troubleshooting
description: Performance tuning and failure-recovery patterns for slow or broken pre-commit hooks.
parent: precommit-setup
load_when: hooks are slow or failing
---

# Performance and Troubleshooting

## Typical Timings

| Check | Single Component | Multiple Components | All Components |
|-------|------------------|---------------------|----------------|
| Global Ruff | ~50ms | ~200ms | ~500ms |
| Global Mypy | ~200ms | ~500ms | ~1s |
| Component Lint | ~2-5s | ~4-10s | ~30-60s |
| Component Typecheck | ~3-8s | ~6-16s | ~60-120s |
| Component Tests | ~5-15s | ~10-30s | ~120-180s |
| **Total** | **~10-30s** | **~20-60s** | **~2-5min** |

## Optimization Strategies

1. **Only test changed components** -- default behavior in
   the Layer 2 scripts.
2. **Parallel execution** -- pre-commit runs hooks
   concurrently when possible.
3. **Caching** -- dependencies cached by uv; mypy uses
   `.mypy_cache/`.
4. **Incremental mypy** -- enable `--incremental` for repeat
   commits in the same session.

## Hooks Too Slow

Only changed components are checked by default. For even
faster commits during active development:

\`\`\`bash
# Skip tests during development
SKIP=run-component-tests git commit -m "WIP: feature development"

# Run tests manually when ready
./scripts/run-component-tests.sh --changed
\`\`\`

## Cache Issues

\`\`\`bash
# Clear pre-commit cache
uv run pre-commit clean

# Clear component caches
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name ".pytest_cache" -type d -exec rm -rf {} +
find . -name ".mypy_cache" -type d -exec rm -rf {} +
\`\`\`

## Hook Failures

\`\`\`bash
# See detailed output
uv run pre-commit run --verbose --all-files

# Run specific component checks manually
cd plugins/my-component
make lint
make typecheck
make test
\`\`\`

## Import Errors in Tests

\`\`\`toml
# Ensure PYTHONPATH is set in pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]
\`\`\`

## Type Checking Errors

\`\`\`toml
# Use per-module overrides for gradual typing
[[tool.mypy.overrides]]
module = "legacy_module.*"
disallow_untyped_defs = false
\`\`\`
