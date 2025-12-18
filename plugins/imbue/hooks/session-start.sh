#!/usr/bin/env bash
# SessionStart hook for imbue plugin - scope-guard awareness
# Injects scope-guard methodology into Claude's session context

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
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

**Branch Thresholds**: 1000/1500/2000 lines | 15/25/30 commits | 3/7/7+ days"

# Escape outputs for JSON - uses jq when available, falls back to pure bash
escape_for_json() {
    local input="$1"
    # Prefer jq for robust JSON escaping (handles unicode, control chars)
    if command -v jq >/dev/null 2>&1; then
        printf '%s' "$input" | jq -Rs '.[:-1] // ""' | sed 's/^"//;s/"$//'
    else
        # Pure bash fallback
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
