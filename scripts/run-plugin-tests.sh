#!/usr/bin/env bash
# Run tests for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-tests.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-tests.sh --all
#   ./scripts/run-plugin-tests.sh --changed (runs tests for plugins with changes)

set -euo pipefail

# A bare name (`bash run-plugin-tests.sh` from inside scripts/) has no
# slash for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

PROJECT_ROOT="$(cd "${MYDIR%/}/.." && pwd)"
readonly PROJECT_ROOT

# Every test invocation below runs behind this wrapper, which strips GIT_* from
# the child environment. `git commit` from a linked worktree points GIT_DIR and
# GIT_INDEX_FILE at the outer repo; a suite that shells out to git in a temp dir
# would otherwise write to the real index (issue #609). One definition, so a new
# call site cannot half-remember it.
WITHOUT_GIT_ENV="${PROJECT_ROOT}/scripts/without-git-env.sh"
readonly WITHOUT_GIT_ENV

readonly REQUIRED_DEPENDENCIES="uv make"
XTRACE=0

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

# Accumulate temp files for cleanup on exit
_TEMP_FILES=()
# The `[@]+` guard expands to nothing when the array is empty. Under
# `set -u`, bash 3.2 treats an empty array as unset and aborts the trap.
# shellcheck disable=SC2317  # invoked indirectly by the EXIT trap below
_cleanup_temp() { rm -f "${_TEMP_FILES[@]+"${_TEMP_FILES[@]}"}" 2>/dev/null || true; }

usage() {
  log "Usage: scripts/run-plugin-tests.sh [-h] [-x|-t] [--all | --changed | PLUGIN...]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --all       Test every plugin (default when no argument is given)\n'
  printf '  --changed   Test only plugins with staged changes\n'
  printf '  PLUGIN...   Test the named plugins under plugins/\n'
}

depcheck() {
  local missing="" utility
  for utility in ${REQUIRED_DEPENDENCIES}; do
    command -v "${utility}" >/dev/null 2>&1 ||
      missing="${missing:+"${missing} "}${utility}"
  done
  case "${missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${missing}"
  return 1
}

