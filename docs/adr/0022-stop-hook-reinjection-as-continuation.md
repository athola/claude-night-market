# ADR-0022: The Autonomous Loop Continues by Riding the Stop Hook

**Date**: 2026-08-23
**Status**: Accepted, with a named open problem
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0007 (records where findings like this one live);
`night-market-research-frontier` problem 6

## Context

Egregore runs a development pipeline without a human turn between
steps. Something has to make the session take another turn after it
decides it is finished. In this ecosystem that something is the Stop
hook: `plugins/egregore/hooks/stop_hook.py` returns
`{"decision": "block", "reason": "..."}`, and the harness feeds the
reason back as the next turn's instruction. That is the entire loop.
Remove it and egregore stops after one turn.

The mechanism is not documented upstream as a continuation primitive.
The hooks reference describes a Stop hook as a gate on whether the
session may stop, and blocking is described as a way to make Claude
continue, not as the supported way to build a work loop. Nothing
upstream promises the reason field will keep being treated as the next
instruction, or that a blocked stop will keep costing one ordinary
turn. This is a claim about the absence of an endorsement, checked
against Claude Code 2.1.241 on 2026-08-23. Re-verify it against the
hooks reference before relying on it, and see the volatile-claims
table below.

Prior art in the same ecosystem rides the same mechanism.
ralph-wiggum's `hooks/stop-hook.sh` emits the same block-and-reason
JSON, and bounds it with an iteration counter read from its state
file: `max_iterations`, where 0 means run forever. So the mechanism is
load-bearing for at least two plugins here, and one of them had already
concluded it needs a bound.

## What riding it cost

Dogfooding the watchdog against a real project in tmux measured three
defects in the resume path, all of them invisible to the test suite:

| Defect | Measured | Fixed in |
|---|---|---|
| Default text output swallowed when the Stop hook blocks | log received 1 byte | `e8f7ca78` |
| `nohup` leaves stdin attached to nothing | every hook stalled 3s and printed a warning into stdout, corrupting the JSON | `e8f7ca78` |
| Stop hook blocked every stop, with no bound | 10 turns and roughly $0.70 for a one-word prompt, on Opus | `9f31a878` |

The third is the one this record is about. Blocking was conditioned on
a static fact, that the manifest holds active work, so a session with
no way to advance the pipeline was handed the prompt back on every
stop until something else intervened.

## Alternatives considered

| Mechanism | Why it does not replace the Stop hook |
|---|---|
| `/loop` | Session-scoped. It schedules prompts inside a live session and dies with it, and it fires on a clock rather than when a turn ends |
| `CronCreate` | Session-scoped by its own description in 2.1.241: jobs "live only in this Claude session", nothing is written to disk, `durable` has no effect, and jobs fire only while the REPL is idle. Recorded in `7f5e1b73` |
| Cloud Routines | Minimum interval one hour, and gated on claude.ai subscription auth. Too coarse for a step loop, and unavailable headless |
| The watchdog (`scripts/watchdog.sh`) | Covers the dead-session case only. It relaunches a session, and cannot make a live session take another turn |
| `claude --bg` supervisor | The one real candidate. It would replace `watchdog.sh` wholesale, which is a larger decision than this record settles. Left open |
| `stop_hook_active` alone | Caps continuation at exactly one turn, which removes the autonomy the loop exists to provide |

## Decision

Keep riding the Stop hook, and bound what it can cost.

`9f31a878` bounds it by stall detection. The hook hashes
`manifest.json` and counts consecutive blocks in
`.egregore/stop-hook-state.json`. A changed hash is progress and
resets the count, as does a new `session_id`, which is what a watchdog
relaunch looks like. At `EGREGORE_STOP_MAX_STALLS` blocks, default 3,
the hook approves the stop and stays released until the hash changes.
State that cannot be written approves the stop as well, because an
unbounded block is the failure being bounded and a released stop is
recoverable.

Both bounds in this ecosystem now count something, and they count
different things. ralph-wiggum's counter caps total turns. Egregore's
caps unproductive turns, which is why it resets on progress and why a
long-running pipeline is not penalized for taking many turns.

The reliance itself is recorded as an open problem rather than
sanctioned. This decision prices the ride. It does not make the
mechanism supported.

## Consequences

The loop keeps working, and its worst case is now three turns per
session instead of an open-ended burn.

Three things stay true and should not be discovered again the hard
way:

- **The product is not bounded.** A watchdog tick that finds a dead
  session relaunches into a fresh stall budget, so an item stuck
  without manifest writes costs about three turns per relaunch for as
  long as the timer runs. Bounding one relaunch does not bound their
  product. The escape hatch is
  `systemctl --user disable --now egregore-watchdog.timer`.
- **Progress is defined as manifest bytes.** A session that writes the
  manifest every turn without advancing the pipeline still loops.
  Tightening that means coupling the hook to the manifest schema, and
  it was not the measured failure, where the stuck session wrote
  nothing at all.
- **The dependency is invisible until it breaks.** No test in this
  repository exercises the harness end of the mechanism, because no
  test can: it depends on how the running harness treats a blocked
  stop. `plugins/egregore/tests/test_night_run_e2e.py` covers the
  driver, not the re-injection. The first symptom of an upstream
  change would be a loop that stops after one turn, or one that stops
  costing a turn per block.

## Volatile claims and how to re-verify

| Claim | Checked | Re-verify with |
|---|---|---|
| Stop-hook re-injection is not endorsed upstream as a continuation mechanism | 2026-08-23, CLI 2.1.241 | The hooks reference in the Claude Code docs, section on Stop hooks and the `decision`/`reason` fields |
| `CronCreate` jobs live only in the current session and `durable` has no effect | 2026-08-23, CLI 2.1.241 | The tool's own description in the running CLI |
| Cloud Routines are minimum one hour and need claude.ai subscription auth | 2026-08 research pass | Routines documentation |
| ralph-wiggum bounds by iteration count, 0 meaning infinite | 2026-08-23, plugin 1.0.0 | `rg -n "MAX_ITERATIONS" ~/.claude/plugins/cache/claude-code-plugins/ralph-wiggum/1.0.0/hooks/stop-hook.sh` |
| Egregore's bound is stall-based, default 3 | 2026-08-23 | `rg -n "DEFAULT_MAX_STALLS" plugins/egregore/hooks/stop_hook.py` |

## When this record closes

Any one of these retires it:

- Upstream documents a continuation primitive that survives a session
  ending, at an interval a step loop can use. Egregore moves to it and
  the Stop hook goes back to gating stops.
- The `claude --bg` supervisor is adopted and carries continuation, so
  the night-run E2E passes with the egregore Stop hook disabled.
- Upstream changes the semantics and the loop breaks, in which case
  this record is the starting point rather than a rediscovery.
