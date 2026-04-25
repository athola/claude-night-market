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

**Token window exhaustion (2.1.71+):** When hitting a rate
limit, egregore schedules a one-shot resume via `CronCreate`
at the cooldown expiry time. The session stays alive and
self-recovers with full context preserved. No watchdog
needed for rate limits.

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
> so flipping is impossible — not just unwise.

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
    "auto_merge": false
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

## vs Ralph Wiggum

| | Ralph Wiggum | Egregore |
|---|---|---|
| Loop mechanism | Stop hook re-injects same prompt | Stop hook reads manifest, injects current step |
| State awareness | None (reads files each time) | Full pipeline state in manifest.json |
| Session management | None | Continuation agents + watchdog daemon |
| Token budgets | None | In-session CronCreate recovery (2.1.71+) + watchdog fallback |
| Crash recovery | None | Watchdog + GitHub issue alerts |
| Progress visibility | None | `/loop 5m /egregore:status` auto-scheduled |
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

## Parallel Execution

Egregore processes independent work items concurrently
using git worktrees. Each item gets its own worktree
and branch, isolated from other in-flight work.

- `detect_independent_items()` groups items by
  `source_ref`; different refs run in parallel,
  shared refs run sequentially
- `max_concurrent_worktrees` (default 3) caps
  simultaneous worktrees
- After completion, `merge_worktree_result()` merges
  each feature branch with `--no-ff`

Within the quality stage, independent steps also run
in parallel waves. Wave 1 dispatches `code-review`,
`unbloat`, and `update-docs` simultaneously; wave 2
runs `code-refinement` and `update-tests` after
`code-review` finishes.

## Agent Specialization

Specialist agents handle specific pipeline steps and
accumulate expertise across sessions:

| Role | Steps | Persisted State |
|------|-------|-----------------|
| reviewer | code-review, pr-review | Review context, metrics |
| documenter | update-docs | Style patterns |
| tester | update-tests | Coverage history |

Specialists are selected via `select_specialist(step)`
and their context files persist in `.egregore/specialists/`.

## Cross-Item Learning

The `learning` module analyzes decision logs from
completed work items to extract reusable patterns:

- **Categories**: tech_stack, failure_mode,
  architecture, approach
- **Success tracking**: each pattern records its
  frequency and success rate across items
- `generate_briefing()` produces a context briefing
  from high-frequency patterns for new work items

Patterns persist in `.egregore/learning/patterns.json`.

## Multi-Repository Support

Egregore can orchestrate work across multiple
repositories via `RepoRegistry`:

- Register repos with `register_repo(name, path)`
- Route work items to repos with `route_item()`
- Each repo tracks its own default branch and labels
- Registry persists in `.egregore/repos.json`

## GitHub Discussions Publishing

Discoveries, insights, and retrospectives from
autonomous sessions are published to GitHub Discussions:

- **Content types**: discovery, insight, contention,
  retrospective
- **Rate limiting**: `max_per_work_item` (default 10)
  prevents flooding
- **Tracking**: published entries are logged to avoid
  duplicate posts
