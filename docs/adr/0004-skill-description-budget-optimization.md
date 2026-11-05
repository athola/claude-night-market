# ADR 0004: Skill Description Budget Optimization

**Date**: 2025-12-31
**Updated**: 2026-11-04
**Status**: Accepted (Updated)
**Context**: Slash Command Character Budget Management

## Problem

Claude Code enforces a character budget for skill descriptions loaded into
context. Exceeding this limit causes skills to become invisible to Claude,
breaking discoverability.

**Initial State (2025-12)**: 15,202 characters (101.3% of 15k budget)

This required users to manually configure their environment,
creating a poor out-of-the-box experience.

## Budget Limit Update (2026-02)

As of Claude Code v2.1.32 (Feb 6, 2026), the skill description budget changed:

- **Dynamic scaling**: Budget is now **2% of the context window** size
- **Fallback**: 16,000 characters (up from the previous 15,000 hardcoded value)
- **Override**: `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable for
  custom limits
- **Ecosystem validator**:
  Set to 20,000 to match 1M context window (GA for Opus/Sonnet 4.6)

For standard 200k-token context windows, 2% yields ~16,000 characters.
With 1M context (GA since April 2026), the budget is ~20,000 characters.

### Sources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - "The budget scales dynamically at 2% of the context window, with a fallback of 16,000 characters."
- [Claude Code v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - "Skill character budget now scales with context window (2% of context)"

## Decision

Optimize skill and command descriptions through systematic reduction while
preserving discoverability.

### Optimization Principles

Optimization focuses on:
- **Concise Descriptions**:
  Removing implementation details from the primary text.
- **Trigger Condensation**: Reducing trigger lists to essential keywords.
- **Redundancy Elimination**: Ensuring descriptions don't repeat tag
  or category information.
- **Discoverability**: Preserving critical keywords while moving verbosity to
  documentation.

## Implementation

### Round 1: Top 5 Verbose Descriptions

1. ✅ abstract/validate-plugin: 264 → 95 chars (-169 chars)
2. ✅ sanctum/pr-review: 247 → 163 chars (-84 chars)
3. ✅ sanctum/tutorial-updates: 194 → 106 chars (-88 chars)
4. ✅ sanctum/doc-updates: 187 → 110 chars (-77 chars)
5. ✅ leyline/usage-logging: 160 → 95 chars (-65 chars)

**Round 1 Savings**: 483 chars

### Round 2: Conservation Plugin Bloat

6. ✅ conservation/bloat-detector: 248 → 110 chars (-138 chars)
7. ✅ conservation/mcp-code-execution: 143 → 105 chars (-38 chars)

**Round 2 Savings**: 176 chars

**Note**: Some multiline descriptions had extra whitespace that was trimmed,
accounting for variance between estimated and actual savings.

## Results

### Final Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Characters** | 15,202 | 14,798 | -404 chars (-2.7%) |
| **Budget Usage** | 101.3% 🔴 | 98.7% ✅ | **Under by 202 chars** |
| **Headroom** | -202 chars | +202 chars | **1.3% buffer** |

### Budget Distribution After Optimization

| Plugin | Components | Total Chars | Avg/Component | Status |
|--------|-----------|-------------|---------------|--------|
| sanctum | 30 | 3,159 (-248) | 105 | Optimized |
| archetypes | 14 | 1,823 | 130 | Consolidation candidate |
| abstract | 23 | 1,759 (-165) | 76 | Excellent |
| leyline | 14 | 1,704 (-67) | 122 | Improved |
| imbue | 12 | 1,137 | 95 | Good |
| pensive | 17 | 820 | 48 | Most efficient |
| conservation | 8 | 729 (-176) | 91 | Debloated |
| memory-palace | 10 | 610 | 61 | Efficient |
| scry | 6 | 596 | 99 | Good |
| minister | 3 | 352 | 117 | Good |
| parseltongue | 7 | 343 | 49 | Most efficient |
| conjure | 3 | 310 | 103 | Good |

## Consequences

### Round 1-2 (2025-12)

Optimization reduced the ecosystem from 15,202 to 14,798 characters (98.7% of
the original 15k limit).

### Round 3 (2026-02)

After ecosystem growth pushed total to 16,711 chars,
a two-pronged approach was applied:
1. **Validator limit raised** to 17,000 (above the new CC 16k fallback)
2. **9 attune skill descriptions condensed** using "Use for/Skip if" pattern
   (-745 chars)

| Metric | Round 1-2 | Round 3 | Current (1M ctx) |
|--------|-----------|---------|---------|
| **Total Chars** | 14,798 | 16,711 → 15,966 | ~20,918 |
| **Validator Limit** | 15,000 | 17,000 | 20,000 |
| **Per-desc Max** | 130 | 130 | 160 |

## 2026-05 Overhaul: Action-Oriented Description Rewrite

All SKILL.md `description:` fields rewritten in May 2026 to use
Anthropic's recommended activation format:

```
[Verb phrase]. Use when [trigger condition].
[Do not use when [negative]; use [alternative] instead.]
```

**Why**: The majority of skills had noun-phrase descriptions that told
Claude WHAT a skill does but not WHEN to invoke it. The `description:`
field is the only signal in the system-reminder Claude uses for skill
selection; triggering skills requires action-oriented triggers.

**Results**:

| Metric | Before (Round 3) | After (2026-05) |
|--------|-----------------|-----------------|
| **Total Chars (raw)** | ~15,966 | 35,472 |
| **With overhead** | ~21k | 70,239 |
| **Avg desc length** | 77.7 chars | 144.6 chars |
| **Skills with a trigger phrase** | ~8% | 100% (majority "Use when"; remainder "Use before/after/for/at") |
| **Per-desc over 160 chars** | 0 | 0 |

The raw description budget grew 2.2x because descriptions now contain
trigger context that drives accurate skill activation. This is within
Claude Code's 1M context budget (~80k available for descriptions with
overhead) and is a deliberate trade-off: better activation accuracy
over minimal budget.

**Template doc**: `docs/skill-description-guide.md`

**Commands excluded**: Slash command `.md` files were not updated:
command descriptions appear in `/help` output for humans and use
noun-phrase format by design (commands are user-typed, not
Claude-selected).

## Future Opportunities

1. **Archetypes consolidation** (potential savings: ~1,500 chars raw)
   - Merge 13 architecture-paradigm-* skills into 1 interactive selector
2. **`SLASH_COMMAND_TOOL_CHAR_BUDGET` env var** - document for power users with
   many plugins

## Monitoring

1. ✅ Pre-commit hook (`validate-description-budget`) fails on a description
   over 160 chars and warns on the total
2. ✅ Validator tracks per-description lengths (160 char max)
3. ⏳ Monitor for description creep in future PRs
4. ⏳ Consider archetypes consolidation if headroom shrinks

## Summary

After the 2026-05 overhaul, all descriptions use action-oriented triggers
("Use when/before/after/for"). Growth is intentional: trigger phrasing
improves skill activation accuracy at the cost of budget.

2026-10-28: 340 components carry 40,741 description chars, 77,801 with
per-component overhead. The validator's total is 90,000 (`DEFAULT_BUDGET`
in `plugins/abstract/scripts/validate_budget.py`, which carries the
arithmetic): about 9% of a 1M window. At the 160-char cap each component
costs 269 chars with overhead, so the total covers 334 components, six
fewer than ship today. The total only warns. The per-description cap is the one
hard failure, so a growing component count never blocks an unrelated
commit. The cost of that choice: on a 200k-context session the listing
exceeds the 16,000-char fallback several times over, and the harness
truncates it. Such a session sees only part of the skill list.
`SLASH_COMMAND_TOOL_CHAR_BUDGET` raises the limit there.

## Measuring Activation (2026-11)

The 2026-05 overhaul bought trigger phrasing with budget on the claim
that it improves activation. Nothing measured that claim until
`scripts/activation/`. The harness it replaced, removed in 2026-10,
measured sensitivity alone on a small set with no negatives, and read
100%. This section records why the suite's numbers can carry a claim,
then how to use it. Settings are in `evals/activation/config.yaml`. The
label schema is in `evals/activation/labels/README.md`. TR-005 in
`docs/tradeoffs.md` records why runs happen in a copied host.

### Decision: two rates, read from kept traces

A case-run is one labeled prompt, one model arm, one repeat. From its
kept trace the analyzer reads the ordered `Skill` tool calls and keeps
those naming an inventory id. Grader verdicts from `claude plugin eval`
are never read for a metric.

- **Sensitivity**: a positive case-run is a hit when its target is
  among the calls.
- **False activation on positives**: another id fired first, or fired
  while the target never did.
- **False activation on negatives**: any id fired.

One rate alone is gameable. A library that fires something on every
prompt scores perfect sensitivity, and one that fires nothing scores a
perfect false-activation rate. Every report and comparison carries all
three.

### Decision: intervals resample clusters

Runs of one item are correlated: a description that confuses the model
confuses it on every prompt aimed there. Treating runs as independent
would understate the interval. The analyzer resamples clusters (a
positive case's target, a negative case's prompt source) with
replacement, B = 2000, seed 0, and reports the percentile interval. The
Wilson interval is recorded beside it in `metrics.json`.

### Decision: anchor sets must sit off the ceiling

A rate at 1.0 cannot rise. A comparison against it can only detect
harm. An anchor run whose sensitivity is 0.95 or higher reports
`ceiling: true` and exits 3, failing the release run. The anchor's
first selection favors near-miss prompts from the router's most
frequent collision pairs, because those are the prompts most likely to
land between 0 and 1. After the first full run, the anchor is refreshed
with cases whose rate is strictly between 0 and 1 on either arm. That
set is chosen on outcomes, and its intervals describe that set alone.

### Decision: a paired delta needs seven conditions

Each case is reduced to activated or not by majority over its R runs.
R is odd, which rules out ties when no run errors. A case tied after
errors is dropped from the pairing and counted. The exact two-sided
McNemar test on the discordant cases (b activated in base only, c in
new only) gives `p = 2 * P(X <= min(b, c))` for `X ~ Bin(b + c, 0.5)`.

Holm's step-down controls the family error at 0.05 across the three
rates: the smallest p is compared with 0.05 / 3, the next with
0.05 / 2, the largest with 0.05. With every discordant case going one
way, p = 2 / 2^n. Seven cases give 0.0156, enough at the strictest
step. Six give 0.031, enough only at the last step after the other two
rates have rejected. Fewer than six can never be significant, and the
report calls that `underpowered` rather than `not significant`.

| Condition | Enforced by |
|---|---|
| C1 paired, fingerprinted | compare refuses differing model, CLI version, plugins, case set, R, tier, item hashes outside the change, a partial run, or a dirty tree |
| C2 two rates | every report and comparison carries sensitivity and both false-activation rates |
| C3 exact McNemar, Holm | `compare.mcnemar_p`, `compare.holm` |
| C4 off the ceiling | anchor runs exit 3 at sensitivity 0.95 or higher |
| C5 clustered intervals | `analyze.cluster_bootstrap` |
| C6 self-check | `mutate.py`: both mutants must show sensitivity `regressed` |
| C7 declared before run | the change file must be committed, and its `declared_at` must be an ancestor of both runs |

Each verdict is one of `improved`, `regressed`, `not significant`,
`underpowered`, or `no evidence of change`. Claims are library or tier
level, never per item.

### Decision: the suite proves it can see a regression

A suite that misses a blanked description will miss a subtle edit.
`mutate.py` makes a clean anchor run, then two mutants in their own
hosts: descriptions of activated targets replaced by `.`, and
descriptions swapped across the router's collision pairs. Each mutant
covers at least 12 activated positive cases. Below 7 it is infeasible,
because 7 one-way cases are the minimum that passes the strictest Holm
step. Between 7 and 11 it runs and reports the shortfall. A failing
self-check marks later comparisons on that anchor set untrusted.

Host plugin files are copies. The eval runner refuses a plugin file
with more than one name, and hard links failed every case (smoke run,
2026-11-03, Claude Code 2.1.317). Dot-directories other than
`.claude-plugin` are skipped, which keeps the copy near 48 MB.

### Decision: labels come from models that are not measured

The answer key is written by a writer model and checked by a judge
model, both chosen so that neither resolves to a measured arm. The
writer drafts from item bodies and the judge reads body excerpts, never
descriptions. Bodies often repeat description wording, and echo risk
falls without vanishing. The judge's candidates are the router's top
eight plus the writer's target. Without the target the judge could only
disagree when the router ranked it low, and the first draft lost 328 of
628 positive labels that way.

A label is queued for a person when the judge names a different target,
when the judge routes a negative prompt to an item, or when the seed-0
random audit picks it (10% of the rest). The router's answer is
recorded on every label under `proposals` and never queues it: its
rank-1 missed about half of the judge-confirmed positives in the first
draft. The router gate therefore measures agreement with labels the
router did not choose, and still cannot show that the model activates
anything.

A writer reply that does not parse drops its whole batch. `draft`
redrafts each short item once, alone, and lists any still short under
`unfilled_items` in `adjudicate.yaml`. `repair` fills them later.

### Using the suite

Every tool is a module in `scripts/activation/`, run from the repo root
as `uv run python -m scripts.activation.<tool>`. The table abbreviates
that to the tool name. Every live command takes `--dry-run`, which
prints the case count and the cost estimate and spends nothing. Live
runs always pass `--max-cost-usd`.

| Check | Cost | When | Command |
|---|---|---|---|
| Router gate | free | pre-commit, on description edits | `router check` |
| Change tier | $6-30 | after a description change you want to claim | `run --tier change --change <file>` |
| Anchor tier | about $60 per arm | before a release | `run --tier anchor --arm default` |
| Self-check | about $180 per arm | after the anchor set changes | `mutate --arm default` |
| Full tier | about $600 per arm | on demand | `run --tier full` |

A full-library case-run cost $0.197 on the session default model in
probe L6 (`.attune/research/activation-quality/local-findings.md`),
because every description is in the prompt. The runner estimates from
the arm's latest committed baseline and falls back to $0.20 for the
default arm. The Haiku arm is reported as unmeasured until its first
run.

**Router gate.** The `check-activation-router` pre-commit hook ranks
every routing target against each labeled prompt with BM25 over names
and descriptions. It fails when labeled MRR drops by more than 0.01, or
when a prompt that ranked its target first now ranks another item first
and one of the two descriptions changed. It is a lexical proxy. When
the change is intended, regenerate the baseline and commit it with the
description edit, and review shows the shift:

```bash
uv run python -m scripts.activation.router baseline
uv run python -m scripts.activation.router report   # top collision pairs
```

**Claiming a change moved the number.**

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

**Reading a report.** Run hosts are written to
`evals/activation/.runs/<run-id>/` (gitignored). `report.md` leads with
the three rates and their 95% cluster-bootstrap intervals, the ceiling
flag, the fingerprint and the cost, then the 20 worst items and the 20
most frequent confusion pairs. Skill calls that name no inventory item
(a built-in skill, for example) are listed and not counted. Commit a
baseline by copying its `report.md` and `metrics.json` to
`evals/activation/reports/baseline-<arm>-<date>.md` and `.json`.

**Building the labeled set.** `config.yaml` lists the writer and judge
candidates. Adjudicate by editing the label YAML and setting
`adjudicated: true`. The anchor and full tiers refuse to run while
coverage fails.

```bash
# one probe per model, then drafts capped at label_max_cost_usd
uv run python -m scripts.activation.labeling resolve
uv run python -m scripts.activation.labeling draft
# fill empty items and re-judge, or rebuild the queue for free
uv run python -m scripts.activation.labeling repair
uv run python -m scripts.activation.labeling requeue
# prompts left to adjudicate, then the coverage gate
uv run python -m scripts.activation.labeling queue
uv run python -m scripts.activation.labels coverage
# writes anchor.txt
uv run python -m scripts.activation.run anchor-select
```

**Shared ids.** The model names a target by id. When a command and a
skill share an id, the listing shows one description, and the inventory
follows the precedence observed in the harness listing: workflow over
command over skill. `inventory` prints how many files a shared id hides
(36 on 2026-11-03). Editing a hidden description changes nothing the
model sees.

### Evidence from the first live run

The 2026-11-03 smoke run (one prompt, $0.20) confirmed that
`result.json` lists cases under `cases[]` with `name`, and runs under
`arms.with[]` with `tracePath` and `error`. A run stopped at
`max_turns` reports `error: "exit 1: Reached maximum number of turns"`
and keeps a full trace, and the runner keeps that trace. All 323
routing ids appeared in the eval child's listing. The prompt from probe
L6 again routed to the deprecated `pensive:shell-review` stub.

Still read from documentation only: `claude -p --output-format json`
reports the answering model under `modelUsage`, and the eval child's
listing follows the shared-id precedence seen in the interactive
session.

## Related

- See ADR-0003 for command description refactoring pattern
- See [Skills Reference](../../book/src/reference/capabilities-skills.md) for
  skill documentation
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) - authoritative budget documentation
- [CC v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - dynamic scaling announcement
