#!/bin/bash
# Run tests for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-tests.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-tests.sh --all
#   ./scripts/run-plugin-tests.sh --changed (runs tests for plugins with changes)

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

run_plugin_tests() {
    local plugin_dir="$1"
    local plugin_name=$(basename "$plugin_dir")

    echo -e "${YELLOW}Testing $plugin_name...${NC}"

    # Check if plugin has tests
    if [ ! -d "$plugin_dir/tests" ]; then
        echo -e "  ${YELLOW}⊘ No tests directory${NC}"
        SKIPPED_PLUGINS+=("$plugin_name")
        return 0
    fi

    # Check if plugin has Makefile with test target
    if [ -f "$plugin_dir/Makefile" ]; then
        if grep -q "^test:" "$plugin_dir/Makefile" 2>/dev/null; then
            # Run using Makefile
            if (cd "$plugin_dir" && make test --quiet 2>&1); then
                echo -e "  ${GREEN}✓ Tests passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                return 0
            else
                echo -e "  ${RED}✗ Tests failed${NC}"
                FAILED_PLUGINS+=("$plugin_name")
                return 1
            fi
        fi
    fi

    # Check if plugin has pyproject.toml with pytest
    if [ -f "$plugin_dir/pyproject.toml" ]; then
        if grep -q "pytest" "$plugin_dir/pyproject.toml" 2>/dev/null; then
            # Run using uv/pytest
            if (cd "$plugin_dir" && uv run python -m pytest tests/ --tb=short --quiet 2>&1); then
                echo -e "  ${GREEN}✓ Tests passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                return 0
            else
                echo -e "  ${RED}✗ Tests failed${NC}"
                FAILED_PLUGINS+=("$plugin_name")
                return 1
            fi
        fi
    fi

    # No test configuration found
    echo -e "  ${YELLOW}⊘ No test configuration${NC}"
    SKIPPED_PLUGINS+=("$plugin_name")
    return 0
}

# Parse arguments
if [ $# -eq 0 ] || [ "$1" == "--all" ]; then
    # Run all plugin tests
    echo -e "${GREEN}=== Running All Plugin Tests ===${NC}"
    echo

    for plugin_dir in plugins/*/; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_tests "$plugin_dir" || true
            echo
        fi
    done

elif [ "$1" == "--changed" ]; then
    # Run tests for plugins with staged changes
    echo -e "${GREEN}=== Running Tests for Changed Plugins ===${NC}"
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

    # Run tests for each changed plugin
    for plugin_dir in $CHANGED_PLUGINS; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_tests "$plugin_dir" || true
            echo
        fi
    done

else
    # Run tests for specified plugins
    echo -e "${GREEN}=== Running Tests for Specified Plugins ===${NC}"
    echo

    for plugin_name in "$@"; do
        plugin_dir="plugins/$plugin_name"
        if [ -d "$plugin_dir" ]; then
            run_plugin_tests "$plugin_dir" || true
            echo
        else
            echo -e "${RED}✗ Plugin not found: $plugin_name${NC}"
            echo
        fi
    done
fi

# Summary
echo -e "${GREEN}=== Test Summary ===${NC}"
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
    echo -e "${RED}ERROR: Some tests failed!${NC}"
    exit 1
fi

echo
echo -e "${GREEN}All tests passed!${NC}"
exit 0
