#!/usr/bin/env bash
# UserPromptSubmit hook for imbue plugin - ongoing scope-guard monitoring
# Checks branch thresholds periodically and warns when approaching limits

set -euo pipefail

readonly EMPTY_OUTPUT='{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ""}}'

# Skip scope-guard for maintenance/admin commands that don't add code
# These commands manage infrastructure, not features
readonly MAINTENANCE_PATTERNS='reinstall-all-plugins|update-all-plugins|update-plugins|update-dependencies|update-version|create-tag|commit-msg|fix-workflow|fix-pr|close-issue|update-labels|verify-plugin|validate-plugin|plugin-review|bloat-scan|unbloat|ai-hygiene-audit|stewardship-health|skill-logs|status|list-skills|catchup|git-catchup|record-terminal|record-browser'

readonly CACHE_TTL="${SCOPE_GUARD_CACHE_TTL:-60}" # seconds

# Thresholds (configurable via environment)
readonly RED_LINES="${SCOPE_GUARD_RED_LINES:-2000}"
readonly YELLOW_LINES="${SCOPE_GUARD_YELLOW_LINES:-1500}"
readonly RED_COMMITS="${SCOPE_GUARD_RED_COMMITS:-30}"
readonly YELLOW_COMMITS="${SCOPE_GUARD_YELLOW_COMMITS:-25}"
readonly RED_DAYS="${SCOPE_GUARD_RED_DAYS:-7}"
readonly YELLOW_DAYS="${SCOPE_GUARD_YELLOW_DAYS:-7}"
readonly RED_FILES="${SCOPE_GUARD_RED_FILES:-15}"
readonly YELLOW_FILES="${SCOPE_GUARD_YELLOW_FILES:-12}"

# Absolute directory of this script. A bare filename (no slash)
# resolves against the working directory.
script_dir() {
  local src="${BASH_SOURCE[0]:-${0}}"
  case "${src}" in
    */*) src="${src%/*}" ;;
    *) src="." ;;
  esac
  (cd "${src:-/}" && pwd)
}

# Portable number extraction (works without grep -P)
extract_stat_number() {
  local stats="${1}"
  local pattern="${2}"
  if printf '%s\n' "test" | grep -oP '\d+' >/dev/null 2>&1; then
    printf '%s\n' "${stats}" | grep -oP "\d+(?= ${pattern})" || printf '%s\n' "0"
  else
    printf '%s\n' "${stats}" | grep -oE "[0-9]+ ${pattern}" | sed 's/ .*//' || printf '%s\n' "0"
  fi
}

# Portable hash: md5sum (Linux) or md5 (macOS)
_hash_str() {
  if command -v md5sum >/dev/null 2>&1; then
    printf '%s\n' "${1}" | md5sum | cut -d' ' -f1
  elif command -v md5 >/dev/null 2>&1; then
    printf '%s\n' "${1}" | md5 -q
  else
    # Fallback: use cksum
    printf '%s\n' "${1}" | cksum | cut -d' ' -f1
  fi
}

