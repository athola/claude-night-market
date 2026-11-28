# ADR-0031: Review Questions Are Answered in Order

**Date**: 2026-11-24
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0021 (PR descriptions), ADR-0029 (PRs as the human gate)

## Context

A pull request review mixes four questions:

1. Is this change needed?
2. Is the approach right, given the time available?
3. Does the code do what it claims?
4. Does it fit the team's understanding of the system?

A maintainer proposed that the first two belong before the PR, in
issues, design docs, RFCs or pairing. The answers then bound the last
two: once the approach is agreed, review time can go to the places it
could still be wrong. `sanctum:pr-review` asked none of this. Its
Phase 1 found a scope baseline, then reviewed the code as if the
approach were open.

A tome research session tested the proposal over two passes, through
practitioner discourse, academic literature and published guidance.

## What the evidence says

**Settling need and approach first has correlational support and
practitioner consensus.** No study measures the effect of agreeing a
design before the PR on review outcomes. Zanaty et al. found
design comments are 9% to 14% of OpenStack review comments, and changes
that draw design feedback are abandoned more often (p < 0.001).
Uchôa et al. found most reviews do little against design degradation,
and long, contested discussions go with more of it. At Google, teams
disagree whether design belongs before the first review or in it, and
the paper names that disagreement as a source of friction. Practitioner
guidance converges: Cheney writes that "A code review is not the place
for arguments about design", and Laycock writes "If we want to explore
alternative solutions, I'd rather do that before implementing one of
them." The GDS Way says "You should not use PRs for architectural
review, as you should do the architectural review before raising the
PR." Berczuk names the symptom when it does not: reviewers "reiterating
design discussions during a review".

The oldest evidence agrees on the order. Fagan's inspection process
inspects the design (I1) as its own stage, then the code (I2). In one
Aetna application, design and code inspections together found 82% of
the errors seen through six months of use. In an IBM sample they raised
coding productivity 23%. That is a formal process measured in 1976
against estimates and a walk-through sample. It is not a controlled
comparison of pull request review.

**It is not needed for every change.** Wayne notes that a separate
design round costs a round and suits large changes. Ship/Show/Ask
grades the ceremony by the change. Google's reviewer guide calls design
"the most important thing to cover in a review", which is the right
default when nothing was agreed earlier.

**No source measures whether an agreed design narrows the bug space.**
That part stays a hypothesis.

**Risk-ordered attention is partly supported.** Defect risk concentrates
by prior defects, size and authorship (Krutauz et al.). Ranking only
beats random selection when it accounts for effort (Mende and Koschke).
Attention fades with size and file position. One preprint measures
latent-bug rates rising from 56.7% at the first file to 61.5% at the
thirtieth. Fagan prescribes the same focus: inspectors first study "the
ranked distributions of error types found by recent inspections" to
"concentrate on the most fruitful areas", and the moderator flags areas
reworked since the design inspection. No study tests risk-guided review
against outcomes.

**Skimming the rest is contradicted.** About three quarters of what
review finds is evolvability rather than function (Mäntylä and
Lassenius; Beller et al.). Review's best-evidenced outcomes are
knowledge transfer and awareness (Bacchelli and Bird; Rigby and Bird).
A review that skips files loses the outcome review is known to deliver.

## Decision

1. **Phase 1 locates the decision record.** `pr-review` records Q1 and
   Q2 as `settled (<link>)` or `unsettled`. Module
   `review-questions.md` holds the lookup order.
2. **A settled decision is checked, not re-argued.** Disagreement with
   it is a new finding category, REVISIT. It is posted on the record and
   does not block. A PR that surfaces facts the decision lacked is
   BLOCKING. A deviation from the record is IN-SCOPE.
3. **Unsettled matters only when the change is design-bearing**: a new
   component, public contract, data model, dependency or cross-team
   behavior. Then the design is reviewed first, and a large objection
   pauses line review.
4. **Q3 is ordered, and the order is disclosed.** Risky hunks are read
   first. The report lists files read lightly.
5. **Q4 covers every file.**
6. **The author supplies both ends.** The description's Why links where
   the need and approach were agreed, and the how ends with a "Where to
   look" line. `pr-prep` warns before a design-bearing PR opens without
   a record. The facts table stays at three rows, because the ADR-0021
   amendment observed reviewers deleting it.

