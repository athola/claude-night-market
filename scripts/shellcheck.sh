#!/bin/sh
# Run shellcheck across all .sh files in the repository.
# Usage: scripts/shellcheck.sh [-h] [-x|-t] [-s SHELL]
set -eu

MYDIR="${0%/*}"
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

REQUIRED_DEPENDENCIES="shellcheck"
XTRACE=0
SHELL_DIALECT="sh"

usage() {
  log "Usage: scripts/shellcheck.sh [-h] [-x|-t] [-s SHELL]"
  printf '  -h       Show this help and exit (exit 0)\n'
  printf '  -x, -t   Enable xtrace (set -x) for debugging\n'
  printf '  -s SHELL Shell dialect passed to shellcheck -s (default: sh)\n'
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

run_shellcheck() {
  _sc_dialect="${1:?run_shellcheck: dialect required}"
  _sc_root="${MYDIR%/*}"
  _sc_fail=0

  log "Running shellcheck -s ${_sc_dialect} on all .sh files…"
  while IFS= read -r _sc_file; do
    shellcheck -s "${_sc_dialect}" "${_sc_file}" || {
      log 4 "Failed: ${_sc_file}"
      _sc_fail=1
    }
  done <<EOF
$(find "${_sc_root}" \
    -not -path "${_sc_root}/.venv/*" \
    -not -path "${_sc_root}/.git/*" \
    -not -path "*/node_modules/*" \
    -name "*.sh" -type f | sort)
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
  run_shellcheck "${SHELL_DIALECT}"
}

main "${@}"
