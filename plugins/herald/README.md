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

## Release Countdown

`scripts/release_countdown.py` holds a release for a window anyone can
pause and nobody can skip (ADR-0029). It announces the release to the
webhook in `RELEASE_WEBHOOK_URL`, waits `--minutes` (1 to 60), and stops
the release when an open issue carries the pause label (default
`release:pause`). Anyone who can label issues can pause.

```bash
RELEASE_WEBHOOK_URL=https://hooks.slack.com/services/... \
  python3 scripts/release_countdown.py --minutes 15 --release v1.2.3 --repo owner/name
```

It exits 0 when the release may leave, 3 when it was paused, and 2 when
it failed closed: an announcement that did not go out, or a pause check
that could not run, stops the release. This repository's publish
workflow runs it only when the `RELEASE_COUNTDOWN_MINUTES` repository
variable is set.

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
