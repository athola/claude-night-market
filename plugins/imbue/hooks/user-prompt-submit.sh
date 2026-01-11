#!/usr/bin/env bash
# UserPromptSubmit hook for imbue plugin - ongoing scope-guard monitoring
# Checks branch thresholds periodically and warns when approaching limits

set -euo pipefail

# Performance optimization: skip if disabled
if [ "${SCOPE_GUARD_DISABLE:-0}" = "1" ]; then
    echo '{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ""}}'
    exit 0
fi

# Portable number extraction (works without grep -P)
extract_stat_number() {
    local stats="$1"
    local pattern="$2"
    if echo "test" | grep -oP '\d+' >/dev/null 2>&1; then
        echo "$stats" | grep -oP "\d+(?= $pattern)" || echo "0"
    else
        echo "$stats" | grep -oE "[0-9]+ $pattern" | sed 's/ .*//' || echo "0"
    fi
}

# Only run in git repositories
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    # Not in a git repo, output empty JSON
    echo '{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ""}}'
    exit 0
fi

# Performance optimization: cache results for 60 seconds
CACHE_FILE="${TMPDIR:-/tmp}/scope-guard-cache-$(git rev-parse --show-toplevel | md5sum | cut -d' ' -f1).txt"
CACHE_TTL="${SCOPE_GUARD_CACHE_TTL:-60}"  # seconds

if [ -f "$CACHE_FILE" ]; then
    cache_age=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ "$cache_age" -lt "$CACHE_TTL" ]; then
        # Cache is fresh, use it
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# Get base branch (configurable via environment)
base_branch="${SCOPE_GUARD_BASE_BRANCH:-main}"

# Check if base branch exists, try alternatives
if ! git rev-parse --verify "$base_branch" > /dev/null 2>&1; then
    if git rev-parse --verify "master" > /dev/null 2>&1; then
        base_branch="master"
    else
        # No valid base branch, skip check
        echo '{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ""}}'
        exit 0
    fi
fi

# Get metrics (optimized for performance)
# Use --shortstat instead of --stat | tail (faster)
lines_changed=0
stat_line=$(git diff "$base_branch" --shortstat 2>/dev/null)
if [ -n "$stat_line" ]; then
    insertions=$(echo "$stat_line" | grep -oE "[0-9]+ insertion" | grep -oE "[0-9]+" || echo "0")
    deletions=$(echo "$stat_line" | grep -oE "[0-9]+ deletion" | grep -oE "[0-9]+" || echo "0")
    lines_changed=$((insertions + deletions))
fi

commits=$(git rev-list --count "$base_branch"..HEAD 2>/dev/null || echo "0")

# Optimize: combine merge-base and log into single operation
merge_base=$(git merge-base "$base_branch" HEAD 2>/dev/null)
if [ -n "$merge_base" ]; then
    merge_base_date=$(git log -1 --format=%ct "$merge_base" 2>/dev/null || echo "$(date +%s)")
else
    merge_base_date=$(date +%s)
fi
current_date=$(date +%s)
days_on_branch=$(( (current_date - merge_base_date) / 86400 ))

# Optimize: use wc -l directly without intermediate pipe
new_files=$(git diff "$base_branch" --name-only --diff-filter=A 2>/dev/null | wc -l)

# Thresholds (configurable via environment)
RED_LINES="${SCOPE_GUARD_RED_LINES:-2000}"
YELLOW_LINES="${SCOPE_GUARD_YELLOW_LINES:-1500}"
RED_COMMITS="${SCOPE_GUARD_RED_COMMITS:-30}"
YELLOW_COMMITS="${SCOPE_GUARD_YELLOW_COMMITS:-25}"
RED_DAYS="${SCOPE_GUARD_RED_DAYS:-7}"
YELLOW_DAYS="${SCOPE_GUARD_YELLOW_DAYS:-7}"
RED_FILES="${SCOPE_GUARD_RED_FILES:-15}"
YELLOW_FILES="${SCOPE_GUARD_YELLOW_FILES:-12}"

# Determine zone and build message
zone="green"
warnings=""

if [ "$lines_changed" -gt "$RED_LINES" ]; then
    zone="red"
    warnings="${warnings}Lines: ${lines_changed} (RED > ${RED_LINES}). "
elif [ "$lines_changed" -gt "$YELLOW_LINES" ]; then
    zone="yellow"
    warnings="${warnings}Lines: ${lines_changed} (YELLOW). "
fi

