# Temporal Awareness

A model has no internal sense of elapsed time. Two messages feel equally
adjacent whether five seconds or five weeks separated them. On resume,
that produces units acted on as though they were written moments ago.

## Compute the Gap, Never Guess It

The previous session's `ended_at` is stored. Read it and subtract:

```python
from memory_palace.session_history import SessionHistoryManager

recent = SessionHistoryManager().get_recent_sessions(count=1)
last_ended = recent[0].ended_at if recent else None
```

State the elapsed time before acting on retrieved units. When no prior
session is found, say that rather than assuming continuity.

The failure this guards is specific. Without an explicit reading, the
only time reference available is whatever was seen at session start, and
a model asked for a timestamp will **fabricate** one from that stale
anchor rather than report that it does not know. Fabricated dates then
enter the record as though they were observed, and every later gap
computed against them is wrong too.

## What Survives Which Gap

| Elapsed | `state` | `open-thread` | `decision` | `finding` |
|---------|---------|---------------|-----------|-----------|
| Under a day | trust | trust | trust | trust |
| A few days | verify | trust | trust | trust |
| Weeks | discard | verify | verify | trust |
| Months | discard | verify | verify | trust |

"Verify" means check the claim against the repository as it stands now
before relying on it. "Discard" means the unit describes a status that
the intervening work has almost certainly invalidated.

## The Event Signal Beats Elapsed Time

Elapsed time is a proxy. What actually matters is whether the world the
unit describes has changed. A unit naming a file modified since the unit
was written is suspect at any age, and a unit whose subject nobody has
touched stays good far longer than its curve suggests.

A unit that declared `files` carries a content fingerprint of each one
in `file_digests`, taken at capture time. Recall recomputes those
digests and compares. When a dependency no longer matches, the unit is
surfaced with a `STALE SIGNAL` line naming the paths that moved.

Three outcomes, and the third matters as much as the others:

| Outcome | Meaning |
|---------|---------|
| unchanged | The bytes match; elapsed time is the only concern left |
| changed | A dependency moved; verify before relying on the claim |
| unknown | The path could not be read, or predates fingerprinting |

`unknown` is deliberately distinct from `unchanged`. Reporting a
dependency nobody could inspect as unchanged is what would make the
check worse than not having one.

## Correction Is the Second Event Signal

A unit that declares no files still has one event that can invalidate
it: being corrected. Recall keeps only the newest unit for each
`(thread, type)` pair across every session it scans, so writing a new
unit on a thread retires the old one without anyone marking it stale.

The older unit is dropped rather than flagged, unlike a moved
dependency. A digest can be tripped by reformatting, so that signal
warns and lets the reader judge. A correction is not fallible in the
same way, because the newer unit is the replacement by construction.

This is why reusing a `Thread` label is load-bearing rather than
cosmetic. A correction filed under a fresh label does not supersede
anything, and both claims then compete on keyword overlap.

The signal is a fingerprint rather than a timestamp because timestamps
lie in both directions. Filesystem mtime is rewritten by clone,
checkout, and rebase, so it reports change where there was none. Git
commit time is blind to uncommitted work. Comparing bytes answers the
question directly.

A moved dependency **flags** the unit; it never removes it. The reader
still needs to know the topic has history, and hiding a unit would
conceal both the history and the fact that the ground shifted.

Where both signals exist, prefer the event. Treat the decay weight as
the fallback for when nothing better is known.
