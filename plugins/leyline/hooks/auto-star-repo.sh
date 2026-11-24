#!/usr/bin/env bash
# SessionStart hook: star athola/claude-night-market once, for a user who
# asked for it by setting leyline's star_repo plugin option (issue #1054).
#
# Usage:
#   (no args)  -- SessionStart: star once if opted in, otherwise do nothing
#   --star     -- star the repo now, by hand
#   -h         -- show usage
#   -x, -t     -- enable xtrace, for debugging by hand
#
# Safety guarantees:
#   - OFF BY DEFAULT: without star_repo set, no network call is made
#   - ONCE: a marker under XDG_STATE_HOME stops every later run and never
#     undoes an unstar. It lives outside the plugin's data directory,
#     which an uninstall deletes
#   - NEVER UNSTARS: No DELETE call exists in this script
#   - NEVER INSTRUCTS THE MODEL: the user is told in a systemMessage
#   - SILENT FAILURE: All errors are swallowed. A failed star leaves no
#     marker, and the next session tries again
#
# Claude Code exports the option to hooks as CLAUDE_PLUGIN_OPTION_STAR_REPO.
# CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1 overrides it.
#
# Auth methods (tried in order):
#   1. gh CLI (if installed and authenticated)
#   2. curl + GITHUB_TOKEN or GH_TOKEN env var
#
# gh and curl are both optional, and a missing one is the silent
# fallthrough above, so there is no depcheck: reporting it would put
# text where the hook contract allows only JSON.
#
# API behavior:
#   GET /user/starred/{owner}/{repo} -> 204 (starred) or 404 (not starred)
#   PUT /user/starred/{owner}/{repo} -> 204 (star added)

set -euo pipefail

OWNER="athola"
REPO="claude-night-market"
API_URL="https://api.github.com/user/starred/${OWNER}/${REPO}"
STATE_DIR="${XDG_STATE_HOME:-${HOME}/.local/state}/claude-night-market"
MARKER="${STATE_DIR}/star-done"
readonly OWNER REPO API_URL STATE_DIR MARKER

# The plugin is installed on its own, so the repository's
# scripts/logging.sh is not on disk beside it. Same interface at
# level 1. Only usage() and a failed --star call it: on the hook path
# stdout is JSON.
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
  log "Usage: auto-star-repo.sh [-h] [-x|-t] [--star]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --star      Star the repository now\n'
  printf '\nEnvironment:\n'
  printf '  CLAUDE_PLUGIN_OPTION_STAR_REPO=true   Star once at session start\n'
  printf '  CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1  Never star at session start\n'
}

# --- Star the repo (called with --star) ---

do_star_gh() {
  command -v gh >/dev/null 2>&1 || return 1
  gh auth status >/dev/null 2>&1 || return 1
  gh api -X PUT "/user/starred/${OWNER}/${REPO}" --silent 2>/dev/null
}

do_star_curl() {
  command -v curl >/dev/null 2>&1 || return 1

  # ${VAR:+set} expands to a fixed word, so -x never traces the token.
  case "${GITHUB_TOKEN:+set}${GH_TOKEN:+set}" in
    "") return 1 ;;
  esac

  # -f: a 401 or 403 must fail the call, or --star reports a star that
  # never happened. -H @- reads the token header from the here-string
  # (curl 7.55.0+): xtrace does not print redirections and ps does not
  # show stdin, so -x and other local users never see the token (#1305).
  curl -fsS -o /dev/null -X PUT \
    -H @- \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API_URL}" 2>/dev/null \
    <<<"Authorization: Bearer ${GITHUB_TOKEN:-${GH_TOKEN:-}}"
}

# --- Helper: emit empty SessionStart JSON and exit ---
_emit_empty() {
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":""}}'
  exit 0
}

# Claude Code writes a boolean option as true or false; accept the other
# usual spellings of yes too.
_opted_in() {
  case "${1:-}" in
    [tT][rR][uU][eE] | 1 | [yY][eE][sS] | [oO][nN]) return 0 ;;
  esac
  return 1
}

_mark_done() {
  mkdir -p "${STATE_DIR}" 2>/dev/null && : >"${MARKER}" 2>/dev/null || true
}

# --- Check star status via gh CLI ---

check_gh() {
  command -v gh >/dev/null 2>&1 || return 1
  gh auth status >/dev/null 2>&1 || return 1

  local status
  # gh exits 1 on a 404, which under pipefail poisons the whole pipeline and
  # turns "not starred" into "404\n000". Capture the headers first.
  local headers
  headers=$(gh api "/user/starred/${OWNER}/${REPO}" --silent -i 2>/dev/null || true)
  status=$(printf '%s\n' "${headers}" | head -1 | grep -oE '[0-9]{3}' || printf '000')

  case "${status}" in
    "204") printf 'starred\n' ;;
    "404") printf 'not_starred\n' ;;
    *) printf 'unknown\n' ;;
  esac
}

# --- Check star status via curl ---

check_curl() {
  command -v curl >/dev/null 2>&1 || return 1

  # ${VAR:+set} expands to a fixed word, so -x never traces the token.
  case "${GITHUB_TOKEN:+set}${GH_TOKEN:+set}" in
    "") return 1 ;;
  esac

  local http_code
  # The token header goes in on stdin, as in do_star_curl.
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H @- \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API_URL}" 2>/dev/null \
    <<<"Authorization: Bearer ${GITHUB_TOKEN:-${GH_TOKEN:-}}" ||
    printf '000')

  case "${http_code}" in
    "204") printf 'starred\n' ;;
    "404") printf 'not_starred\n' ;;
    *) printf 'unknown\n' ;;
  esac
}

# --- Main: check status, prompt if not starred ---

main() {
  # Claude Code passes no argv; -x/-t exists for debugging by hand.
  case "${1:-}" in
    -x | -t)
      set -x
      shift
      ;;
  esac

  # Any other argument falls through to the check.
  case "${1:-}" in
    *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
      usage
      exit 0
      ;;
    "--star")
      if do_star_gh 2>/dev/null || do_star_curl 2>/dev/null; then
        exit 0
      fi
      log 4 "Could not star ${OWNER}/${REPO}: gh is not logged in and the token PUT failed"
      exit 1
      ;;
  esac

  # --- Opt-in, opt-out and once checks ---
  case "${CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT:-}" in
    "1") _emit_empty ;;
  esac
  _opted_in "${CLAUDE_PLUGIN_OPTION_STAR_REPO:-}" || _emit_empty
  if [ -e "${MARKER}" ]; then
    _emit_empty
  fi

  local result
  result=$(check_gh 2>/dev/null || check_curl 2>/dev/null || printf 'unknown\n')

  case "${result}" in
    "starred")
      _mark_done
      ;;
    "not_starred")
      if do_star_gh 2>/dev/null || do_star_curl 2>/dev/null; then
        _mark_done
        # One line: the hook is async, and Claude Code before v2.1.295
        # parses only a one-line async response.
        printf '%s\n' '{"systemMessage":"leyline starred athola/claude-night-market on GitHub, as its star_repo option asked. Thank you. It will not star again.","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":""}}'
        exit 0
      fi
      ;;
  esac
  _emit_empty
}

main "$@"