## Rejected alternatives

**Trust the rest when a record exists.** This was the proposal's
strongest form. It was rejected because no source supports it and the
evolvability findings argue against it.

**Route settled-design disagreement as BACKLOG.** A backlog issue tracks
debt in code. A REVISIT questions a decision, and belongs on the record
that made it, where the people who decided will see it.

**A pre-PR gate that blocks without a record.** ADR-0029 keeps the PR as
the human gate. A second gate before it would add ceremony to routine
changes that the evidence says do not need it.

## Consequences

Reviews of agreed work get shorter where it counts: no design debate on
a decided approach. Reviews of unagreed design-bearing work get longer
and say why. The "Read lightly" list makes partial attention visible.

The contract test `plugins/sanctum/tests/unit/skills/test_review_questions.py`
anchors each passage, including the command's copy of Phase 1.

Research gaps: Reddit was unreachable in both passes, and Semantic
Scholar was mostly rate-limited (OpenAlex answered instead). Fagan's
1976 figures were not read. No study of design agreement's effect on
review outcomes was found.

## Sources

- Zanaty, Hirao, McIntosh, Ihara, Matsumoto, "An empirical study of
  design discussions in code review", ESEM 2018.
  <https://doi.org/10.1145/3239235.3239525>
- Uchôa et al., "How Does Modern Code Review Impact Software Design
  Degradation?", ICSME 2020. <https://doi.org/10.1109/icsme46990.2020.00055>
- Sadowski, Söderberg, Church, Sipko, Bacchelli, "Modern code review: a
  case study at Google", ICSE-SEIP 2018 (full text read).
  <https://doi.org/10.1145/3183519.3183525>
- Bacchelli and Bird, "Expectations, outcomes, and challenges of modern
  code review", ICSE 2013. <https://doi.org/10.1109/icse.2013.6606617>
- Mäntylä and Lassenius, "What types of defects are really discovered in
  code reviews?", TSE 2009. <https://doi.org/10.1109/tse.2008.71>
- Beller, Bacchelli, Zaidman, Juergens, "Modern code reviews in
  open-source projects: which problems do they fix?", MSR 2014.
  <https://doi.org/10.1145/2597073.2597082>
- Rigby and Bird, "Convergent contemporary software peer review
  practices", ESEC/FSE 2013. <https://doi.org/10.1145/2491411.2491444>
- Krutauz, Dey, Rigby, Mockus, "Do code review measures explain the
  incidence of post-release defects?", EMSE 2020.
  <https://doi.org/10.1007/s10664-020-09837-4>
- Mende and Koschke, "Effort-aware defect prediction models", CSMR 2010.
  <https://doi.org/10.1109/csmr.2010.18>
- Rahman, Codabux, Roy, "Does Order Matter?", arXiv 2609.22610
  (preprint, abstract only). <https://arxiv.org/abs/2609.22610>
- Fagan, "Design and code inspections to reduce errors in program
  development", IBM Systems Journal 15(3), 1976 (full text read).
  <https://doi.org/10.1147/sj.153.0182>
- GDS, "Pull requests", The GDS Way (reviewed 2026-08-20).
  <https://gds-way.digital.cabinet-office.gov.uk/standards/pull-requests.html>
- Berczuk, "Contextual Pull Requests", 2025.
  <https://steveberczuk.substack.com/p/contextual-pull-requests>
- Google, "What to look for in a code review".
  <https://google.github.io/eng-practices/review/reviewer/looking-for.html>
- Wilsenach, "Ship / Show / Ask".
  <https://martinfowler.com/articles/ship-show-ask.html>
- Oxide, "RFD 1: Requests for Discussion".
  <https://rfd.shared.oxide.computer/rfd/1>
- Cheney, "Talk, then code". <https://dave.cheney.net/?p=3585>
- Laycock, "Code review".
  <https://martinfowler.com/rachels-ramblings/code-review.html>
- Wayne, "Code review vs code proofreading".
  <https://buttondown.com/hillelwayne/archive/code-review-vs-code-proofreading>
