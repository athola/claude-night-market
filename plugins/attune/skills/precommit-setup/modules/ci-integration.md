---
name: ci-integration
description: GitHub Actions and GitLab CI workflow patterns mirroring local pre-commit checks.
parent: precommit-setup
load_when: configuring CI to run the same checks as pre-commit
---

# CI Integration

Verify CI runs the same comprehensive checks that pre-commit
runs locally. Drift between local hooks and CI is the most
common cause of "works on my machine" PRs.

## GitHub Actions

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
