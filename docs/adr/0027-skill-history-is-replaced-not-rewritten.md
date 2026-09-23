# ADR-0027: Skill History Is Replaced, Not Rewritten

**Date**: 2026-09-23
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0024 (tome channel cards, whose research workflow
produced the recency findings below)

## Context

The concurrent splay tree paper does not fit how skills are looked up
here. The concurrency problem it studies does show up here, though:
parallel hooks share one JSON file, and that file could lose every
skill's history.

Aksenov, van Bevern and Shilkin, "Concurrent Splay-Based Tree" (arXiv
2606.28889, 2026), rotate an accessed node only when its depth exceeds
`B·log(m/ac(x))` and stop at `A·log(m/ac(x))`, where `m` counts all
accesses and `ac(x)` counts accesses to `x`. The tuned constants are
A=0.5-0.7 and B=2-2.5. Counters are exact 64-bit integers or 6-bit
Morris counters, which increment with probability `2^-r` and estimate
`2^r`. Static optimality is proved for the sequential read-only tree.
On top of Bronson's concurrent AVL tree the design wins at 95/5 and
99/1 skew and loses at 90/10, uniform and Zipf alpha=1.

The question was how to retrieve recently and frequently used tools,
hooks and workflows. The access data that exists is the skill
invocation log under `~/.claude/skills/logs`: 352 events over 49
skills. The top skill takes 20% of calls, the top five 49% and the top
ten 70%. Entropy is 4.48 bits against 5.61 for a uniform spread. That
skew is below the level where the paper wins, and 49 keys fit one
dictionary with constant-time lookup. No tree has a depth to reduce.

A `tome:research` pass (run as a single agent, not the four-channel
fan-out) reached the same verdict from the literature. Count-min
sketches, W-TinyLFU, ARC and Morris counters exist for memory or scale
limits that 49 to 500 keys never reach. An exact count per key is free
at this size, and a Morris counter only adds variance to counts of 10
to 70.

While mapping who reads these logs, the retrieval path turned out to
have a race. `skill_execution_logger.py` and `homeostatic_monitor.py`
both match `PostToolUse:Skill`, and Claude Code runs matching hooks in
parallel. The logger truncated `.history.json` and then wrote it. A
reader could parse an empty or half-written file. A writer that did so
logged the decode error, continued from an empty dictionary and saved
it, which erased every other skill.

Evidence, from four writer processes of 200 evaluations each and one
reader of 4000 parses over a 49-skill seed:

| Run | Seeded skills kept | Updates kept | Torn reads |
|-----|-------------------:|-------------:|-----------:|
| [E1] before | 0/49 | 6/800 | 234/4000 |
| [E2] after | 49/49 | 800/800 | 0/4000 |

This is synthetic stress. The live file holds 353 accuracies against
352 logged events, so no wipe has happened there yet.

## Decision

`ContinualEvaluator._save_history` writes to a temp file in the same
directory and renames it over `.history.json` with `os.replace`. A
process that opens the file reads either the old version or the new one.

`evaluate_iteration` takes an exclusive `fcntl.flock` on
`.history.json.lock`, reloads, appends and saves under it. Parallel
subagents are concurrent writers, and two writers that load one
snapshot drop one execution. With the rename and no lock, the test
kept 5 of 25 updates per writer.

`fcntl` is POSIX-only. No workflow or hook in this repository targets
Windows, and `leyline/quota_tracker.py` already imports it unguarded.

## Recorded, not built

Nothing reads recency or frequency for skills today, so none of the
following is code yet. The first consumer that needs it should start
here.

- Keep an exact count and a last-seen timestamp per key, scored in the
  zoxide style with decay. Do not use a tree, a sketch or an
  approximate counter below a few thousand keys.
- If a small hot set is ever shown to users, use the paper's two
  thresholds as a hysteresis band. Enter above the high score and leave
  only below the low one, so skills ranked near the cutoff stay put.
  Segmented LRU uses the same split between probation and protection.
- For the last K events, read the JSONL file backwards in blocks from
  the end. For events since a time, open only the date-named files on
  or after that date.

## Consequences

- A torn read no longer erases history, and concurrent executions are
  all counted. `tests/hooks/test_history_concurrency.py` fails when
  either the rename or the lock is removed.
- Each skill execution now waits on a lock. On a copy of the live
  history, `evaluate_iteration` took 0.63 ms median and 0.77 ms at p95
  over 200 calls, lock included.
- `.history.json` still grows by one list entry per execution. At 353
  entries it is 5 KB, and growth stays unaddressed until a size is
  shown to cost hook latency.
- A file that is corrupt for reasons other than a race is still loaded
  as empty and saved over. That is a separate decision.
