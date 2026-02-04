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

# Determine plugin root directory (SCRIPT_DIR already set above for json_utils.sh)
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
scope_guard_summary="## scope-guard Quick Reference

**When to invoke** \`Skill(imbue:scope-guard)\`:
- After brainstorming sessions (before documenting designs)
- Before finalizing implementation plans
- When proposing new features or abstractions
- When branch metrics approach thresholds

**Worthiness Formula**: \`(BizValue + TimeCrit + RiskReduce) / (Complexity + TokenCost + ScopeDrift)\`
- Score > 2.0: Implement now
- Score 1.0-2.0: Discuss first
- Score < 1.0: Defer to backlog

**Anti-Overengineering Rules**:
- Ask clarifying questions BEFORE proposing solutions
- No abstraction until 3rd use case
- Defer 'nice to have' features to backlog
- Stay within branch budget (default: 3 major features)

**Branch Thresholds**: 1000/1500/2000 lines | 15/25/30 commits | 3/7/7+ days

## proof-of-work Quick Reference

**When to invoke** \`Skill(imbue:proof-of-work)\`:
- Before claiming ANY implementation is complete
- Before saying 'should work' or 'will work'
- Before recommending untested solutions
- After making code changes that need verification

**Required Evidence**:
- \`[E1]\`, \`[E2]\` references with command outputs
- Functional tests (not just syntax checks)
- Status: PASS / FAIL / BLOCKED

**Red Flags (STOP immediately)**:
| Thought | Action |
|---------|--------|
| 'This looks correct' | RUN IT |
| 'Should work' | TEST IT |
| 'Syntax valid' | FUNCTIONAL TEST |

## The Iron Law (TDD Compliance)

\`\`\`
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
\`\`\`

**Self-Check Before Writing Code**:
| Question | Wrong Answer | Action |
|----------|--------------|--------|
| Evidence of failure/need? | No | STOP - document failure first |
| Testing pre-conceived impl? | Yes | STOP - let test DRIVE design |
| Feeling design uncertainty? | No | STOP - uncertainty is GOOD |
| Did test drive impl? | No | STOP - doing it backwards |

**TDD TodoWrite Items**:
- \`proof:iron-law-red\` - Failing test written FIRST
- \`proof:iron-law-green\` - Minimal implementation passes
- \`proof:iron-law-refactor\` - Improved without behavior change

## rigorous-reasoning Quick Reference

**When to invoke** \`Skill(imbue:rigorous-reasoning)\`:
- Analyzing conflicts, disagreements, or ethical questions
- Evaluating contested claims or competing positions
- When self-monitoring detects sycophantic patterns

**Priority Signals (override defaults)**:
- No courtesy agreement: Agreement requires validity, not politeness
- Checklist over intuition: Follow analysis, not initial reactions
- Uncomfortable conclusions stay uncomfortable: Don't sand down edges

**Red Flags (STOP - you're being sycophantic)**:
| Thought | Action |
|---------|--------|
| 'I agree that...' | VALIDATE first |
| 'You're right...' | CHECK for evidence |
| 'Great point!' | Does this ADD value? |
| 'To be fair...' | Are you HEDGING without evidence? |

**Conflict Analysis Checklist**:
1. Set aside initial reactions (name the bias)
2. Complete harm/rights checklist (concrete harm? which right?)
3. Assess proportionality (was response proportionate?)
4. Commit to conclusion (follow checklist, not gut)
5. Guard against retraction (only update for substantive reasons)"

# escape_for_json is now provided by shared/json_utils.sh

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
