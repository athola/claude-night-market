#!/usr/bin/env bash
# Install egregore watchdog as a macOS launchd agent
# Usage: install_launchd.sh [-h] [-x|-t] [interval] [workdir]
set -euo pipefail

# ${0%/*} returns its input unchanged when $0 has no slash
# (`bash install_launchd.sh`), where dirname gave ".".
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

REQUIRED_DEPENDENCIES="launchctl"
readonly REQUIRED_DEPENDENCIES

PLIST_NAME="com.egregore.watchdog"
readonly PLIST_NAME

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
  log "Usage: install_launchd.sh [-h] [-x|-t] [interval] [workdir]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  interval    Seconds between watchdog runs (default: 300)\n'
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
  log 5 "launchd agents are macOS only; on Linux use install_systemd.sh"
  return 1
}

# Plist values are XML text. bash 5.2+ reads & in a replacement as the
# matched text unless patsub_replacement is off. bash 3.2 has no such
# option, so the shopt fails there and is ignored.
xml_escape() {
  shopt -u patsub_replacement 2>/dev/null || true
  local s="${1}"
  s="${s//&/&amp;}"
  s="${s//</&lt;}"
  s="${s//>/&gt;}"
  printf '%s' "${s}"
}

write_plist() {
  XML_SCRIPT="$(xml_escape "${WATCHDOG_SCRIPT}")"
  XML_DIR="$(xml_escape "${WORKING_DIR}")"

  cat >"${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${XML_SCRIPT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${XML_DIR}</string>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>StandardOutPath</key>
    <string>${XML_DIR}/.egregore/watchdog-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${XML_DIR}/.egregore/watchdog-launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF
}

load_agent() {
  GUI_DOMAIN="gui/$(id -u)"
  readonly GUI_DOMAIN
  # bootstrap refuses a label that is already loaded, so a re-install kept
  # the old job. Unload it first; failure here means it was not loaded.
  launchctl bootout "${GUI_DOMAIN}/${PLIST_NAME}" 2>/dev/null || true
  if launchctl bootstrap "${GUI_DOMAIN}" "${PLIST_PATH}"; then
    : # modern macOS (10.10+)
  else
    launchctl load "${PLIST_PATH}" # fallback for older macOS
  fi
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

  INTERVAL="${1:-300}"
  WORKING_DIR="${2:-$(pwd)}"
  WATCHDOG_SCRIPT="$(cd "${MYDIR}" && pwd)/watchdog.sh"
  PLIST_PATH="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"
  readonly INTERVAL WORKING_DIR WATCHDOG_SCRIPT PLIST_PATH

  depcheck || exit 1

  if [ ! -f "${WATCHDOG_SCRIPT}" ]; then
    log 5 "watchdog.sh not found at ${WATCHDOG_SCRIPT}"
    exit 1
  fi

  write_plist
  load_agent
  log "Installed: ${PLIST_PATH}"
  log "Checking every ${INTERVAL}s in ${WORKING_DIR}"
  log "To uninstall: launchctl bootout ${GUI_DOMAIN}/${PLIST_NAME} 2>/dev/null || launchctl unload ${PLIST_PATH}; rm ${PLIST_PATH}"
}

main "$@"
