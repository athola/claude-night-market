#!/usr/bin/env bash
# Gemini CLI Status Monitor
# Usage: status.sh [-h] [-x|-t]

set -euo pipefail

# ${0%/*} returns its input unchanged when $0 has no slash
# (`bash status.sh`), where dirname gave ".".
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# Each section already reports its own tool as unavailable, so a missing
# one is a warning, not a reason to stop the report.
OPTIONAL_DEPENDENCIES="python3 gemini"
readonly OPTIONAL_DEPENDENCIES

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
  log "Usage: status.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
}

optional_depcheck() {
  for _od_util in ${OPTIONAL_DEPENDENCIES}; do
    command -v "${_od_util}" >/dev/null 2>&1 ||
      log 3 "Optional utility not found: ${_od_util}"
  done
}

report_quota() {
  log "**Quota Status**:"
  python3 "${SCRIPTS}/quota_tracker.py" --status 2>/dev/null || log "  Quota tracker unavailable"
  log ""
}

report_usage() {
  log "**Usage Summary (24h)**:"
  python3 -c "
from usage_logger import GeminiUsageLogger
import json
try:
    logger = GeminiUsageLogger()
    summary = logger.get_usage_summary()
    print(f'  Requests: {summary[\"total_requests\"]}')
    print(f'  Tokens: {summary[\"total_tokens\"]:,}')
    print(f'  Success Rate: {summary[\"success_rate\"]:.1f}%')
except Exception as e:
    print(f'  Error: {e}')
" 2>/dev/null || log "  Usage logger unavailable"
  log ""
}

report_errors() {
  log "**Recent Errors**:"
  python3 -c "
from usage_logger import GeminiUsageLogger
import json
try:
    logger = GeminiUsageLogger()
    errors = logger.get_recent_errors(3)
    if errors:
        for error in errors[-3:]:
            timestamp = error['timestamp'].split('T')[1][:8]
            print(f'  {timestamp}: {error[\"error\"]}')
    else:
        print('  No recent errors')
except Exception:
    print('  No error data available')
" 2>/dev/null || log "  Error log unavailable"
  log ""
}

report_auth() {
  log "**Authentication**:"
  if gemini auth status >/dev/null 2>&1; then
    log "  Authenticated"
  else
    log "  Not authenticated or quota exhausted"
  fi
  log ""
}

report_commands() {
  log "**Quick Commands**:"
  log "  • Monitor quota: python3 ${SCRIPTS}/quota_tracker.py --status"
  log "  • View usage: PYTHONPATH=${SCRIPTS} python3 -c 'from usage_logger import GeminiUsageLogger; print(GeminiUsageLogger().get_usage_summary())'"
  log "  • Check auth: gemini auth status"
}

main() {
  # Unrecognized arguments are ignored, as they always were.
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

  optional_depcheck

  # The Python helpers live in ../scripts, not in the caller's directory.
  SCRIPTS="$(cd "${MYDIR}/../scripts" && pwd)"
  readonly SCRIPTS
  export PYTHONPATH="${SCRIPTS}${PYTHONPATH:+:${PYTHONPATH}}"

  log "**Gemini CLI Status Report**"
  log "=================================="
  log ""

  report_quota
  report_usage
  report_errors
  report_auth
  report_commands
}

main "$@"
