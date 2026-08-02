# Model and Harness Update Workflow: Specification

**Date**: 2026-08-02
**Status**: Approved for execution
**Mission**: `model-harness-updates` (standard: specify, plan, execute)
**Branch**: `hotfixes-1.9.18`

## Problem

This repo pins model tiers, effort levels, and harness features across
24 plugins, 208 plugin skills, 163 commands, 56 agents, 711 hook files,
15 local skills, and 9 rules. When Anthropic ships a model or Claude
Code ships a version, those pins rot silently. Nothing in the repo
records what upstream looked like the last time we adjusted, so every
audit restarts from zero and re-derives the same delta by hand.

The rot is measured, not hypothetical. As of this specification:

| Evidence | Value |
|----------|-------|
| Files referencing a model name or ID | 141 |
| Files with dated IDs outside gated surfaces | 48 |
| References to `claude-opus-5` (shipped) | 0 |
| References to `claude-fable-5` (shipped) | 0 |
| `VALID_MODELS` in `check_agent_model_matrix.py` | `{haiku, sonnet, opus}` |
| Shipped tiers the gate cannot express | `fable` |
| `VALID_EFFORTS` in the same gate | `{low, medium, high}` |
| Shipped effort levels the gate cannot express | `xhigh`, `max` |

The last two rows are the sharpest case. `scripts/check_agent_model_matrix.py`
is a hard gate that rejects any agent pinning a tier outside its
frozen set. Fable 5 shipped. No agent in this repo can pin `fable`,
because the gate that exists to prevent model rot has itself rotted.
A model release broke a guard whose job was to survive model releases.

## Goals

1. Detect drift between the last recorded upstream state and the
   current one, deterministically and without a model in the loop.
2. Record a watermark so each run reports only what changed since the
   previous run, rather than restating the full inventory.
3. Research what a given model or harness release actually changed,
   using the tome plugin when installed and web search otherwise.
4. Map research findings onto the asset classes they affect and apply
   the updates.
5. Prove the sweep with evidence and write a new watermark only after
   the proof passes.

## Non-goals

- Rewriting agent frontmatter to dated model IDs. The repo
  deliberately pins tier aliases (`haiku`, `sonnet`, `opus`) in agent
  frontmatter, and `check_agent_model_matrix.py` bans dated IDs there.
  This workflow extends that vocabulary when a tier ships. It never
  reverses the policy.
- Replacing `check_agent_model_matrix.py`, `check_skill_graph_drift.py`,
  or any existing gate. This workflow feeds them and widens their
  vocabularies. It duplicates none of their checks.
- Automatic unattended commits. The sweep proposes and applies edits
  inside a normal review and gate cycle.

## Triggers

The workflow runs on either event:

| Trigger | Detection | Authority |
|---------|-----------|-----------|
| Model release | Research channel reports a tier or ID absent from the ledger | Web research |
| Harness release | `claude --version` differs from the ledger | Deterministic |

Harness drift is fully scriptable because the installed binary reports
its own version. Model drift is not: no local command enumerates the
current roster, so the ledger holds the last known roster and research
establishes the current one. The workflow states this split plainly
rather than pretending both halves are automatic.

## The ledger

A single file, `.claude/upstream-baseline.json`, holds the watermark.

```json
{
  "schema_version": 1,
  "harness": {
    "product": "claude-code",
    "version": "2.1.220",
    "recorded_at": "2026-08-02"
  },
  "models": {
    "tiers": ["haiku", "sonnet", "opus", "fable"],
    "ids": {
      "fable": "claude-fable-5",
      "opus": "claude-opus-5",
      "sonnet": "claude-sonnet-5",
      "haiku": "claude-haiku-4-5-20251001"
    },
    "recorded_at": "2026-08-02"
  },
  "vocabularies": {
    "effort_levels": ["low", "medium", "high", "xhigh", "max"]
  },
  "last_migration": {
    "id": "2026-08-02-initial",
    "trigger": "bootstrap",
    "from": {"harness": null, "model_tiers": []},
    "to": {"harness": "2.1.220", "model_tiers": ["haiku", "sonnet", "opus", "fable"]},
    "assets_changed": 0,
    "report": "docs/model-harness-updates/migrations/2026-08-02-initial.md"
  },
  "history": []
}
```

