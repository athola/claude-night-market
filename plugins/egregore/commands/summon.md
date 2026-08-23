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

Runs `Skill(egregore:summon)`, which with its five modules carries the
orchestration loop, the manifest mode, the pipeline mapping, the
context-overflow and token-budget protocols, the progress monitoring
and the failure handling. The usage, options and the stop path below
belong to the command.

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

Bounded mode (stops when time window expires):

```
/egregore:summon --bounded --window 2d --issues 42,43,44
```

## Options

| Option           | Default | Description                  |
|------------------|---------|------------------------------|
| `<prompt>`       | none    | Free-text work description   |
| `--window`       | `5h`    | Time window (e.g. 5h, 7d)   |
| `--bounded`      | false   | Stop when time window expires|
| `--issues`       | none    | Comma-separated issue numbers|
| `--issues-label` | none    | GitHub label to pull issues  |

The egregore runs indefinitely by default. Pass
`--bounded` to set a hard time limit. In both modes,
the egregore scans for new work after completing all
current items. The only difference is that bounded mode
exits when the time window expires.

## Stopping the Egregore

The egregore does not stop on its own. To shut it down:

```
/egregore:dismiss
```

This pauses all active work items, saves state, and
removes the pidfile. You can resume later with another
`/egregore:summon`.

## See Also

- `/egregore:status` to check progress.
- `/egregore:dismiss` to stop gracefully.
- `/egregore:install-watchdog` to enable auto-relaunch.
