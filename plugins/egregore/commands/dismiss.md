---
name: dismiss
description: Stop egregore gracefully, saving all state
usage: /egregore:dismiss
---

# dismiss

Stop the egregore gracefully. All in-progress work is
saved so it can be resumed later.

## What It Does

1. Marks all active work items as `paused` in
   `.egregore/manifest.json`.
2. Saves the current pipeline position for each item so
   resumption starts at the right step.
3. Removes the pidfile (`.egregore/pid`) so the watchdog
   does not relaunch the session.
4. Logs the dismissal event to the decision log.

## When To Use

- You need to reclaim your machine or API quota.
- You want to review progress before the egregore
  continues.
- Something went wrong and you want to stop processing
  before more items are affected.

## See Also

- `/egregore:summon` to start or resume processing.
- `/egregore:status` to review current state before
  dismissing.
