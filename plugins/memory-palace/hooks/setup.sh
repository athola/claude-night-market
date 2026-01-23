#!/usr/bin/env bash
# Setup hook for memory-palace plugin - initialization and maintenance
# Triggered via: claude --init, claude --init-only, or claude --maintenance
#
# This hook handles tasks that should NOT run on every session:
# - Knowledge garden directory creation
# - Index rebuilding
# - Stale entry cleanup (maintenance)
# - Web capture cleanup (maintenance)
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

# Knowledge garden paths
GARDEN_ROOT="${HOME}/.claude/knowledge-garden"
SKILL_LOGS_ROOT="${HOME}/.claude/skills/logs"
WEB_CAPTURES_DIR="${HOME}/.claude/web-captures"

# Setup context message
setup_context=""

# =============================================================================
# INIT TASKS (--init, --init-only)
# =============================================================================
if [ "$TRIGGER_TYPE" = "init" ]; then
    init_tasks=()

    # 1. Create knowledge garden structure
    if [ ! -d "$GARDEN_ROOT" ]; then
        mkdir -p "${GARDEN_ROOT}"/{seeds,seedlings,evergreen,compost,meta}
        init_tasks+=("Created knowledge garden: ${GARDEN_ROOT}")
    else
        init_tasks+=("Knowledge garden: exists")
    fi

    # 2. Create project palace structure if in a git repo
    if [ -d "${PROJECT_DIR}/.git" ]; then
        PALACE_DIR="${PROJECT_DIR}/.claude/palace"
        if [ ! -d "$PALACE_DIR" ]; then
            mkdir -p "${PALACE_DIR}"/{entrance,library,workshop,review-chamber/{decisions,patterns,standards,lessons},garden}
            init_tasks+=("Created project palace: ${PALACE_DIR}")
        else
            init_tasks+=("Project palace: exists")
        fi
    fi

    # 3. Create skill logs directory
    if [ ! -d "$SKILL_LOGS_ROOT" ]; then
        mkdir -p "$SKILL_LOGS_ROOT"
        init_tasks+=("Created skill logs directory: ${SKILL_LOGS_ROOT}")
    else
        init_tasks+=("Skill logs directory: exists")
    fi

    # 4. Create web captures directory
    if [ ! -d "$WEB_CAPTURES_DIR" ]; then
        mkdir -p "$WEB_CAPTURES_DIR"
        init_tasks+=("Created web captures directory: ${WEB_CAPTURES_DIR}")
    else
        init_tasks+=("Web captures directory: exists")
    fi

    # 5. Initialize index file if missing
    INDEX_FILE="${GARDEN_ROOT}/meta/index.json"
    if [ ! -f "$INDEX_FILE" ]; then
        cat > "$INDEX_FILE" << 'INDEX'
{
  "version": "1.0.0",
  "created": "{{timestamp}}",
  "last_maintenance": null,
  "entry_count": 0,
  "categories": {
    "seeds": 0,
    "seedlings": 0,
    "evergreen": 0,
    "compost": 0
  }
}
INDEX
        # Replace timestamp
        sed -i.bak "s/{{timestamp}}/$(date -Iseconds)/" "$INDEX_FILE" 2>/dev/null || \
            sed -i '' "s/{{timestamp}}/$(date -Iseconds)/" "$INDEX_FILE" 2>/dev/null || true
        rm -f "${INDEX_FILE}.bak" 2>/dev/null || true
        init_tasks+=("Created garden index: ${INDEX_FILE}")
    fi

    # 6. Set environment variables via CLAUDE_ENV_FILE
    if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
        echo "export MEMORY_PALACE_GARDEN_ROOT=\"${GARDEN_ROOT}\"" >> "$CLAUDE_ENV_FILE"
        echo "export MEMORY_PALACE_SKILL_LOGS=\"${SKILL_LOGS_ROOT}\"" >> "$CLAUDE_ENV_FILE"
        init_tasks+=("Persisted environment variables")
    fi

    # Build context message
    setup_context="[memory-palace:init] Initialization complete
Tasks:
$(printf '  - %s\n' "${init_tasks[@]}")"

fi

