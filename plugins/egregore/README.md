# Egregore Plugin

Autonomous agent orchestrator for full development lifecycles
with zero human input.

Named after the occult concept of a thought-form created by
collective belief, egregore embodies a persistent autonomous
will that outlives any single Claude session. It orchestrates
specialist skills through a 16-step pipeline, manages token
budgets across session boundaries, and recovers from crashes
without human intervention.

## Quick Start

```bash
# One-shot a project from a prompt
/egregore:summon "Build a REST API for todos with auth and tests" --window 5h

# Process GitHub issues
/egregore:summon --issues 42,43,47 --window 7d

# Run indefinitely (pauses on rate limits, resumes after cooldown)
/egregore:summon "Build X" --indefinite

# Install the watchdog for crash recovery
/egregore:install-watchdog --window 5h
```

## How It Works

Egregore has three layers:

```
  Manifest (.egregore/manifest.json)
  Persistent memory: work queue, pipeline state, decisions
                    |
  Orchestrator Skill (egregore:summon)
  The will: picks work, invokes skills, advances pipeline
                    |
  Watchdog Daemon (watchdog.sh)
  Persistence: relaunches sessions after crashes/cooldowns
```

Each work item flows through a 16-step pipeline:

```
INTAKE        BUILD           QUALITY            SHIP
------        -----           -------            ----
parse    ->  brainstorm  ->  code-review   ->  prepare-pr
validate     specify         unbloat           pr-review
prioritize   blueprint       code-refinement   fix-pr
             execute         update-tests      merge
                             update-docs
```

At each step, egregore invokes the appropriate existing
night-market skill (attune, pensive, sanctum, conserve).

## Commands

| Command | Description |
|---------|-------------|
| `/egregore:summon` | Start autonomous work |
| `/egregore:dismiss` | Stop gracefully |
| `/egregore:status` | Show progress |
| `/egregore:install-watchdog` | Install crash recovery daemon |
| `/egregore:uninstall-watchdog` | Remove the daemon |

## Session Management

**Context overflow:** Uses existing continuation agent
pattern. At 80% context, saves state and spawns a fresh
agent that reads the manifest and continues.

**Token window exhaustion:** When hitting a rate limit,
egregore saves a cooldown timestamp to `budget.json` and
exits. The watchdog checks every 5 minutes and relaunches
after the cooldown passes.

**Crashes:** The watchdog detects stale pidfiles (process
died) and relaunches automatically. An alert is created
as a GitHub issue so the overseer knows what happened.

## Notifications

All events are non-blocking notifications (never pause
for approval):

| Event | Default | Description |
|-------|---------|-------------|
| crash | on | Session died |
| rate_limit | on | Entering cooldown |
| pipeline_failure | on | Work item failed 3x |
| completion | on | All work done |
| watchdog_relaunch | on | Session relaunched |

**Tier 1 (default):** GitHub issues labeled
`egregore/alert`. Repo owner gets email automatically.

**Tier 2 (opt-in):** Webhooks to Slack, Discord, ntfy.sh,
or any URL.

## Configuration

Stored in `.egregore/config.json`:

```json
{
  "overseer": {
    "method": "github-repo-owner",
    "webhook_url": null,
    "webhook_format": "generic"
  },
  "alerts": {
    "on_crash": true,
    "on_rate_limit": true,
    "on_pipeline_failure": true,
    "on_completion": true,
    "on_watchdog_relaunch": true
  },
  "pipeline": {
    "max_attempts_per_step": 3,
    "skip_brainstorm_for_issues": true,
    "auto_merge": false
  },
  "budget": {
    "window_type": "5h",
    "cooldown_padding_minutes": 10
  }
}
```

## vs Ralph Wiggum

| | Ralph Wiggum | Egregore |
|---|---|---|
| Loop mechanism | Stop hook re-injects same prompt | Stop hook reads manifest, injects current step |
| State awareness | None (reads files each time) | Full pipeline state in manifest.json |
| Session management | None | Continuation agents + watchdog daemon |
| Token budgets | None | Reactive cooldown with auto-resume |
| Crash recovery | None | Watchdog + GitHub issue alerts |
| Decision making | Blind repetition | Autonomous with decision logging |
| Pipeline | None | 16-step across 4 stages |

## Watchdog Setup

The watchdog is a simple shell script run by your OS
scheduler. No background daemons, no compiled code.

```bash
# macOS: creates ~/Library/LaunchAgents/com.egregore.watchdog.plist
/egregore:install-watchdog

# Linux: creates ~/.config/systemd/user/egregore-watchdog.timer
/egregore:install-watchdog

# Remove
/egregore:uninstall-watchdog
```

## Development

```bash
cd plugins/egregore
make deps       # Install dependencies
make test       # Run tests (75 tests)
make lint       # Run linting
make check      # Run all checks
```

## Roadmap

Future evolution toward parallel agent swarm ("The Overmind"):

1. Parallel work items via git worktrees
2. Parallel pipeline stages (independent quality gates)
3. Agent specialization (dedicated reviewer, documenter)
4. Cross-item learning (decisions inform future strategy)
5. Multi-repo support
