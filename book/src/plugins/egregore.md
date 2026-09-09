# egregore

Autonomous agent orchestrator for full development
lifecycles with session budget management and crash
recovery.

## Overview

Egregore spawns autonomous Claude Code sessions that
execute multi-step development tasks without human input.
It manages session budgets, provides crash recovery via
a watchdog daemon, and validates output quality before
merging.

## Installation

```bash
/plugin install egregore@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `summon` | Spawn autonomous session with budget | Delegating full tasks |
| `quality-gate` | Pre-merge quality validation | Before merging autonomous work |
| `install-watchdog` | Install crash-recovery watchdog | Setting up monitoring |
| `uninstall-watchdog` | Remove watchdog | Cleaning up monitoring |

## Commands

| Command | Description |
|---------|-------------|
| `/summon` | Spawn autonomous agent session |
| `/dismiss` | Terminate autonomous session |
| `/status` | Check session status |
| `/install-watchdog` | Install crash-recovery daemon |
| `/uninstall-watchdog` | Remove watchdog daemon |

## Agents

| Agent | Description |
|-------|-------------|
| `orchestrator` | Manages autonomous development lifecycle |
| `sentinel` | Watchdog agent for crash recovery |

## Usage Examples

### Spawn an Autonomous Session

```bash
# Summon with default budget
/summon "Implement feature X"

# Check status
/status

# Dismiss when done
/dismiss
```

### Install Watchdog

```bash
# Set up crash recovery monitoring
/install-watchdog

# Remove when no longer needed
/uninstall-watchdog
```

## Hooks

| Hook | Event | Description |
|------|-------|-------------|
| `session_start_hook.py` | SessionStart | Injects manifest context into new sessions |
| `user_prompt_hook.py` | UserPromptSubmit | Reminds orchestrator to resume after user interrupts |
| `stop_hook.py` | Stop | Prevents early exit while work items remain |

The `UserPromptSubmit` hook lets users interact with a
running egregore session without breaking the orchestration
loop. After handling the user's request, the orchestrator
re-reads the manifest and resumes where it left off.

## Self-Healing Heartbeat

A recurring cron (`*/5 * * * *`) detects stalled pipelines
and re-enters the orchestration loop automatically.
This catches edge cases where context compaction or
unexpected errors break the loop despite the hooks.

## Stop Hook Stall Bound

The Stop hook blocks the session from stopping while the
manifest holds active work, which is how the loop continues
without a human turn. That condition is static, so blocking
on it alone re-injects the prompt forever. Dogfooding
measured ten turns and roughly $0.70 of Opus for a one-word
prompt in a project whose manifest had active items and no
way to advance them.

The block is bounded by stall detection. The hook hashes
`manifest.json` and keeps a count in
`.egregore/stop-hook-state.json`:

| Event | Effect |
|---|---|
| Manifest hash changed since the last block | Count resets to zero |
| New `session_id` (a watchdog relaunch) | Count resets to zero |
| Block with the hash unchanged | Count increments |
| Count reaches `EGREGORE_STOP_MAX_STALLS` (default 3) | Hook approves the stop and stays released until the hash changes |
| State file cannot be written | Hook approves the stop |

The last row is deliberate. An unbounded block is the
failure being bounded here, and a released stop is
recoverable because the watchdog relaunches the session. A
step that legitimately runs longer than three turns without
writing the manifest is paused rather than lost, since the
watchdog relaunches it on the next tick with a fresh count.
Raise `EGREGORE_STOP_MAX_STALLS` to give such steps more
room.

**What the bound does not settle.** Stop-hook re-injection
is not an upstream-documented continuation mechanism. The
sanctioned primitives, `/loop` and `CronCreate`, are
session-scoped, so neither replaces it. This bound prices
the ride and does not sanction it. The full record,
including the alternatives considered and what would retire
the reliance, is
[ADR-0022](../../../docs/adr/0022-stop-hook-reinjection-as-continuation.md).
The bound takes manifest bytes as its definition of
progress, so a session that writes the manifest every turn
without advancing the pipeline still loops. That is not the
measured failure, where a stuck session wrote nothing at
all.

**Residual cost, unbounded by this change.** A watchdog tick
that finds a dead session relaunches into a fresh stall
budget. An item stuck without manifest writes therefore
costs about three turns per relaunch, every tick, for as
long as the timer runs. Bounding one relaunch does not bound
their product. That product is the systemd timer decision,
and the escape hatch stays the same:

```bash
systemctl --user disable --now egregore-watchdog.timer
```

## Architecture

Egregore uses a convention-based approach where
autonomous sessions follow project conventions stored
in `conventions/`. The orchestrator agent manages the
session lifecycle, while the sentinel agent monitors
for crashes and restarts sessions as needed.

## Parallel Execution

Independent work items run concurrently in git worktrees,
each on its own branch, isolated from other in-flight work.
`detect_independent_items()` groups items by `source_ref`,
so different refs run in parallel and shared refs run in
sequence. `max_concurrent_worktrees` (default 3) caps the
simultaneous worktrees, and `merge_worktree_result()` merges
each feature branch with `--no-ff` when the item completes.

Within the quality stage, independent steps run in parallel
waves under the dependency-graph scheduling in
`stage_parallel.py`. Wave 1 dispatches `code-review`,
`unbloat` and `update-docs` together. Wave 2 runs
`code-refinement` and `update-tests` once `code-review`
finishes.

## Agent Specialization

Specialist agents handle specific pipeline steps and
accumulate expertise across sessions. `select_specialist(step)`
picks one, and its context file persists in
`.egregore/specialists/`.

| Role | Steps | Persisted state |
|------|-------|-----------------|
| reviewer | code-review, pr-review | Review context, metrics |
| documenter | update-docs | Style patterns |
| tester | update-tests | Coverage history |

## Cross-Item Learning

The `learning` module reads decision logs from completed
work items and extracts reusable patterns in four
categories: tech stack, failure mode, architecture and
approach. Each pattern records its frequency and its success
rate across items, and `generate_briefing()` builds a
context briefing for a new work item from the
high-frequency ones. Patterns persist in
`.egregore/learning/patterns.json`.

## Multi-Repository Support

`RepoRegistry` orchestrates work across repositories.
`register_repo(name, path)` adds one, `route_item()` sends a
work item to it, and each repo tracks its own default branch
and labels. The registry persists in `.egregore/repos.json`.

## GitHub Discussions Publishing

Discoveries, insights, contentions and retrospectives from
autonomous sessions are published to GitHub Discussions.
`max_per_work_item` (default 10) rate-limits a single item,
and published entries are logged so a rerun does not post
them twice.

## Related Plugins

- [conjure](conjure.md): External LLM delegation
- [conserve](conserve.md): Context management
- [sanctum](sanctum.md): Git workflow integration
