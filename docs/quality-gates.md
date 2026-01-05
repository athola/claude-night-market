# Quality Gates & Code Quality System

A three-layer quality system that maintains high code standards for both new and existing code in the Claude Night Market ecosystem.

## Table of Contents

- [Overview](#overview)
- [The Three-Layer Defense](#the-three-layer-defense)
- [Pre-Commit Hooks](#pre-commit-hooks)
- [Manual Quality Scripts](#manual-quality-scripts)
- [Configuration Files](#configuration-files)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The quality system operates on three layers:

1. **Pre-Commit Hooks** (Layer 1) - Automatic enforcement on every commit
2. **Manual/CI Scripts** (Layer 2) - Comprehensive checks on-demand
3. **Documentation & Tracking** (Layer 3) - Audit baselines and progress tracking

### Current Status

**New Code (Changed Files):** ✅ **100% Protected** 🛡️
- Every commit is checked for linting, type safety, tests, and security
- No new technical debt can enter the repository

**Existing Code (Unchanged Files):** 📋 **Technical Debt Documented**
- Baseline audits track existing issues
- Action plans guide remediation
- See [Code Quality Baseline Archive](./archive/2026-01/)

## The Three-Layer Defense

### Layer 1: Fast Global Checks (Runs on All Files)

**Ruff** - Ultra-fast Python linter and formatter
- Checks: PEP 8, common bugs, code smells
- Speed: ~50ms for typical changes
- Auto-fixes: Yes (--fix flag enabled)

**Mypy** - Static type checker
- Checks: Type annotations and type safety
- Speed: ~200ms for typical changes
- Scope: All Python files in plugins/ and scripts/

### Layer 2: Plugin-Specific Checks (Runs on Changed Plugins Only)

**Lint Changed Plugins** (\`run-plugin-lint.sh --changed\`)
- Uses plugin's Makefile lint target or ruff
- Runs plugin-specific linting
- Speed: ~2-5s per plugin

**Type Check Changed Plugins** (\`run-plugin-typecheck.sh --changed\`)
- Uses plugin's Makefile typecheck target or mypy
- Enforces strict type checking per plugin configuration
- Speed: ~3-8s per plugin

**Test Changed Plugins** (\`run-plugin-tests.sh --changed\`)
- Runs test suite for changed plugins
- Blocks commit if any tests fail
- Speed: ~5-15s per plugin

### Layer 3: Validation Hooks

- Plugin structure validation
- Skill validation (abstract, imbue)
- Context optimization checks
- Security scanning (bandit)

## Pre-Commit Hooks

### Hook Execution Order

When you commit, hooks run in this order:

\`\`\`
1. ✓ File Validation (whitespace, YAML, TOML, JSON syntax)
2. ✓ Security Scanning (bandit - checks for security issues)
3. ✓ Global Linting (ruff - fast, all Python files)
4. ✓ Global Type Checking (mypy - all Python files)
5. ✓ Plugin-Specific Linting (changed plugins only)
6. ✓ Plugin-Specific Type Checking (changed plugins only)
7. ✓ Plugin Tests (changed plugins only)
8. ✓ Plugin Structure Validation
9. ✓ Skill Validation
10. ✓ Context Optimization

All must pass for commit to succeed.
\`\`\`

### Plugin Validation Hooks

\`\`\`yaml
validate-abstract-skills     # Validates skill frontmatter and structure
validate-imbue-skills         # Validates Imbue skill patterns
validate-*-plugin             # Structure validation per plugin
check-context-optimization    # Context window optimization checks
\`\`\`

Scripts live in \`plugins/abstract/scripts/\`:
- \`abstract_validator.py\` - Skill validation
- \`validate-plugin.py\` - Plugin structure validation
- \`context_optimizer.py\` - Context optimization analysis

### Standard Quality Checks

- \`trailing-whitespace\`, \`end-of-file-fixer\` - Formatting
- \`check-yaml\`, \`check-toml\`, \`check-json\` - Config validation
- \`bandit\` - Security scanning
- \`ruff\`, \`ruff-format\` - Linting and formatting
- \`mypy\` - Type checking

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

**Just code normally!** Pre-commit hooks handle everything:

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

- [Testing Guide](./testing-guide.md) - Comprehensive testing documentation
- [Plugin Development Guide](./plugin-development-guide.md) - Plugin development standards
- [Code Quality Baseline Archive](./archive/2026-01/) - Historical audit snapshots
- [Pre-commit configuration](../.pre-commit-config.yaml) - Hook definitions