# =============================================================================
# MAINTENANCE TASKS (--maintenance)
# =============================================================================
if [ "$TRIGGER_TYPE" = "maintenance" ]; then
    maint_tasks=()

    # 1. Clean stale web captures (older than 30 days, pending_review status)
    if [ -d "$WEB_CAPTURES_DIR" ]; then
        stale_count=$(find "$WEB_CAPTURES_DIR" -name "*.md" -type f -mtime +30 2>/dev/null | wc -l | tr -d ' ')
        if [ "$stale_count" -gt 0 ]; then
            # Move to compost, don't delete
            COMPOST_DIR="${GARDEN_ROOT}/compost/web-captures-$(date +%Y%m%d)"
            mkdir -p "$COMPOST_DIR"
            find "$WEB_CAPTURES_DIR" -name "*.md" -type f -mtime +30 -exec mv {} "$COMPOST_DIR/" \; 2>/dev/null || true
            maint_tasks+=("Composted ${stale_count} stale web captures (>30 days)")
        else
            maint_tasks+=("Web captures: no stale entries")
        fi
    fi

    # 2. Rotate skill logs (keep last 90 days)
    if [ -d "$SKILL_LOGS_ROOT" ]; then
        old_logs=$(find "$SKILL_LOGS_ROOT" -name "*.jsonl" -type f -mtime +90 2>/dev/null | wc -l | tr -d ' ')
        if [ "$old_logs" -gt 0 ]; then
            find "$SKILL_LOGS_ROOT" -name "*.jsonl" -type f -mtime +90 -delete 2>/dev/null || true
            maint_tasks+=("Deleted ${old_logs} skill log files (>90 days)")
        else
            maint_tasks+=("Skill logs: no old entries to clean")
        fi
    fi

    # 3. Rebuild index counts
    if [ -d "$GARDEN_ROOT" ]; then
        seeds_count=$(find "${GARDEN_ROOT}/seeds" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        seedlings_count=$(find "${GARDEN_ROOT}/seedlings" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        evergreen_count=$(find "${GARDEN_ROOT}/evergreen" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        compost_count=$(find "${GARDEN_ROOT}/compost" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        total=$((seeds_count + seedlings_count + evergreen_count))

        INDEX_FILE="${GARDEN_ROOT}/meta/index.json"
        if [ -f "$INDEX_FILE" ] && command -v jq >/dev/null 2>&1; then
            jq --arg ts "$(date -Iseconds)" \
               --argjson seeds "$seeds_count" \
               --argjson seedlings "$seedlings_count" \
               --argjson evergreen "$evergreen_count" \
               --argjson compost "$compost_count" \
               --argjson total "$total" \
               '.last_maintenance = $ts | .entry_count = $total | .categories = {seeds: $seeds, seedlings: $seedlings, evergreen: $evergreen, compost: $compost}' \
               "$INDEX_FILE" > "${INDEX_FILE}.tmp" && mv "${INDEX_FILE}.tmp" "$INDEX_FILE"
            maint_tasks+=("Rebuilt index: ${total} active entries (${compost_count} composted)")
        else
            maint_tasks+=("Garden stats: ${total} active entries (${compost_count} composted)")
        fi
    fi

    # 4. Check for duplicate web captures
    if [ -d "$WEB_CAPTURES_DIR" ] && command -v md5sum >/dev/null 2>&1; then
        dupes=$(find "$WEB_CAPTURES_DIR" -name "*.md" -type f -exec md5sum {} \; 2>/dev/null | \
                sort | uniq -d -w32 | wc -l | tr -d ' ')
        if [ "$dupes" -gt 0 ]; then
            maint_tasks+=("Found ${dupes} potential duplicate captures (manual review recommended)")
        else
            maint_tasks+=("No duplicate captures detected")
        fi
    fi

    # Build context message
    setup_context="[memory-palace:maintenance] Maintenance complete
Tasks:
$(printf '  - %s\n' "${maint_tasks[@]}")"

fi

# =============================================================================
# OUTPUT
# =============================================================================

escape_for_json() {
    local input="$1"
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs '.[:-1] // ""' | sed 's/^"//;s/"$//'
    else
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
