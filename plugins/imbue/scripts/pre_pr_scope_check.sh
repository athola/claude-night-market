#!/usr/bin/env bash
# pre_pr_scope_check.sh
# Checks branch metrics against scope-guard thresholds before PR creation.
#
# Usage: pre_pr_scope_check.sh [-h] [-x|-t] [base-branch]
# Default base branch: main, else master.
#
# Installed as .git/hooks/pre-push, git runs it as `hook <remote> <url>`.
# A first argument that names a configured remote is that call, and the
# default base is used.
#
# Exit codes:
#   0 - Green or yellow zone, proceed
#   1 - Red zone, requires justification
#   3 - Base branch not found

set -euo pipefail

# Thresholds (configurable via environment)
GREEN_LINES="${SCOPE_GUARD_GREEN_LINES:-1000}"
YELLOW_LINES="${SCOPE_GUARD_YELLOW_LINES:-1500}"
RED_LINES="${SCOPE_GUARD_RED_LINES:-2000}"

GREEN_FILES="${SCOPE_GUARD_GREEN_FILES:-8}"
YELLOW_FILES="${SCOPE_GUARD_YELLOW_FILES:-12}"
RED_FILES="${SCOPE_GUARD_RED_FILES:-15}"

GREEN_COMMITS="${SCOPE_GUARD_GREEN_COMMITS:-15}"
YELLOW_COMMITS="${SCOPE_GUARD_YELLOW_COMMITS:-25}"
RED_COMMITS="${SCOPE_GUARD_RED_COMMITS:-30}"

GREEN_DAYS="${SCOPE_GUARD_GREEN_DAYS:-3}"
YELLOW_DAYS="${SCOPE_GUARD_YELLOW_DAYS:-7}"
RED_DAYS="${SCOPE_GUARD_RED_DAYS:-7}"

COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_GREEN='\033[0;32m'
COLOR_NONE='\033[0m'

readonly GREEN_LINES YELLOW_LINES RED_LINES GREEN_FILES YELLOW_FILES RED_FILES
readonly GREEN_COMMITS YELLOW_COMMITS RED_COMMITS GREEN_DAYS YELLOW_DAYS RED_DAYS
readonly COLOR_RED COLOR_YELLOW COLOR_GREEN COLOR_NONE

BASE_BRANCH=""
MERGE_BASE=""
XTRACE=0
HAS_YELLOW=0
HAS_RED=0

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
  log "Usage: pre_pr_scope_check.sh [-h] [-x|-t] [base-branch]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  base-branch Branch to measure from (default: main, else master)\n'
  printf '\nThresholds come from SCOPE_GUARD_{GREEN,YELLOW,RED}_{LINES,FILES,COMMITS,DAYS}.\n'
  printf 'SCOPE_GUARD_OVERRIDE=1 turns a red verdict into exit 0.\n'
}

# A pre-push hook's first argument is a remote name, not a branch.
is_remote() {
  git remote 2>/dev/null | grep -qxF -- "${1}"
}

# Metrics are measured from the merge-base: commits that landed on the
# base after the fork are not this branch's work.
resolve_base() {
  _rb_candidates="${BASE_BRANCH:-main master}"
  for _rb_candidate in ${_rb_candidates}; do
    if MERGE_BASE=$(git merge-base "${_rb_candidate}" HEAD 2>/dev/null); then
      BASE_BRANCH="${_rb_candidate}"
      return 0
    fi
  done
  log 5 "pre_pr_scope_check: no merge-base with ${_rb_candidates}"
  exit 3
}

# Digits before a word in the `git diff --stat` summary line, else 0.
extract_stat_number() {
  printf '%s\n' "${1}" | grep -oE "[0-9]+ ${2}" | sed 's/ .*//' || printf '0\n'
}

get_lines_changed() {
  _lc_stats=$(git diff "${MERGE_BASE}" --stat 2>/dev/null | tail -1)
  case "${_lc_stats}" in
    "")
      printf '0\n'
      return 0
      ;;
  esac
  _lc_insertions=$(extract_stat_number "${_lc_stats}" "insertion")
  _lc_deletions=$(extract_stat_number "${_lc_stats}" "deletion")
  printf '%d\n' "$((_lc_insertions + _lc_deletions))"
}

