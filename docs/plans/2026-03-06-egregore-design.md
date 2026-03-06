# Egregore Plugin Design

*Date: 2026-03-06*
*Status: Approved*

## Overview

Egregore is an autonomous agent orchestrator plugin for
claude-night-market that manages full development lifecycles
with zero human input. Named after the occult concept of a
thought-form created by collective belief, egregore embodies
a persistent autonomous will that outlives any single Claude
session.

It builds on the ralph-wiggum pattern (Stop hook iteration
loop) but replaces blind repetition with intelligent pipeline
orchestration, session budget awareness, and crash recovery.

## Conceptual Model

The egregore has three layers:

**Manifest** (`.egregore/manifest.json`): The persistent
memory and intent. Stores work queue, pipeline state per
item, session budget tracking, overseer config, and decision
log. This is the source of truth: any session can pick up
where the last left off by reading it.

**Orchestrator Skill** (`egregore:summon`): The will. Reads
the manifest, picks the next work item, invokes specialist
skills in sequence, hands off to continuation agents on
context overflow, and tracks token/time budget.

**Watchdog Daemon** (`egregore-watchdog.sh`): The
persistence mechanism. A simple shell script run via
launchd (macOS) or systemd timer (Linux) that monitors
session health, detects token window exhaustion, relaunches
claude after cooldown, and alerts the overseer on anomalies.

## Architecture Approach

**Selected: "The Collective" (Approach B)** with extension
points toward "The Overmind" (Approach C).

A top-level orchestrator skill runs the full pipeline by
invoking existing night-market skills sequentially. Uses
the existing continuation agent pattern for context
overflow. An external watchdog daemon handles session death
and token window exhaustion.

Future evolution toward Approach C adds parallel work item
processing, parallel pipeline stages, and agent
specialization.

## Pipeline

Each work item flows through four stages:

```
INTAKE          BUILD              QUALITY             SHIP
------          -----              -------             ----
parse    -->  brainstorm   -->   code-review   -->   prepare-pr
validate       specify            unbloat             pr-review
prioritize     blueprint          code-refinement     fix-pr
               execute            update-tests        merge
                                  update-docs
```

Stage transitions are idempotent. If egregore crashes
mid-stage, the manifest records the last completed step.
On resume, it re-enters the current stage from the top.

### Per-item manifest entry

```json
{
  "id": "wrk_001",
  "source": "prompt|github-issue",
  "source_ref": "Build a REST API" | "#42",
  "branch": "egregore/wrk-001-rest-api",
  "pipeline_stage": "quality",
  "pipeline_step": "code-refinement",
  "started_at": "2026-03-06T10:00:00Z",
  "decisions": [
    {
      "at": "2026-03-06T10:05:00Z",
      "step": "brainstorm",
      "chose": "Express + SQLite",
      "why": "simplicity"
    }
  ],
  "attempts": 1,
  "max_attempts": 3,
  "status": "active|paused|completed|failed"
}
```

### Failure handling

If a step fails 3 times, egregore marks the item `failed`,
logs the reason, moves to the next work item, and continues.

## Session Budget Management

### Context budget (existing infrastructure)

Uses the existing continuation agent pattern. At 80%
context, egregore saves state to manifest plus
session-state.md and spawns a continuation agent.

### Token window budget (new capability)

Stored in `.egregore/budget.json`:

```json
{
  "window_type": "5h|7d",
  "window_started_at": "ISO8601",
  "estimated_tokens_used": 1200000,
  "session_count": 3,
  "last_rate_limit_at": null,
  "cooldown_until": null
}
```

Detection is reactive: egregore runs until it hits a rate
limit, records the error with a cooldown timestamp, exits
cleanly, and lets the watchdog relaunch after cooldown.

## Watchdog Daemon

A shell script (~60 lines) run via OS-level schedulers
every 5 minutes.

### Responsibilities

1. Check if an egregore session is active (pidfile)
2. If no session and work remains: check cooldown
3. If cooldown passed: relaunch `claude`
4. If session crashed (stale pidfile): alert and relaunch
5. Log everything to `.egregore/watchdog.log`

