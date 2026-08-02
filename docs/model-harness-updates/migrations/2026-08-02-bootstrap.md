# Migration 2026-08-02-bootstrap

**Trigger**: bootstrap (first run, establishing the watermark)
**Harness**: Claude Code 2.1.220
**Branch**: `hotfixes-1.9.18`

## Delta

| Field | From | To |
|-------|------|----|
| `harness.version` | (unrecorded) | `2.1.220` |
| `models.tiers` | (unrecorded) | `haiku`, `sonnet`, `opus`, `fable` |
| `vocabularies.effort_levels` | (unrecorded) | `low`, `medium`, `high`, `xhigh`, `max` |
| `ratchets.dated_ids_backlog` | (unrecorded) | `123` |

No prior ledger existed, so this run establishes the baseline rather
than diffing against one. Every later run reports only what moved since
this record.

## Findings

The bootstrap run surfaced drift that had accumulated with no watermark
to catch it. Sources are the harness environment declaration and the
tool schemas the running harness exposes, both read directly rather
than recalled.

| Finding | Source | Classes implicated |
|---------|--------|--------------------|
| `fable` is a shipped tier (`claude-fable-5`) absent from the gate vocabulary | Harness model roster declaration | Gate vocabularies, docs of record |
| `xhigh` and `max` are shipped effort levels absent from the gate vocabulary | `Workflow` and `ReportFindings` tool schemas | Gate vocabularies, docs of record |
| Current model IDs are `claude-fable-5`, `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001` | Harness model roster declaration | Ledger only |

The first finding is the sharpest. `scripts/check_agent_model_matrix.py`
is a hard gate that rejects any agent pinning a tier outside
`VALID_MODELS`. Fable shipped and that set was never widened, so no
agent in this repo could pin it. The guard whose purpose was to prevent
model rot had itself rotted, and nothing was watching the watcher.

## Applied

| Asset class | Change |
|-------------|--------|
| Gate vocabularies | `VALID_MODELS` gains `fable`; `VALID_EFFORTS` gains `xhigh` and `max` |
| Docs of record | `docs/agent-model-matrix.md` gains a Creative tier row, the effort-level range, and a pointer to this workflow |

Both changes widen only. No previously accepted value was removed, so
no agent that passed before can fail now. All 56 agents still pass.

## Skipped

| Class | Reason |
|-------|--------|
| Agent frontmatter | No agent needs reassignment. Making `fable` available is separate from deciding an agent belongs in it, and that judgment gets its own review. |
| The 123 dated model IDs | Most live in docs, tests, and historical notes where a dated ID is correct. Capped by ratchet rather than rewritten. Fixing them is a follow-up sweep with its own review. |
| Hooks, commands, plugin skills | No finding implicated them. Recorded here so the next run does not re-derive this. |

## Ratchet note

`ratchets.dated_ids_backlog` was set to `122`, the count measured
against the tree before this work, then raised to `123`.

The extra entry is `modules/drift-detection.md`, which documents the
`dated_ids` class and cites `claude-opus-4-6` as an example of what it
catches. Documentation about dated IDs necessarily contains one. The
ratchet counted it, which is the ratchet working: it detected a real
increase and forced this note rather than absorbing the change
silently.

## Evidence

```
$ python3 scripts/check_upstream_drift.py     # before the sweep
upstream drift: 3 finding(s)
  vocabulary (2)
    - VALID_MODELS cannot express model tier(s) fable recorded in the ledger
    - VALID_EFFORTS cannot express effort level(s) max, xhigh recorded in the ledger

$ python3 scripts/check_upstream_drift.py     # after the sweep
upstream drift: none
exit: 0

$ python3 scripts/check_agent_model_matrix.py
All 56 agents pin an explicit model and effort, 202 skills carry no
dated model IDs, and the matrix roster matches disk.
exit: 0

$ uv run pytest tests/unit/test_check_upstream_drift.py -q
42 passed

$ uv run pytest tests/scripts/test_check_agent_model_matrix.py -q
50 passed
```

## Follow-ups

- Reduce the dated-ID backlog below 123 and lower the ratchet in the
  same change.
- Decide whether any existing agent belongs in the Creative tier now
  that `fable` is available.
