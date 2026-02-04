#!/usr/bin/env bash
# SessionStart hook for conservation plugin - resource optimization awareness
# Injects context-optimization, token-conservation, and CPU/GPU performance guidance
# at session start for proactive resource management.
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

# Source shared JSON utilities (provides get_json_field, escape_for_json)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../../../scripts/shared/json_utils.sh
source "${SCRIPT_DIR}/../../../scripts/shared/json_utils.sh"

# Read hook input from stdin to get agent_type (Claude Code 2.1.2+)
HOOK_INPUT=""
AGENT_TYPE=""
if read -t 0.1 -r HOOK_INPUT 2>/dev/null; then
    AGENT_TYPE=$(get_json_field "$HOOK_INPUT" "agent_type")
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

# Determine plugin root directory (SCRIPT_DIR already set above for json_utils.sh)
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
| `clear-context` | **Auto-clear workflow** | Context > 80% OR long multi-step tasks |
| `token-conservation` | Token usage strategies, quota tracking | Start of session, before heavy loads |
| `cpu-gpu-performance` | Resource monitoring, selective testing | Before builds/tests/training |

### Key Thresholds (Three-Tier MECW Alerts)

| Level | Threshold | Action |
|-------|-----------|--------|
| OK | < 40% | Continue normally |
| WARNING | 40-50% | Plan optimization, monitor growth |
| CRITICAL | 50-80% | Immediate optimization, summarize/delegate |
| **EMERGENCY** | **80%+** | **Invoke `Skill(conserve:clear-context)` NOW** |

### Proactive Self-Monitoring (IMPORTANT)

During **long-running or multi-step tasks** (brainstorms, execute-plan, large refactors):

1. **Check context periodically**: Run `/context` at natural breakpoints
2. **At 80%+ usage**: Immediately invoke `Skill(conserve:clear-context)`
3. **The skill will**: Save session state, spawn continuation agent, resume seamlessly

**Why self-monitor?** The `CLAUDE_CONTEXT_USAGE` env var may not be set.
Proactive checking prevents auto-compact penalties.

### Conservation Tactics

1. **Prefer targeted over broad**: `rg`/`sed -n` slices vs whole files
2. **Delegate compute**: Use external tooling for intensive tasks
3. **Compress context**: Summarize prior steps, remove redundant history
4. **Scope narrow**: Diff-based testing vs full suite
5. **Checkpoint long tasks**: Save state at natural breakpoints

### Skill Invocation

- `Skill(conserve:clear-context)` - **Auto-clear with continuation agent**
- `Skill(conserve:context-optimization)` - MECW assessment and optimization
- `Skill(conserve:token-conservation)` - Token budget planning
- `Skill(conserve:cpu-gpu-performance)` - Resource monitoring discipline

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

# escape_for_json is now provided by shared/json_utils.sh

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
