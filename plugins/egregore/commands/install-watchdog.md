---
name: install-watchdog
description: >-
  Install the egregore watchdog daemon for automatic
  session relaunching
usage: >-
  /egregore:install-watchdog [--window 5h|7d]
  [--interval SECONDS]
---

# install-watchdog

Install a system-level daemon that monitors the egregore
and relaunches it after crashes, rate limits, or context
overflows.

Runs `Skill(egregore:install-watchdog)`, which carries the installation
steps for launchd and systemd, the uninstall path and the
troubleshooting. The prerequisites and options below belong to the
command.

## Prerequisites

- `jq` must be installed (used to parse manifest and
  budget files).
- The `claude` CLI must be on your PATH.

## Options

| Option       | Default | Description                   |
|--------------|---------|-------------------------------|
| `--window`   | `5h`    | Time window for the session   |
| `--interval` | `300`   | Check interval in seconds     |

## See Also

- `/egregore:uninstall-watchdog` to remove the daemon.
- `/egregore:summon` to start processing.
