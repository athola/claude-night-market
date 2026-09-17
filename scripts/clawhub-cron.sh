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
# Under the repo, not /tmp: another user cannot pre-create it and disable
# the job. mkdir is atomic, so check-then-create cannot race, and the trap
# clears it on any exit; a SIGKILL leaves a directory whose age says so.
LOCK="$REPO_ROOT/.clawhub-sync.lock"

# Prevent overlapping runs
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date): Lock $LOCK exists, skipping" >> "$LOG"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

echo "" >> "$LOG"
echo "=== $(date): clawhub-cron run ===" >> "$LOG"

# Ensure PATH includes node/clawhub
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v25.2.1/bin:$PATH"

cd "$REPO_ROOT"
# No explicit version -- clawhub-submit.sh auto-detects from
# plugins/abstract/.claude-plugin/plugin.json so the cron stays
# correct across releases.
EXIT_CODE=0
bash scripts/clawhub-submit.sh >> "$LOG" 2>&1 || EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
  echo "$(date): All skills synced. Removing cron job." >> "$LOG"
  crontab -l 2>/dev/null | grep -v "clawhub-cron" | crontab - 2>/dev/null || true
  echo "$(date): Cron job removed." >> "$LOG"
else
  echo "$(date): Partial sync (exit $EXIT_CODE). Will retry next hour." >> "$LOG"
fi
