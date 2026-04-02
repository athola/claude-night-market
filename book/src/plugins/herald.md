# herald

Shared notification library for Claude Code plugins.

## Overview

Herald was extracted from egregore to provide independent
notification capabilities. Any plugin can send alerts
through herald without depending on the full egregore
orchestrator.

Herald is a pure library plugin: it declares no skills,
commands, agents, or hooks. Plugins import its Python
API directly (guarded with try/except per ADR-0001).

## Installation

```bash
/plugin install herald@claude-night-market
```

## Features

- GitHub issue creation via `gh` CLI
- Webhook delivery to Slack, Discord, or generic endpoints
- SSRF protection with URL validation
- Configurable source labels for multi-plugin use

## Alert Events

| Event | Value | Description |
|-------|-------|-------------|
| `CRASH` | `crash` | Process or agent crash |
| `RATE_LIMIT` | `rate_limit` | API quota exceeded |
| `PIPELINE_FAILURE` | `pipeline_failure` | Build or deploy failure |
| `COMPLETION` | `completion` | Task finished |
| `WATCHDOG_RELAUNCH` | `watchdog_relaunch` | Watchdog restarted agent |

## Usage

```python
from notify import AlertEvent, alert

alert(
    event=AlertEvent.CRASH,
    detail="Worker process crashed",
    source="my-plugin",
)
```

See the [herald README](../../../plugins/herald/README.md)
for webhook examples.