run_plugin_tests() {
  local plugin_dir="${1}"
  local plugin_name
  plugin_name="${plugin_dir%/}"
  plugin_name="${plugin_name##*/}"
  local temp_output
  temp_output=$(mktemp "/tmp/test_output_${plugin_name}_XXXXXX")
  _TEMP_FILES+=("${temp_output}")

  log "Testing ${plugin_name}..."

  # Check if plugin has tests
  if [ ! -d "${plugin_dir}/tests" ]; then
    log "  ⊘ No tests directory"
    SKIPPED_PLUGINS+=("${plugin_name}")
    return 0
  fi

  # Check if plugin has Makefile with test target
  if [ -f "${plugin_dir}/Makefile" ]; then
    if grep -q "^test:" "${plugin_dir}/Makefile" 2>/dev/null; then
      # Run using Makefile - capture output, show on failure.
      # Redirect stdout first, then point stderr at it: `2>&1 > file`
      # reads left to right and would leave stderr on the terminal.
      if (cd "${plugin_dir}" && "${WITHOUT_GIT_ENV}" make test --quiet >"${temp_output}" 2>&1); then
        log "  ✓ Tests passed"
        PASSED_PLUGINS+=("${plugin_name}")
        rm -f "${temp_output}"
        return 0
      else
        log "  ✗ Tests failed"
        # Print the run that actually failed before re-running. The
        # re-run is a different run: when the failure is intermittent
        # it passes, and deleting this capture unread leaves no record
        # of what broke.
        log "Output of the failing run:"
        cat "${temp_output}"
        log "Re-running with verbose output:"
        (cd "${plugin_dir}" && "${WITHOUT_GIT_ENV}" make test 2>&1)
        FAILED_PLUGINS+=("${plugin_name}")
        rm -f "${temp_output}"
        return 1
      fi
    fi
  fi

  # Check if plugin has pyproject.toml with pytest
  if [ -f "${plugin_dir}/pyproject.toml" ]; then
    if grep -q "pytest" "${plugin_dir}/pyproject.toml" 2>/dev/null; then
      # Read coverage threshold from [tool.nightmarket] if set
      local cov_threshold
      cov_threshold=$(awk '
                /^\[tool\.nightmarket\]/ { in_nm=1; next }
                /^\[/ { in_nm=0 }
                in_nm && /^coverage_threshold[[:space:]]*=/ {
                    split($0, a, "="); gsub(/[[:space:]]/, "", a[2]); print a[2]; exit
                }
            ' "${plugin_dir}/pyproject.toml")

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
      if (cd "${plugin_dir}" && "${WITHOUT_GIT_ENV}" uv run python -m pytest tests/ --tb=short --quiet ${cov_flag[@]+"${cov_flag[@]}"} >"${temp_output}" 2>&1); then
        log "  ✓ Tests passed"
        PASSED_PLUGINS+=("${plugin_name}")
        rm -f "${temp_output}"
        return 0
      else
        log "  ✗ Tests failed"
        # See the Makefile branch above: print the failing run before
        # the re-run, so an intermittent failure leaves evidence.
        log "Output of the failing run:"
        cat "${temp_output}"
        log "Re-running with verbose output:"
        (cd "${plugin_dir}" && "${WITHOUT_GIT_ENV}" uv run python -m pytest tests/ --tb=short ${cov_flag[@]+"${cov_flag[@]}"} 2>&1)
        FAILED_PLUGINS+=("${plugin_name}")
        rm -f "${temp_output}"
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
  log "  ✗ Has tests/ but no test configuration"
  log "     Add a pyproject.toml configuring pytest, or a Makefile with a"
  log "     'test:' target. See plugins/cartograph/pyproject.toml."
  FAILED_PLUGINS+=("${plugin_name}")
  rm -f "${temp_output}"
  return 1
}

# A plugin is what carries a manifest, not whatever happens to sit in plugins/.
# The bare plugins/*/ glob also matched the gitignored plugins/__pycache__ left
# behind by a root-level pytest run, and the loop dutifully announced
# "Testing __pycache__...".
is_plugin_dir() {
  local dir="${1}"
  [ -f "${dir}/.claude-plugin/plugin.json" ] || [ -f "${dir}/openpackage.yml" ]
}

# Runs from PROJECT_ROOT (main enters it in a subshell), so every plugin
# path below is relative to the repository root.
run_selected() {
  trap _cleanup_temp EXIT

  local plugin_dir plugin_name changed_files changed_plugins
  case "${1:-}" in
    "" | --all)
      # Run all plugin tests
      banner "Running All Plugin Tests"

      for plugin_dir in plugins/*/; do
        if [ -d "${plugin_dir}" ] && is_plugin_dir "${plugin_dir}"; then
          run_plugin_tests "${plugin_dir}" || true
        fi
      done
      ;;
    --changed)
      # Run tests for plugins with staged changes
      banner "Running Tests for Changed Plugins"

      # Get list of changed files
      changed_files=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || :)

      case "${changed_files}" in
        "")
          log "No staged changes found"
          exit 0
          ;;
      esac

      # Extract unique plugin directories
      changed_plugins=$(printf '%s\n' "${changed_files}" | grep "^plugins/" | cut -d/ -f1-2 | sort -u)

      case "${changed_plugins}" in
        "")
          log "No plugin changes detected"
          exit 0
          ;;
      esac

      # Run tests for each changed plugin
      while IFS= read -r plugin_dir; do
        if [ -d "${plugin_dir}" ]; then
          run_plugin_tests "${plugin_dir}" || true
        fi
      done <<<"${changed_plugins}"
      ;;
    *)
      # Run tests for specified plugins
      banner "Running Tests for Specified Plugins"

      for plugin_name in "$@"; do
        plugin_dir="plugins/${plugin_name}"
        if [ -d "${plugin_dir}" ]; then
          run_plugin_tests "${plugin_dir}" || true
        else
          log "✗ Plugin not found: ${plugin_name}"
        fi
      done
      ;;
  esac

  # Summary
  banner "Test Summary"

  if [ ${#PASSED_PLUGINS[@]} -gt 0 ]; then
    log "✓ Passed (${#PASSED_PLUGINS[@]}): ${PASSED_PLUGINS[*]}"
  fi

  if [ ${#SKIPPED_PLUGINS[@]} -gt 0 ]; then
    log "⊘ Skipped (${#SKIPPED_PLUGINS[@]}): ${SKIPPED_PLUGINS[*]}"
  fi

  if [ ${#FAILED_PLUGINS[@]} -gt 0 ]; then
    log "✗ Failed (${#FAILED_PLUGINS[@]}): ${FAILED_PLUGINS[*]}"
    log "ERROR: Some tests failed!"
    exit 1
  fi

  log "All tests passed!"
  exit 0
}

main() {
  local arg
  local positional=()
  for arg in "$@"; do
    case "${arg}" in
      -h | *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP])
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
      *) positional+=("${arg}") ;;
    esac
  done
  set -- "${positional[@]+"${positional[@]}"}"

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1
  # The subshell scopes the cd; its exit status is the script's.
  (cd "${PROJECT_ROOT}" && run_selected "$@")
}

main "$@"
