---
name: summon
description: >-
  Summon the egregore to autonomously process work items
  through the full development lifecycle. Runs indefinitely
  by default until dismissed.
usage: >-
  /egregore:summon "<prompt>" [--window 5h|7d]
  [--bounded] [--issues N,N] [--issues-label LABEL]
---

# summon

Launch the egregore to autonomously process work items
through planning, implementation, testing, and PR
creation. By default the egregore runs indefinitely,
scanning for new work after completing its current
manifest. Use `/egregore:dismiss` to stop it.

## When To Use

- You have one or more issues or tasks to process
  without manual intervention.
- You want to run a multi-hour or multi-day development
  pipeline overnight or over a weekend.
- You want the agent to self-recover from crashes and
  rate limits via the watchdog.
- You want continuous autonomous processing that finds
  and handles new work as it appears.

## When NOT To Use

- For quick, single-file changes. Just do them directly.
- When you need tight human-in-the-loop review at every
  step. Use normal Claude sessions instead.
- On repositories you do not trust the agent to modify.
  Egregore creates branches and opens PRs autonomously.

## Usage

From a prompt:

```
/egregore:summon "Refactor the auth module to use JWT"
```

From GitHub issues by number:

```
/egregore:summon --issues 42,43,44
```

From GitHub issues by label:

```
/egregore:summon --issues-label "egregore"
```

Bounded mode (stops after processing all items):

```
/egregore:summon --bounded --issues 42,43,44
```

## Options

| Option           | Default | Description                  |
|------------------|---------|------------------------------|
| `<prompt>`       | none    | Free-text work description   |
| `--window`       | `5h`    | Time window (e.g. 5h, 7d)   |
| `--bounded`      | false   | Stop after all items finish  |
| `--issues`       | none    | Comma-separated issue numbers|
| `--issues-label` | none    | GitHub label to pull issues  |

The egregore runs indefinitely by default. Pass
`--bounded` to get the old finite behavior where it
exits after all work items are completed or failed.

## What Happens

1. Egregore parses the prompt or fetches issues.
2. Work items are written to `.egregore/manifest.json`.
3. Each item moves through the pipeline: plan, implement,
   test, PR.
4. On crash or rate limit, the watchdog relaunches the
   session automatically.
5. When all current items are completed or failed, the
   egregore scans for new work:
   - Fetches open GitHub issues with the configured label.
   - Scans for untracked `TODO`/`FIXME` comments.
   - Runs the test suite and checks for new failures.
   - Checks for open PRs needing review fixes.
6. New work items are added to the manifest and the
   cycle repeats from step 3.
7. This loop continues indefinitely until you run
   `/egregore:dismiss` to stop it.

In `--bounded` mode, step 5-7 are skipped. The egregore
posts a completion summary and exits after step 4.

## Stopping the Egregore

The egregore does not stop on its own. To shut it down:

```
/egregore:dismiss
```

This pauses all active work items, saves state, and
removes the pidfile. You can resume later with another
`/egregore:summon`.

## Progress Monitoring (2.1.71+)

While the egregore runs, you can monitor progress with
`/loop`:

```
/loop 5m /egregore:status
```

This emits a status summary every 5 minutes between turns.
The egregore also schedules this automatically on startup.

## See Also

- `/egregore:status` to check progress.
- `/egregore:dismiss` to stop gracefully.
- `/egregore:install-watchdog` to enable auto-relaunch.
