---
name: component-level-hooks
description: Layer 2 per-component pre-commit checks for monorepos and plugin architectures.
parent: precommit-setup
load_when: project has multiple components or plugins
---

# Component-Specific Checks (Layer 2)

For monorepos, plugin architectures, or projects with multiple
components, add per-component quality checks. Each script
detects changed components from staged files and runs lint /
typecheck / test only against the affected components.

## Python Monorepo or Plugin Architecture

Create three quality-check scripts under `scripts/`. All three
share the same change-detection pattern.

### 1. Lint Changed Components (`scripts/run-component-lint.sh`)

\`\`\`bash
#!/bin/bash
# Lint only changed components based on staged files

set -euo pipefail

# Detect changed components from staged files
CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u) || true

if [ -z "\$CHANGED_COMPONENTS" ]; then
    echo "No components changed"
    exit 0
fi

echo "Linting changed components: \$CHANGED_COMPONENTS"

FAILED=()

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Linting \$component..."
        # Capture exit code to properly propagate failures
        local exit_code=0
        if [ -f "plugins/\$component/Makefile" ] && grep -q "^lint:" "plugins/\$component/Makefile"; then
            (cd "plugins/\$component" && make lint) || exit_code=\$?
        else
            (cd "plugins/\$component" && uv run ruff check .) || exit_code=\$?
        fi
        if [ "\$exit_code" -ne 0 ]; then
            FAILED+=("\$component")
        fi
    fi
done

if [ \${#FAILED[@]} -gt 0 ]; then
    echo "Lint failed for: \${FAILED[*]}"
    exit 1
fi
\`\`\`

### 2. Type Check Changed Components (`scripts/run-component-typecheck.sh`)

\`\`\`bash
#!/bin/bash
# Type check only changed components

set -euo pipefail

CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u) || true

if [ -z "\$CHANGED_COMPONENTS" ]; then
    exit 0
fi

echo "Type checking changed components: \$CHANGED_COMPONENTS"

FAILED=()

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Type checking \$component..."
        # Capture output and exit code separately to properly propagate failures
        local output
        local exit_code=0
        if [ -f "plugins/\$component/Makefile" ] && grep -q "^typecheck:" "plugins/\$component/Makefile"; then
            output=\$(cd "plugins/\$component" && make typecheck 2>&1) || exit_code=\$?
        else
            output=\$(cd "plugins/\$component" && uv run mypy src/ 2>&1) || exit_code=\$?
        fi
        # Display output (filter make noise)
        echo "\$output" | grep -v "^make\[" || true
        if [ "\$exit_code" -ne 0 ]; then
            FAILED+=("\$component")
        fi
    fi
done

if [ \${#FAILED[@]} -gt 0 ]; then
    echo "Type check failed for: \${FAILED[*]}"
    exit 1
fi
\`\`\`

### 3. Test Changed Components (`scripts/run-component-tests.sh`)

\`\`\`bash
#!/bin/bash
# Test only changed components

set -euo pipefail

CHANGED_COMPONENTS=\$(git diff --cached --name-only | grep -E '^(plugins|components)/' | cut -d/ -f2 | sort -u) || true

if [ -z "\$CHANGED_COMPONENTS" ]; then
    exit 0
fi

echo "Testing changed components: \$CHANGED_COMPONENTS"

FAILED=()

for component in \$CHANGED_COMPONENTS; do
    if [ -d "plugins/\$component" ]; then
        echo "Testing \$component..."
        # Capture exit code to properly propagate failures
        local exit_code=0
        if [ -f "plugins/\$component/Makefile" ] && grep -q "^test:" "plugins/\$component/Makefile"; then
            (cd "plugins/\$component" && make test) || exit_code=\$?
        else
            (cd "plugins/\$component" && uv run pytest tests/) || exit_code=\$?
        fi
        if [ "\$exit_code" -ne 0 ]; then
            FAILED+=("\$component")
        fi
    fi
done

if [ \${#FAILED[@]} -gt 0 ]; then
    echo "Tests failed for: \${FAILED[*]}"
    exit 1
fi
\`\`\`

## Add to Pre-commit Configuration

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
