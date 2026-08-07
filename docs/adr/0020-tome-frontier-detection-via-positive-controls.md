# ADR-0020: Detect a Thin Field with Positive Controls, Not Overlap Estimation

**Date**: 2026-08-07
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0018 (tome graph reuse over build)

## Context

Tome runs research across four channels and renders a report. It cannot
distinguish a topic with little published work from a search that went
badly. Both produce few findings, and every term
`compute_quality_score` blends (channel coverage, source diversity,
mean relevance) describes the search rather than the field.

The conflation is not cosmetic. `research_planner.replan()`
down-weights a channel that returned nothing. That is correct when the
field is empty and harmful when the query was wrong, because the next
pass then searches the right channel less.

A five-channel research pass was run before designing the fix. This ADR
records what it decided and what it rejected. The working synthesis is
local and untracked by design; the decision is here and the contract is
in `plugins/tome/tests/unit/test_channel_outcomes.py`.

## Decision

Distinguish the two cases with a **positive control measured
independently of result volume**, not with a statistic computed from
result counts.

1. Channel outcome is derived from a per-channel query record and takes
   one of six values: `ok`, `empty`, `error`, `rate_limited`,
   `degraded`, `unknown`. Status is computed from the logs, never
   stored beside them.
2. A session with no query record derives `unknown`, never `empty`.
   Silence is not evidence about a field.
3. The strong verdict requires passing channel controls, not a minimum
   query count.
4. A null is reported with the floor it was measured against, never as
   a bare zero.
5. The verdict is a claim about the search, not about the literature.

## Alternatives rejected

**Capture-recapture over channel overlap.** This was the leading
candidate. Systematic reviewers estimate missed studies from overlap
between independent searches (Kastner et al. 2009; Webster and Kemp
2013), needing no ground truth, which is exactly the constraint here.

Rejected on three grounds. Tome's channels violate the independence
assumption by construction, because Semantic Scholar ingests arXiv and
aggregators crawl the same publishers. Positive dependence makes
Lincoln-Petersen *underestimate* what was missed, so the bias points
toward false confidence and points hardest when channels overlap most.
The estimator is undefined at zero overlap, and near-zero overlap is
the regime in question. Dedup error dominates at single-digit result
counts, where systematic reviews absorb it across hundreds of records
with human reference management.

**A query-performance-prediction term in the verdict.** Every strong
predictor (Clarity, WIG, NQC, UEF) requires a populated ranked list to
compute a mean or a standard deviation, so all are undefined at zero
results. Only the pre-retrieval family is computable there, at roughly
15% correlation with actual effectiveness against roughly 35% for the
post-retrieval family. Worth using to trigger reformulation; not worth
grading a finding with.

**A fourth term inside `compute_quality_score`.** Every existing term
measures the search, so a blend cannot separate a thin field from a
broken one however it is weighted. The distinction needs a categorical
verdict beside the score, not another continuous dimension. For the
same reason the score is deliberately kept out of the report: printing
a search-quality number next to a field-quality verdict invites the
reader to read one as the other.

**A minimum query count as the gate.** The pre-research plan gated the
strong verdict on queries-per-channel. Counting queries cannot assess
them, and three queries built from the same wrong root word are one
query.

**A stored per-channel status field.** Two persisted representations of
one fact can disagree after a partial save, and then neither can be
trusted. Deriving costs one function. See
`.claude/rules/ceremony-requires-need.md`.

## Why positive controls

Analytical chemistry solved this and made the solution a precondition
for reporting: a method blank and a matrix spike run alongside every
batch, and system suitability testing gates the run on them (USP
General Chapter 621; IUPAC limit-of-detection guidance). A result is
not reportable unless the instrument demonstrated it could see what it
was looking for.

The mapping carries no metaphorical slack. A channel is the instrument,
a canary query whose target is known to be indexed is the matrix spike,
canary recall is the recovery percentage, and the detection floor is
the minimum publication density the spent budget could have found.

The TRIZ pass supplied the reason this specific property matters.
Separating the cases on a condition is the right frame, but a condition
derived from result volume cannot adjudicate result volume; it stays
circular until the condition is instrumented by something else. A
control is that something else.

Two reporting conventions follow. Non-detections carry their floor, as
SETI publishes upper limits with the searched parameter volume so nulls
accumulate across runs (Uno et al., MNRAS 522:4649, 2023). And
"confidence" splits into evidential strength and search quality, as
GRADE separates certainty from recommendation strength, which is what
lets a firm statement coexist with weak evidence without hedging in
prose.

## Consequences

Channel outcome is representable and persisted; `from_dict` defaults
the field so sessions written earlier still load. `QueryLog` now
derives `succeeded` from an error kind and refuses an unexplained
failure, since a failure with no named cause is indistinguishable from
a clean empty result.

Canary infrastructure is new scope. It is not built, and no verdict
depending on it may ship until it is.

The report must stop skipping channels that produced nothing, which is
the change that makes any of this visible to a reader.

Two constants in `plugins/tome/src/tome/synthesis/quality.py`
(`_SKEW_THRESHOLD` 0.75, `_RECENCY_GAP_YEARS` 3) carry no source and
are labeled unvalidated in code rather than left to read as measured.

## What is not claimed

Whether canary queries fit tome's dispatch budget is unmeasured, and a
canary target can go stale as an index changes, reporting a false
defect. Neither is addressed.

Nothing here detects a field that exists under different vocabulary. A
control proves a channel can see; it cannot prove the query used the
words the field uses. That failure mode is open.

The claim that no integrated quantitative coverage estimator exists in
open review tooling is a literature-absence claim as of 2026-08-07,
consistent across three channels, and should be re-checked before being
cited outside this repo.
