---
name: validation-hooks
description: Layer 3 custom validation hooks for project-specific structure and pattern checks.
parent: precommit-setup
load_when: enforcing project conventions or schema rules
---

# Validation Hooks (Layer 3)

Add custom validation hooks for project-specific requirements
beyond what generic linters cover (structure, ADR compliance,
schema invariants, security patterns).

## Example: Plugin Structure Validation

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

## Custom Hook Patterns

Add project-specific hooks for architectural or coverage rules:

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
        name: Verify Test Coverage
        entry: python3 scripts/check_coverage.py
        language: system
        pass_filenames: false
        files: ^(plugins|src)/.*\\.py\$
\`\`\`

## Hook Bypass Policy

`SKIP=<hook> git commit` and `git commit --no-verify`
**must not be used**. Hooks exist to keep the tree
green; bypassing them moves broken code into history,
where the next commit fights yesterday's bug instead
of today's feature.

If a hook fails, fix the underlying issue. If a hook
is wrong (false positive, slow, irrelevant), fix the
hook configuration. If commit pressure is the problem,
land a smaller change. There is no supported workflow
in this codebase that ends with a bypassed hook.
