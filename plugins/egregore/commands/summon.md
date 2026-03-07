---
name: summon
description: >-
  Summon the egregore to autonomously process work items
  through the full development lifecycle
usage: >-
  /egregore:summon "<prompt>" [--window 5h|7d]
  [--indefinite] [--issues N,N] [--issues-label LABEL]
---

# summon

Launch the egregore to autonomously process work items
through planning, implementation, testing, and PR
creation.

## When To Use

- You have one or more issues or tasks to process
  without manual intervention.
- You want to run a multi-hour or multi-day development
  pipeline overnight or over a weekend.
- You want the agent to self-recover from crashes and
  rate limits via the watchdog.

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

Indefinite mode (runs until dismissed):

```
/egregore:summon --indefinite --issues-label "egregore"
```

## Options

| Option           | Default | Description                  |
|------------------|---------|------------------------------|
| `<prompt>`       | none    | Free-text work description   |
| `--window`       | `5h`    | Time window (e.g. 5h, 7d)   |
| `--indefinite`   | false   | Run until dismissed          |
| `--issues`       | none    | Comma-separated issue numbers|
| `--issues-label` | none    | GitHub label to pull issues  |

## What Happens

1. Egregore parses the prompt or fetches issues.
2. Work items are written to `.egregore/manifest.json`.
3. Each item moves through the pipeline: plan, implement,
   test, PR.
4. On crash or rate limit, the watchdog relaunches the
   session automatically.
5. On completion, a summary is posted and the manifest
   is marked done.

## See Also

- `/egregore:status` to check progress.
- `/egregore:dismiss` to stop gracefully.
- `/egregore:install-watchdog` to enable auto-relaunch.