main() {
  case "${1:-}" in
    -x) set -x ;;
  esac

  # Performance optimization: skip if disabled
  case "${SCOPE_GUARD_DISABLE:-0}" in
    1)
      printf '%s\n' "${EMPTY_OUTPUT}"
      exit 0
      ;;
  esac

  # Read stdin (hook protocol sends JSON with prompt content)
  stdin_data=""
  if ! [ -t 0 ]; then
    stdin_data=$(cat 2>/dev/null || true)
  fi

  if printf '%s\n' "${stdin_data}" | grep -qiE "/(${MAINTENANCE_PATTERNS})" 2>/dev/null; then
    printf '%s\n' "${EMPTY_OUTPUT}"
    exit 0
  fi

  # Only run in git repositories. One rev-parse answers both "is this a
  # repo" and "where is its root": every git call costs 0.5-0.8s on a
  # machine whose git is the Xcode shim, and this hook runs on every
  # prompt against a 30s budget.
  if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    # Not in a git repo, output empty JSON
    printf '%s\n' "${EMPTY_OUTPUT}"
    exit 0
  fi

  # Performance optimization: cache results for 60 seconds
  # A cache in shared /tmp at a predictable name is readable and writable by
  # every user on the host, and its contents land in additionalContext. Keep
  # it under the caller's own cache directory and refuse a file we do not own.
  CACHE_DIR="${XDG_CACHE_HOME:-${HOME}/.cache}/imbue"
  mkdir -p "${CACHE_DIR}" 2>/dev/null || true
  CACHE_FILE="${CACHE_DIR}/scope-guard-cache-$(_hash_str "${repo_root}").txt"

  if [ -f "${CACHE_FILE}" ] && [ -O "${CACHE_FILE}" ]; then
    cache_age=$(($(date +%s) - $(stat -c %Y "${CACHE_FILE}" 2>/dev/null || stat -f %m "${CACHE_FILE}" 2>/dev/null || printf '%s\n' 0)))
    if [ "${cache_age}" -lt "${CACHE_TTL}" ]; then
      # Cache is fresh, use it
      cat "${CACHE_FILE}"
      exit 0
    fi
  fi

  # Get base branch (configurable via environment)
  base_branch="${SCOPE_GUARD_BASE_BRANCH:-main}"

  # Resolve the base branch with the merge-base call the metrics need
  # anyway; a ref that does not exist fails it, so no separate --verify
  # round trip is spent on the question.
  if ! merge_base=$(git merge-base "${base_branch}" HEAD 2>/dev/null); then
    if merge_base=$(git merge-base "master" HEAD 2>/dev/null); then
      base_branch="master"
    else
      # No valid base branch, skip check
      printf '%s\n' "${EMPTY_OUTPUT}"
      exit 0
    fi
  fi

  # Get metrics. One diff answers both questions: --numstat lines carry
  # added and deleted counts per file (a dash for binary files), and
  # --raw lines carry the status letter that says which files are new.
  # Two diffs cost two git start-ups, which is the whole budget here.
  lines_changed=0
  diff_out=$(git diff "${base_branch}" --raw --numstat 2>/dev/null) || diff_out=""
  if [ -n "${diff_out}" ]; then
    insertions=$(printf '%s\n' "${diff_out}" | awk -F'\t' '$0 !~ /^:/ && $1 ~ /^[0-9]+$/ { a += $1 } END { print a + 0 }')
    deletions=$(printf '%s\n' "${diff_out}" | awk -F'\t' '$0 !~ /^:/ && $2 ~ /^[0-9]+$/ { d += $2 } END { print d + 0 }')
    lines_changed=$((insertions + deletions))
  fi

  commits=$(git rev-list --count "${base_branch}"..HEAD 2>/dev/null || printf '%s\n' "0")

  # Optimize: combine merge-base and log into single operation
  if [ -n "${merge_base}" ]; then
    merge_base_date=$(git log -1 --format=%ct "${merge_base}" 2>/dev/null || date +%s)
  else
    merge_base_date=$(date +%s)
  fi
  current_date=$(date +%s)
  days_on_branch=$(((current_date - merge_base_date) / 86400))

  new_files=$(printf '%s\n' "${diff_out}" | grep -c '^:[0-7]* [0-7]* [0-9a-f]* [0-9a-f]* A') || new_files=0

  # Determine zone and build message
  zone="green"
  warnings=""

  if [ "${lines_changed}" -gt "${RED_LINES}" ]; then
    zone="red"
    warnings="${warnings}Lines: ${lines_changed} (RED > ${RED_LINES}). "
  elif [ "${lines_changed}" -gt "${YELLOW_LINES}" ]; then
    zone="yellow"
    warnings="${warnings}Lines: ${lines_changed} (YELLOW). "
  fi

  if [ "${commits}" -gt "${RED_COMMITS}" ]; then
    zone="red"
    warnings="${warnings}Commits: ${commits} (RED > ${RED_COMMITS}). "
  elif [ "${commits}" -gt "${YELLOW_COMMITS}" ]; then
    case "${zone}" in red) ;; *) zone="yellow" ;; esac
    warnings="${warnings}Commits: ${commits} (YELLOW). "
  fi

  if [ "${days_on_branch}" -gt "${RED_DAYS}" ]; then
    zone="red"
    warnings="${warnings}Days: ${days_on_branch} (RED > ${RED_DAYS}). "
  elif [ "${days_on_branch}" -gt "${YELLOW_DAYS}" ]; then
    case "${zone}" in red) ;; *) zone="yellow" ;; esac
    warnings="${warnings}Days: ${days_on_branch} (YELLOW). "
  fi

  if [ "${new_files}" -gt "${RED_FILES}" ]; then
    zone="red"
    warnings="${warnings}New files: ${new_files} (RED > ${RED_FILES}). "
  elif [ "${new_files}" -gt "${YELLOW_FILES}" ]; then
    case "${zone}" in red) ;; *) zone="yellow" ;; esac
    warnings="${warnings}New files: ${new_files} (YELLOW). "
  fi

  # Build context message based on zone
  context=""
  case "${zone}" in
    red)
      context="scope-guard: RED ZONE - ${warnings}Before adding features, evaluate with Skill(imbue:scope-guard). Consider splitting branch or deferring work to backlog."
      ;;
    yellow)
      context="scope-guard: YELLOW - ${warnings}Monitor scope carefully."
      ;;
  esac

  # Source vendored JSON utilities (D-01).
  SCRIPT_DIR="$(script_dir)"
  PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
  # shellcheck source=plugins/imbue/hooks/shared/json_utils.sh
  source "${PLUGIN_ROOT}/hooks/shared/json_utils.sh"

  context_escaped=$(escape_for_json "${context}")

  # Build JSON output
  output=$(
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "${context_escaped}"
  }
}
EOF
  )

  # Cache the output for future invocations (reduces git overhead).
  # The trap covers every path that does not reach the rename. This hook
  # runs on every prompt submission, so a stranded temp file per failure
  # accumulates at the rate the failure path is taken. `rm -f` on an empty
  # variable is a no-op, so the trap is safe before the assignment lands.
  cache_tmp=""
  trap 'rm -f "${cache_tmp}"' EXIT
  cache_tmp=$(mktemp "${CACHE_DIR}/scope-guard-cache.XXXXXX" 2>/dev/null) && {
    printf '%s\n' "${output}" >"${cache_tmp}" && mv -f "${cache_tmp}" "${CACHE_FILE}"
  } 2>/dev/null || true

  # Output JSON
  printf '%s\n' "${output}"

  exit 0
}

main "$@"
