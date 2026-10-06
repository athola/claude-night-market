#!/usr/bin/env bash
# Verify vendored JSON utilities match scripts/shared/json_utils.sh.
#
# Each plugin keeps a byte-identical copy of json_utils.sh under
# hooks/shared/ so its hooks can source via
# ${CLAUDE_PLUGIN_ROOT}/hooks/shared/json_utils.sh from the Claude
# Code plugin cache. This script enforces that those vendored
# copies stay byte-identical to the canonical.
#
# Usage: scripts/shared/check-json-utils-drift.sh [-h] [-x|-t]
#
# Exit codes:
#   0 - all vendored copies match the canonical
#   1 - drift detected (one or more vendored copies differ)
#   2 - usage / file-not-found error

set -euo pipefail

# A bare name (`bash check-json-utils-drift.sh` from inside scripts/shared/)
# has no slash for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/../logging.sh"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
readonly REPO_ROOT
readonly CANONICAL="${REPO_ROOT}/scripts/shared/json_utils.sh"

readonly VENDORED=(
  "plugins/imbue/hooks/shared/json_utils.sh"
  "plugins/conserve/hooks/shared/json_utils.sh"
  "plugins/memory-palace/hooks/shared/json_utils.sh"
)

XTRACE=0

usage() {
  log "Usage: scripts/shared/check-json-utils-drift.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
}

check_drift() {
  local drift=0 vendored vendored_path

  if [ ! -f "${CANONICAL}" ]; then
    log 4 "canonical not found: ${CANONICAL}"
    return 2
  fi

  for vendored in "${VENDORED[@]}"; do
    vendored_path="${REPO_ROOT}/${vendored}"
    if [ ! -f "${vendored_path}" ]; then
      log 4 "vendored copy missing: ${vendored}"
      drift=1
      continue
    fi
    if ! diff -q "${CANONICAL}" "${vendored_path}" >/dev/null 2>&1; then
      log 4 "DRIFT: ${vendored} differs from ${CANONICAL}"
      diff "${CANONICAL}" "${vendored_path}" || true
      drift=1
    fi
  done

  case "${drift}" in
    0) ;;
    *)
      log 4 "vendored JSON utilities have drifted from canonical."
      log 4 "Re-run: cp scripts/shared/json_utils.sh <each vendored path>"
      return 1
      ;;
  esac

  log "OK: all vendored JSON utilities match canonical."
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
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  check_drift
}

main "$@"
