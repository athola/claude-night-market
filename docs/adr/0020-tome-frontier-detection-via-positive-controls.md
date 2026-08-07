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
6. Only channels that answer by searching an external index may take
   part in the verdict, and only their findings are counted toward it.

## Only retrieval channels may testify

`RETRIEVAL_CHANNELS` in `tome/models.py` names the three channels whose
answers come from an index: `academic`, `code`, `discourse`. `triz` is
excluded, and the exclusion is load-bearing in two directions.

It must not be counted. `triz` generates cross-domain analogies rather
than retrieving records of prior work. Counting its output toward the
sparsity threshold lets the tool satisfy that threshold with text it
wrote itself, so a topic with four invented bridges and no papers reads
exactly like one with four papers. The verdict would then be grading
the field on its own output, which is the failure mode the control
mechanism exists to prevent, arriving through the denominator instead
of through the numerator.

It must not be controlled. A positive control asks whether a channel
can retrieve a document known to be in its index. For a channel with no
index the question is malformed rather than merely unanswered, and
demanding one pins every session carrying `triz` to `INCONCLUSIVE` for
a reason that says nothing about coverage.

The narrow reading matters: this is not a general exemption. A
retrieval channel that runs without a control still forces
`INCONCLUSIVE`, and retrieved findings still suppress a thin verdict.
Both negative cases are held by tests in
`tests/unit/test_frontier_channel_roles.py`, because an exemption that
quietly widened would restore the hole it was carved to avoid.

## The sparsity threshold is measured, not tuned

`_F_THIN` is 3 and stays 3. It was never calibrated, and calibrating it
against the labeled corpus would produce a number that looks earned and
is not. Two facts bound what tuning could mean here, both verified
against the code rather than argued from principle.

It discriminates in one narrow band. With three retrieval channels, the
constant changes a verdict only when exactly two are controlled-empty
and the third holds few findings. At three empty the total is zero and
`THIN_FIELD_CANDIDATE` fires under any threshold. At one empty the
branch is unreachable. Most topics never enter the band, so the
effective sample for tuning is far smaller than the corpus.

It counts a reported subset. The threshold compares against
`session.findings`, which is what the agents chose to report, and their
own instructions cap that ("at most 10 findings", "top 2-3 posts"). The
count of results a query actually returned lives in the query log and
feeds `channel_outcomes` instead. A threshold fitted to the reported
number would shift the next time an agent's markdown reworded a cap.

So `make frontier-matrix` reports three things instead of one tuned
integer: the confusion matrix of label against verdict, a sweep of the
threshold across a range showing how many verdicts move, and the
false-THIN rate on the `covered-obscure` class. That last is the honest
headline. Those topics are abundantly published under vocabulary the
obvious query misses, nothing in this design detects vocabulary
mismatch, and `labels.yaml` already names the rate at which they read
thin as "the bound on the signal's value". It is a property to report,
not a defect to tune away.

The matrix carries its own caveat and so does this decision: each topic
is one recorded run from a nondeterministic, rate-limited pipeline, so
the numbers describe the pipeline and the verdict jointly. No test
asserts against them, deliberately. A test pinning an agreement rate
would enshrine a calibration through the back door and turn honest
degradation into a red build.

## Canary targets are re-verified on demand

The three targets are third-party documents, and from inside the
verdict a moved target is indistinguishable from a broken channel: the
control did not come back either way. The remedies are opposite, so
`make verify-canaries` classifies four ways rather than two, separating
`TARGET_MOVED` (edit `canary.py`) from `CHANNEL_ERROR` (investigate the
channel), with `RATE_LIMITED` failing nothing.

It is a script rather than a test on purpose. A test's binary result
collapses the distinction the job exists to draw, and tome's pytest
config carries no `-m "not network"` default, so a network test would
run in CI and redden the suite whenever a third party hiccuped. The
fetch is the only network I/O under `src/tome/`, contained in
`scripts/`, wrapping a pure classifier that tests offline.

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
results. That is the load-bearing fact here and it is mathematical, not
empirical. Only the pre-retrieval family is computable in that regime,
and it is the substantially weaker family: the survey literature
consistently reports it as the cheaper and less accurate of the two.
Specific correlation figures were quoted to this decision by a research
agent that flagged its own source attribution as unverified, so they
are deliberately not repeated. Worth using to trigger reformulation;
not worth grading a finding with.

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
