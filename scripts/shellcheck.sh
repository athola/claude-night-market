#!/bin/sh
# Run shellcheck across every tracked .sh file in the repository.
# Usage: scripts/shellcheck.sh [-h] [-x|-t] [-s SHELL] [-S SEVERITY]
set -eu

MYDIR="${0%/*}"
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

REQUIRED_DEPENDENCIES="shellcheck git"
XTRACE=0
# Empty means "let each file's shebang decide". 37 of the 39 scripts here
# declare bash, so pinning a dialect reports every bash construct as an
# SC3xxx portability violation against a target no script claimed.
SHELL_DIALECT=""
# The floor separates defects from notes. Below `warning` the gate's
# verdict is dominated by style opinions and stops being read.
SEVERITY="warning"

usage() {
  log "Usage: scripts/shellcheck.sh [-h] [-x|-t] [-s SHELL] [-S SEVERITY]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  -s SHELL    Force a shell dialect (default: each shebang decides)\n'
  printf '  -S SEVERITY shellcheck severity floor: error, warning, info, style\n'
  printf '              (default: warning)\n'
}

depcheck() {
  _dc_missing=""
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 ||
      _dc_missing="${_dc_missing:+"${_dc_missing} "}${_dc_util}"
  done
  case "${#_dc_missing}" in
    0) return 0 ;;
  esac
  log 5 "Required utilities not found: ${_dc_missing}"
  log 5 "Install with your package manager, e.g.: brew install ${_dc_missing}"
  return 1
}

# The repository root, absolute. `${MYDIR%/*}` returned its input unchanged
# when the invocation had no leading path (`scripts/shellcheck.sh`), so the
# scan root became `scripts` and 24 of the 39 scripts, every hook among
# them, were never looked at.
repo_root() {
  (cd "${MYDIR%/}/.." && pwd)
}

run_shellcheck() {
  _sc_root="$(repo_root)"
  _sc_fail=0
  # -x follows `.`/`source` directives. Without it every library-sourcing
  # script raises SC1091 and the gate fails on itself.
  set -- -x -S "${SEVERITY}"
  case "${SHELL_DIALECT}" in
    "") ;;
    *) set -- "$@" -s "${SHELL_DIALECT}" ;;
  esac

  # Captured before the loop: inside the heredoc below a failing
  # `git ls-files` does not trip `set -e`, and an empty list read as a pass.
  _sc_files="$(cd "${_sc_root}" && git ls-files '*.sh')" || {
    log 5 "git ls-files failed; is ${_sc_root} a git worktree?"
    return 1
  }
  case "${_sc_files}" in
    "")
      log 5 "No tracked .sh files found under ${_sc_root}."
      return 1
      ;;
  esac

  log "Running shellcheck -S ${SEVERITY} on every tracked .sh file…"
  while IFS= read -r _sc_file; do
    case "${_sc_file}" in
      "") continue ;;
    esac
    shellcheck "$@" "${_sc_root}/${_sc_file}" || {
      log 4 "Failed: ${_sc_file}"
      _sc_fail=1
    }
  done <<EOF
$(printf '%s\n' "${_sc_files}" | sort)
EOF

  case "${_sc_fail}" in
    0) log "All scripts passed." ;;
    *)
      log 4 "One or more scripts failed shellcheck."
      return 1
      ;;
  esac
}

main() {
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t)
        XTRACE=1
        ;;
      -s)
        SHELL_DIALECT="${2:?-s requires a shell dialect argument}"
        shift
        ;;
      -S)
        SEVERITY="${2:?-S requires a severity argument}"
        shift
        ;;
      *)
        log 4 "Unknown option: ${1}"
        usage
        exit 1
        ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1
  run_shellcheck
}

main "$@"
