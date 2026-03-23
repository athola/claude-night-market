#!/usr/bin/env bash
# stargazer-overlap.sh - Analyze stargazer overlap for community targeting
#
# Fetches stargazers of athola/claude-night-market, then for each
# stargazer fetches their starred repos to build a frequency map of
# co-starred repositories. Outputs a markdown table of the top results.
#
# Usage:
#   bash scripts/stargazer-overlap.sh
#   bash scripts/stargazer-overlap.sh --limit 50
#   bash scripts/stargazer-overlap.sh --limit 100 --top 30
#
# Requires: gh (authenticated), jq, bash 4+

set -euo pipefail

REPO="athola/claude-night-market"
LIMIT=50
TOP=20
DELAY=0.5

# ---------- argument parsing ----------

usage() {
  cat <<'USAGE'
Usage: stargazer-overlap.sh [OPTIONS]

Analyze stargazer overlap for community targeting.

Options:
  --limit N   Max stargazers to analyze (default: 50, 0 = all)
  --top N     Number of top repos to display (default: 20)
  --delay N   Seconds between per-user API calls (default: 0.5)
  --help      Show this help message
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --top)
      TOP="$2"
      shift 2
      ;;
    --delay)
      DELAY="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

# ---------- preflight checks ----------

if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI is required but not installed" >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "ERROR: gh is not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

# ---------- rate limit helpers ----------

get_rate_remaining() {
  # Returns remaining core API calls, or -1 on error
  local remaining
  remaining=$(gh api rate_limit --jq '.resources.core.remaining' 2>/dev/null) || true
  if [[ -z "$remaining" || ! "$remaining" =~ ^[0-9]+$ ]]; then
    echo "-1"
  else
    echo "$remaining"
  fi
}

check_rate_limit() {
  local remaining
  remaining=$(get_rate_remaining)
  if [[ "$remaining" -eq 0 ]]; then
    echo "  Rate limit exhausted. Stopping early." >&2
    return 1
  elif [[ "$remaining" -gt 0 && "$remaining" -lt 50 ]]; then
    echo "  Low rate limit ($remaining remaining). Sleeping 60s..." >&2
    sleep 60
  fi
  return 0
}

# ---------- data fetching ----------

fetch_stargazers() {
  # Fetch stargazer logins, respecting --limit
  echo "Fetching stargazers for $REPO..." >&2
  local logins
  logins=$(gh api --paginate "repos/$REPO/stargazers" --jq '.[].login' 2>/dev/null) || {
    echo "ERROR: Failed to fetch stargazers. Check gh auth." >&2
    exit 1
  }

  if [[ -z "$logins" ]]; then
    echo "ERROR: No stargazers found." >&2
    exit 1
  fi

  if [[ "$LIMIT" -gt 0 ]]; then
    logins=$(echo "$logins" | head -n "$LIMIT")
  fi

  local count
  count=$(echo "$logins" | wc -l | tr -d ' ')
  echo "  Found $count stargazer(s) to process." >&2
  echo "$logins"
}

fetch_user_stars() {
  # Fetch repos starred by a given user. Returns owner/repo, one per line.
  local login="$1"
  local stars
  stars=$(gh api --paginate "users/$login/starred" --jq '.[].full_name' 2>/dev/null) || true
  echo "$stars"
}

# ---------- main logic ----------

# Temporary files for the frequency map
FREQ_FILE=$(mktemp)
trap 'rm -f "$FREQ_FILE"' EXIT

echo "=== Stargazer Overlap Analysis ==="
echo "  Repo:  $REPO"
echo "  Limit: ${LIMIT:-all}"
echo "  Top:   $TOP"
echo ""

# Fetch stargazers
STARGAZERS=$(fetch_stargazers)
TOTAL=$(echo "$STARGAZERS" | wc -l | tr -d ' ')

# Process each stargazer
IDX=0
while IFS= read -r login; do
  [[ -z "$login" ]] && continue
  ((IDX++)) || true

  echo "  [$IDX/$TOTAL] Fetching stars for $login..." >&2

  stars=$(fetch_user_stars "$login")
  if [[ -z "$stars" ]]; then
    # Might be rate-limited or user has no public stars
    check_rate_limit || break
    continue
  fi

  # Append each starred repo to the frequency file
  echo "$stars" >> "$FREQ_FILE"

  # Rate limit courtesy delay
  if [[ "$IDX" -lt "$TOTAL" ]]; then
    sleep "$DELAY"
  fi
done <<< "$STARGAZERS"

echo "" >&2
echo "Building frequency map..." >&2

# Build the frequency map:
# 1. Sort all repo names
# 2. Count unique occurrences
# 3. Remove our own repo
# 4. Sort by count descending
# 5. Take top N
if [[ ! -s "$FREQ_FILE" ]]; then
  echo "No co-starred repos found." >&2
  exit 1
fi

RESULTS=$(
  sort "$FREQ_FILE" \
    | grep -v "^$" \
    | uniq -c \
    | sort -rn \
    | grep -v " ${REPO}$" \
    | head -n "$TOP"
)

if [[ -z "$RESULTS" ]]; then
  echo "No co-starred repos found after filtering." >&2
  exit 1
fi

# ---------- output markdown table ----------

echo ""
echo "| Rank | Repo | Co-stargazers |"
echo "|------|------|---------------|"

RANK=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  ((RANK++)) || true
  # Each line from uniq -c looks like: "  42 owner/repo"
  count=$(echo "$line" | awk '{print $1}')
  repo=$(echo "$line" | awk '{print $2}')
  echo "| $RANK | $repo | $count |"
done <<< "$RESULTS"

echo ""
echo "Analyzed $IDX stargazer(s). Top $TOP co-starred repos shown above."
