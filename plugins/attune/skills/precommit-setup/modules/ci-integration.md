---
name: ci-integration
description: GitHub Actions and GitLab CI workflow patterns mirroring local pre-commit checks.
parent: precommit-setup
---

# CI Integration

Verify CI runs the same thorough checks that pre-commit
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
  # Layer 1: the fast global checks from standard-hooks.md
  # (pre-commit-hooks, ruff, mypy, bandit) go here unchanged

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
