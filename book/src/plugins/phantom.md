# phantom

Computer use toolkit for desktop automation via Claude's
vision and action API.

## Overview

Phantom enables Claude to interact with desktop environments
through screenshot capture, mouse/keyboard control, and
an autonomous agent loop.
It wraps Claude's Computer Use API for sandboxed GUI
automation workflows.

## Security Precautions

Computer use grants Claude direct control over mouse,
keyboard, and screen reading. Follow these precautions:

- **Run in a sandboxed environment** (VM, container, or
  dedicated machine). Never run on a machine with access
  to production systems or sensitive credentials.
- **Review tasks before execution.** The `/control-desktop`
  command displays the planned actions. Confirm before
  allowing execution.
- **Limit network access.** Restrict outbound connections
  from the sandbox to prevent data exfiltration if the
  agent navigates to an unintended URL.
- **Do not store credentials** in the sandbox environment.
  If a workflow requires login, use temporary tokens with
  narrow scope.
- **Monitor active sessions.** The desktop-pilot agent
  runs autonomously. Watch for unexpected navigation or
  input actions and terminate if behavior deviates.

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