### Malware avoidance

- Uses legitimate OS schedulers (launchd plist, systemd
  unit) rather than custom daemons
- Explicit user opt-in via `/egregore:install-watchdog`
- Pure shell script, fully auditable, no compiled code
- Standard install locations
  (`~/Library/LaunchAgents/` on macOS)
- No network calls from the watchdog itself
- Clean uninstall via `/egregore:uninstall-watchdog`

### Installation

```bash
/egregore:install-watchdog --window 5h
# macOS: ~/Library/LaunchAgents/com.egregore.watchdog.plist
# Linux: ~/.config/systemd/user/egregore-watchdog.timer

/egregore:uninstall-watchdog
# Removes plist/unit, pidfile, watchdog log
```

## Overseer Notifications

### Tier 1: GitHub Issue Alerts (default)

Egregore creates GitHub issues labeled `egregore/alert`
on events. The repo owner receives email notifications
automatically through GitHub.

### Tier 2: Webhooks (opt-in)

Posts JSON payloads to a configurable URL. Format adapters
for Slack, Discord, ntfy.sh, and generic JSON. Fires in
addition to GitHub issues, not instead of.

### Alert events (all default on, none blocking)

| Event | Description |
|-------|-------------|
| `crash` | Session died unexpectedly |
| `rate_limit` | Token window exhausted, entering cooldown |
| `pipeline_failure` | Work item failed max attempts |
| `completion` | All work items finished |
| `watchdog_relaunch` | Watchdog restarted a session |

### Overseer configuration

```json
{
  "overseer": {
    "method": "github-repo-owner",
    "email": null,
    "webhook_url": null,
    "webhook_format": "generic"
  }
}
```

The `method` field defaults to `github-repo-owner`, which
uses `gh api` to discover the repo owner. Can be overridden
with an explicit email or webhook URL.

## Decision-Making Authority

Egregore operates with full autonomy. It makes its best
judgment call at every decision point and keeps going.
The overseer is alerted only on crashes, rate limits,
pipeline failures, completions, and watchdog relaunches.
No decision ever blocks on human approval.

A decision log is maintained in the manifest for post-hoc
auditing.

## Plugin Structure

```
plugins/egregore/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── summon/
│   │   ├── SKILL.md
│   │   └── modules/
│   │       ├── pipeline.md
│   │       ├── budget.md
│   │       ├── intake.md
│   │       └── decisions.md
│   ├── install-watchdog/
│   │   └── SKILL.md
│   └── uninstall-watchdog/
│       └── SKILL.md
├── commands/
│   ├── summon.md
│   ├── dismiss.md
│   ├── status.md
│   ├── install-watchdog.md
│   └── uninstall-watchdog.md
├── agents/
│   ├── orchestrator.md
│   └── sentinel.md
├── hooks/
│   ├── hooks.json
│   ├── stop_hook.py
│   └── session_start_hook.py
├── scripts/
│   ├── watchdog.sh
│   ├── install_launchd.sh
│   └── install_systemd.sh
├── templates/
│   ├── relaunch-prompt.md
│   ├── alert-crash.md
│   ├── alert-completion.md
│   └── webhook-payloads/
│       ├── slack.json
│       ├── discord.json
│       └── generic.json
├── tests/
├── pyproject.toml
├── Makefile
└── README.md
```

## Invocation

```bash
# From a prompt
/egregore:summon "Build a REST API" --window 5h

# From GitHub issues
/egregore:summon --issues 42,43,47 --window 7d

# From a label query
/egregore:summon --issues-label "egregore/queue" --window 5h

# Indefinite (runs until done, waits on rate limits)
/egregore:summon "Build X" --indefinite
```

## Configuration

Stored in `.egregore/config.json`:

```json
{
  "overseer": {
    "method": "github-repo-owner",
    "email": null,
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

## Future Evolution (Approach C: "The Overmind")

GitHub issues to create after v1:

1. Parallel work items via separate worktrees
2. Parallel pipeline stages (independent quality gates)
3. Agent specialization (dedicated reviewer, documenter)
4. Cross-item learning (decisions inform future strategy)
5. Multi-repo support
