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

## Architecture

Egregore uses a convention-based approach where
autonomous sessions follow project conventions stored
in `conventions/`. The orchestrator agent manages the
session lifecycle, while the sentinel agent monitors
for crashes and restarts sessions as needed.

## Parallel Execution

Independent work items run concurrently via git
worktrees (up to 3 by default). Within the quality
stage, independent steps execute in parallel waves
using dependency-graph scheduling from
`stage_parallel.py`.

## Agent Specialization

Specialist agents (reviewer, documenter, tester)
handle specific pipeline steps and accumulate context
across sessions. Profiles persist in
`.egregore/specialists/`.

## Cross-Item Learning

The `learning` module extracts patterns from decision
logs (tech stack choices, failure modes, architecture
decisions) and generates briefings for new work items
based on historical success rates.

## Multi-Repository Support

`RepoRegistry` manages work across multiple
repositories, routing items by labels and tracking
per-repo configuration in `.egregore/repos.json`.

## GitHub Discussions Publishing

Discoveries, insights, and retrospectives from
autonomous sessions are published to GitHub
Discussions with rate limiting and deduplication.

## Related Plugins

- [conjure](conjure.md) -- External LLM delegation
- [conserve](conserve.md) -- Context management
- [sanctum](sanctum.md) -- Git workflow integration
