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

### 1M Context Strategy

The 1M window (GA for Opus/Sonnet 4.6) does not replace
conservation -- it changes what conservation means.
A 1M window full of stale tool outputs performs worse
than 200K of structured, relevant state.

**Plan-Clear-Implement pattern** (recommended workflow):
1. Build the full plan (spec-kit, built-in planning, etc.)
2. `/clear` or `/compact` to start clean
3. Implement without compaction -- maintain full context
4. Iterate while still on topic with the same context
5. Repeat for the next plan

**Quota awareness**: Larger context = more input tokens
per turn = faster quota burn. Surgical reads protect
your budget even when the window allows more.

**Agentic isolation**: Parallel agents compound bloat.
Use git worktrees (`isolation: "worktree"`) to keep each
agent context lean and prevent cross-contamination.

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
- `normal` - Default, full conservation guidance

### Scope-Guard Principles (from imbue)

- **Worthiness**: `(BizValue + TimeCrit + RiskReduce) / (Complexity + TokenCost + ScopeDrift)` -- >2.0 implement, 1-2 discuss, <1 defer
- **Anti-overengineering**: Ask before proposing; no abstraction until 3rd use; defer nice-to-haves; stay within branch budget
- **Branch thresholds**: 1000/1500/2000 lines | 15/25/30 commits | 3/7/7+ days (green/yellow/red)
- **Proof-of-work**: Never claim "should work" -- run it, test it, cite evidence `[E1]`/`[E2]`
- **Iron Law**: No implementation without a failing test first
- **Rigorous reasoning**: No courtesy agreement; follow analysis checklists, not gut reactions
- Invoke `Skill(imbue:scope-guard)`, `Skill(imbue:proof-of-work)`, or `Skill(imbue:rigorous-reasoning)` for full methodology'

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
