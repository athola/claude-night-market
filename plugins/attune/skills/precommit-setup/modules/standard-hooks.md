---
name: standard-hooks
description: Layer 1 fast global pre-commit checks for Python, Rust, and TypeScript projects.
parent: precommit-setup
load_when: configuring base linters
---

# Standard Hooks (Layer 1)

Fast global checks that run on every commit (typically 50-200ms total).

## Python Projects

### Basic Quality Checks

1. **pre-commit-hooks** -- file validation (trailing whitespace,
   EOF, YAML/TOML/JSON syntax)
2. **ruff** -- ultra-fast linting and formatting (~50ms)
3. **ruff-format** -- code formatting
4. **mypy** -- static type checking (~200ms)
5. **bandit** -- security scanning

### Configuration

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
    rev: 1.8.3
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
\`\`\`

## Rust Projects

1. **rustfmt** -- code formatting
2. **clippy** -- linting
3. **cargo-check** -- compilation check

## TypeScript Projects

1. **eslint** -- linting
2. **prettier** -- code formatting
3. **tsc** -- type checking
