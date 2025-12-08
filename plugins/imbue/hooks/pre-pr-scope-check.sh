#!/bin/bash
# pre-pr-scope-check.sh
# Checks branch metrics against scope-guard thresholds before PR creation
#
# Usage: ./pre-pr-scope-check.sh [base-branch]
# Default base branch: main
#
# Exit codes:
#   0 - Green zone, proceed
#   1 - Red zone, requires justification
#   2 - Yellow zone (warning only, still exits 0)

set -euo pipefail

BASE_BRANCH="${1:-main}"

# Thresholds (configurable via environment)
GREEN_LINES="${SCOPE_GUARD_GREEN_LINES:-1000}"
YELLOW_LINES="${SCOPE_GUARD_YELLOW_LINES:-1500}"
RED_LINES="${SCOPE_GUARD_RED_LINES:-2000}"

GREEN_FILES="${SCOPE_GUARD_GREEN_FILES:-8}"
YELLOW_FILES="${SCOPE_GUARD_YELLOW_FILES:-12}"
RED_FILES="${SCOPE_GUARD_RED_FILES:-15}"

GREEN_COMMITS="${SCOPE_GUARD_GREEN_COMMITS:-15}"
YELLOW_COMMITS="${SCOPE_GUARD_YELLOW_COMMITS:-25}"
RED_COMMITS="${SCOPE_GUARD_RED_COMMITS:-30}"

GREEN_DAYS="${SCOPE_GUARD_GREEN_DAYS:-3}"
YELLOW_DAYS="${SCOPE_GUARD_YELLOW_DAYS:-7}"
RED_DAYS="${SCOPE_GUARD_RED_DAYS:-7}"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Get metrics
get_lines_changed() {
    local stats
    stats=$(git diff "$BASE_BRANCH" --stat 2>/dev/null | tail -1)
    if [[ -z "$stats" ]]; then
        echo "0"
        return
    fi
    # Extract insertions and deletions
    local insertions deletions
    insertions=$(echo "$stats" | grep -oP '\d+(?= insertion)' || echo "0")
    deletions=$(echo "$stats" | grep -oP '\d+(?= deletion)' || echo "0")
    echo $((insertions + deletions))
}

get_new_files() {
    git diff "$BASE_BRANCH" --name-only --diff-filter=A 2>/dev/null | wc -l
}

get_commits() {
    git rev-list --count "$BASE_BRANCH"..HEAD 2>/dev/null || echo "0"
}

get_days_on_branch() {
    local merge_base_date current_date
    merge_base_date=$(git log -1 --format=%ct "$(git merge-base "$BASE_BRANCH" HEAD 2>/dev/null)" 2>/dev/null || echo "$(date +%s)")
    current_date=$(date +%s)
    echo $(( (current_date - merge_base_date) / 86400 ))
}

# Determine zone for a metric
get_zone() {
    local value=$1
    local green=$2
    local yellow=$3
    local red=$4

    if [[ $value -gt $red ]]; then
        echo "red"
    elif [[ $value -gt $yellow ]]; then
        echo "yellow"
    elif [[ $value -gt $green ]]; then
        echo "yellow"
    else
        echo "green"
    fi
}

