# Quality Gates & Code Quality System

A three-layer system to maintain code standards for new and existing code in the Claude Night Market ecosystem.

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

The quality system uses three layers to enforce standards: **Pre-Commit Hooks** (Layer 1) for automatic enforcement, **Manual/CI Scripts** (Layer 2) for full checks, and **Documentation & Tracking** (Layer 3) for auditing.

### Current Status

*   **New Code**: Every commit undergoes linting, type checks, tests, and security scans.
*   **Existing Code**: Baseline audits track legacy issues. See [Code Quality Baseline Archive](./archive/2026-01/).

## The Three Layers

### Layer 1: Fast Global Checks
Runs on all files. **Ruff** handles linting and formatting (~50ms, auto-fixes enabled). **Mypy** checks type annotations across all Python files (~200ms).

### Layer 2: Plugin-Specific Checks
Runs only on changed plugins. Scripts like `run-plugin-lint.sh`, `run-plugin-typecheck.sh`, and `run-plugin-tests.sh` execute plugin-specific targets. Tests block commits on failure.

### Layer 3: Validation Hooks
Validates plugin structure, skill frontmatter (abstract, imbue), context optimization, and security (bandit).

## Pre-Commit Hooks

### Hook Execution Order

Commits trigger the following sequence: File validation (syntax), Security scanning (bandit), Global Linting (ruff), Global Type Checking (mypy), Plugin-Specific checks (lint, typecheck, tests), and finally Structure/Skill/Context validation. All checks must pass.

### Plugin Validation Hooks

The `plugins/abstract/scripts/` directory contains validators: `abstract_validator.py` (skills), `validate-plugin.py` (structure), and `context_optimizer.py`.

### Standard Quality Checks

Standard hooks handle formatting (`trailing-whitespace`, `end-of-file-fixer`), configuration validation (`check-yaml`, `check-toml`, `check-json`), security (`bandit`), linting (`ruff`), and type checking (`mypy`).

## Manual Quality Scripts

### Individual Scripts

Run full checks on-demand:

\`\`\`bash
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
\`\`\`

### Use Cases

| Scenario | Command | Speed |
|----------|---------|-------|
| **Daily Dev** | Pre-commit (automatic) | 10-30s |
| **Pre-PR** | \`./scripts/check-all-quality.sh\` | 2-5min |
| **Monthly Audit** | \`./scripts/check-all-quality.sh --report\` | 2-5min |
| **CI/CD** | \`make lint && make typecheck && make test\` | 2-5min |

## Configuration Files

### Quality Gates (\`.claude/quality_gates.json\`)

Defines thresholds across four dimensions:

| Dimension | Key Settings |
|-----------|--------------|
| Performance | \`max_file_size_kb: 20\`, \`max_tokens_per_file: 5000\`, \`max_complexity_score: 12\` |
| Security | \`block_hardcoded_secrets: true\`, \`block_insecure_functions: true\` |
| Maintainability | \`max_technical_debt_ratio: 0.3\`, \`max_nesting_depth: 5\` |
| Compliance | \`require_plugin_structure: true\`, \`require_proper_metadata: true\` |

### Context Governance (\`.claude/context_governance.json\`)

Enforces context optimization patterns:

| Setting | Value |
|---------|-------|
| \`require_progressive_disclosure\` | \`true\` |
| \`require_modular_structure\` | \`true\` |
| \`optimization_patterns.progressive_disclosure\` | \`["overview", "basic", "advanced", "reference"]\` |
| \`optimization_patterns.modular_structure\` | \`["modules/", "examples/", "scripts/"]\` |

### Pre-Commit Configuration

**File**: \`.pre-commit-config.yaml\`

Key sections:
- **Code Quality Hooks** - Plugin-specific lint/typecheck/test
- **Global Quality** - Fast ruff and mypy on all files
- **Validation Hooks** - Plugin structure and skill validation
- **Standard Hooks** - File format, security, etc.

## Usage Guide

### For Daily Development

**Develop normally.** Pre-commit hooks handle everything:

\`\`\`bash
# Edit code
vim plugins/minister/src/minister/tracker.py

# Commit (hooks run automatically)
git add plugins/minister/src/minister/tracker.py
git commit -m "feat: improve tracker logic"

# If checks fail, fix and try again
\`\`\`

### For Testing Before Commit

\`\`\`bash
# Test what will run in pre-commit
./scripts/run-plugin-lint.sh minister
./scripts/run-plugin-typecheck.sh minister
./scripts/run-plugin-tests.sh minister

# Then commit
git commit -m "feat: add feature"
\`\`\`

### For Full Codebase Audit

\`\`\`bash
# Quick check
./scripts/check-all-quality.sh

# Detailed check with report
./scripts/check-all-quality.sh --report
# Report saved to: audit/quality-report-TIMESTAMP.md
\`\`\`

## Troubleshooting

### Common Issues & Fixes

See [Testing Guide - Troubleshooting](./testing-guide.md#troubleshooting) for troubleshooting of test failures.

#### Linting Errors

\`\`\`
E501 Line too long (100 > 88 characters)
\`\`\`

**Fix**: Ruff auto-fixes most issues:
\`\`\`bash
cd plugins/minister && uv run ruff check --fix
\`\`\`

#### Type Errors

\`\`\`
error: "ProjectTracker" has no attribute "initiative_tracker"
\`\`\`

**Fix**: Add missing attribute, remove references, or update type stubs

#### "Hook script not found"

\`\`\`bash
# Reinstall hooks
pre-commit install --install-hooks
\`\`\`

### Skipping Hooks (Emergency Only)

\`\`\`bash
# Skip all hooks (DANGEROUS)
git commit --no-verify -m "emergency: critical hotfix"

# Skip specific hook
SKIP=run-plugin-tests git commit -m "WIP: tests in progress"
\`\`\`

## Best Practices

### For Developers

1. **Run checks before committing**
2. **Fix issues incrementally**
3. **Write type hints** for all new functions
4. **Keep tests green**

### For Plugin Maintainers

1. **Configure strict type checking**
2. **Add Makefile targets** for lint/typecheck/test
3. **Document requirements**

## Running Validation

\`\`\`bash
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
\`\`\`

## See Also

- [Testing Guide](./testing-guide.md) - Testing documentation
- [Plugin Development Guide](./plugin-development-guide.md) - Plugin development standards
- [Code Quality Baseline Archive](./archive/2026-01/) - Historical audit snapshots
- [Pre-commit configuration](../.pre-commit-config.yaml) - Hook definitions
