#!/usr/bin/env bash
# SessionStart hook for conservation plugin - resource optimization awareness
# Injects context-optimization, token-conservation, and CPU/GPU performance guidance
# at session start for proactive resource management.
#
# Bypass modes:
#   CONSERVATION_MODE=quick   - Skip loading for fast processing tasks
#   CONSERVATION_MODE=deep    - Allow more resources for thorough analysis
#   CONSERVATION_MODE=normal  - Default, load all conservation guidance (default)

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check bypass mode from environment
CONSERVATION_MODE="${CONSERVATION_MODE:-normal}"

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
conservation_summary='## Conservation Skills - Session Optimization

**Active at session start to optimize performance, tokens, and context.**

### Quick Reference

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `context-optimization` | MECW principles, 50% context rule | Context > 30% utilization |
| `token-conservation` | Token usage strategies, quota tracking | Start of session, before heavy loads |
| `cpu-gpu-performance` | Resource monitoring, selective testing | Before builds/tests/training |

### Key Thresholds (Two-Tier MECW Alerts)

- **Context (40%)**: WARNING - Plan optimization soon, monitor growth rate
- **Context (50%)**: CRITICAL - Immediate optimization required, summarize/delegate
- **Context (< 40%)**: OK - Continue normally
- **Token Quota**: 5-hour rolling cap + weekly cap (check with `/status`)
- **CPU/GPU**: Establish baseline before heavy tasks

### Conservation Tactics

1. **Prefer targeted over broad**: `rg`/`sed -n` slices vs whole files
2. **Delegate compute**: Use external tooling for intensive tasks
3. **Compress context**: Summarize prior steps, remove redundant history
4. **Scope narrow**: Diff-based testing vs full suite

### Skill Invocation

- `Skill(conservation:context-optimization)` - MECW assessment and optimization
- `Skill(conservation:token-conservation)` - Token budget planning
- `Skill(conservation:cpu-gpu-performance)` - Resource monitoring discipline

### Bypass Modes

Set `CONSERVATION_MODE` environment variable:
- `quick` - Skip guidance for fast processing
- `deep` - Allow extended resources for thorough analysis
- `normal` - Default, full conservation guidance'

# Add deep mode notice if applicable
if [ -n "$deep_mode_msg" ]; then
    conservation_summary="$deep_mode_msg

$conservation_summary"
fi

# Escape outputs for JSON - uses jq when available, falls back to pure bash
escape_for_json() {
    local input="$1"
    # Prefer jq for robust JSON escaping (handles unicode, control chars)
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs '.[:-1] // ""' | sed 's/^"//;s/"$//'
    else
        # Pure bash fallback - less robust but functional
        echo "[conservation:session-start] Warning: jq not found, using bash fallback for JSON escaping" >&2
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
