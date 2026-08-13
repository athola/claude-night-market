# Verification and Re-baseline

Step 5. The sweep is not done when the edits land. It is done when the
proofs pass and the new watermark is recorded, in that order.

Writing the ledger before the proof passes records a migration that
never happened, which is the exact failure the ledger exists to
prevent. A wrong watermark is worse than no watermark: the next run
diffs against a fiction and reports a delta that does not exist.

## Proof sequence

Run these in order. A failure at any step sends the work back to the
sweep, never forward to the ledger.

```bash
# 1. No drift remains
python3 scripts/check_upstream_drift.py

# 2. The matrix gate accepts the tree
python3 scripts/check_agent_model_matrix.py

# 3. The detector's own tests still hold
uv run pytest tests/unit/test_check_upstream_drift.py -q

# 4. The gate's tests still hold, including the ledger binding
uv run pytest tests/scripts/test_check_agent_model_matrix.py -q

# 5. The skill's contract holds
uv run pytest tests/unit/skills/ -q

# 6. Every class the sweep touched passes its owner check
#    (plugin suites for hooks, markdown gates for docs)
```

Capture the output of each. The migration report cites them.

## The ledger binding

`tests/scripts/test_check_agent_model_matrix.py` asserts that every
tier and effort level in the ledger is accepted by the gate. That
binding is what makes future drift loud:

- A model release widens the ledger.
- The binding test fails immediately.
- The gate is widened to match.
- The test passes and the sweep proceeds.

Do not weaken this test to make a run pass. A failing binding means the
ledger and the gate disagree, and one of them is wrong.

## The migration report

Every run writes one, including a run that found no drift. Path:

```
docs/migrations/<date>-<slug>.md
```

Required contents:

| Section | Holds |
|---------|-------|
| Trigger | Model release, harness update, or scheduled check |
| Delta | Ledger `from` and `to`, stated explicitly |
| Findings | Each research claim with its source URL |
| Applied | Which asset classes changed, and the diff size |
| Skipped | Classes deliberately not touched, with the reason |
| Evidence | Command output proving each gate passed |

The **Skipped** section carries more weight than it looks like it
should. A class that was considered and consciously left alone is a
decision. A class nobody thought about is a gap. The report is the only
place that distinguishes them.

## Recording the new watermark

`record_migration` in `scripts/check_upstream_drift.py` handles the
mechanics: it appends the previous `last_migration` to `history` and
writes the new one.

**Snapshot the starting state before mutating the ledger.** This is the
step that is easy to skip and expensive to get wrong.

```python
import sys
sys.path.insert(0, "scripts")
import check_upstream_drift as cud

path = ".claude/upstream-baseline.json"
ledger = cud.load_ledger(path)

# Capture where this run started, before any mutation.
from_state = cud.snapshot_state(ledger)

ledger["harness"]["version"] = "<new version>"
ledger["harness"]["recorded_at"] = "<date>"
# widen models.tiers / models.ids / vocabularies as the sweep required

updated = cud.record_migration(
    ledger,
    {
        "id": "<date>-<slug>",
        "trigger": "model-release",
        "assets_changed": <count>,
        "report": "docs/migrations/<date>-<slug>.md",
    },
    from_state=from_state,
)
cud.write_ledger(path, updated)
```

Omitting `from_state` records `from` equal to `to`. That is right for a
scheduled check that changed nothing and wrong for everything else.

An earlier version of this function derived `from` from the previous
migration's `to` instead. It recorded a 140-version harness gap as
`2.1.220` to `2.1.220`, because the previous record had over-claimed
and nothing cross-checked it against the ledger's own state. A
watermark that reports a no-op for real work is worse than no watermark,
since the next run trusts it.

## Ordering when the harness moved

For a harness bump there is no code change that makes the old and new
version numbers equal. Updating the ledger **is** the remediation for
the `harness` drift class, once the sweep has handled whatever the
changelog implicated. So the order for a harness run is:

1. Sweep the assets the release notes implicated.
2. Prove those: gates and tests, everything except the drift check.
3. Update the ledger and record the migration.
4. Run the drift check last. It must exit `0`.

The drift check still runs before anything is considered done. It just
cannot pass until the watermark moves, which is the one case where step
1 of the five-step sequence resolves at the end rather than the start.

Then run the detector once more. It must exit `0` against the ledger it
just wrote. A ledger that fails its own detector is malformed.

## A clean run still updates the ledger

When the detector exits `0` on entry, the run still records a
migration with trigger `scheduled-check` and `assets_changed: 0`. This
is what makes "we checked and nothing had moved" distinguishable from
"nobody has checked since March". Without it, a quiet ledger is
ambiguous, and ambiguity here defaults to the optimistic reading.
