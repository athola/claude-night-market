#!/usr/bin/env bash
# health-snapshot.sh: read-only repo health summary for claude-night-market.
#
# Runs the cheap, non-mutating diagnostic checks and prints a PASS/FAIL
# table. Failing checks dump their output to stderr so the table stays
# clean. Exit 0 when every check passes, 1 otherwise.
#
# Dependencies: bash, python3. No uv, no network, no writes.
#
# Usage: health-snapshot.sh [-h] [-x|-t]
# No `set -e`: a failing check must be recorded, not end the run.
set -u

# A bare name (`bash health-snapshot.sh` from its own directory) has no
# slash, and `${0%/*}` would return the name itself.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# Script lives at .claude/skills/<skill>/scripts/; repo root is 4 levels
# up. The skill is repo-local, so the repository's logging.sh is always
# there.
REPO_ROOT="$(cd "${MYDIR%/}/../../../.." && pwd)"
readonly REPO_ROOT

# shellcheck source=scripts/logging.sh
. "${REPO_ROOT}/scripts/logging.sh"

XTRACE=0
NAMES=()
RESULTS=()
overall=0

usage() {
  log "Usage: ${MYDIR%/}/health-snapshot.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
}

run_check() {
  local name="${1}"
  shift
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  NAMES+=("${name}")
  case "${rc}" in
    0) RESULTS+=("PASS") ;;
    *)
      RESULTS+=("FAIL")
      overall=1
      log 4 "--- ${name} failed (exit ${rc}) ---"
      log 4 "${out}"
      ;;
  esac
}

validate_all_plugins() {
  local rc=0 p
  for p in plugins/*/; do
    [ -f "${p}.claude-plugin/plugin.json" ] || continue
    if ! python3 plugins/abstract/scripts/validate_plugin.py "${p%/}" \
      >/dev/null 2>&1; then
      log 4 "validate_plugin.py FAILED for ${p%/}"
      rc=1
    fi
  done
  return "${rc}"
}

# Runs from the repository root, so every check path is root-relative.
snapshot() {
  local i
  run_check "plugin-structure (validate_plugin.py, all plugins)" validate_all_plugins
  run_check "capabilities-sync (docs vs registrations)" bash scripts/capabilities-sync-check.sh
  run_check "supply-chain-scan (lockfile blocklist)" python3 scripts/supply_chain_scan.py
  run_check "skill-graph-drift (ratchet)" python3 scripts/check_skill_graph_drift.py
  run_check "exit-criteria-drift (ratchet)" python3 scripts/check_skill_exit_criteria_drift.py
  run_check "description-budget (160-char / 90K ceiling)" python3 plugins/abstract/scripts/validate_budget.py

  log "$(printf '%-50s %s' "CHECK" "RESULT")"
  log "$(printf '%-50s %s' "-----" "------")"
  for i in "${!NAMES[@]}"; do
    log "$(printf '%-50s %s' "${NAMES[${i}]}" "${RESULTS[${i}]}")"
  done

  case "${overall}" in
    0) log "Health snapshot: ALL CHECKS PASSED" ;;
    *) log 4 "Health snapshot: FAILURES DETECTED (details on stderr above)" ;;
  esac
  return "${overall}"
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

  (cd "${REPO_ROOT}" && snapshot)
}

main "$@"