get_new_files() {
  git diff "${MERGE_BASE}" --name-only --diff-filter=A 2>/dev/null | wc -l | tr -d ' '
}

get_commits() {
  git rev-list --count "${MERGE_BASE}..HEAD" 2>/dev/null || printf '0\n'
}

get_days_on_branch() {
  _db_base_date=$(git log -1 --format=%ct "${MERGE_BASE}" 2>/dev/null || date +%s)
  _db_now=$(date +%s)
  printf '%d\n' "$(((_db_now - _db_base_date) / 86400))"
}

# Zone for a value given its green, yellow and red thresholds. Above
# either the green or the yellow bound is yellow, so a yellow bound set
# below green moves the start of the yellow zone down.
get_zone() {
  if [ "${1}" -gt "${4}" ]; then
    printf 'red\n'
  elif [ "${1}" -gt "${3}" ] || [ "${1}" -gt "${2}" ]; then
    printf 'yellow\n'
  else
    printf 'green\n'
  fi
}

# Print one metric line in its zone color and record the worst zone.
# Arguments: label, value, green, yellow, red.
show_metric() {
  _sm_zone=$(get_zone "${2}" "${3}" "${4}" "${5}")
  case "${_sm_zone}" in
    green)
      log "$(printf '%-17s %b%5d%b (< %d)' "${1}" "${COLOR_GREEN}" "${2}" "${COLOR_NONE}" "${3}")"
      ;;
    yellow)
      log "$(printf '%-17s %b%5d%b (> %d, threshold: %d)' "${1}" "${COLOR_YELLOW}" "${2}" "${COLOR_NONE}" "${3}" "${5}")"
      HAS_YELLOW=1
      ;;
    red)
      log "$(printf '%-17s %b%5d%b (> %d RED ZONE)' "${1}" "${COLOR_RED}" "${2}" "${COLOR_NONE}" "${5}")"
      HAS_RED=1
      ;;
  esac
}

report_verdict() {
  case "${HAS_RED}${HAS_YELLOW}" in
    1*)
      log "$(printf '%bSCOPE GUARD: RED ZONE%b' "${COLOR_RED}" "${COLOR_NONE}")"
      log "Branch exceeds thresholds. Required before PR:"
      log "  1. Document why scope expanded"
      log "  2. Identify items to split to backlog"
      log "  3. Re-score Worthiness with current scope"
      log "  4. Get explicit approval to continue"
      log "To override: SCOPE_GUARD_OVERRIDE=1 ${0}"
      case "${SCOPE_GUARD_OVERRIDE:-0}" in
        1)
          log 3 "Override enabled. Proceeding with warning."
          exit 0
          ;;
      esac
      exit 1
      ;;
    01)
      log "$(printf '%bSCOPE GUARD: YELLOW ZONE%b' "${COLOR_YELLOW}" "${COLOR_NONE}")"
      log "Branch approaching thresholds. Before continuing:"
      log "  1. Does this still match the original scope?"
      log "  2. What is the current Worthiness Score?"
      log "  3. Can anything be split to backlog?"
      exit 0
      ;;
    *)
      log "$(printf '%bSCOPE GUARD: GREEN ZONE%b' "${COLOR_GREEN}" "${COLOR_NONE}")"
      log "All metrics within acceptable limits. Proceed with PR."
      exit 0
      ;;
  esac
}

main() {
  _main_first=1
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
      *)
        case "${_main_first}" in
          1)
            _main_first=0
            if ! is_remote "${1}"; then
              BASE_BRANCH="${1}"
            fi
            ;;
        esac
        ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  resolve_base
  log "scope-guard: Pre-PR Threshold Check"
  log "Base branch: ${BASE_BRANCH}"
  log "Metrics:"
  show_metric "Lines changed:" "$(get_lines_changed)" \
    "${GREEN_LINES}" "${YELLOW_LINES}" "${RED_LINES}"
  show_metric "New files:" "$(get_new_files)" \
    "${GREEN_FILES}" "${YELLOW_FILES}" "${RED_FILES}"
  show_metric "Commits:" "$(get_commits)" \
    "${GREEN_COMMITS}" "${YELLOW_COMMITS}" "${RED_COMMITS}"
  show_metric "Days on branch:" "$(get_days_on_branch)" \
    "${GREEN_DAYS}" "${YELLOW_DAYS}" "${RED_DAYS}"
  report_verdict
}

main "$@"
