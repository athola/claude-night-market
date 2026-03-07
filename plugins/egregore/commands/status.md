---
name: status
description: Show current egregore state and progress
usage: /egregore:status
---

# status

Display the current state of the egregore, including work
item progress, pipeline position, and budget.

## What It Shows

- **Work item summary table.** Each item with its ID,
  reference, status, and current pipeline stage/step.
- **Pipeline position.** Which stage and step the active
  item is currently executing.
- **Budget status.** Tokens used, tokens remaining, and
  whether a cooldown is active.
- **Session counts.** How many sessions have run and how
  many continuations (watchdog relaunches) have occurred.
- **Decision log tail.** The last 10 entries from the
  decision log showing recent autonomous choices.

## See Also

- `/egregore:summon` to start or resume processing.
- `/egregore:dismiss` to stop gracefully.
