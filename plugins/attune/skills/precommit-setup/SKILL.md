---
name: precommit-setup
description: Configure comprehensive three-layer pre-commit quality system with linting, type checking, and testing enforcement
model: claude-sonnet-4
tools: [Read, Write, Bash]
---

# Pre-commit Setup Skill

Configure a comprehensive three-layer pre-commit quality system that enforces linting, type checking, and testing before commits.

## Use When

- Setting up new project with code quality enforcement
- Adding pre-commit hooks to existing project
- Upgrading from basic linting to comprehensive quality system
- Setting up monorepo/plugin architecture with per-component quality checks
- Updating pre-commit hook versions

## Philosophy: Three-Layer Defense

This skill implements a comprehensive quality system based on three layers:

1. **Layer 1: Fast Global Checks** - Quick linting and type checking on all files (~50-200ms)
2. **Layer 2: Component-Specific Checks** - Detailed linting, type checking, and testing for changed components only (~10-30s)
3. **Layer 3: Validation Hooks** - Structure validation, security scanning, and custom checks

**Key Principle**: New code is automatically checked before commit, preventing technical debt from entering the repository.

## Standard Hooks (Layer 1)

### Python Projects

#### Basic Quality Checks
1. **pre-commit-hooks** - File validation (trailing whitespace, EOF, YAML/TOML/JSON syntax)
2. **ruff** - Ultra-fast linting and formatting (~50ms)
3. **ruff-format** - Code formatting
4. **mypy** - Static type checking (~200ms)
5. **bandit** - Security scanning

#### Configuration

