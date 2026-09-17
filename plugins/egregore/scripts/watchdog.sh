#!/usr/bin/env bash
# egregore-watchdog.sh
#
# Checks if egregore needs relaunching. Run via launchd or
# systemd timer every 5 minutes. Pure shell, no network calls,
# fully auditable.
set -euo pipefail

# Resolved once, absolute: the relaunch below cds into the manifest's
# project_dir, and a relative pid file would then be written under the
# timer's working directory and checked under another.
EGREGORE_DIR="$(cd "${EGREGORE_DIR:-.egregore}" 2>/dev/null && pwd || printf '%s' "${EGREGORE_DIR:-.egregore}")"
MANIFEST="$EGREGORE_DIR/manifest.json"
BUDGET="$EGREGORE_DIR/budget.json"
PIDFILE="$EGREGORE_DIR/pid"
LOG="$EGREGORE_DIR/watchdog.log"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ): $*" >> "$LOG"; }

# No manifest = nothing to do
if [[ ! -f "$MANIFEST" ]]; then
    exit 0
fi

# Check if work remains
if ! command -v jq &>/dev/null; then
    log "ERROR: jq not installed, cannot parse manifest"
    exit 1
fi

remaining=$(jq '[.work_items[] | select(.status == "active" or .status == "paused")] | length' "$MANIFEST" 2>/dev/null || echo "0")
if [[ "$remaining" -eq 0 ]]; then
    log "No active work items, exiting"
    exit 0
fi

# Check cooldown
if [[ -f "$BUDGET" ]]; then
    cooldown=$(jq -r '.cooldown_until // empty' "$BUDGET" 2>/dev/null)
    if [[ -n "$cooldown" ]]; then
        now=$(date +%s)
        if [[ "$(uname)" == "Darwin" ]]; then
            until_ts=$(date -jf "%Y-%m-%dT%H:%M:%S" "${cooldown%%.*}" +%s 2>/dev/null || echo "0")
        else
            until_ts=$(date -d "$cooldown" +%s 2>/dev/null || echo "0")
        fi
        if [[ "$now" -lt "$until_ts" ]]; then
            log "In cooldown until $cooldown, waiting"
            exit 0
        fi
    fi
fi

# Check if session already running
if [[ -f "$PIDFILE" ]]; then
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        exit 0  # session alive
    fi
    log "Stale pid $pid detected (crash). Cleaning up."
    rm -f "$PIDFILE"
fi

# Read project dir from manifest
project_dir=$(jq -r '.project_dir' "$MANIFEST" 2>/dev/null)
if [[ -z "$project_dir" || "$project_dir" == "null" ]]; then
    project_dir="$(pwd)"
elif [[ ! -d "$project_dir" ]]; then
    log "ERROR: project_dir '$project_dir' from manifest does not exist; aborting relaunch"
    exit 1
fi

# Relaunch
log "Relaunching egregore session ($remaining active items)"
cd "$project_dir" || { log "ERROR: cd to '$project_dir' failed; aborting"; exit 1; }

relaunch_prompt="$EGREGORE_DIR/relaunch-prompt.md"
if [[ -f "$relaunch_prompt" ]]; then
    prompt_content="$(cat "$relaunch_prompt")"
else
    prompt_content="Egregore resuming. Read .egregore/manifest.json and invoke Skill(egregore:summon) to continue the pipeline."
fi

# --output-format json because the default text format is swallowed
# when the Stop hook blocks the stop, leaving no record of the run.
# </dev/null because hooks read stdin, and nohup leaves it attached to
# nothing: each hook then stalls 3s and prints a warning onto the same
# stream as the result, which corrupts it.
nohup claude -p "$prompt_content" --output-format json < /dev/null >> "$LOG" 2>&1 &
echo $! > "$PIDFILE"
log "Launched with PID $!"
