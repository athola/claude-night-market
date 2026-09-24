#!/usr/bin/env bash
# Run linting for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-lint.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-lint.sh --all
#   ./scripts/run-plugin-lint.sh --changed (runs linting for plugins with changes)

set -euo pipefail

# A bare name (`bash run-plugin-lint.sh` from inside scripts/) has no
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

readonly REQUIRED_DEPENDENCIES="uv make"
XTRACE=0

# A check that rewrites the tree hides the diff it exists to report, so
# --fix is opt-in. check-all-quality.sh forwards it when asked.
# An array rather than a string, so the optional flag is passed as one
# argument without relying on word-splitting an unquoted expansion.
#
# Expanded as ${LINT_FIX[@]+"${LINT_FIX[@]}"} rather than "${LINT_FIX[@]}":
# under `set -u`, bash 3.2 (stock macOS /bin/bash) reports
# "LINT_FIX[@]: unbound variable" for an empty array, which is the common
# case here since --fix is off by default.
LINT_FIX=()

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

usage() {
  log "Usage: scripts/run-plugin-lint.sh [-h] [-x|-t] [--fix] [--all | --changed | PLUGIN...]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --fix       Let ruff rewrite the tree (off by default)\n'
  printf '  --all       Lint every plugin (default when no argument is given)\n'
  printf '  --changed   Lint only plugins with staged changes\n'
  printf '  PLUGIN...   Lint the named plugins under plugins/\n'
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

run_plugin_lint() {
  local plugin_dir="${1}"
  local plugin_name
  plugin_name="${plugin_dir%/}"
  plugin_name="${plugin_name##*/}"

  log "Linting ${plugin_name}..."

  # Check if plugin has source code
  if [ ! -d "${plugin_dir}/src" ] && [ ! -d "${plugin_dir}/scripts" ]; then
    log "  ⊘ No Python source code"
    SKIPPED_PLUGINS+=("${plugin_name}")
    return 0
  fi

  # Check if plugin has Makefile with lint target
  if [ -f "${plugin_dir}/Makefile" ]; then
    if grep -q "^lint:" "${plugin_dir}/Makefile" 2>/dev/null; then
      # Run using Makefile - capture exit code separately to avoid pipeline masking
      local lint_output lint_exit=0
      lint_output=$(cd "${plugin_dir}" && make lint 2>&1) || lint_exit=${?}
      # Filter make noise when displaying
      printf '%s\n' "${lint_output}" | grep -v "^make\[" || true
      case "${lint_exit}" in
        0)
          log "  ✓ Linting passed"
          PASSED_PLUGINS+=("${plugin_name}")
          return 0
          ;;
        *)
          log "  ✗ Linting failed"
          FAILED_PLUGINS+=("${plugin_name}")
          return 1
          ;;
      esac
    fi
  fi

  # Fallback: Run ruff directly
  if [ -f "${plugin_dir}/pyproject.toml" ] && grep -q "ruff" "${plugin_dir}/pyproject.toml" 2>/dev/null; then
    if (cd "${plugin_dir}" && uv run ruff check . ${LINT_FIX[@]+"${LINT_FIX[@]}"} 2>&1); then
      log "  ✓ Linting passed"
      PASSED_PLUGINS+=("${plugin_name}")
      return 0
    else
      log "  ✗ Linting failed"
      FAILED_PLUGINS+=("${plugin_name}")
      return 1
    fi
  fi

  # No lint configuration found - use global ruff
  if command -v ruff &>/dev/null; then
    if ruff check "${plugin_dir}" ${LINT_FIX[@]+"${LINT_FIX[@]}"} --config pyproject.toml 2>&1; then
      log "  ✓ Linting passed"
      PASSED_PLUGINS+=("${plugin_name}")
      return 0
    else
      log "  ✗ Linting failed"
      FAILED_PLUGINS+=("${plugin_name}")
      return 1
    fi
  fi

  log "  ⊘ No lint configuration"
  SKIPPED_PLUGINS+=("${plugin_name}")
  return 0
}

# Runs from PROJECT_ROOT (main enters it in a subshell), so every plugin
# path below is relative to the repository root.
run_selected() {
  local plugin_dir plugin_name changed_files changed_plugins
  case "${1:-}" in
    "" | --all)
      # Run all plugin linting
      banner "Running Linting Across All Plugins"

      for plugin_dir in plugins/*/; do
        if [ -d "${plugin_dir}" ]; then
          run_plugin_lint "${plugin_dir}" || true
        fi
      done
      ;;
    --changed)
      # Run linting for plugins with staged changes
      banner "Running Linting for Changed Plugins"

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

      # Run linting for each changed plugin
      while IFS= read -r plugin_dir; do
        if [ -d "${plugin_dir}" ]; then
          run_plugin_lint "${plugin_dir}" || true
        fi
      done <<<"${changed_plugins}"
      ;;
    *)
      # Run linting for specified plugins
      banner "Running Linting for Specified Plugins"

      for plugin_name in "$@"; do
        plugin_dir="plugins/${plugin_name}"
        if [ -d "${plugin_dir}" ]; then
          run_plugin_lint "${plugin_dir}" || true
        else
          log "✗ Plugin not found: ${plugin_name}"
        fi
      done
      ;;
  esac

  # Summary
  banner "Linting Summary"

  if [ ${#PASSED_PLUGINS[@]} -gt 0 ]; then
    log "✓ Passed (${#PASSED_PLUGINS[@]}): ${PASSED_PLUGINS[*]}"
  fi

  if [ ${#SKIPPED_PLUGINS[@]} -gt 0 ]; then
    log "⊘ Skipped (${#SKIPPED_PLUGINS[@]}): ${SKIPPED_PLUGINS[*]}"
  fi

  if [ ${#FAILED_PLUGINS[@]} -gt 0 ]; then
    log "✗ Failed (${#FAILED_PLUGINS[@]}): ${FAILED_PLUGINS[*]}"
    log "ERROR: Linting failed!"
    exit 1
  fi

  log "All linting checks passed!"
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
      --fix) LINT_FIX=(--fix) ;;
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
