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

  # Ensure PATH includes node/clawhub. cron's PATH holds neither, and a
  # pinned node version stopped finding clawhub at the first upgrade, so
  # nvm's default alias is used, then the newest installed version.
  local node_bin
  node_bin="$(nvm_node_bin)"
  export PATH="${HOME}/.local/bin:${node_bin}${PATH}"

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

# Print "<dir>:" for nvm's node bin directory, or nothing without nvm.
# The default alias is followed through nvm's alias files (default to
# lts/* to lts/jod to v22.11.0). A partial version such as `25` takes the
# newest install of that major. `node`, an unknown alias, or no alias takes
# the newest install, and so does an alias naming no installed version.
# Newest is by version number: by name, v9.x sorts after v25.x and brings
# back the stale node this lookup exists to avoid.
nvm_node_bin() {
  _versions="${HOME}/.nvm/versions/node"
  _alias="default"
  _hops=0
  while [ "${_hops}" -lt 5 ] && [ -f "${HOME}/.nvm/alias/${_alias}" ]; do
    _alias="$(cat "${HOME}/.nvm/alias/${_alias}")"
    _hops=$((_hops + 1))
  done
  _alias="${_alias#v}"
  case "${_alias}" in
    [0-9]*)
      [ -d "${_versions}/v${_alias}/bin" ] && printf '%s:' "${_versions}/v${_alias}/bin" && return 0
      _glob="v${_alias}."
      ;;
    *) _glob="v" ;;
  esac
  for _glob in "${_glob}" v; do
    _newest="$(
      for _dir in "${_versions}/${_glob}"*/bin; do
        if [ -d "${_dir}" ]; then
          _version="${_dir%/bin}"
          printf '%s %s\n' "${_version##*/v}" "${_dir}"
        fi
      done | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1
    )"
    case "${_newest}" in
      "") ;;
      *) printf '%s:' "${_newest#* }" && return 0 ;;
    esac
  done
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
