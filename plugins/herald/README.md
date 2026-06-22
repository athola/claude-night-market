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

## Stop-Hook Continuation Judge

Herald registers a `Stop` hook, `double-shot-latte`, that decides
whether Claude has more autonomous work to do when a turn ends.
It reads the last assistant message and continues only on an
explicit statement of intent to keep working.
A question, a handoff, or a completion signal lets the turn stop.
The default is to stop, so finished work is not nagged.

To prevent runaway loops, the judge allows up to 10 auto-continue
cycles (configurable) within a 5-minute window before pausing to
check in.
When the limit is reached it stops, names the limit, and invites
you to reply if more work remains.
The counter is then reset, so a resumed run starts a fresh budget
rather than re-tripping the limit.

### Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `DOUBLE_SHOT_LATTE_MAX_CONTINUATIONS` | `10` | Auto-continue cycles allowed in the window before a check-in. A non-positive-integer value falls back to the default. |
| `DOUBLE_SHOT_LATTE_LLM` | unset | Set to `1` to consult an LLM as a tiebreaker on ambiguous turns. |
| `DOUBLE_SHOT_LATTE_MODEL` | `haiku` | Model used for the optional LLM tiebreaker. |

The judge is pure Python standard library and needs no `jq`,
`claude` CLI, or `/tmp`, so it behaves the same on Linux, macOS,
and Windows.
The optional LLM tiebreaker falls back to the deterministic
verdict when `claude` is unavailable, so the default behavior
never depends on the network.

## Design note

Herald registers no skills intentionally. It is a hook-and-script
library: other plugins call its scripts directly or invoke its hooks
rather than using it as a skill source. Adding skills here would
create an inappropriate coupling layer between notification mechanics
and skill dispatch.

## Development

```bash
make deps    # Install dependencies
make test    # Run tests
make check   # Run all checks (lint, type-check, test)
```
