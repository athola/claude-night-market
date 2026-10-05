# P1: shadow observation, then opt-in on a bounded item

## P1a: shadow read (no behavior change)

Verdicts are recorded in the manifest even with the flag off (the
`egregore:quality-gate` skill records every verdict as a decision entry
`{"step": ..., "chose": ..., "why": ...}`). So the flag-off world
already contains the shadow data: items that advanced to `completed`
despite a `fix-required` verdict. Count them in any repo where egregore
has run:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

path = Path(".egregore/manifest.json")
if not path.exists():
    print(json.dumps({"error": "no manifest; egregore has not run here"}))
    raise SystemExit(0)
data = json.loads(path.read_text())
items = data.get("work_items") or data.get("items") or []
flagged = [
    {"id": i.get("id"), "status": i.get("status")}
    for i in items
    if any(d.get("chose") == "fix-required" for d in i.get("decisions", []))
]
print(json.dumps(
    {"total_items": len(items), "items_with_fix_required": flagged},
    indent=2,
))
EOF
```

Expected: a JSON summary. Any entry with `"status": "completed"` in
`items_with_fix_required` is a shadow-mode false completion: the exact
event the gate exists to prevent. Record the count as the P2 baseline.

Branch: no manifest exists in this repo's root (egregore is typically
summoned in target repos, and `.egregore/` state lives where it ran).
If you have no manifest anywhere, skip to P1b and generate one.

## P1b: enable the gate on a bounded run

The opt-in path is hand-editing the config JSON. This exact shape is
what `test_completion_integrity_loads_from_raw_json` covers:
unspecified pipeline fields keep their defaults.

```bash
mkdir -p .egregore
cat > .egregore/config.json <<'EOF'
{"pipeline": {"completion_integrity": true}}
EOF
```

Warning: if `.egregore/config.json` already exists, edit the existing
`pipeline` object instead of overwriting the file, or you will reset
overseer and alert settings to defaults.

Then run a small, disposable work item in bounded mode (bounded mode
stops when the time window expires, so the loop cannot run away while
you observe):

```
/egregore:summon "<one small, well-specified task>" --bounded --window 5h
```

Before summoning, read "Stopping and relaunch machinery" at the end
of this section: bounded mode expires on its own, but the watchdog
and SessionStart hook can still resurrect the loop.

What it logs and where:

- `.egregore/manifest.json`: per-item `status` (`active`, `paused`,
  `pending` count as unfinished for the Stop hook, while `completed`
  and `failed` are terminal), `attempts`, `max_attempts` (default 3),
  and the `decisions` array holding each quality verdict.
- `.egregore/relaunch-prompt.md`: the re-injection prompt the egregore
  Stop hook (`plugins/egregore/hooks/stop_hook.py`) uses when it blocks
  an exit with active work remaining.
- Overseer alerts per `.egregore/config.json` (`pipeline_failure`
  fires when an item exhausts attempts).

Expected observations with the flag on, per the documented contract in
`plugins/egregore/skills/quality-gate/SKILL.md` and
`agents/orchestrator.md`:

1. A `fix-required` verdict routes to failure handling: the item
   retries in place, and after `max_attempts` it is marked `failed`
   with the overseer alerted. It is never silently `completed`.
2. Merge is held for human review regardless of `auto_merge`: the PR
   is prepared but left open.
3. The loop itself does not halt: it continues with the next active
   item.

Gate P1 branches:

- An item reaches `completed` with an unresolved `fix-required`
  decision while the flag is true: the orchestrator ignored its
  instructions. This confirms the prompt-level enforcement gap in the
  problem statement. Record the manifest as evidence and carry it into
  P3. The finding argues for solution (a) or (b) in the SKILL.md
  menu, which move enforcement out of the prompt.
- The item loops in retry forever: `max_attempts` is not being
  incremented. That is an orchestrator bug, not a gate result. File it
  with the manifest attached.

#### Stopping and relaunch machinery

Know the stop path before you summon. The loop runs indefinitely by
default and never stops on its own
(`plugins/egregore/commands/dismiss.md`).

- `/egregore:dismiss` is the only sanctioned stop. It pauses all
  active items in the manifest, cancels the orchestrator's cron jobs,
  and removes the pidfile (`.egregore/pid`).
- The pidfile is what the watchdog daemon polls. If
  `/egregore:install-watchdog` has run on the machine,
  `plugins/egregore/scripts/watchdog.sh` fires every 5 minutes via
  launchd or systemd and relaunches a session whenever the manifest
  has unfinished work, the budget allows it, and no pidfile marks a
  live session. Killing a session without dismissing therefore gets
  you silently relaunched sessions.
- A SessionStart hook (matcher `startup|resume` in
  `plugins/egregore/hooks/hooks.json`) auto-resumes orchestration in
  new and resumed sessions while egregore state is active. Closing
  the terminal is not a stop either.
- `.egregore/budget.json` bounds spend. The watchdog checks it before
  relaunching, so an exhausted budget halts relaunches even without a
  dismiss.
