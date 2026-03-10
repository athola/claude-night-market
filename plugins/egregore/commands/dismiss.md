---
name: dismiss
description: >-
  The ONLY way to stop the egregore. Human-initiated
  graceful shutdown that saves all state.
usage: /egregore:dismiss
---

# dismiss

The sole mechanism for stopping the egregore.
The egregore runs indefinitely by default and will
never stop on its own. Only a human issuing this
command can end an egregore session.

All in-progress work is saved so it can be resumed
later with `/egregore:summon`.

## What It Does

1. Marks all active work items as `paused` in
   `.egregore/manifest.json`.
2. Saves the current pipeline position for each item so
   resumption starts at the right step.
3. Cancels any scheduled cron jobs (progress pulses,
   work-scan polls) created by the orchestrator.
4. Removes the pidfile (`.egregore/pid`) so the watchdog
   does not relaunch the session.
5. Logs the dismissal event to the decision log.

## Important

The egregore never dismisses itself. It is designed to
run autonomously and indefinitely, scanning for new work
after completing its current manifest. This command is
the only way to interrupt that cycle.

If you want the egregore to stop after processing a
fixed set of items without manual intervention, use
`/egregore:summon --bounded` instead of dismissing.

## When To Use

- You need to reclaim your machine or API quota.
- You want to review progress before the egregore
  continues.
- Something went wrong and you want to stop processing
  before more items are affected.
- You are done with the egregore for now and want a
  clean shutdown.

## See Also

- `/egregore:summon` to start or resume processing.
- `/egregore:status` to review current state before
  dismissing.
