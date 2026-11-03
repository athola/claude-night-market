# Activation Quality

**Audience**: practitioner, a maintainer editing a skill, command or
workflow description who needs to know whether the edit helped.
Statistics and design rationale for experts:
[deep dive](deep-dive/activation-quality.md).

The activation suite reports how often the library routes a labeled
prompt to the right item, and whether a change moved that number. It
reports two rates, never one. **Sensitivity** is the share of positive
case-runs where the target item fired. **False activation** is the
share where the wrong item fired, reported separately for negative
prompts (nothing should fire) and positive prompts (another item fired
first).

## What runs where

| Check | Cost | When | Command |
|---|---|---|---|
| Router gate | free | pre-commit, on description edits | `uv run python -m scripts.activation.router check` |
| Change tier | $6-30 | after a description change you want to claim | `run --tier change --change <file>` |
| Anchor tier | about $60 per arm | before a release | `run --tier anchor --arm default` |
| Self-check | about $180 per arm | after the anchor set changes | `mutate --arm default` |
| Full tier | about $600 per arm | on demand | `run --tier full` |

Every tool is a module in `scripts/activation/`, run from the repo
root as `uv run python -m scripts.activation.<tool>`. The table and
steps abbreviate that to the tool name. Every live command takes
`--dry-run`, which prints the case count and the cost estimate, and
spends nothing. Live runs always pass `--max-cost-usd`.

## The router gate

The pre-commit hook ranks every routing target against each labeled
prompt with BM25 over names and descriptions. It fails when labeled
MRR drops by more than 0.01, or when a prompt that ranked its target
first now ranks another item first and one of the two descriptions
changed. It is a lexical proxy. Passing it says nothing about whether
the model activates the item.

When the change is intended, regenerate the baseline and commit it
with the description edit. Review then shows the shift:

```bash
uv run python -m scripts.activation.router baseline
uv run python -m scripts.activation.router report   # top collision pairs
```

## Claiming that a change moved the number

1. Write `evals/activation/changes/<date>-<slug>.yaml` naming the items
   you will edit:

   ```yaml
   schema_version: 1
   id: 2026-11-03-shell-review-redirect
   description: Point pensive:shell-review at unified-review.
   items: [pensive:shell-review]
   ```

2. On the base tree, freeze the affected cases and commit the file:
   `uv run python -m scripts.activation.run declare <file>`.
3. Run the base: `run --tier change --change <file>`.
4. Make the edit, commit it, and run the same command again.
5. Compare the two runs:

   ```bash
   uv run python -m scripts.activation.compare \
     <base>/metrics.json <new>/metrics.json --change <file>
   ```

The comparison refuses when the runs differ in model, Claude Code
version, loaded plugins, case set or R, when an item outside the change
file changed, when either run was partial or made on a dirty tree, or
when the change file was declared after a run. Each verdict is one of
`improved`, `regressed`, `not significant`, `underpowered` (fewer than
6 discordant cases, which can never reach significance), or `no
evidence of change`. Claims are library or tier level, never per item.

## Reading a report

Run hosts live under `evals/activation/.runs/<run-id>/` (gitignored).
`report.md` leads with the three rates and their 95% cluster-bootstrap
intervals, the ceiling flag, the fingerprint and the cost, then the 20
worst items and the 20 most frequent confusion pairs. Skill calls that
name no inventory item (a built-in skill, for example) are listed and
not counted.

An anchor run with sensitivity of 0.95 or higher sets `ceiling: true`
and exits 3. A set at ceiling cannot show an improvement. Refresh
the anchor before trusting it as a release gate. Commit a baseline by
copying its `report.md` and `metrics.json` to
`evals/activation/reports/baseline-<arm>-<date>.md` and `.json`.

## Building the labeled set

Labels are written by models that are not measured, then adjudicated
by a person. `config.yaml` lists the writer and judge candidates.

```bash
# one probe per model, then drafts capped at label_max_cost_usd
uv run python -m scripts.activation.labeling resolve
uv run python -m scripts.activation.labeling draft
# prompts left to adjudicate, then the coverage gate
uv run python -m scripts.activation.labeling queue
uv run python -m scripts.activation.labels coverage
# writes anchor.txt
uv run python -m scripts.activation.run anchor-select
```

Adjudicate by editing the label YAML and setting `adjudicated: true`.
The anchor and full tiers refuse to run while coverage fails.

## Shared ids

The model names a target by id. When a command and a skill share an id,
the listing shows one description, and the inventory follows the
precedence observed in the harness listing: workflow over command over
skill. `inventory` prints how many files a shared id hides (36 on
2026-11-03). Editing a hidden description changes nothing the model
sees.
