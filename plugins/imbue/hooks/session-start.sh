#!/usr/bin/env bash
# SessionStart hook for imbue plugin - scope-guard awareness
# Injects scope-guard methodology into Claude's session context
#
# Updated for Claude Code 2.1.2: Reads agent_type from hook input via stdin
# to customize scope-guard injection based on the invoking agent.
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
# Agent-aware behavior:
#   Review/optimization agents get abbreviated scope-guard reminders
#   Implementation agents get full scope-guard methodology

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# Source vendored JSON utilities (canonical: scripts/shared/json_utils.sh).
# Vendored under hooks/shared/ so the hook works from the Claude Code
# plugin cache. CLAUDE_PLUGIN_ROOT is set by Claude Code; SCRIPT_DIR
# fallback supports direct invocation in tests/CI.
# F5: use a dedicated variable so the later PLUGIN_ROOT assignment
# (line ~58) does not silently clobber it. Mirrors conserve's pattern.
PLUGIN_ROOT_FOR_UTILS="${CLAUDE_PLUGIN_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
# shellcheck source=plugins/imbue/hooks/shared/json_utils.sh
source "${PLUGIN_ROOT_FOR_UTILS}/hooks/shared/json_utils.sh"

# Read hook input from stdin to get agent_type (Claude Code 2.1.2+)
HOOK_INPUT=""
AGENT_TYPE=""
if read -t 1 -r HOOK_INPUT 2>/dev/null; then
    AGENT_TYPE=$(get_json_field "$HOOK_INPUT" "agent_type")
fi

# Lightweight agents that skip full scope-guard methodology
case "$AGENT_TYPE" in
    code-reviewer|architecture-reviewer|rust-auditor|bloat-auditor|context-optimizer)
        # Review/optimization agents: minimal scope-guard context
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "[imbue] Agent '${AGENT_TYPE}' - scope-guard abbreviated: Focus on review quality, not implementation scope."
  }
}
EOF
        exit 0
        ;;
esac

# Determine plugin root directory
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Portable number extraction (works without grep -P)
# Usage: extract_number "string" "pattern_word" -> outputs the number before pattern_word
extract_stat_number() {
    local stats="$1"
    local pattern="$2"
    # Try grep -oP first (GNU grep with PCRE), fall back to grep -oE + sed
    if echo "test" | grep -oP '\d+' >/dev/null 2>&1; then
        echo "$stats" | grep -oP "\d+(?= $pattern)" || echo "0"
    else
        # Portable fallback: use grep -oE and sed
        echo "$stats" | grep -oE "[0-9]+ $pattern" | sed 's/ .*//' || echo "0"
    fi
}

# Check if we're in a git repository
in_git_repo=false
if git rev-parse --git-dir > /dev/null 2>&1; then
    in_git_repo=true
fi

# Build scope-guard reminder based on context
scope_guard_reminder=""

if [ "$in_git_repo" = true ]; then
    # Get branch metrics for context
    base_branch="${SCOPE_GUARD_BASE_BRANCH:-main}"

    # Try to get metrics, fall back gracefully
    lines_changed=0
    commits=0
    days_on_branch=0

    if git rev-parse --verify "$base_branch" > /dev/null 2>&1; then
        stat_line=$(git diff "$base_branch" --stat 2>/dev/null | tail -1)
        insertions=$(extract_stat_number "$stat_line" "insertion")
        deletions=$(extract_stat_number "$stat_line" "deletion")
        lines_changed=$((insertions + deletions))
        commits=$(git rev-list --count "$base_branch"..HEAD 2>/dev/null || echo "0")

        merge_base_date=$(git log -1 --format=%ct "$(git merge-base "$base_branch" HEAD 2>/dev/null)" 2>/dev/null || echo "$(date +%s)")
        current_date=$(date +%s)
        days_on_branch=$(( (current_date - merge_base_date) / 86400 ))
    fi

    # Determine zone
    zone="green"
    if [ "$lines_changed" -gt 2000 ] || [ "$commits" -gt 30 ] || [ "$days_on_branch" -gt 7 ]; then
        zone="red"
    elif [ "$lines_changed" -gt 1000 ] || [ "$commits" -gt 15 ] || [ "$days_on_branch" -gt 3 ]; then
        zone="yellow"
    fi

    # Build zone-specific message
    if [ "$zone" = "red" ]; then
        scope_guard_reminder="\\n\\n**SCOPE-GUARD RED ZONE**: Branch has ${lines_changed} lines, ${commits} commits, ${days_on_branch} days. Before adding features, run \`Skill(imbue:scope-guard)\` to evaluate scope."
    elif [ "$zone" = "yellow" ]; then
        scope_guard_reminder="\\n\\n**SCOPE-GUARD YELLOW ZONE**: Branch approaching thresholds (${lines_changed} lines, ${commits} commits, ${days_on_branch} days). Consider scope when adding features."
    fi
fi

# Read scope-guard skill summary (lightweight version for session context)
scope_guard_summary="## imbue quick reference

Routing only. Each skill body carries its own checklists and thresholds.

\`Skill(imbue:scope-guard)\` -- after brainstorming, before finalizing a
plan, when proposing a feature or an abstraction, or when branch metrics
approach the limits. Worthiness is
\`(BizValue + TimeCrit + RiskReduce) / (Complexity + TokenCost + ScopeDrift)\`:
above 2.0 implement, 1.0 to 2.0 discuss first, below 1.0 defer. Branch
thresholds are 1000/1500/2000 lines, 15/25/30 commits, 3/7/7+ days.

\`Skill(imbue:proof-of-work)\` -- before claiming an implementation is
complete, or recommending a solution you have not run. Evidence is command
output cited as \`[E1]\`, from a functional test rather than a syntax check,
reported PASS / FAIL / BLOCKED. The Iron Law it enforces: no implementation
without a failing test first.

\`Skill(imbue:rigorous-reasoning)\` -- when analyzing a conflict, a contested
claim, or competing positions, where the comfortable answer and the correct
one may differ."

summary_escaped=$(escape_for_json "$scope_guard_summary")
reminder_escaped=$(escape_for_json "$scope_guard_reminder")

# Output context injection as JSON
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${summary_escaped}${reminder_escaped}"
  }
}
EOF

exit 0
