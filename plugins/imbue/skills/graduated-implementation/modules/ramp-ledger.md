# Ramp Ledger

A ramp that leaves no trace cannot be audited, and an unauditable
demonstration is the Duolingo failure waiting to happen: a cheap
signal nobody checks. The ramp ledger records each notch climbed so
the demonstration that earned it can be reviewed later, by a different
person than the one who produced the increment. This is the four-eyes
audit trail applied to the ambition ramp.

## What a ledger entry records

One entry per rung climbed, appended when a ramp token is minted:

| Field | Meaning |
|-------|---------|
| `increment` | Which slice this is (1, 2, 3, ...) for the feature. |
| `rung_before` / `rung_after` | The rung width before and after the notch. |
| `stakes` | The risk tier (GREEN/YELLOW/RED/CRITICAL) that set the gate. |
| `gate` | `evidence` (low stakes) or `explanation` (high stakes). |
| `demonstration` | The recorded proof: for an evidence gate, the test command and its result plus the tradeoff entry; for an explanation gate, the novel question asked and a one-line summary of the human's unaided answer. |
| `outcome` | `ramped`, `held` (understanding below the band), or `demoted` (a regression or a failed explanation dropped the rung). |

## Where it lives

The `guard_scope_ramp.py` hook appends one JSON line per notch to
`.imbue/ramp-ledger.jsonl` whenever a token widens the rung, capturing
the increment number, the rung before and after, the risk tier, the
gate, and a timestamp. That file is gitignored and session-local: it
is the raw trail, not the permanent record.

The durable home is the project decision journal,
`leyline:decision-journal`. A ramp entry is a decision with a
consequence (the wider rung), so it belongs alongside the tradeoff
entries that minted it, not in a separate store. Promote each
`.imbue/ramp-ledger.jsonl` line into the decision journal with the
`demonstration` text filled in (the hook records the structural fields;
the human records what was actually asked and answered). The
`.imbue/ramp-ok` token is ephemeral; the journal entry is permanent.

## Why the demonstration text is the point

The ledger field that matters is `demonstration`, and for high-stakes
rungs it must be the answer to a *novel* question about the actual
change, not a recap the agent supplied. A reviewer reading the ledger
later should be able to tell whether the human understood the
increment or rubber-stamped it. If the recorded demonstration could
have been written without reading the diff, the gate was gamed and the
entry is evidence of it. Record what was actually asked and actually
answered, in the human's words.

## What the ledger is not

It is not a burndown chart or a velocity metric. Counting rungs
climbed and optimizing for more of them per hour reproduces the exact
Goodhart failure the gate exists to prevent: the streak that decouples
from skill. The ledger is read backward, to audit that each ramp was
earned, not forward, to set a pace.
