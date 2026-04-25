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

## Skip Specific Hooks (Emergency Use)

\`\`\`bash
# Skip specific hook for one commit
SKIP=run-component-tests git commit -m "WIP: tests in progress"

# Skip component checks but keep global checks
SKIP=run-component-lint,run-component-typecheck,run-component-tests git commit -m "WIP"

# Skip all hooks (DANGEROUS - use only for emergencies)
git commit --no-verify -m "Emergency fix"
\`\`\`

Document the reason whenever a hook is skipped; SKIP is a
last-resort tool, not a routine workflow.