if [ "$commits" -gt "$RED_COMMITS" ]; then
    zone="red"
    warnings="${warnings}Commits: ${commits} (RED > ${RED_COMMITS}). "
elif [ "$commits" -gt "$YELLOW_COMMITS" ]; then
    [ "$zone" != "red" ] && zone="yellow"
    warnings="${warnings}Commits: ${commits} (YELLOW). "
fi

if [ "$days_on_branch" -gt "$RED_DAYS" ]; then
    zone="red"
    warnings="${warnings}Days: ${days_on_branch} (RED > ${RED_DAYS}). "
elif [ "$days_on_branch" -gt "$YELLOW_DAYS" ]; then
    [ "$zone" != "red" ] && zone="yellow"
    warnings="${warnings}Days: ${days_on_branch} (YELLOW). "
fi

if [ "$new_files" -gt "$RED_FILES" ]; then
    zone="red"
    warnings="${warnings}New files: ${new_files} (RED > ${RED_FILES}). "
elif [ "$new_files" -gt "$YELLOW_FILES" ]; then
    [ "$zone" != "red" ] && zone="yellow"
    warnings="${warnings}New files: ${new_files} (YELLOW). "
fi

# Build context message based on zone
context=""
if [ "$zone" = "red" ]; then
    context="scope-guard: RED ZONE - ${warnings}Before adding features, evaluate with Skill(imbue:scope-guard). Consider splitting branch or deferring work to backlog."
elif [ "$zone" = "yellow" ]; then
    context="scope-guard: YELLOW - ${warnings}Monitor scope carefully."
fi

# Escape for JSON - uses jq when available, falls back to pure bash
escape_for_json() {
    local input="$1"
    # Prefer jq for production-grade JSON escaping (handles unicode, control chars)
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs '.[:-1] // ""' | sed 's/^"//;s/"$//'
    else
        # Pure bash fallback with complete JSON control character handling
        # WARNING: jq is recommended for production use. Install with: apt-get install jq
        [ "${JSON_ESCAPE_WARN:-0}" = "0" ] && echo "[WARN] jq not found, using bash fallback for JSON escaping. Install jq for better performance." >&2 && export JSON_ESCAPE_WARN=1
        local output=""
        local i char
        for (( i=0; i<${#input}; i++ )); do
            char="${input:$i:1}"
            case "$char" in
                '\'$'\\') output+='\\\\' ;;
                '"') output+='\\"' ;;
                $'\n') output+='\\n' ;;
                $'\r') output+='\\r' ;;
                $'\t') output+='\\t' ;;
                $'\b') output+='\\b' ;;  # Backspace
                $'\f') output+='\\f' ;;  # Form feed
                # Handle other control characters (U+0000-U+001F)
                $'\x00') output+='\\u0000' ;;
                $'\x01') output+='\\u0001' ;;
                $'\x02') output+='\\u0002' ;;
                $'\x03') output+='\\u0003' ;;
                $'\x04') output+='\\u0004' ;;
                $'\x05') output+='\\u0005' ;;
                $'\x06') output+='\\u0006' ;;
                $'\x07') output+='\\u0007' ;;
                $'\x0e') output+='\\u000e' ;;
                $'\x0f') output+='\\u000f' ;;
                $'\x10') output+='\\u0010' ;;
                $'\x11') output+='\\u0011' ;;
                $'\x12') output+='\\u0012' ;;
                $'\x13') output+='\\u0013' ;;
                $'\x14') output+='\\u0014' ;;
                $'\x15') output+='\\u0015' ;;
                $'\x16') output+='\\u0016' ;;
                $'\x17') output+='\\u0017' ;;
                $'\x18') output+='\\u0018' ;;
                $'\x19') output+='\\u0019' ;;
                $'\x1a') output+='\\u001a' ;;
                $'\x1b') output+='\\u001b' ;;
                $'\x1c') output+='\\u001c' ;;
                $'\x1d') output+='\\u001d' ;;
                $'\x1e') output+='\\u001e' ;;
                $'\x1f') output+='\\u001f' ;;
                *) output+="$char" ;;
            esac
        done
        printf '%s' "$output"
    fi
}

context_escaped=$(escape_for_json "$context")

# Build JSON output
output=$(cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "${context_escaped}"
  }
}
EOF
)

# Cache the output for future invocations (reduces git overhead)
echo "$output" > "$CACHE_FILE" 2>/dev/null || true

# Output JSON
echo "$output"

exit 0
