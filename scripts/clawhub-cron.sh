#!/usr/bin/env bash
# Cron wrapper for clawhub-submit. Runs hourly until all skills
# are synced, then removes itself from crontab.
#
# Install: crontab -e, add:
#   0 * * * * /home/alext/claude-night-market/scripts/clawhub-cron.sh
#
# Logs to: /tmp/clawhub-sync.log

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG="/tmp/clawhub-sync.log"
LOCK="/tmp/clawhub-sync.lock"

# Prevent overlapping runs
if [ -f "$LOCK" ]; then
  echo "$(date): Lock file exists, skipping" >> "$LOG"
  exit 0
fi
trap 'rm -f "$LOCK"' EXIT
touch "$LOCK"

echo "" >> "$LOG"
echo "=== $(date): clawhub-cron run ===" >> "$LOG"

# Ensure PATH includes node/clawhub
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v25.2.1/bin:$PATH"

cd "$REPO_ROOT"
bash scripts/clawhub-submit.sh v1.8.3 >> "$LOG" 2>&1
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
  echo "$(date): All skills synced. Removing cron job." >> "$LOG"
  crontab -l 2>/dev/null | grep -v "clawhub-cron" | crontab - 2>/dev/null || true
  echo "$(date): Cron job removed." >> "$LOG"
else
  echo "$(date): Partial sync (exit $EXIT_CODE). Will retry next hour." >> "$LOG"
fi
