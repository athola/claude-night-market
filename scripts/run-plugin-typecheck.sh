#!/usr/bin/env bash
# Run type checking for specified plugins or all plugins
#
# Usage:
#   ./scripts/run-plugin-typecheck.sh [plugin1] [plugin2] ...
#   ./scripts/run-plugin-typecheck.sh --all
#   ./scripts/run-plugin-typecheck.sh --changed (runs type checks for plugins with changes)

set -euo pipefail

# A bare name (`bash run-plugin-typecheck.sh` from inside scripts/) has no
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

# Pin the interpreter uv builds each plugin venv with. CI (typecheck.yml) uses
# setup-python 3.12; left alone, uv picks the LOWEST interpreter a plugin's
# requires-python allows (3.9), and a different interpreter resolves different
# dependency versions. That is not hypothetical: tome's 3.9 venv resolved numpy
# 2.0.2 (pre-PEP 695 stubs) and passed, while CI's 3.12 venv resolved a numpy
# whose stubs mypy could not parse. The gate was green locally and red in CI
# for a week. Pinning here makes the pre-commit hook and the CI job the same
# check. The mypy TARGET stays 3.9 via each plugin's python_version.
UV_PYTHON="${TYPECHECK_PYTHON:-3.12}"
readonly UV_PYTHON
export UV_PYTHON

readonly REQUIRED_DEPENDENCIES="uv make"
XTRACE=0

FAILED_PLUGINS=()
PASSED_PLUGINS=()
SKIPPED_PLUGINS=()

usage() {
  log "Usage: scripts/run-plugin-typecheck.sh [-h] [-x|-t] [--all | --changed | PLUGIN...]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --all       Type check every plugin (default when no argument is given)\n'
  printf '  --changed   Type check only plugins with staged changes\n'
  printf '  PLUGIN...   Type check the named plugins under plugins/\n'
  printf '  TYPECHECK_PYTHON (env) interpreter uv builds venvs with (default: 3.12)\n'
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

# Type check a plugin's hooks/ directory under its own (strict) mypy config.
# Hooks are not part of src/ or the Makefile typecheck target for most plugins,
# so without this they go unchecked and type errors accumulate. Returns 0 on
# pass or when there is nothing to check, 1 on failure.
run_hooks_typecheck() {
  local plugin_dir="${1}"

  # Only run when hooks/ actually contains Python modules. compgen -G does
  # the glob internally (no shellcheck SC2012 ls-as-test smell, and no
  # reliance on a non-matching glob being passed literally to ls).
  if ! compgen -G "${plugin_dir}/hooks/*.py" >/dev/null; then
    return 0
  fi

  log "  ↳ Type checking hooks/..."
  # `python -m mypy`, never bare `mypy`. `uv run mypy` falls back to whatever
  # is on PATH when the project environment has no mypy, so a plugin that
  # never declared it passed on any machine with a global mypy installed and
  # died on a clean CI runner with "Failed to spawn: mypy". Going through the
  # project interpreter resolves mypy only from that plugin's own environment,
  # which makes this gate mean the same thing locally and in CI.
  if (cd "${plugin_dir}" && uv run python -m mypy hooks/ 2>&1); then
    return 0
  fi
  return 1
}

run_plugin_typecheck() {
  local plugin_dir="${1}"
  local plugin_name
  plugin_name="${plugin_dir%/}"
  plugin_name="${plugin_name##*/}"
  local main_rc=0
  local checked=0

  log "Type checking ${plugin_name}..."

  # Primary source check: prefer a Makefile typecheck target (custom layouts),
  # then fall back to running mypy on src/ or scripts/ directly.
  if [ -f "${plugin_dir}/Makefile" ] &&
    (grep -qE "^(typecheck|type-check):" "${plugin_dir}/Makefile" 2>/dev/null ||
      (cd "${plugin_dir}" && make -n typecheck >/dev/null 2>&1)); then
    # Prefer explicit target in Makefile, fall back to typecheck
    local target
    target=$(grep -oE "^(typecheck|type-check):" "${plugin_dir}/Makefile" 2>/dev/null | head -1 | tr -d ':')
    case "${target}" in
      "") target="typecheck" ;;
    esac
    # Capture output and exit code separately to avoid pipeline exit code issues
    local output
    local exit_code=0
    output=$(cd "${plugin_dir}" && make "${target}" 2>&1) || exit_code=${?}
    # Filter and display output (excluding make's nested job messages)
    printf '%s\n' "${output}" | grep -v "^make\[" || true
    case "${exit_code}" in
      0) ;;
      *) main_rc=1 ;;
    esac
    checked=1
  elif { [ -d "${plugin_dir}/src" ] || [ -d "${plugin_dir}/scripts" ]; } &&
    [ -f "${plugin_dir}/pyproject.toml" ] &&
    grep -q "mypy" "${plugin_dir}/pyproject.toml" 2>/dev/null; then
    local src_target="src"
    [ -d "${plugin_dir}/src" ] || src_target="scripts"
    # python -m mypy, for the same reason as the hooks check above.
    if ! (cd "${plugin_dir}" && uv run python -m mypy "${src_target}/" 2>&1); then
      main_rc=1
    fi
    checked=1
  fi

  # Hooks check: always run when hooks/ has Python, regardless of how (or
  # whether) the primary source was checked above. This is the gap that let
  # hook type errors accumulate unnoticed.
  if compgen -G "${plugin_dir}/hooks/*.py" >/dev/null; then
    run_hooks_typecheck "${plugin_dir}" || main_rc=1
    checked=1
  fi

  case "${checked}" in
    0)
      log "  ⊘ No type checking configuration"
      SKIPPED_PLUGINS+=("${plugin_name}")
      return 0
      ;;
  esac

  case "${main_rc}" in
    0)
      log "  ✓ Type checking passed"
      PASSED_PLUGINS+=("${plugin_name}")
      return 0
      ;;
  esac

  log "  ✗ Type checking failed"
  FAILED_PLUGINS+=("${plugin_name}")
  return 1
}

