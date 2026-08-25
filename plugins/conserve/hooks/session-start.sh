#!/usr/bin/env bash
# SessionStart hook for conservation plugin - resource optimization + scope-guard awareness
# Injects context-optimization, token-conservation, CPU/GPU performance guidance,
# and scope-guard principles (consolidated from imbue) at session start.
#
# Updated for Claude Code 2.1.2: Reads agent_type from hook input via stdin
# to customize context injection based on the invoking agent.
#
# Hook Input Schema (Claude Code 2.1.2+):
# {
#   "agent_type": "string",      // e.g., "code-reviewer", "implementation-agent"
#   "source": "string",          // e.g., "cli", "editor"
#   "session_id": "string"       // Unique session identifier
# }
#
# Backward Compatibility: Gracefully handles missing stdin (older versions)
# Performance: <50ms typical, <200ms worst-case
#
# Bypass modes:
#   CONSERVATION_MODE=quick   - Skip loading for fast processing tasks
#   CONSERVATION_MODE=deep    - Allow more resources for thorough analysis
#   CONSERVATION_MODE=normal  - Default, load all conservation guidance (default)
#
# Agent-aware modes (via --agent flag in Claude Code 2.1.2+):
#   Lightweight agents (code-reviewer, etc.) get abbreviated guidance

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# Source vendored JSON utilities (D-01).
PLUGIN_ROOT_FOR_UTILS="${CLAUDE_PLUGIN_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
# shellcheck source=plugins/conserve/hooks/shared/json_utils.sh
source "${PLUGIN_ROOT_FOR_UTILS}/hooks/shared/json_utils.sh"

# Read hook input from stdin to get agent_type (Claude Code 2.1.2+)
HOOK_INPUT=""
AGENT_TYPE=""
if read -t 1 -r HOOK_INPUT 2>/dev/null; then
    AGENT_TYPE=$(get_json_field "$HOOK_INPUT" "agent_type")
    # Validate: only allow alphanumeric, hyphens, and underscores
    if [[ -n "$AGENT_TYPE" && ! "$AGENT_TYPE" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "[conserve] WARNING: Invalid agent_type value, ignoring" >&2
        AGENT_TYPE=""
    fi
fi

# Lightweight agents that get abbreviated guidance
case "$AGENT_TYPE" in
    code-reviewer|architecture-reviewer|rust-auditor|bloat-auditor)
        # Review agents: minimal conservation context
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "[conserve] Agent '${AGENT_TYPE}' - abbreviated guidance: Monitor context, use targeted reads."
  }
}
EOF
        exit 0
        ;;
esac

# Determine plugin root directory
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check bypass mode from environment
CONSERVATION_MODE="${CONSERVATION_MODE:-normal}"

# Validate CONSERVATION_MODE to prevent injection of unexpected values
case "$CONSERVATION_MODE" in
    normal|quick|deep|standard|aggressive|minimal|off) ;;
    *)
        echo "[conserve] WARNING: Unknown CONSERVATION_MODE='${CONSERVATION_MODE}', defaulting to 'normal'" >&2
        CONSERVATION_MODE="normal"
        ;;
esac

# Handle bypass modes
case "$CONSERVATION_MODE" in
    quick)
        # Quick mode: minimal overhead, skip conservation guidance
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Conservation mode: QUICK - Resource optimization guidance skipped for fast processing."
  }
}
EOF
        exit 0
        ;;
    deep)
        # Deep mode: allow more resources, provide abbreviated guidance
        deep_mode_msg="Conservation mode: DEEP ANALYSIS - Extended resource usage permitted for thorough analysis. Monitor context usage but prioritize completeness over conservation."
        ;;
    *)
        # Normal mode: full conservation guidance
        deep_mode_msg=""
        ;;
esac

# Build conservation skills summary for session context injection
conservation_summary='## conserve: session optimization

Context bands, and what each asks for: under 40% carry on; 40-50% plan the
optimization; 50-80% act on it, summarizing or delegating; at 80% invoke
`Skill(conserve:clear-context)`, which checkpoints state and hands off to a
continuation agent. `CLAUDE_CONTEXT_USAGE` is often unset, so run `/context`
at natural breakpoints rather than waiting to be told a number.

Skills: `Skill(conserve:context-optimization)` for MECW assessment,
`Skill(conserve:token-conservation)` for quota planning,
`Skill(conserve:cpu-gpu-performance)` before builds, tests and training runs.

A 1M window retires none of this, it changes the arithmetic. 1M of stale
tool output reasons worse than 200K of relevant state, and every turn pays
for the whole window against quota. Plan, `/clear`, then implement.

`CONSERVATION_MODE` selects the register: `quick` skips this guidance,
`deep` allows extended resources, `normal` is the default.'

# Add deep mode notice if applicable
if [ -n "$deep_mode_msg" ]; then
    conservation_summary="$deep_mode_msg

$conservation_summary"
fi

summary_escaped=$(escape_for_json "$conservation_summary")

# Output context injection as JSON
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${summary_escaped}"
  }
}
EOF

exit 0
