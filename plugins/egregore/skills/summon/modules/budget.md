---
name: budget
description: Token window management protocol
category: orchestration
---

# Budget Module

Manages token budget windows, detects rate limits, calculates
cooldown periods, and triggers graceful shutdown when limits
are reached.

## Budget Window

An egregore session operates within a budget window (default:
5 hours).
The window tracks cumulative token usage and rate limit
events across multiple sessions.

The budget state is in `.egregore/budget.json`:

```json
{
  "window_type": "5h",
  "window_started_at": "2026-03-04T10:00:00+00:00",
  "estimated_tokens_used": 0,
  "session_count": 1,
  "last_rate_limit_at": null,
  "cooldown_until": null
}
```

## Rate Limit Detection

The orchestrator detects rate limits through two signals:

1. **API error response**: a skill invocation fails with an
   HTTP 429 or a rate-limit error message from the Claude
   API.
2. **Explicit retry-after header**: the error includes a
   retry-after duration in seconds.

When either signal is detected, the orchestrator must stop
work immediately and enter cooldown.

## Cooldown Calculation

The cooldown duration is computed as follows:

```
cooldown_minutes = retry_after_seconds / 60
                 + config.budget.cooldown_padding_minutes
```

The padding (default: 10 minutes) prevents the watchdog from
relaunching too early and hitting the same rate limit again.

If no retry-after header is present, use a default cooldown
of 30 minutes plus padding.

## Rate Limit Recovery

When a rate limit is detected:

1. **Save manifest**: write the current pipeline state to
   `.egregore/manifest.json` so no progress is lost.
2. **Record rate limit**: call
   `budget.record_rate_limit(cooldown_minutes)` to update
   the budget state.
3. **Save budget**: write `.egregore/budget.json` with the
   updated cooldown timestamp.
4. **Alert overseer**: send a notification via the configured
   channel (see `notify.py`) with the rate limit details and
   expected resume time.

### In-Session Recovery (attended sessions only)

`CronCreate` schedules a one-shot resume at the cooldown
expiry, and it works only while the session that created it
is still running. Its own description is explicit: jobs
"live only in this Claude session", nothing is written to
disk, the `durable` parameter "has no effect", and jobs fire
only while the REPL is idle.

So this path applies when a person is sitting with an open
session. It does not apply to the unattended night run,
which is headless and exits when the limit stops it. Ask
`window.plan_resume()` rather than choosing by hand.

```
CronCreate(
  cron: "<min> <hour> * * *",
  prompt: "Cooldown expired. Read .egregore/manifest.json
    and resume the pipeline. Invoke
    Skill(egregore:summon) to continue.",
  recurring: false
)
```

**What it buys, and what it costs:**

- Buys: the session stays alive, so no context is lost and
  no manifest is re-read
- Buys: fires at cooldown_until instead of within a
  five-minute poll
- Costs: the job dies with the session, so nothing resumes
  if the session exits, the terminal closes, or the machine
  reboots
- Costs: a weekly window can renew days out, longer than
  any session should be held open for it

The session remains idle between the rate limit and the
scheduled prompt. When the cron fires, the orchestration
loop resumes with the full conversation context intact.

### Fallback: Exit and Watchdog

This is the default path, not a degraded one. Use it
whenever the session will not survive the wait, whenever
the reset is more than a day out, and whenever the run is
unattended:

5. **Exit cleanly**: exit with code 0. A non-zero exit
   would trigger the watchdog's crash handler instead of
   the cooldown-aware restart path.

The watchdog checks `budget.json` before relaunching and
waits until the cooldown expires.

## Pre-Launch Cooldown Check

Before starting any work, the orchestrator must check:

```python
if is_in_cooldown(budget):
    # Do not start. Exit and let the watchdog retry later.
    sys.exit(0)
```

The watchdog also performs this check before launching a new
session.
This double-check prevents races where the watchdog reads a
stale budget file.

## Window Reset

The budget window resets when `window_started_at` is older
than the configured `window_type` duration.
On reset:

1. Set `estimated_tokens_used` to 0.
2. Set `session_count` to 0.
3. Set `window_started_at` to the current time.
4. Clear `last_rate_limit_at` and `cooldown_until`.
5. Save `budget.json`.

## Token Estimation

Exact token counts are not always available.
The orchestrator uses these heuristics:

- **Per-session estimate**: each Claude session uses roughly
  100k-200k tokens depending on task complexity.
- **Increment on session start**: add the per-session
  estimate to `estimated_tokens_used` when a new session
  begins.
- **Post-hoc correction**: if the session completes
  normally, adjust the estimate based on actual conversation
  length (word count * 1.3 as a rough token multiplier).

These estimates are for observability and alerting, not for
hard enforcement.

### `rate_limits` Statusline Field (2.1.80+)

The statusline input now includes `rate_limits` with
5-hour and 7-day rate limit usage (`used_percentage`,
`resets_at`). The orchestrator can use this for more
accurate rate limit detection than the heuristic
estimates in the budget window, triggering cooldown
before hitting hard limits.

### Token Estimation Fix (2.1.75+)

Claude Code fixed token estimation over-counting for
`thinking` and `tool_use` blocks, which previously
triggered premature context compaction. Sessions now
use more of their available context window before
compaction. This is especially relevant for egregore
sessions using Opus 4.6 with extended thinking: the
orchestrator can maintain longer conversation context
before compaction interrupts the pipeline loop.

Combined with the 1M context default for Max/Team/
Enterprise (2.1.75+), egregore sessions benefit from
significantly longer uninterrupted orchestration runs.
Rate limit errors are the authoritative signal for budget
exhaustion.