\`\`\`yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.2
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.0
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
\`\`\`

### Rust Projects

1. **rustfmt** - Code formatting
2. **clippy** - Linting
3. **cargo-check** - Compilation check

### TypeScript Projects

1. **eslint** - Linting
2. **prettier** - Code formatting
3. **tsc** - Type checking

## Component-Specific Checks (Layer 2)

For monorepos, plugin architectures, or projects with multiple components, add per-component quality checks.

### Python Monorepo/Plugin Architecture

Create quality check scripts:

#### 1. Lint Changed Components (`scripts/run-component-lint.sh`)

\`\`\`bash
#!/bin/bash
# Lint only changed components based on staged files

set -e

# Detect changed components from staged files
CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u)

if [ -z "\$CHANGED_COMPONENTS" ]; then
    echo "No components changed"
    exit 0
fi

echo "Linting changed components: \$CHANGED_COMPONENTS"

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Linting \$component..."
        cd "plugins/\$component"
        if [ -f "Makefile" ] && grep -q "^lint:" Makefile; then
            make lint
        else
            uv run ruff check .
        fi
        cd ../..
    fi
done
\`\`\`

#### 2. Type Check Changed Components (`scripts/run-component-typecheck.sh`)

\`\`\`bash
#!/bin/bash
# Type check only changed components

set -e

CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u)

if [ -z "\$CHANGED_COMPONENTS" ]; then
    exit 0
fi

echo "Type checking changed components: \$CHANGED_COMPONENTS"

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Type checking \$component..."
        cd "plugins/\$component"
        if [ -f "Makefile" ] && grep -q "^typecheck:" Makefile; then
            make typecheck
        else
            uv run mypy src/
        fi
        cd ../..
    fi
done
\`\`\`

#### 3. Test Changed Components (`scripts/run-component-tests.sh`)

\`\`\`bash
#!/bin/bash
# Test only changed components

set -e

CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u)

if [ -z "\$CHANGED_COMPONENTS" ]; then
    exit 0
fi

echo "Testing changed components: \$CHANGED_COMPONENTS"

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Testing \$component..."
        cd "plugins/\$component"
        if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
            make test
        else
            uv run pytest tests/
        fi
        cd ../..
    fi
done
\`\`\`

### Add to Pre-commit Configuration

\`\`\`yaml
# .pre-commit-config.yaml (continued)

  # Layer 2: Component-Specific Quality Checks
  - repo: local
    hooks:
      - id: run-component-lint
        name: Lint Changed Components
        entry: ./scripts/run-component-lint.sh
        language: system
        pass_filenames: false
        files: ^(plugins|components)/.*\\.py\$

      - id: run-component-typecheck
        name: Type Check Changed Components
        entry: ./scripts/run-component-typecheck.sh
        language: system
        pass_filenames: false
        files: ^(plugins|components)/.*\\.py\$

      - id: run-component-tests
        name: Test Changed Components
        entry: ./scripts/run-component-tests.sh
        language: system
        pass_filenames: false
        files: ^(plugins|components)/.*\\.(py|md)\$
\`\`\`

## Validation Hooks (Layer 3)

Add custom validation hooks for project-specific requirements.

### Example: Plugin Structure Validation

\`\`\`yaml
  # Layer 3: Validation Hooks
  - repo: local
    hooks:
      - id: validate-plugin-structure
        name: Validate Plugin Structure
        entry: python3 scripts/validate_plugins.py
        language: system
        pass_filenames: false
        files: ^plugins/.*\$
\`\`\`

## Workflow

### 1. Create Configuration Files

\`\`\`bash
# Create .pre-commit-config.yaml
python3 plugins/attune/scripts/attune_init.py \\
  --lang python \\
  --name my-project \\
  --path .

# Create quality check scripts (for monorepos)
mkdir -p scripts
chmod +x scripts/run-component-*.sh
\`\`\`

### 2. Configure Python Type Checking

Create `pyproject.toml` with strict type checking:

\`\`\`toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
strict = true

# Per-component configuration
[[tool.mypy.overrides]]
module = "plugins.*"
strict = true
\`\`\`

### 3. Configure Testing

\`\`\`toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-v",                    # Verbose output
    "--strict-markers",      # Strict marker enforcement
    "--cov=src",             # Coverage for src/
    "--cov-report=term",     # Terminal coverage report
]

markers = [
    "slow: marks tests as slow (deselect with '-m \\"not slow\\"')",
    "integration: marks tests as integration tests",
]
\`\`\`

### 4. Install and Test Hooks

\`\`\`bash
# Install pre-commit tool
uv sync --extra dev

# Install git hooks
uv run pre-commit install

# Test on all files (first time)
uv run pre-commit run --all-files

# Normal usage - test on staged files
git add .
git commit -m "feat: add feature"
# Hooks run automatically
\`\`\`

### 5. Create Manual Quality Scripts

For comprehensive quality checks (CI/CD, monthly audits):

#### `scripts/check-all-quality.sh`

\`\`\`bash
#!/bin/bash
# Comprehensive quality check for all components

set -e

echo "=== Running Comprehensive Quality Checks ==="

# Lint all components
./scripts/run-component-lint.sh --all

# Type check all components
./scripts/run-component-typecheck.sh --all

# Test all components
./scripts/run-component-tests.sh --all

echo "=== ✓ All Quality Checks Passed ==="
\`\`\`

## Hook Execution Order

Pre-commit hooks run in this order:

\`\`\`
1. ✓ File Validation (whitespace, EOF, YAML/TOML/JSON syntax)
2. ✓ Security Scanning (bandit)
3. ✓ Global Linting (ruff - all files)
4. ✓ Global Type Checking (mypy - all files)
5. ✓ Component Linting (changed components only)
6. ✓ Component Type Checking (changed components only)
7. ✓ Component Tests (changed components only)
8. ✓ Custom Validation (structure, patterns, etc.)
\`\`\`

All must pass for commit to succeed.

## Performance Optimization

### Typical Timings

| Check | Single Component | Multiple Components | All Components |
|-------|------------------|---------------------|----------------|
| Global Ruff | ~50ms | ~200ms | ~500ms |
| Global Mypy | ~200ms | ~500ms | ~1s |
| Component Lint | ~2-5s | ~4-10s | ~30-60s |
| Component Typecheck | ~3-8s | ~6-16s | ~60-120s |
| Component Tests | ~5-15s | ~10-30s | ~120-180s |
| **Total** | **~10-30s** | **~20-60s** | **~2-5min** |

### Optimization Strategies

1. **Only test changed components** - Default behavior
2. **Parallel execution** - Hooks run concurrently when possible
3. **Caching** - Dependencies cached by uv
4. **Incremental mypy** - Use `--incremental` flag

## Hook Configuration

### Skip Specific Hooks

\`\`\`bash
# Skip specific hook for one commit
SKIP=run-component-tests git commit -m "WIP: tests in progress"

# Skip component checks but keep global checks
SKIP=run-component-lint,run-component-typecheck,run-component-tests git commit -m "WIP"

# Skip all hooks (DANGEROUS - use only for emergencies)
git commit --no-verify -m "Emergency fix"
\`\`\`

### Custom Hooks

Add project-specific hooks:

\`\`\`yaml
  - repo: local
    hooks:
      - id: check-architecture
        name: Validate Architecture Decisions
        entry: python3 scripts/check_architecture.py
        language: system
        pass_filenames: false
        files: ^(plugins|src)/.*\\.py\$

      - id: check-coverage
        name: Ensure Test Coverage
        entry: python3 scripts/check_coverage.py
        language: system
        pass_filenames: false
        files: ^(plugins|src)/.*\\.py\$
\`\`\`

## CI Integration

Ensure CI runs the same comprehensive checks:

\`\`\`yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run Comprehensive Quality Checks
        run: ./scripts/check-all-quality.sh

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
\`\`\`

## Troubleshooting

### Hooks Too Slow

**Solution**: Only changed components are checked by default. For even faster commits:

\`\`\`bash
# Skip tests during development
SKIP=run-component-tests git commit -m "WIP: feature development"

# Run tests manually when ready
./scripts/run-component-tests.sh --changed
\`\`\`

### Cache Issues

\`\`\`bash
# Clear pre-commit cache
uv run pre-commit clean

# Clear component caches
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name ".pytest_cache" -type d -exec rm -rf {} +
find . -name ".mypy_cache" -type d -exec rm -rf {} +
\`\`\`

### Hook Failures

\`\`\`bash
# See detailed output
uv run pre-commit run --verbose --all-files

# Run specific component checks manually
cd plugins/my-component
make lint
make typecheck
make test
\`\`\`

### Import Errors in Tests

\`\`\`toml
# Ensure PYTHONPATH is set in pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]
\`\`\`

### Type Checking Errors

\`\`\`toml
# Use per-module overrides for gradual typing
[[tool.mypy.overrides]]
module = "legacy_module.*"
disallow_untyped_defs = false
\`\`\`

## Best Practices

### For New Projects

1. **Start with strict settings** - Easier to maintain from the beginning
2. **Configure type checking** - Use `strict = true` in `tool.mypy`
3. **Set up testing early** - Include pytest in pre-commit hooks
4. **Document exceptions** - If you skip hooks, document why

### For Existing Projects

1. **Gradual adoption** - Start with global checks, add component checks later
2. **Fix existing issues** - Run quality checks on all files, fix progressively
3. **Create baseline** - Document current state for tracking improvement
4. **Use `--no-verify` sparingly** - Only for true emergencies

### For Monorepos/Plugin Architectures

1. **Per-component Makefiles** - Standardize lint/typecheck/test targets
2. **Shared configurations** - Use root `pyproject.toml` for common settings
3. **Component detection** - Automatically detect changed components
4. **Progressive disclosure** - Show summary first, details on failure

## Complete Example: Python Monorepo

\`\`\`yaml
# .pre-commit-config.yaml
repos:
  # Layer 1: Fast Global Checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.2
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.0
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]

  # Layer 2: Component-Specific Checks
  - repo: local
    hooks:
      - id: run-component-lint
        name: Lint Changed Components
        entry: ./scripts/run-component-lint.sh
        language: system
        pass_filenames: false
        files: ^plugins/.*\\.py\$

      - id: run-component-typecheck
        name: Type Check Changed Components
        entry: ./scripts/run-component-typecheck.sh
        language: system
        pass_filenames: false
        files: ^plugins/.*\\.py\$

      - id: run-component-tests
        name: Test Changed Components
        entry: ./scripts/run-component-tests.sh
        language: system
        pass_filenames: false
        files: ^plugins/.*\\.(py|md)\$

  # Layer 3: Validation Hooks
  - repo: local
    hooks:
      - id: validate-plugin-structure
        name: Validate Plugin Structure
        entry: python3 scripts/validate_plugins.py
        language: system
        pass_filenames: false
        files: ^plugins/.*\$
\`\`\`

## Related Skills

- `Skill(attune:project-init)` - Full project initialization
- `Skill(attune:workflow-setup)` - GitHub Actions setup
- `Skill(attune:makefile-generation)` - Generate component Makefiles

## See Also

- [Quality Gates Documentation](../../../docs/quality-gates.md) - Comprehensive quality system guide
- [Testing Guide](../../../docs/testing-guide.md) - Testing best practices
