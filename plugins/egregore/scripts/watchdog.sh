#!/usr/bin/env bash
# egregore-watchdog.sh
#
# Checks if egregore needs relaunching. Run via launchd or
# systemd timer every 5 minutes. Pure shell, no network calls,
# fully auditable.
# Usage: watchdog.sh [-h] [-x|-t]
set -euo pipefail

REQUIRED_DEPENDENCIES="jq"
readonly REQUIRED_DEPENDENCIES

XTRACE=0

# The plugin is installed on its own, so the repository's
# scripts/logging.sh is not on disk beside it. This is the same
# interface at level 1: informational output on stdout, errors on
# stderr, and no bare echo anywhere.
log() {
  _log_level=1
  case "${1:-}" in
    [0-9])
      _log_level="${1}"
      shift
      ;;
  esac
  case "${_log_level}" in
    4 | 5) printf '[ERROR] %s\n' "${*}" >&2 ;;
    2 | 3) printf '[WARN]  %s\n' "${*}" >&2 ;;
    *) printf '[INFO]  %s\n' "${*}" ;;
  esac
}

# The watchdog's record of each tick. A timer runs it unattended, so
# this file is what an operator reads; its timestamped format is kept.
wlog() { printf '%s: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${*}" >>"${LOG}"; }

usage() {
  log "Usage: watchdog.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '\nEnvironment overrides:\n'
  printf '  EGREGORE_DIR  (default: .egregore)\n'
}

# Resolved once, absolute: the relaunch below cds into the manifest's
# project_dir, and a relative pid file would then be written under the
# timer's working directory and checked under another.
resolve_paths() {
  EGREGORE_DIR="$(cd "${EGREGORE_DIR:-.egregore}" 2>/dev/null && pwd || printf '%s' "${EGREGORE_DIR:-.egregore}")"
  MANIFEST="${EGREGORE_DIR}/manifest.json"
  BUDGET="${EGREGORE_DIR}/budget.json"
  PIDFILE="${EGREGORE_DIR}/pid"
  LOG="${EGREGORE_DIR}/watchdog.log"
  readonly EGREGORE_DIR MANIFEST BUDGET PIDFILE LOG
}

# Reports to the watchdog log, not stderr: nobody reads a timer's
# stderr, and the log is where every other refusal is recorded.
depcheck() {
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 || {
      wlog "ERROR: ${_dc_util} not installed, cannot parse manifest"
      return 1
    }
  done
}

# Exits 0 when the cooldown in budget.json has not yet passed.
check_cooldown() {
  [ -f "${BUDGET}" ] || return 0
  if ! cooldown=$(jq -r '.cooldown_until // empty' "${BUDGET}" 2>/dev/null); then
    wlog "ERROR: ${BUDGET} does not parse; cooldown unknown, not relaunching"
    exit 1
  fi
  case "${cooldown}" in
    "") return 0 ;;
  esac
  now=$(date +%s)
  case "$(uname)" in
    Darwin)
      # cooldown_until is always written in UTC. BSD date -j reads the
      # wall-clock fields in the local zone and cannot parse the
      # "+00:00" offset, so parse the first 19 characters as UTC.
      until_ts=$(TZ=UTC date -jf "%Y-%m-%dT%H:%M:%S" "${cooldown:0:19}" +%s 2>/dev/null || printf '0')
      ;;
    *)
      until_ts=$(date -d "${cooldown}" +%s 2>/dev/null || printf '0')
      ;;
  esac
  if [ "${now}" -lt "${until_ts}" ]; then
    wlog "In cooldown until ${cooldown}, waiting"
    exit 0
  fi
}

# Exits 0 when the recorded session is still alive.
check_running() {
  [ -f "${PIDFILE}" ] || return 0
  pid=$(cat "${PIDFILE}")
  if kill -0 "${pid}" 2>/dev/null; then
    exit 0 # session alive
  fi
  wlog "Stale pid ${pid} detected (crash). Cleaning up."
  rm -f "${PIDFILE}"
}

relaunch() {
  # Read project dir from manifest
  project_dir=$(jq -r '.project_dir' "${MANIFEST}" 2>/dev/null)
  case "${project_dir}" in
    "" | null)
      project_dir="$(pwd)"
      ;;
    *)
      if [ ! -d "${project_dir}" ]; then
        wlog "ERROR: project_dir '${project_dir}' from manifest does not exist; aborting relaunch"
        exit 1
      fi
      ;;
  esac

  wlog "Relaunching egregore session (${remaining} active items)"
  # Not a subshell: the session started below must run in project_dir.
  cd "${project_dir}" || {
    wlog "ERROR: cd to '${project_dir}' failed; aborting"
    exit 1
  }

  relaunch_prompt="${EGREGORE_DIR}/relaunch-prompt.md"
  if [ -f "${relaunch_prompt}" ]; then
    prompt_content="$(cat "${relaunch_prompt}")"
  else
    prompt_content="Egregore resuming. Read .egregore/manifest.json and invoke Skill(egregore:summon) to continue the pipeline."
  fi

  # --output-format json because the default text format is swallowed
  # when the Stop hook blocks the stop, leaving no record of the run.
  # </dev/null because hooks read stdin, and nohup leaves it attached to
  # nothing: each hook then stalls 3s and prints a warning onto the same
  # stream as the result, which corrupts it.
  nohup claude -p "${prompt_content}" --output-format json </dev/null >>"${LOG}" 2>&1 &
  printf '%s\n' "${!}" >"${PIDFILE}"
  wlog "Launched with PID ${!}"
}

main() {
  # A timer passes no argv; unrecognized arguments are ignored as before.
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  resolve_paths

  # No manifest = nothing to do
  [ -f "${MANIFEST}" ] || exit 0

  # Check if work remains
  depcheck || exit 1

  # A manifest that does not parse is an error. Reading it as zero items
  # logged a truncated write as "No active work items".
  if ! remaining=$(jq '[.work_items[] | select(.status == "active" or .status == "paused")] | length' "${MANIFEST}" 2>/dev/null); then
    wlog "ERROR: ${MANIFEST} does not parse; not relaunching"
    exit 1
  fi
  case "${remaining}" in
    0)
      wlog "No active work items, exiting"
      exit 0
      ;;
  esac

  check_cooldown
  check_running
  relaunch
}

main "$@"
