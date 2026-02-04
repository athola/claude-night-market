#!/usr/bin/env bash
# Shared JSON utilities for Claude Code hooks
# Provides portable JSON handling across BSD/macOS/Linux with jq/grep/sed fallbacks
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/../../scripts/shared/json_utils.sh"
#   # or with absolute path:
#   source "/path/to/scripts/shared/json_utils.sh"
#
# Functions:
#   get_json_field <json_string> <field_name>  - Extract field value from JSON
#   escape_for_json <string>                    - Escape string for JSON embedding
#
# Examples:
#   AGENT_TYPE=$(get_json_field "$HOOK_INPUT" "agent_type")
#   ESCAPED=$(escape_for_json "$MULTILINE_TEXT")

# Prevent double-sourcing
[[ -n "${_JSON_UTILS_LOADED:-}" ]] && return 0
_JSON_UTILS_LOADED=1

# Extract a field value from a JSON string
# Uses three-tier fallback: jq → GNU grep → POSIX sed
#
# Arguments:
#   $1 - JSON string to parse
#   $2 - Field name to extract
#
# Returns:
#   Field value on stdout, empty string if not found
#
# Example:
#   AGENT_TYPE=$(get_json_field '{"agent_type":"code-reviewer"}' "agent_type")
#   # Returns: code-reviewer
get_json_field() {
    local json="$1"
    local field="$2"
    local value=""

    if command -v jq >/dev/null 2>&1; then
        # Tier 1: jq (most reliable)
        value=$(echo "$json" | jq -r ".${field} // empty" 2>/dev/null || echo "")
    elif echo "test" | grep -oP '\d+' >/dev/null 2>&1; then
        # Tier 2: GNU grep with Perl regex
        value=$(echo "$json" | grep -oP "\"${field}\"\\s*:\\s*\"\\K[^\"]+" 2>/dev/null || echo "")
    else
        # Tier 3: POSIX-compliant sed (universal fallback)
        value=$(echo "$json" | sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" 2>/dev/null || echo "")
    fi

    printf '%s' "$value"
}

# Escape a string for safe embedding in JSON
# Uses jq when available, falls back to pure bash for portability
#
# Arguments:
#   $1 - String to escape
#
# Returns:
#   JSON-escaped string on stdout (without surrounding quotes)
#
# Example:
#   ESCAPED=$(escape_for_json "Hello\nWorld")
#   # Returns: Hello\nWorld (with literal backslash-n)
escape_for_json() {
    local input="$1"

    # Prefer jq for production-grade JSON escaping (handles unicode, control chars)
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs '.[:-1] // ""' | sed 's/^"//;s/"$//'
    else
        # Pure bash fallback with complete JSON control character handling
        # WARNING: jq is recommended for production use. Install with: apt-get install jq
        [ "${_JSON_ESCAPE_WARN:-0}" = "0" ] && echo "[WARN] jq not found, using bash fallback for JSON escaping. Install jq for better performance." >&2 && export _JSON_ESCAPE_WARN=1

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
