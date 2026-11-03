# Activation Quality: Design and Statistics

**Audience**: expert, someone judging whether the suite's numbers can
carry a claim. The how-to is [activation-quality.md](../activation-quality.md).

The suite's claim is narrow on purpose: a library-level rate with an
honest interval, and a paired delta that refuses to exist unless seven
conditions hold. This page says why each condition is there.

## Rates

A case-run is one labeled prompt, one model arm, one repeat. From its
kept trace the analyzer reads the ordered `Skill` tool calls and keeps
those naming an inventory id. A positive case-run is a hit when its
target is among them. It is a false activation when another id fired
first, or when another id fired and the target never did. A negative
case-run is a false activation when any id fired. Grader verdicts from
`claude plugin eval` are never read for a metric.

One rate alone is gameable. A library that fires something on every
prompt scores perfect sensitivity, and one that fires nothing scores a
perfect false-activation rate. The removed 2026-10 harness measured
only the first, on a small set with no negatives, and read 100%.

## The ceiling

A rate at 1.0 cannot rise. A comparison against it can only detect
harm. An anchor set whose baseline sensitivity is 0.95 or higher is
reported as `ceiling: true` and fails the release run. The anchor's
first selection favors near-miss prompts from the router's most
frequent collision pairs for this reason: they are the prompts most
likely to land between 0 and 1. After the first full run, the anchor is
refreshed with cases whose rate is strictly between 0 and 1 on either
arm. That set is chosen on outcomes, and its intervals describe that
set alone.

## Intervals

Runs of one item are correlated: a description that confuses the model
confuses it on every prompt aimed there. Treating runs as independent
would understate the interval. The analyzer resamples clusters (a
positive case's target, a negative case's prompt source) with
replacement, B = 2000, seed 0, and reports the percentile interval. The
Wilson interval is recorded beside it in `metrics.json`.

## The paired test

Each case is reduced to activated or not by majority over its R runs. R
is odd so ties cannot happen when no run errors. A case tied after
errors is dropped from the pairing and counted. The exact two-sided
McNemar test on the discordant cases (b activated in base only, c in
new only) gives `p = 2 * P(X <= min(b, c))` for `X ~ Bin(b + c, 0.5)`.

Holm's step-down controls the family error at 0.05 across the three
rates tested together: the smallest p is compared with 0.05 / 3, the next
with 0.05 / 2, the largest with 0.05. With every discordant case going
one way, p = 2 / 2^n. Seven cases give 0.0156, enough at the strictest
step. Six give 0.031, enough only at the last step after the other two
rates have rejected. Fewer than six can never be significant, and the
report calls that `underpowered` rather than `not significant`.

## The seven conditions

| Condition | Enforced by |
|---|---|
| C1 paired, fingerprinted | compare refuses differing model, CLI version, plugins, case set, R, tier, or item hashes outside the change |
| C2 two rates | every report and comparison carries sensitivity and both false-activation rates |
| C3 exact McNemar, Holm | `compare.mcnemar_p`, `compare.holm` |
| C4 off the ceiling | anchor runs exit 3 at sensitivity 0.95 or higher |
| C5 clustered intervals | `analyze.cluster_bootstrap` |
| C6 self-check | `mutate.py`: both mutants must show sensitivity `regressed` |
| C7 declared before run | the change file must be committed, and its `declared_at` must be an ancestor of both runs |

## Mutation self-check

A suite that cannot see a blanked description cannot see a subtle edit.
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

## Labels and echo risk

The answer key is written by a writer model and checked by a judge
model, both chosen so that neither resolves to a measured arm. The
writer drafts from item bodies and the judge reads body excerpts, never
descriptions. Bodies often repeat description wording, and echo risk
falls without vanishing. The judge's candidates are the router's top
eight plus the writer's target. Without the target the judge could only
disagree when the router ranked it low, and the first draft lost 328 of
628 positive labels that way. The router's own answer is recorded on
each label and never queues it. The router gate therefore measures
agreement with labels the router did not choose, and still cannot show
that the model activates anything.

A writer reply that does not parse drops its whole batch. `draft`
redrafts each short item once, alone, and lists any still short under
`unfilled_items` in `adjudicate.yaml`. `repair` fills them later.

## Cost model

A full-library case-run cost $0.197 on the session default model in
probe L6 (`.attune/research/activation-quality/local-findings.md`),
because every description is in the prompt. The runner estimates from
the arm's latest committed baseline and falls back to $0.20 for the
default arm. The Haiku arm is reported as unmeasured until its first
run.

## What the first live run confirmed

The 2026-11-03 smoke run (one prompt, $0.20) confirmed that
`result.json` lists cases under `cases[]` with `name`, and runs under
`arms.with[]` with `tracePath` and `error`. A run stopped at
`max_turns` reports `error: "exit 1: Reached maximum number of turns"`
and keeps a full trace. The runner keeps that trace. All 323 routing ids
appeared in the eval child's listing. The prompt from probe L6 again
routed to the deprecated `pensive:shell-review` stub.

Still read from documentation only: `claude -p --output-format json`
reports the answering model under `modelUsage`, and the eval child's
listing follows the shared-id precedence seen in the interactive
session.
