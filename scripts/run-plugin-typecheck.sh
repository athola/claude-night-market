#!/usr/bin/env bash
# Run type checking for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-typecheck.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-typecheck.sh --all
#   ./scripts/run-plugin-typecheck.sh --changed (runs type checks for plugins with changes)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Pin the interpreter uv builds each plugin venv with. CI (typecheck.yml) uses
# setup-python 3.12; left alone, uv picks the LOWEST interpreter a plugin's
# requires-python allows (3.9), and a different interpreter resolves different
# dependency versions. That is not hypothetical: tome's 3.9 venv resolved numpy
# 2.0.2 (pre-PEP 695 stubs) and passed, while CI's 3.12 venv resolved a numpy
# whose stubs mypy could not parse. The gate was green locally and red in CI
# for a week. Pinning here makes the pre-commit hook and the CI job the same
# check. The mypy TARGET stays 3.9 via each plugin's python_version.
export UV_PYTHON="${TYPECHECK_PYTHON:-3.12}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

# Type check a plugin's hooks/ directory under its own (strict) mypy config.
# Hooks are not part of src/ or the Makefile typecheck target for most plugins,
# so without this they go unchecked and type errors accumulate. Returns 0 on
# pass or when there is nothing to check, 1 on failure.
run_hooks_typecheck() {
    local plugin_dir="$1"

    # Only run when hooks/ actually contains Python modules. compgen -G does
    # the glob internally (no shellcheck SC2012 ls-as-test smell, and no
    # reliance on a non-matching glob being passed literally to ls).
    if ! compgen -G "$plugin_dir/hooks/*.py" >/dev/null; then
        return 0
    fi

    echo -e "  ${YELLOW}↳ Type checking hooks/...${NC}"
    # `python -m mypy`, never bare `mypy`. `uv run mypy` falls back to whatever
    # is on PATH when the project environment has no mypy, so a plugin that
    # never declared it passed on any machine with a global mypy installed and
    # died on a clean CI runner with "Failed to spawn: mypy". Going through the
    # project interpreter resolves mypy only from that plugin's own environment,
    # which makes this gate mean the same thing locally and in CI.
    if (cd "$plugin_dir" && uv run python -m mypy hooks/ 2>&1); then
        return 0
    fi
    return 1
}

run_plugin_typecheck() {
    local plugin_dir="$1"
    local plugin_name=$(basename "$plugin_dir")
    local main_rc=0
    local checked=0

    echo -e "${YELLOW}Type checking $plugin_name...${NC}"

    # Primary source check: prefer a Makefile typecheck target (custom layouts),
    # then fall back to running mypy on src/ or scripts/ directly.
    if [ -f "$plugin_dir/Makefile" ] && \
       ( grep -qE "^(typecheck|type-check):" "$plugin_dir/Makefile" 2>/dev/null || \
         (cd "$plugin_dir" && make -n typecheck >/dev/null 2>&1) ); then
        # Prefer explicit target in Makefile, fall back to typecheck
        local target=$(grep -oE "^(typecheck|type-check):" "$plugin_dir/Makefile" 2>/dev/null | head -1 | tr -d ':')
        if [ -z "$target" ]; then
            target="typecheck"
        fi
        # Capture output and exit code separately to avoid pipeline exit code issues
        local output
        local exit_code=0
        output=$(cd "$plugin_dir" && make "$target" 2>&1) || exit_code=$?
        # Filter and display output (excluding make's nested job messages)
        echo "$output" | grep -v "^make\[" || true
        [ "$exit_code" -ne 0 ] && main_rc=1
        checked=1
    elif { [ -d "$plugin_dir/src" ] || [ -d "$plugin_dir/scripts" ]; } && \
         [ -f "$plugin_dir/pyproject.toml" ] && \
         grep -q "mypy" "$plugin_dir/pyproject.toml" 2>/dev/null; then
        local src_target="src"
        [ -d "$plugin_dir/src" ] || src_target="scripts"
        # python -m mypy, for the same reason as the hooks check above.
        if ! (cd "$plugin_dir" && uv run python -m mypy "$src_target/" 2>&1); then
            main_rc=1
        fi
        checked=1
    fi

    # Hooks check: always run when hooks/ has Python, regardless of how (or
    # whether) the primary source was checked above. This is the gap that let
    # hook type errors accumulate unnoticed.
    if compgen -G "$plugin_dir/hooks/*.py" >/dev/null; then
        run_hooks_typecheck "$plugin_dir" || main_rc=1
        checked=1
    fi

    if [ "$checked" -eq 0 ]; then
        echo -e "  ${YELLOW}⊘ No type checking configuration${NC}"
        SKIPPED_PLUGINS+=("$plugin_name")
        return 0
    fi

    if [ "$main_rc" -eq 0 ]; then
        echo -e "  ${GREEN}✓ Type checking passed${NC}"
        PASSED_PLUGINS+=("$plugin_name")
        return 0
    fi

    echo -e "  ${RED}✗ Type checking failed${NC}"
    FAILED_PLUGINS+=("$plugin_name")
    return 1
}

# A plugin is what carries a manifest, not whatever happens to sit in plugins/.
# The bare plugins/*/ glob also matched the gitignored plugins/__pycache__ left
# behind by a root-level pytest run, which then showed up in the summary as a
# skipped plugin. Mirrors is_plugin_dir in run-plugin-tests.sh.
is_plugin_dir() {
    local dir="$1"
    [ -f "$dir/.claude-plugin/plugin.json" ] || [ -f "$dir/openpackage.yml" ]
}

# Parse arguments
if [ $# -eq 0 ] || [ "$1" == "--all" ]; then
    # Run all plugin type checking
    echo -e "${GREEN}=== Running Type Checks Across All Plugins ===${NC}"
    echo

    for plugin_dir in plugins/*/; do
        if [ -d "$plugin_dir" ] && is_plugin_dir "$plugin_dir"; then
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
    while IFS= read -r plugin_dir; do
        if [ -d "$plugin_dir" ]; then
            run_plugin_typecheck "$plugin_dir" || true
            echo
        fi
    done <<< "$CHANGED_PLUGINS"

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