# A plugin is what carries a manifest, not whatever happens to sit in plugins/.
# The bare plugins/*/ glob also matched the gitignored plugins/__pycache__ left
# behind by a root-level pytest run, which then showed up in the summary as a
# skipped plugin. Mirrors is_plugin_dir in run-plugin-tests.sh.
is_plugin_dir() {
  local dir="${1}"
  [ -f "${dir}/.claude-plugin/plugin.json" ] || [ -f "${dir}/openpackage.yml" ]
}

# Runs from PROJECT_ROOT (main enters it in a subshell), so every plugin
# path below is relative to the repository root.
run_selected() {
  local plugin_dir plugin_name changed_files changed_plugins
  case "${1:-}" in
    "" | --all)
      # Run all plugin type checking
      banner "Running Type Checks Across All Plugins"

      for plugin_dir in plugins/*/; do
        if [ -d "${plugin_dir}" ] && is_plugin_dir "${plugin_dir}"; then
          run_plugin_typecheck "${plugin_dir}" || true
        fi
      done
      ;;
    --changed)
      # Run type checking for plugins with staged changes
      banner "Running Type Checks for Changed Plugins"

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

      # Run type checking for each changed plugin
      while IFS= read -r plugin_dir; do
        if [ -d "${plugin_dir}" ]; then
          run_plugin_typecheck "${plugin_dir}" || true
        fi
      done <<<"${changed_plugins}"
      ;;
    *)
      # Run type checking for specified plugins
      banner "Running Type Checks for Specified Plugins"

      for plugin_name in "$@"; do
        plugin_dir="plugins/${plugin_name}"
        if [ -d "${plugin_dir}" ]; then
          run_plugin_typecheck "${plugin_dir}" || true
        else
          log "✗ Plugin not found: ${plugin_name}"
        fi
      done
      ;;
  esac

  # Summary
  banner "Type Checking Summary"

  if [ ${#PASSED_PLUGINS[@]} -gt 0 ]; then
    log "✓ Passed (${#PASSED_PLUGINS[@]}): ${PASSED_PLUGINS[*]}"
  fi

  if [ ${#SKIPPED_PLUGINS[@]} -gt 0 ]; then
    log "⊘ Skipped (${#SKIPPED_PLUGINS[@]}): ${SKIPPED_PLUGINS[*]}"
  fi

  if [ ${#FAILED_PLUGINS[@]} -gt 0 ]; then
    log "✗ Failed (${#FAILED_PLUGINS[@]}): ${FAILED_PLUGINS[*]}"
    log "ERROR: Type checking failed!"
    exit 1
  fi

  log "All type checks passed!"
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
