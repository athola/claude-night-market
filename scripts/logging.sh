# scripts/logging.sh: POSIX logging library
# Source this file before calling log() or banner().
# No shebang, no execute bit, no set -e or set -u.

case "${__logging_loaded:-NULL}" in
  1) return 0 ;;
esac

readonly __logging_loaded=1

# Log level threshold; override via LOG_LEVEL env var.
# 0=debug 1=info 2=warn 3=notice 4=error 5=crit
LOG_LEVEL="${LOG_LEVEL:-1}"

# log [LEVEL] MESSAGE ...
# LEVEL: 0-5 numeric (default 1/info when omitted).
# Levels 0-4 honour LOG_LEVEL threshold; 5 always prints.
log() {
  _log_level=1
  case "${1:-}" in
    [0-9])
      _log_level="${1}"
      shift
      ;;
  esac
  case "${_log_level}" in
    0)
      [ "${LOG_LEVEL}" -le 0 ] || return 0
      printf '[DEBUG] %s\n' "${*}" >&2
      ;;
    1)
      [ "${LOG_LEVEL}" -le 1 ] || return 0
      printf '[INFO]  %s\n' "${*}"
      ;;
    2)
      [ "${LOG_LEVEL}" -le 2 ] || return 0
      printf '[WARN]  %s\n' "${*}" >&2
      ;;
    3)
      [ "${LOG_LEVEL}" -le 3 ] || return 0
      printf '[NOTE]  %s\n' "${*}" >&2
      ;;
    4)
      [ "${LOG_LEVEL}" -le 4 ] || return 0
      printf '[ERROR] %s\n' "${*}" >&2
      ;;
    5)
      printf '[CRIT]  %s\n' "${*}" >&2
      ;;
  esac
}

# banner MESSAGE [WIDTH]
# Prints a box-bordered heading to stdout.
banner() {
  _banner_msg="${1:?banner: message required}"
  _banner_width="${2:-60}"
  _banner_line="$(printf '%*s' "${_banner_width}" '' | tr ' ' '=')"
  printf '\n%s\n  %s\n%s\n\n' \
    "${_banner_line}" "${_banner_msg}" "${_banner_line}"
}
