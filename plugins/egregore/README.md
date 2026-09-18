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

**Token window exhaustion:** When a run hits a usage limit,
`scripts/window.py` reads the reset instant from what the API
actually returned and records it in `budget.cooldown_until`.
The watchdog's OS timer polls that value and relaunches once
the window has renewed.

`CronCreate` can schedule the resume instead, but only inside
a session that stays alive to run it. The tool's own
description says its jobs live only in the running session,
that nothing is written to disk, that `durable` has no
effect, and that jobs fire only while the REPL is idle. A
headless `claude -p` night run that exits on a usage limit is
exactly the case it cannot cover, so the watchdog is the
default and `CronCreate` is the attended-session shortcut.
`plan_resume()` picks between them and says why.

**Token window exhaustion (pre-2.1.71 fallback):** Saves a
cooldown timestamp to `budget.json` and exits. The watchdog
checks every 5 minutes and relaunches after cooldown.

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

> **Why opt-in?** Per [docs/inclusive-defaults.md][inc],
> webhooks send session data to external services using
> user-supplied URLs. There is no reasonable default URL,
> so flipping is impossible, not merely unwise.

[inc]: ../../docs/inclusive-defaults.md

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
    "auto_merge": false,
    "completion_integrity": false
  },
  "budget": {
    "window_type": "5h",
    "cooldown_padding_minutes": 10
  }
}
```

> **Why `auto_merge: false`?** Per [docs/inclusive-defaults.md][inc],
> merging a PR without human review is irreversible-ish
> (revert PR is messy and visible in history). Egregore is
> already opt-in at `/egregore:summon`; `auto_merge`
> gates the no-human-loop transition specifically.

> **Why `completion_integrity: false`?** Default off keeps the
> historical posture: the loop runs indefinitely and advances on any
> non-crash step result. Set it to `true` to make a quality verdict of
> `fix-required` block advancement to ship (so an item cannot complete
> with unresolved blocking findings) and hold merge for human review.
> It never halts the overall loop, only the offending item.

## vs Ralph Wiggum

| | Ralph Wiggum | Egregore |
|---|---|---|
| Loop mechanism | Stop hook re-injects same prompt, bounded by an iteration count | Stop hook reads manifest, injects current step, bounded by stall detection |
| State awareness | None (reads files each time) | Full pipeline state in manifest.json |
| Session management | None | Continuation agents and watchdog daemon |
| Token budgets | None | Watchdog resume at the recorded reset instant; CronCreate only while a session survives |
| Crash recovery | None | Watchdog and GitHub issue alerts |
| Progress visibility | None | `/loop 5m /egregore:status` auto-scheduled |
| Decision making | Blind repetition | Autonomous with decision logging |
| Pipeline | None | 16-step across 4 stages |

## Stop Hook Stall Bound

The Stop hook blocks a session from stopping while the
manifest holds active work, which is how the loop continues
without a human turn. Blocking on that alone re-injects the
prompt forever, so the block is bounded: the hook hashes
`manifest.json`, counts consecutive blocks with the hash
unchanged, and approves the stop at
`EGREGORE_STOP_MAX_STALLS` (default 3). A manifest change or
a watchdog relaunch resets the count.

The table of reset and increment events, what the bound does
not settle, and the residual cost of repeated relaunches are
in the [book page][book]. The decision itself is
[ADR-0022](../../docs/adr/0022-stop-hook-reinjection-as-continuation.md).

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
make test       # Run tests
make lint       # Run linting
make check      # Run all checks
```

## Quality Stage

The QUALITY stage enforces project conventions and code
quality before work items reach SHIP. Three components:

```
Orchestrator Agent
  │
  ├── manifest.py (existing)
  │     └── WorkItem.quality_config
  │
  ├── quality-gate skill
  │     ├── routing table
  │     ├── verdict calculation
  │     └── mode selection (self/PR)
  │
  ├── conventions.py
  │     ├── load_codex()
  │     ├── check_conventions()
  │     └── built-in checkers
  │
  └── codex.yml
        └── C1-C5 convention definitions
```

**Data flow**: orchestrator reaches quality stage, reads
the work item's `quality_config`, invokes the quality-gate
skill for each step. The skill loads `codex.yml`, runs
convention checks, invokes mapped skills (pensive, conserve,
sanctum), collects findings, and calculates a verdict:
pass, pass-with-warnings, or fix-required.

**Conventions enforced** (from PR history analysis):

- **C1**: No ephemeral artifacts committed
- **C2**: Markdown prose wraps at 80 chars
- **C3**: No AI slop markers in documentation
- **C4**: Python 3.9 compatibility in hooks
- **C5**: Scope-guard compliance (line/file thresholds)

**Modes**: self-review (pre-PR, runs all 5 quality steps)
and PR-review (invoked by other agents for cross-review).

## Further Reading

These behaviors are documented on the [book page][book]:

- **Parallel execution**: worktree isolation,
  `max_concurrent_worktrees`, and the two quality-stage waves
- **Agent specialization**: the reviewer, documenter and
  tester roles and the state each keeps
- **Cross-item learning**: pattern categories and how a
  briefing is generated
- **Multi-repository support**: `RepoRegistry` routing
- **GitHub Discussions publishing**: content types, rate
  limiting and deduplication

[book]: ../../book/src/plugins/egregore.md
