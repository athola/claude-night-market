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

## Architecture

Egregore uses a convention-based approach where
autonomous sessions follow project conventions stored
in `conventions/`. The orchestrator agent manages the
session lifecycle, while the sentinel agent monitors
for crashes and restarts sessions as needed.

## Related Plugins

- [conjure](conjure.md) -- External LLM delegation
- [conserve](conserve.md) -- Context management
- [sanctum](sanctum.md) -- Git workflow integration
