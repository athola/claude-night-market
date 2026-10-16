#!/usr/bin/env bash
# Cron wrapper for clawhub-submit. Runs hourly until all skills
# are synced, then removes itself from crontab.
#
# Install: crontab -e, add:
#   0 * * * * /home/alext/claude-night-market/scripts/clawhub-cron.sh
#
# Usage: scripts/clawhub-cron.sh [-h] [-x|-t]
#
# Logs to: /tmp/clawhub-sync.log

set -euo pipefail

# A bare name (`bash clawhub-cron.sh` from inside scripts/) has no slash
# for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

REPO_ROOT="$(cd "${MYDIR%/}/.." && pwd)"
readonly REPO_ROOT
readonly LOG="${CLAWHUB_SYNC_LOG:-/tmp/clawhub-sync.log}"
# Under the repo, not /tmp: another user cannot pre-create it and disable
# the job. mkdir is atomic, so check-then-create cannot race, and the trap
# clears it on any exit; a SIGKILL leaves a directory whose age says so.
readonly LOCK="${REPO_ROOT}/.clawhub-sync.lock"

XTRACE=0

usage() {
  log "Usage: scripts/clawhub-cron.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  CLAWHUB_SYNC_LOG (env) log file (default: /tmp/clawhub-sync.log)\n'
}

# The sync log is a file read by people tailing it, so its lines keep the
# "<date>: message" shape rather than logging.sh prefixes.
log_line() {
  printf '%s: %s\n' "$(date)" "${1}" >>"${LOG}"
}

run_sync() {
  # A run takes minutes. A lock older than two hours was left by a killed
  # run, and without reclaiming it every later run skipped forever.
  find "${LOCK}" -maxdepth 0 -type d -mmin +120 -exec rmdir {} \; 2>/dev/null || true

  # Prevent overlapping runs
  if ! mkdir "${LOCK}" 2>/dev/null; then
    log_line "Lock ${LOCK} exists, skipping"
    return 0
  fi
  trap 'rmdir "${LOCK}" 2>/dev/null' EXIT

  printf '\n' >>"${LOG}"
  printf '=== %s: clawhub-cron run ===\n' "$(date)" >>"${LOG}"

  # Ensure PATH includes node/clawhub
  export PATH="${HOME}/.local/bin:${HOME}/.nvm/versions/node/v25.2.1/bin:${PATH}"

  # No explicit version -- clawhub-submit.sh auto-detects from
  # plugins/abstract/.claude-plugin/plugin.json so the cron stays
  # correct across releases.
  local exit_code=0
  (cd "${REPO_ROOT}" && bash scripts/clawhub-submit.sh) >>"${LOG}" 2>&1 || exit_code=$?

  case "${exit_code}" in
    0)
      log_line "All skills synced. Removing cron job."
      crontab -l 2>/dev/null | grep -v "clawhub-cron" | crontab - 2>/dev/null || true
      log_line "Cron job removed."
      ;;
    *)
      log_line "Partial sync (exit ${exit_code}). Will retry next hour."
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
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  run_sync
}

main "$@"
