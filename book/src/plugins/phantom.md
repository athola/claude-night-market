# phantom

Computer use toolkit for desktop automation via Claude's
vision and action API.

## Overview

Phantom enables Claude to interact with desktop environments
through screenshot capture, mouse/keyboard control, and
an autonomous agent loop.
It wraps Claude's Computer Use API for sandboxed GUI
automation workflows.

## Installation

```bash
/plugin install phantom@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `computer-control` | Desktop automation via screenshot capture, mouse/keyboard control | Automating GUI tasks in sandboxed environments |

## Commands

| Command | Description |
|---------|-------------|
| `/control-desktop` | Run a computer use task on the desktop |

## Agents

| Agent | Description |
|-------|-------------|
| `desktop-pilot` | Autonomous desktop control with multi-step GUI workflows |

## Usage Examples

### Control a Desktop

```bash
# Run a GUI automation task
/control-desktop "Open the browser and navigate to example.com"

# Use the agent for multi-step workflows
Agent(phantom:desktop-pilot)
```

## Dependencies

Phantom uses skills from other plugins:

- **leyline:error-patterns**: Error handling and recovery