# Main
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  scope-guard: Pre-PR Threshold Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Base branch: $BASE_BRANCH"
    echo ""

    # Collect metrics
    local lines files commits days
    lines=$(get_lines_changed)
    files=$(get_new_files)
    commits=$(get_commits)
    days=$(get_days_on_branch)

    # Determine zones
    local lines_zone files_zone commits_zone days_zone
    lines_zone=$(get_zone "$lines" "$GREEN_LINES" "$YELLOW_LINES" "$RED_LINES")
    files_zone=$(get_zone "$files" "$GREEN_FILES" "$YELLOW_FILES" "$RED_FILES")
    commits_zone=$(get_zone "$commits" "$GREEN_COMMITS" "$YELLOW_COMMITS" "$RED_COMMITS")
    days_zone=$(get_zone "$days" "$GREEN_DAYS" "$YELLOW_DAYS" "$RED_DAYS")

    # Track worst zone
    local has_yellow=false
    local has_red=false

    # Display results
    echo "Metrics:"
    echo "────────────────────────────────────────────────"

    # Lines
    case $lines_zone in
        green)  printf "  Lines changed:    ${GREEN}%5d${NC} (< %d)\n" "$lines" "$GREEN_LINES" ;;
        yellow) printf "  Lines changed:    ${YELLOW}%5d${NC} (> %d, threshold: %d)\n" "$lines" "$GREEN_LINES" "$RED_LINES"; has_yellow=true ;;
        red)    printf "  Lines changed:    ${RED}%5d${NC} (> %d RED ZONE)\n" "$lines" "$RED_LINES"; has_red=true ;;
    esac

    # Files
    case $files_zone in
        green)  printf "  New files:        ${GREEN}%5d${NC} (< %d)\n" "$files" "$GREEN_FILES" ;;
        yellow) printf "  New files:        ${YELLOW}%5d${NC} (> %d, threshold: %d)\n" "$files" "$GREEN_FILES" "$RED_FILES"; has_yellow=true ;;
        red)    printf "  New files:        ${RED}%5d${NC} (> %d RED ZONE)\n" "$files" "$RED_FILES"; has_red=true ;;
    esac

    # Commits
    case $commits_zone in
        green)  printf "  Commits:          ${GREEN}%5d${NC} (< %d)\n" "$commits" "$GREEN_COMMITS" ;;
        yellow) printf "  Commits:          ${YELLOW}%5d${NC} (> %d, threshold: %d)\n" "$commits" "$GREEN_COMMITS" "$RED_COMMITS"; has_yellow=true ;;
        red)    printf "  Commits:          ${RED}%5d${NC} (> %d RED ZONE)\n" "$commits" "$RED_COMMITS"; has_red=true ;;
    esac

    # Days
    case $days_zone in
        green)  printf "  Days on branch:   ${GREEN}%5d${NC} (< %d)\n" "$days" "$GREEN_DAYS" ;;
        yellow) printf "  Days on branch:   ${YELLOW}%5d${NC} (> %d, threshold: %d)\n" "$days" "$GREEN_DAYS" "$RED_DAYS"; has_yellow=true ;;
        red)    printf "  Days on branch:   ${RED}%5d${NC} (> %d RED ZONE)\n" "$days" "$RED_DAYS"; has_red=true ;;
    esac

    echo ""
    echo "────────────────────────────────────────────────"

    # Final verdict
    if [[ $has_red == true ]]; then
        echo ""
        printf "${RED}🛑 SCOPE GUARD: RED ZONE${NC}\n"
        echo ""
        echo "Branch exceeds thresholds. Required before PR:"
        echo "  1. Document why scope expanded"
        echo "  2. Identify items to split to backlog"
        echo "  3. Re-score Worthiness with current scope"
        echo "  4. Get explicit approval to continue"
        echo ""
        echo "To override: SCOPE_GUARD_OVERRIDE=1 $0"
        echo ""

        if [[ "${SCOPE_GUARD_OVERRIDE:-0}" == "1" ]]; then
            echo "Override enabled. Proceeding with warning."
            exit 0
        fi
        exit 1

    elif [[ $has_yellow == true ]]; then
        echo ""
        printf "${YELLOW}⚠️  SCOPE GUARD: YELLOW ZONE${NC}\n"
        echo ""
        echo "Branch approaching thresholds. Before continuing:"
        echo "  1. Does this still match the original scope?"
        echo "  2. What's the current Worthiness Score?"
        echo "  3. Can anything be split to backlog?"
        echo ""
        exit 0

    else
        echo ""
        printf "${GREEN}✓ SCOPE GUARD: GREEN ZONE${NC}\n"
        echo ""
        echo "All metrics within acceptable limits. Proceed with PR."
        echo ""
        exit 0
    fi
}

main "$@"
