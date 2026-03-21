#!/usr/bin/env bash
# Setup hook for conserve plugin - one-time initialization and maintenance
# Triggered via: claude --init, claude --init-only, or claude --maintenance
#
# This hook handles tasks that should NOT run on every session:
# - Dependency validation (jq)
# - Session state directory creation
# - Context baseline establishment
#
# Claude Code 2.1.10+ required for Setup hook support.

set -euo pipefail

# Read hook input to determine trigger type
HOOK_INPUT=""
TRIGGER_TYPE="init"
if read -t 0.1 -r HOOK_INPUT 2>/dev/null; then
    if command -v jq >/dev/null 2>&1; then
        TRIGGER_TYPE=$(echo "$HOOK_INPUT" | jq -r '.trigger // "init"' 2>/dev/null || echo "init")
    fi
fi

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Project directory from environment or current working directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Setup context message
setup_context=""

# =============================================================================
# INIT TASKS (--init, --init-only)
# =============================================================================
if [ "$TRIGGER_TYPE" = "init" ]; then
    setup_tasks=()

    # 1. Validate jq dependency (recommended for JSON processing)
    if ! command -v jq >/dev/null 2>&1; then
        setup_tasks+=("WARNING: jq not installed. Install with: brew install jq (macOS) or apt install jq (Linux). Some hooks will use fallback processing.")
    else
        setup_tasks+=("jq: OK (v$(jq --version 2>&1 | head -1 | sed 's/jq-//'))")
    fi

    # 2. Create session state directory if needed
    SESSION_STATE_DIR="${PROJECT_DIR}/.claude"
    if [ ! -d "$SESSION_STATE_DIR" ]; then
        mkdir -p "$SESSION_STATE_DIR"
        setup_tasks+=("Created session state directory: ${SESSION_STATE_DIR}")
    else
        setup_tasks+=("Session state directory: exists")
    fi

    # 3. Create session-state.md template if it doesn't exist
    SESSION_STATE_FILE="${CONSERVE_SESSION_STATE_PATH:-${SESSION_STATE_DIR}/session-state.md}"
    # Validate SESSION_STATE_FILE stays within allowed directories
    if [ -n "${CONSERVE_SESSION_STATE_PATH:-}" ]; then
        _resolved_state="$(readlink -f "$SESSION_STATE_FILE" 2>/dev/null || echo "$SESSION_STATE_FILE")"
        _home_prefix="$(readlink -f "$HOME" 2>/dev/null || echo "$HOME")"
        case "$_resolved_state" in
            "${_home_prefix}"*|"${PROJECT_DIR}"*) ;;
            *)
                echo "[conserve] WARNING: CONSERVE_SESSION_STATE_PATH escapes allowed dirs, using default" >&2
                SESSION_STATE_FILE="${SESSION_STATE_DIR}/session-state.md"
                ;;
        esac
    fi
    if [ ! -f "$SESSION_STATE_FILE" ]; then
        cat > "$SESSION_STATE_FILE" << 'TEMPLATE'
# Session State

## Metadata
- created: {{timestamp}}
- handoff_count: 0
- status: fresh

## Objective
<!-- Describe the current objective -->

## Progress Summary
<!-- Summarize completed work -->

## Context to Re-read
<!-- List critical files that should be re-read on continuation -->

## Immediate Next Step
<!-- What should happen next -->

## Success Criteria
- [ ] Criteria 1
- [ ] Criteria 2
TEMPLATE
        # Replace timestamp placeholder
        if sed -i.bak "s/{{timestamp}}/$(date -Iseconds)/" "$SESSION_STATE_FILE" 2>/dev/null; then
            rm -f "${SESSION_STATE_FILE}.bak" 2>/dev/null || true
        else
            sed -i '' "s/{{timestamp}}/$(date -Iseconds)/" "$SESSION_STATE_FILE" 2>/dev/null || true
        fi
        setup_tasks+=("Created session state template: ${SESSION_STATE_FILE}")
    fi

    # 4. Set environment variables via CLAUDE_ENV_FILE
    if [ -n "${CLAUDE_ENV_FILE:-}" ] && { [ -w "${CLAUDE_ENV_FILE}" ] || [ ! -e "${CLAUDE_ENV_FILE}" ]; }; then
        echo "export CONSERVE_SESSION_STATE_PATH=\"${SESSION_STATE_FILE}\"" >> "$CLAUDE_ENV_FILE"
        setup_tasks+=("Persisted CONSERVE_SESSION_STATE_PATH to environment")
    fi

    # Build context message
    setup_context="[conserve:setup] Initialization complete (trigger: ${TRIGGER_TYPE})
Tasks completed:
$(printf '  - %s\n' "${setup_tasks[@]}")"

fi

# =============================================================================
# MAINTENANCE TASKS (--maintenance)
# =============================================================================
if [ "$TRIGGER_TYPE" = "maintenance" ]; then
    maintenance_tasks=()

    # 1. Clean up old session state backups
    SESSION_STATE_DIR="${PROJECT_DIR}/.claude"
    if [ -d "$SESSION_STATE_DIR" ]; then
        backup_count=$(find "$SESSION_STATE_DIR" -name "session-state*.bak" -type f 2>/dev/null | wc -l | tr -d ' ')
        if [ "$backup_count" -gt 0 ]; then
            find "$SESSION_STATE_DIR" -name "session-state*.bak" -type f -mtime +7 -delete 2>/dev/null || true
            maintenance_tasks+=("Cleaned session state backups older than 7 days")
        fi
    fi

    # 2. Check for stale continuation audit logs
    AUDIT_LOG="${CLAUDE_CODE_TMPDIR:-/tmp}/continuation-audit.log"
    if [ -f "$AUDIT_LOG" ]; then
        line_count=$(wc -l < "$AUDIT_LOG" 2>/dev/null | tr -d ' ')
        if [ "$line_count" -gt 1000 ]; then
            # Rotate: keep last 500 lines
            tail -500 "$AUDIT_LOG" > "${AUDIT_LOG}.tmp" && mv "${AUDIT_LOG}.tmp" "$AUDIT_LOG"
            maintenance_tasks+=("Rotated continuation audit log (was ${line_count} lines, kept 500)")
        else
            maintenance_tasks+=("Continuation audit log: OK (${line_count} lines)")
        fi
    fi

    # 3. Validate hook dependencies
    deps_ok=true
    for dep in jq python3; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            maintenance_tasks+=("Missing optional dependency: $dep")
            deps_ok=false
        fi
    done
    if [ "$deps_ok" = true ]; then
        maintenance_tasks+=("All dependencies: OK")
    fi

    # Build context message
    setup_context="[conserve:maintenance] Maintenance complete (trigger: ${TRIGGER_TYPE})
Tasks completed:
$(printf '  - %s\n' "${maintenance_tasks[@]}")"

fi

# =============================================================================
# OUTPUT
# =============================================================================

# Escape for JSON
escape_for_json() {
    local input="$1"
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs 'rtrimstr("\n")' | sed 's/^"//;s/"$//'
    else
        # Pure bash fallback with complete JSON control character handling
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

context_escaped=$(escape_for_json "$setup_context")

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "Setup",
    "additionalContext": "${context_escaped}"
  }
}
EOF

exit 0
