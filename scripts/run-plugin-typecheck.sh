#!/bin/bash
# Run type checking for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-typecheck.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-typecheck.sh --all
#   ./scripts/run-plugin-typecheck.sh --changed (runs type checks for plugins with changes)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

run_plugin_typecheck() {
    local plugin_dir="$1"
    local plugin_name=$(basename "$plugin_dir")

    echo -e "${YELLOW}Type checking $plugin_name...${NC}"

    # Check if plugin has Makefile with typecheck/type-check target FIRST
    # This allows plugins with custom source layouts to use their own typecheck targets
    if [ -f "$plugin_dir/Makefile" ]; then
        # Check both the Makefile itself and if make recognizes the target (from includes)
        if grep -qE "^(typecheck|type-check):" "$plugin_dir/Makefile" 2>/dev/null || \
           (cd "$plugin_dir" && make -n typecheck >/dev/null 2>&1); then
            # Run using Makefile
            # Prefer explicit target in Makefile, fall back to typecheck
            local target=$(grep -oE "^(typecheck|type-check):" "$plugin_dir/Makefile" 2>/dev/null | head -1 | tr -d ':')
            if [ -z "$target" ]; then
                target="typecheck"
            fi
            # Capture output and exit code separately to avoid pipeline exit code issues
            local output
            local exit_code
            output=$(cd "$plugin_dir" && make "$target" 2>&1) || exit_code=$?
            # Filter and display output (excluding make's nested job messages)
            echo "$output" | grep -v "^make\[" || true
            if [ "${exit_code:-0}" -eq 0 ]; then
                echo -e "  ${GREEN}✓ Type checking passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                return 0
            else
                echo -e "  ${RED}✗ Type checking failed${NC}"
                FAILED_PLUGINS+=("$plugin_name")
                return 1
            fi
        fi
    fi

    # Check if plugin has source code
    if [ ! -d "$plugin_dir/src" ] && [ ! -d "$plugin_dir/scripts" ]; then
        echo -e "  ${YELLOW}⊘ No Python source code${NC}"
        SKIPPED_PLUGINS+=("$plugin_name")
        return 0
    fi

    # Fallback: Run mypy directly if configured
    if [ -f "$plugin_dir/pyproject.toml" ] && grep -q "mypy" "$plugin_dir/pyproject.toml" 2>/dev/null; then
        # Check if src directory exists
        if [ -d "$plugin_dir/src" ]; then
            if (cd "$plugin_dir" && uv run mypy src/ 2>&1); then
                echo -e "  ${GREEN}✓ Type checking passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                return 0
            else
                echo -e "  ${RED}✗ Type checking failed${NC}"
                FAILED_PLUGINS+=("$plugin_name")
                return 1
            fi
        elif [ -d "$plugin_dir/scripts" ]; then
            if (cd "$plugin_dir" && uv run mypy scripts/ 2>&1); then
                echo -e "  ${GREEN}✓ Type checking passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                return 0
            else
                echo -e "  ${RED}✗ Type checking failed${NC}"
                FAILED_PLUGINS+=("$plugin_name")
                return 1
            fi
        fi
    fi

    echo -e "  ${YELLOW}⊘ No type checking configuration${NC}"
    SKIPPED_PLUGINS+=("$plugin_name")
    return 0
}

# Parse arguments
if [ $# -eq 0 ] || [ "$1" == "--all" ]; then
    # Run all plugin type checking
    echo -e "${GREEN}=== Running Type Checks Across All Plugins ===${NC}"
    echo

    for plugin_dir in plugins/*/; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_typecheck "$plugin_dir" || true
            echo
        fi
    done

elif [ "$1" == "--changed" ]; then
    # Run type checking for plugins with staged changes
    echo -e "${GREEN}=== Running Type Checks for Changed Plugins ===${NC}"
    echo

    # Get list of changed files
    CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || echo "")

    if [ -z "$CHANGED_FILES" ]; then
        echo -e "${YELLOW}No staged changes found${NC}"
        exit 0
    fi

    # Extract unique plugin directories
    CHANGED_PLUGINS=$(echo "$CHANGED_FILES" | grep "^plugins/" | cut -d/ -f1-2 | sort -u)

    if [ -z "$CHANGED_PLUGINS" ]; then
        echo -e "${YELLOW}No plugin changes detected${NC}"
        exit 0
    fi

    # Run type checking for each changed plugin
    for plugin_dir in $CHANGED_PLUGINS; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_typecheck "$plugin_dir" || true
            echo
        fi
    done

else
    # Run type checking for specified plugins
    echo -e "${GREEN}=== Running Type Checks for Specified Plugins ===${NC}"
    echo

    for plugin_name in "$@"; do
        plugin_dir="plugins/$plugin_name"
        if [ -d "$plugin_dir" ]; then
            run_plugin_typecheck "$plugin_dir" || true
            echo
        else
            echo -e "${RED}✗ Plugin not found: $plugin_name${NC}"
            echo
        fi
    done
fi

# Summary
echo -e "${GREEN}=== Type Checking Summary ===${NC}"
echo

if [ ${#PASSED_PLUGINS[@]} -gt 0 ]; then
    echo -e "${GREEN}✓ Passed (${#PASSED_PLUGINS[@]}):${NC} ${PASSED_PLUGINS[*]}"
fi

if [ ${#SKIPPED_PLUGINS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⊘ Skipped (${#SKIPPED_PLUGINS[@]}):${NC} ${SKIPPED_PLUGINS[*]}"
fi

if [ ${#FAILED_PLUGINS[@]} -gt 0 ]; then
    echo -e "${RED}✗ Failed (${#FAILED_PLUGINS[@]}):${NC} ${FAILED_PLUGINS[*]}"
    echo
    echo -e "${RED}ERROR: Type checking failed!${NC}"
    exit 1
fi

echo
echo -e "${GREEN}All type checks passed!${NC}"
exit 0
