# Herald

Standalone notification system for Claude Code plugins.
Provides GitHub issue alerts and webhook support
(Slack, Discord, generic).

## Overview

Herald was extracted from the egregore plugin to allow
independent installation of notification functionality.
Any plugin can use herald to send alerts without depending
on the full egregore orchestrator.

## Features

- GitHub issue creation via `gh` CLI
- Webhook delivery to Slack, Discord, or generic endpoints
- SSRF protection with URL validation
- Configurable source labels for multi-plugin use

## Usage

```python
from notify import AlertEvent, alert

# Send a GitHub issue alert
alert(
    event=AlertEvent.CRASH,
    detail="Worker process crashed",
    source="my-plugin",
)

# Send to Slack webhook
alert(
    event=AlertEvent.PIPELINE_FAILURE,
    webhook_url="https://hooks.slack.com/services/T00/B00/xxx",
    webhook_format="slack",
    detail="Build failed on main",
)
```

## Alert Events

| Event | Value | Description |
|-------|-------|-------------|
| CRASH | `crash` | Process or agent crash |
| RATE_LIMIT | `rate_limit` | API quota exceeded |
| PIPELINE_FAILURE | `pipeline_failure` | Build/deploy failure |
| COMPLETION | `completion` | Task finished |
| WATCHDOG_RELAUNCH | `watchdog_relaunch` | Watchdog restarted agent |

## Development

```bash
make deps    # Install dependencies
make test    # Run tests
make check   # Run all checks (lint, type-check, test)
```
