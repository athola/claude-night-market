---
name: night-market-model-and-harness-updates
description: 'Sweep plugins, skills, agents, commands, and hooks after a model release or Claude Code version bump. Use when upstream ships. Do not use for routine edits; use night-market-change-control.'
---

# Night Market Model and Harness Updates

When Anthropic ships a model or Claude Code ships a version, the pins
scattered through this repo rot silently. This skill runs the sweep that
finds the rot, researches what actually changed, applies the updates,
and records where upstream stood so the next run reports only the new
delta.

The watermark is the point. Without it every audit restarts from zero
and re-derives the same answer by hand. `.claude/upstream-baseline.json`
holds the last recorded upstream state, and each run diffs against it.

## When to run

| Trigger | Signal |
|---------|--------|
| Model release | A tier or model ID ships that the ledger does not record |
| Harness release | `claude --version` differs from the ledger |
| Scheduled check | Monthly, to catch a release nobody noticed |

## The five steps

Run them in order. Each one gates the next.

```bash
# 1. Detect. Deterministic, no model in the loop.
python3 scripts/check_upstream_drift.py

# 2. Research what changed (only when step 1 reports drift).
#    Release notes and model cards are mandatory sources.

# 3. Map findings onto asset classes.

# 4. Sweep the implicated classes.

# 5. Prove, then record the new watermark.
python3 scripts/check_upstream_drift.py && \
python3 scripts/check_agent_model_matrix.py
```

Step 5 runs before the ledger is written, never after. Recording a
migration that has not passed its proof is the failure the ledger exists
to prevent.

## What the detector proves and what it cannot

Harness drift is fully deterministic: the installed binary reports its
own version. Model drift is not. No local command enumerates the current
roster, so the ledger holds the last known roster and research
establishes the current one. The skill states this split rather than
pretending both halves are automatic.

The detector reports four classes:

| Class | Meaning |
|-------|---------|
| `harness` | Installed version differs from the ledger |
| `vocabulary` | A gate's frozen set omits a value the ledger records |
| `dated_ids` | Dated model IDs above the recorded ratchet |
| `unknown_tier` | Frontmatter names a tier absent from the roster |

The `vocabulary` class is the one that earns this skill. `VALID_MODELS`
in `scripts/check_agent_model_matrix.py` is a hard gate that rejects any
agent pinning an unlisted tier. When Fable shipped and that set was not
widened, the guard whose job was to prevent model rot had itself rotted,
and no agent in the repo could pin the new tier. The detector now fails
on that condition instead of waiting for someone to trip over it.

## Modules

Load only what the run needs.

| Module | Load when |
|--------|-----------|
| `modules/drift-detection.md` | Always, at step 1 |
| `modules/research-protocol.md` | Step 1 reported drift |
| `modules/asset-sweep.md` | Research produced findings to apply |
| `modules/verification.md` | Before writing the ledger |

## Guardrails

- Widen vocabularies, never narrow them. Removing an accepted value
  breaks agents that currently pass.
- Agent frontmatter pins tier aliases, never dated model IDs.
  `check_agent_model_matrix.py` enforces this and the policy stands.
  A new tier widens the vocabulary. It does not reverse the rule.
- The `dated_ids` ratchet may fall and may hold. Raising it needs a
  reason recorded in the migration report.
- External captures under `data/staging/` are other people's text.
  The detector skips them and so does the sweep.

## Exit Criteria

- [ ] `python3 scripts/check_upstream_drift.py` exits `0`.
- [ ] `python3 scripts/check_agent_model_matrix.py` exits `0`.
- [ ] `uv run pytest tests/unit/test_check_upstream_drift.py` passes.
- [ ] Every research claim applied carries a source URL, and release
      notes plus the model card were both consulted.
- [ ] A migration report exists under
      `docs/migrations/`. The directory is gitignored, so the report is
      a local working artifact. Route durable content out of it before
      you finish: findings to `docs/knowledge-corpus/`, open items to
      `docs/backlog/queue.md`, state to the ledger.
- [ ] `.claude/upstream-baseline.json` records the new harness version,
      model roster, and `last_migration`, with the previous entry
      appended to `history`.
- [ ] Any asset class the research implicated was either updated or
      recorded in the report as deliberately skipped.