Contract:

- The ledger is the only source of "what upstream looked like last
  time". Nothing else records it.
- A migration appends its previous `last_migration` to `history` and
  replaces `last_migration`. History is never rewritten.
- A run that changes no assets still updates `recorded_at` when it
  confirms no drift, so a clean check is distinguishable from a check
  that never ran.

## Drift detection contract

`scripts/check_upstream_drift.py` is deterministic, read-only, and
idempotent, matching the house pattern set by
`check_skill_graph_drift.py` and `check_skill_exit_criteria_drift.py`.

It reports four drift classes:

| Class | Meaning |
|-------|---------|
| `harness` | Installed `claude --version` differs from the ledger |
| `vocabulary` | A gate's frozen set omits a value the ledger records |
| `dated_ids` | A file pins a dated model ID outside gated surfaces |
| `unknown_tier` | A file references a tier absent from the ledger |

Exit codes follow the house convention for gates: `0` when no drift,
`1` when drift is found, `2` on a usage or environment error.

The `vocabulary` class is what catches the Fable case. The script
reads `VALID_MODELS` and `VALID_EFFORTS` out of the gate source and
compares them against the ledger, so a tier recorded in the ledger but
missing from the gate is reported rather than discovered by a failing
agent months later.

## Research protocol

When drift is detected, the workflow researches what changed before
touching any asset.

1. If the tome plugin is installed, run `Skill(tome:research)` with a
   query built from the drift report. Tome dispatches parallel channel
   agents across code search, discourse, and papers.
2. If tome is absent, fall back to `WebSearch` and `WebFetch` against
   the release notes, model cards, and changelog for the named
   version.
3. Either path must produce a findings set where each claim carries a
   source URL. Claims without a source are dropped, per the repo
   evidence bar.

Detection of tome is a filesystem check for the plugin directory, not
an assumption.

## Asset sweep

Research findings map onto asset classes through an impact table. Each
class has an owner check that proves the update landed.

| Asset class | Location | Proof |
|-------------|----------|-------|
| Agent frontmatter | `plugins/*/agents/*.md` | `check_agent_model_matrix.py` |
| Gate vocabularies | `scripts/check_*.py` | Unit tests |
| Skills | `plugins/*/skills/**/SKILL.md` | `check_agent_model_matrix.py` |
| Local skills | `.claude/skills/*/SKILL.md` | Drift script |
| Commands | `plugins/*/commands/*.md` | Drift script |
| Hooks | `plugins/*/hooks/**` | Plugin test suites |
| Docs of record | `docs/agent-model-matrix.md` | `check_agent_model_matrix.py` |
| Rules | `.claude/rules/*.md` | Review |

A sweep touches only classes the research findings implicate. A model
that adds a tier touches vocabularies, the matrix doc, and agent
frontmatter. A harness release that renames a hook event touches hooks
and the plugin reference. The impact table prevents a blanket rewrite.

## Verification and re-baseline

The sweep is complete when, in order:

1. `python3 scripts/check_upstream_drift.py` exits `0`.
2. `python3 scripts/check_agent_model_matrix.py` exits `0`.
3. The unit tests for the drift script pass.
4. A migration report exists under
   `docs/model-harness-updates/migrations/`.

Only then does the workflow write the new ledger. Writing the
watermark before the proof passes would record a migration that never
happened, which is the failure mode the ledger exists to prevent.

## Acceptance criteria

- [ ] `.claude/upstream-baseline.json` exists and validates against
      the schema.
- [ ] `scripts/check_upstream_drift.py` exits `0` on a clean tree and
      `1` when a drift class is injected.
- [ ] The drift script detects the Fable vocabulary gap before the
      fix and stops detecting it after.
- [ ] `.claude/skills/night-market-model-and-harness-updates/SKILL.md`
      exists with frontmatter and an Exit Criteria section.
- [ ] Unit tests cover all four drift classes plus ledger read and
      write.
- [ ] `check_agent_model_matrix.py` accepts `fable`, `xhigh`, and
      `max` after the sweep, and its tests prove it.
- [ ] A migration report records the bootstrap run.
