#!/usr/bin/env bash
# Install egregore watchdog as a systemd user timer
# Usage: install_systemd.sh [-h] [-x|-t] [interval] [workdir]
set -euo pipefail

# ${0%/*} returns its input unchanged when $0 has no slash
# (`bash install_systemd.sh`), where dirname gave ".".
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

REQUIRED_DEPENDENCIES="systemctl"
readonly REQUIRED_DEPENDENCIES

SERVICE_NAME="egregore-watchdog"
readonly SERVICE_NAME

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

usage() {
  log "Usage: install_systemd.sh [-h] [-x|-t] [interval] [workdir]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  interval    Minutes between watchdog runs (default: 5)\n'
  printf '  workdir     Project directory the watchdog runs in (default: $PWD)\n'
}

depcheck() {
  _dc_missing=""
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 ||
      _dc_missing="${_dc_missing:+"${_dc_missing} "}${_dc_util}"
  done
  case "${_dc_missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${_dc_missing}"
  log 5 "systemd user timers need a systemd host; on macOS use install_launchd.sh"
  return 1
}

write_units() {
  mkdir -p "${UNIT_DIR}"

  cat >"${UNIT_DIR}/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Egregore Watchdog Service

[Service]
Type=oneshot
WorkingDirectory=${WORKING_DIR}
ExecStart="${EXEC_SCRIPT}"
EOF

  cat >"${UNIT_DIR}/${SERVICE_NAME}.timer" <<EOF
[Unit]
Description=Egregore Watchdog Timer

[Timer]
OnBootSec=${INTERVAL}min
OnUnitActiveSec=${INTERVAL}min

[Install]
WantedBy=timers.target
EOF
}

main() {
  # Flags lead; the positionals after them keep their meaning, so a
  # workdir ending in "help" is not read as a help request.
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t)
        XTRACE=1
        shift
        ;;
      *) break ;;
    esac
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  INTERVAL="${1:-5}"
  WORKING_DIR="${2:-$(pwd)}"
  WATCHDOG_SCRIPT="$(cd "${MYDIR}" && pwd)/watchdog.sh"
  UNIT_DIR="${HOME}/.config/systemd/user"
  # Quoted so a space does not split the path, and % doubled so systemd does
  # not read it as a unit specifier.
  EXEC_SCRIPT="${WATCHDOG_SCRIPT//%/%%}"
  readonly INTERVAL WORKING_DIR WATCHDOG_SCRIPT UNIT_DIR EXEC_SCRIPT

  depcheck || exit 1

  write_units
  systemctl --user daemon-reload
  systemctl --user enable --now "${SERVICE_NAME}.timer"
  log "Installed: ${SERVICE_NAME}.timer"
  log "Checking every ${INTERVAL}min in ${WORKING_DIR}"
  log "To uninstall: systemctl --user disable --now ${SERVICE_NAME}.timer"
}

main "$@"
