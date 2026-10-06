#!/usr/bin/env bash
# Start virtual display and window manager for computer use
# Usage: entrypoint.sh [command [args...]]
#
# Every argument is the command to exec once the display is up, so this
# script parses no flags of its own: a -h or -x here belongs to the task.
# Run it under `bash -x` to trace it.
set -euo pipefail

REQUIRED_DEPENDENCIES="Xvfb mktemp"
readonly REQUIRED_DEPENDENCIES

# A missing window manager or panel never stopped the task, so these
# are reported and the task still runs.
OPTIONAL_DEPENDENCIES="mutter tint2"
readonly OPTIONAL_DEPENDENCIES

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
  return 1
}

optional_depcheck() {
  for _od_util in ${OPTIONAL_DEPENDENCIES}; do
    command -v "${_od_util}" >/dev/null 2>&1 ||
      log 3 "Optional utility not found: ${_od_util}"
  done
}

# Start Xvfb (virtual framebuffer). -displayfd makes it write the display
# number once it accepts clients; a dead Xvfb (a stale /tmp/.X1-lock, say)
# stops the entrypoint instead of running the task against no display.
start_display() {
  ready_file="$(mktemp)"
  Xvfb :1 -screen 0 1920x1080x24 -displayfd 3 3>"${ready_file}" &
  xvfb_pid="${!}"
  tries=0
  until [ -s "${ready_file}" ]; do
    if ! kill -0 "${xvfb_pid}" 2>/dev/null; then
      log 5 "Xvfb exited before display :1 was ready"
      exit 1
    fi
    tries=$((tries + 1))
    if [ "${tries}" -gt 100 ]; then
      log 5 "Xvfb was not ready on :1 after 10s"
      exit 1
    fi
    sleep 0.1
  done
  rm -f "${ready_file}"
}

main() {
  depcheck || exit 1
  optional_depcheck

  start_display

  # Start a lightweight window manager
  mutter --replace --display=:1 &
  sleep 1

  # Start panel
  tint2 &

  log "Display environment ready on :1 (1920x1080)"
  log "Run tasks with: python -m phantom.cli <task>"

  # If arguments provided, run them; otherwise keep alive
  case "${#}" in
    0) exec bash ;;
    *) exec "$@" ;;
  esac
}

main "$@"
