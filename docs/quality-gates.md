# Quality Gates and Code Quality System

We use a three-layer system to maintain code standards within the Claude Night Market ecosystem.

## Table of Contents

- [Overview](#overview)
- [The Three Layers](#the-three-layers)
- [Pre-Commit Hooks](#pre-commit-hooks)
- [Manual Quality Scripts](#manual-quality-scripts)
- [Configuration Files](#configuration-files)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

Our quality system relies on three layers: **Pre-Commit Hooks** (Layer 1) for automatic enforcement, **Manual/CI Scripts** (Layer 2) for full checks, and **Documentation & Tracking** (Layer 3) for auditing.

**Status**
- **New Code**: Every commit undergoes linting, type checks, tests, and security scans.
- **Existing Code**: We track legacy issues through baseline audits. See [Code Quality Baseline Archive](./archive/2026-01/).

## The Three Layers

We organize quality checks into three distinct layers to balance speed and thoroughness.

**Layer 1: Fast Global Checks**
Ruff handles linting and formatting, while Mypy verifies type annotations across all Python files. These run quickly to catch common errors immediately.

**Layer 2: Plugin-Specific Checks**
These run only on changed plugins to execute targets like `run-plugin-lint.sh` and `run-plugin-tests.sh`. This keeps feedback loops tight during focused development.

**Layer 3: Validation Hooks**
We verify plugin structure, skill frontmatter, context optimization, and security using tools like Bandit. This ensures structural integrity and security compliance.

## Pre-Commit Hooks

### Hook Execution Order

Commits trigger a specific sequence of checks:
1. File validation (syntax)
2. Security scanning (bandit)
3. Global Linting (ruff)
4. Global Type Checking (mypy)
5. Plugin-Specific checks (lint, typecheck, tests)
6. Structure/Skill/Context validation

All checks must pass for the commit to succeed.

### Plugin Validation Hooks

The `plugins/abstract/scripts/` directory contains our validators: `abstract_validator.py` for skills, `validate_plugin.py` for structure, and `context_optimizer.py`.

### Standard Quality Checks

We use standard hooks for formatting (`trailing-whitespace`, `end-of-file-fixer`), configuration validation (`check-yaml`, `check-toml`, `check-json`), security (`bandit`), linting (`ruff`), and type checking (`mypy`).

## Manual Quality Scripts

### Individual Scripts

You can run full checks on-demand.

```bash
# Lint all plugins (or specific ones)
./scripts/run-plugin-lint.sh --all
./scripts/run-plugin-lint.sh minister imbue

# Type check all plugins (or specific ones)
./scripts/run-plugin-typecheck.sh --all
./scripts/run-plugin-typecheck.sh minister imbue

# Test all plugins (or specific ones)
./scripts/run-plugin-tests.sh --all
./scripts/run-plugin-tests.sh minister imbue

# Full check (all three)
./scripts/check-all-quality.sh
./scripts/check-all-quality.sh --report
```

### Use Cases

For daily development, rely on the automatic pre-commit hooks (10-30s). Before submitting a PR, run `./scripts/check-all-quality.sh` (2-5min) to ensure everything is clean. We run full reports monthly using the `--report` flag. CI/CD pipelines execute `make lint && make typecheck && make test`.

## Configuration Files

### Quality Gates (`.claude/quality_gates.json`)

This file defines thresholds across four dimensions:

- **Performance**: Files must be under 20KB and 5000 tokens, with a complexity score below 12.
- **Security**: We block hardcoded secrets and insecure functions.
- **Maintainability**: Technical debt ratio must be below 0.3, with nesting depth no more than 5.
- **Compliance**: Plugins must follow the required structure and include proper metadata.

### Context Governance (`.claude/context_governance.json`)

Enforces context optimization patterns, requiring progressive disclosure (overview, basic, advanced, reference) and modular structure.

### Pre-Commit Configuration

The `.pre-commit-config.yaml` file defines our hooks, categorized into code quality, global quality, validation, and standard hooks.

## Usage Guide

### For Daily Development

Develop normally. Pre-commit hooks will handle the checks.

```bash
# Edit code
vim plugins/minister/src/minister/tracker.py

# Commit (hooks run automatically)
git add plugins/minister/src/minister/tracker.py
git commit -m "feat: improve tracker logic"

# If checks fail, fix and try again
```

### For Testing Before Commit

To see what will run in pre-commit without committing:

```bash
./scripts/run-plugin-lint.sh minister
./scripts/run-plugin-typecheck.sh minister
./scripts/run-plugin-tests.sh minister
```

### For Full Codebase Audit

```bash
# Quick check
./scripts/check-all-quality.sh

# Detailed check with report
./scripts/check-all-quality.sh --report
```

## Troubleshooting

### Common Issues & Fixes

For test failures, see the [Testing Guide](./testing-guide.md).

**Linting Errors:** Ruff often auto-fixes issues. Run `uv run ruff check --fix` in the plugin directory.

**Type Errors:** If an attribute is missing (e.g., `"ProjectTracker" has no attribute "initiative_tracker"`), add the attribute, remove the reference, or update the type stubs.

**"Hook script not found":** Reinstall hooks with `pre-commit install --install-hooks`.

### Skipping Hooks (Emergency)

Use sparingly.

```bash
# Skip all hooks (not recommended)
git commit --no-verify -m "emergency: critical hotfix"

# Skip specific hook
SKIP=run-plugin-tests git commit -m "WIP: tests in progress"
```

## Best Practices

**For Developers:** Run checks before committing, fix issues incrementally, write type hints for new functions, and keep tests green.

**For Plugin Maintainers:** Configure strict type checking, add Makefile targets for quality checks, and document requirements.

## Running Validation

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run run-plugin-lint
pre-commit run run-plugin-typecheck
pre-commit run run-plugin-tests

# Run manual quality scripts
./scripts/run-plugin-lint.sh --all
./scripts/run-plugin-typecheck.sh --all
./scripts/run-plugin-tests.sh --all
./scripts/check-all-quality.sh --report
```

## See Also

- [Testing Guide](./testing-guide.md) - Testing documentation
- [Plugin Development Guide](./plugin-development-guide.md) - Plugin development standards
- [Code Quality Baseline Archive](./archive/2026-01/) - Historical audit snapshots
- [Pre-commit configuration](../.pre-commit-config.yaml) - Hook definitions
