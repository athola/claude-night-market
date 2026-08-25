#!/usr/bin/env bash
# Run tests for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-tests.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-tests.sh --all
#   ./scripts/run-plugin-tests.sh --changed (runs tests for plugins with changes)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Every test invocation below runs behind this wrapper, which strips GIT_* from
# the child environment. `git commit` from a linked worktree points GIT_DIR and
# GIT_INDEX_FILE at the outer repo; a suite that shells out to git in a temp dir
# would otherwise write to the real index (issue #609). One definition, so a new
# call site cannot half-remember it.
WITHOUT_GIT_ENV="$PROJECT_ROOT/scripts/without-git-env.sh"

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

# Accumulate temp files for cleanup on exit
_TEMP_FILES=()
# shellcheck disable=SC2317  # invoked indirectly by the EXIT trap below
_cleanup_temp() { rm -f "${_TEMP_FILES[@]}" 2>/dev/null || true; }
trap _cleanup_temp EXIT

run_plugin_tests() {
    local plugin_dir="$1"
    local plugin_name
    plugin_name=$(basename "$plugin_dir")
    local temp_output
    temp_output=$(mktemp "/tmp/test_output_${plugin_name}_XXXXXX")
    _TEMP_FILES+=("$temp_output")

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
            # Run using Makefile - capture output, show on failure.
            # Redirect stdout first, then point stderr at it: `2>&1 > file`
            # reads left to right and would leave stderr on the terminal.
            if (cd "$plugin_dir" && "$WITHOUT_GIT_ENV" make test --quiet > "$temp_output" 2>&1); then
                echo -e "  ${GREEN}✓ Tests passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                rm -f "$temp_output"
                return 0
            else
                echo -e "  ${RED}✗ Tests failed${NC}"
                echo -e "${YELLOW}Re-running with verbose output:${NC}"
                echo
                (cd "$plugin_dir" && "$WITHOUT_GIT_ENV" make test 2>&1)
                FAILED_PLUGINS+=("$plugin_name")
                rm -f "$temp_output"
                return 1
            fi
        fi
    fi

    # Check if plugin has pyproject.toml with pytest
    if [ -f "$plugin_dir/pyproject.toml" ]; then
        if grep -q "pytest" "$plugin_dir/pyproject.toml" 2>/dev/null; then
            # Read coverage threshold from [tool.nightmarket] if set
            local cov_threshold
            cov_threshold=$(awk '
                /^\[tool\.nightmarket\]/ { in_nm=1; next }
                /^\[/ { in_nm=0 }
                in_nm && /^coverage_threshold[[:space:]]*=/ {
                    split($0, a, "="); gsub(/[[:space:]]/, "", a[2]); print a[2]; exit
                }
            ' "$plugin_dir/pyproject.toml")

            # An array, not a string: quoting an empty string would hand pytest
            # a literal "" and it would read that as a path to collect. An empty
            # array expands to no words at all, which is what "no threshold set"
            # has to mean.
            local cov_flag=()
            if [ -n "${cov_threshold}" ] && [ "${cov_threshold}" -gt 0 ] 2>/dev/null; then
                cov_flag=(--cov-fail-under="${cov_threshold}")
            fi

            # Run using uv/pytest - capture output, show on failure.
            # Redirect stdout before stderr; see the Makefile branch above.
            if (cd "$plugin_dir" && "$WITHOUT_GIT_ENV" uv run python -m pytest tests/ --tb=short --quiet ${cov_flag[@]+"${cov_flag[@]}"} > "$temp_output" 2>&1); then
                echo -e "  ${GREEN}✓ Tests passed${NC}"
                PASSED_PLUGINS+=("$plugin_name")
                rm -f "$temp_output"
                return 0
            else
                echo -e "  ${RED}✗ Tests failed${NC}"
                echo -e "${YELLOW}Re-running with verbose output:${NC}"
                echo
                (cd "$plugin_dir" && "$WITHOUT_GIT_ENV" uv run python -m pytest tests/ --tb=short ${cov_flag[@]+"${cov_flag[@]}"} 2>&1)
                FAILED_PLUGINS+=("$plugin_name")
                rm -f "$temp_output"
                return 1
            fi
        fi
    fi

    # Tests exist but nothing above knew how to run them. The "no tests" case
    # already returned a skip further up, so reaching here means the plugin
    # ships a tests/ directory and no way to execute it. That is a broken
    # plugin, not a plugin without tests, and reporting it as a skip is what
    # kept cartograph's 40 tests out of every gate while `make test` stayed
    # green. Fail loudly instead: a suite nobody can run is worse than no suite,
    # because it looks like coverage.
    echo -e "  ${RED}✗ Has tests/ but no test configuration${NC}"
    echo -e "     Add a pyproject.toml configuring pytest, or a Makefile with a"
    echo -e "     'test:' target. See plugins/cartograph/pyproject.toml."
    FAILED_PLUGINS+=("$plugin_name")
    rm -f "$temp_output"
    return 1
}

# A plugin is what carries a manifest, not whatever happens to sit in plugins/.
# The bare plugins/*/ glob also matched the gitignored plugins/__pycache__ left
# behind by a root-level pytest run, and the loop dutifully announced
# "Testing __pycache__...".
is_plugin_dir() {
    local dir="$1"
    [ -f "$dir/.claude-plugin/plugin.json" ] || [ -f "$dir/openpackage.yml" ]
}

# Parse arguments
if [ $# -eq 0 ] || [ "$1" == "--all" ]; then
    # Run all plugin tests
    echo -e "${GREEN}=== Running All Plugin Tests ===${NC}"
    echo

    for plugin_dir in plugins/*/; do
        if [ -d "$plugin_dir" ] && is_plugin_dir "$plugin_dir"; then
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
    while IFS= read -r plugin_dir; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_tests "$plugin_dir" || true
            echo
        fi
    done <<< "$CHANGED_PLUGINS"

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
