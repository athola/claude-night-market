---
name: precommit-setup
description: Configure pre-commit hooks for code formatting, linting, and security checks
model: claude-sonnet-4
tools: [Read, Write, Bash]
---

# Pre-commit Setup Skill

Configure pre-commit hooks to enforce code quality before commits.

## Use When

- Setting up new project with code quality enforcement
- Adding pre-commit hooks to existing project
- Updating pre-commit hook versions

## Standard Hooks

### Python Hooks

1. **pre-commit-hooks** - Basic checks (trailing whitespace, EOF, YAML syntax)
2. **ruff** - Fast linting and formatting
3. **mypy** - Type checking
4. **bandit** - Security scanning (optional)

### Rust Hooks

1. **rustfmt** - Code formatting
2. **clippy** - Linting
3. **cargo-check** - Compilation check

### TypeScript Hooks

1. **eslint** - Linting
2. **prettier** - Code formatting
3. **tsc** - Type checking

## Workflow

### 1. Create Configuration

```bash
# Render .pre-commit-config.yaml from template
python3 plugins/attune/scripts/attune_init.py \
  --lang python \
  --name my-project \
  --path .
```

This creates `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.2
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### 2. Install Hooks

```bash
# Install pre-commit tool
uv sync --extra dev

# Install git hooks
uv run pre-commit install

# Output:
# pre-commit installed at .git/hooks/pre-commit
```

### 3. Test Hooks

```bash
# Run on all files
uv run pre-commit run --all-files

# Test on staged files
git add .
uv run pre-commit run
```

### 4. Update Hook Versions

```bash
# Update to latest versions
uv run pre-commit autoupdate

# Example output:
# Updating https://github.com/astral-sh/ruff-pre-commit ... updating v0.14.0 -> v0.14.2
```

## Hook Configuration

### Skip Specific Hooks

```bash
# Skip specific hook for one commit
SKIP=mypy git commit -m "Work in progress"

# Skip all hooks for one commit
git commit --no-verify -m "Emergency fix"
```

### Custom Hooks

Add project-specific hooks in `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: uv run pytest --collect-only -q
        language: system
        pass_filenames: false
        always_run: true
```

## CI Integration

Ensure CI runs the same checks:

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: Run pre-commit
        run: |
          pip install pre-commit
          pre-commit run --all-files
```

## Troubleshooting

### Hooks Too Slow

```yaml
# Run only on changed files (default)
# vs
# Run on all files (slower)
uv run pre-commit run --all-files
```

### Cache Issues

```bash
# Clear pre-commit cache
uv run pre-commit clean
```

### Hook Failures

```bash
# See detailed output
uv run pre-commit run --verbose --all-files
```

## Related Skills

- `Skill(attune:project-init)` - Full project initialization
- `Skill(attune:workflow-setup)` - GitHub Actions setup
