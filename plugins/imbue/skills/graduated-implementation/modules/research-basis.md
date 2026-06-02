# Research Basis: Graduated Implementation

The evidence base behind this skill. The SKILL.md Overview
summarizes the load-bearing findings; this module preserves the full
tables, failure modes, cross-domain convergence, and citations for
auditing the claims.

## Thread A: the advancement number is real and converges

Five independent literatures land on the same target band: keep the
learner where they succeed most of the time but not all of it, and
move the difficulty to hold that point.

| Source | Mechanism | Encodable criterion |
|--------|-----------|---------------------|
| Wilson et al. 2019, Nature Comms 10:4646 | optimal training error for gradient learners | success rate ~85% (error 15.87%); above the band advance, below it hold |
| Bloom 1968 / Keller 1968 (PSI) | mastery learning, formative gate per unit | advance a unit at >=90% (Keller: 9/10) on a fresh check |
| Corbett & Anderson 1995 (BKT) | latent mastery HMM, slip/guess noise model | advance when p(mastery) >= 0.95 |
| Platanios et al. 2019 (NAACL) | competence-based curriculum | only attempt tasks with difficulty CDF <= c(t); c(t)=sqrt(t(1-c0^2)/T + c0^2) |
| Ericsson et al. 1993 | deliberate practice at edge of ability | advance the target on reliable success; isolate the weak rep otherwise |
| Vygotsky 1978 / Csikszentmihalyi 1990 | ZPD / flow channel | succeed with support, fade support, move the zone on unsupported success |

The 85% rule is the quantitative spine: it is the same number the ZPD
boundary, the edge of ability, and the flow channel all gesture at,
derived formally rather than by analogy.

## Thread B: the three failure modes are documented with numbers

| Failure mode | Evidence | Guard |
|--------------|----------|-------|
| Advancing too fast (under-mastery) | BKT semantic degeneracy p(G)+p(S)>1 (Doroudi & Brunskill 2017); fading before retrieval is durable (Bjork 1992) | bound the estimate (plausibility limits); require several consistent successes, not one |
| Never advancing (over-drill / boredom) | Cen & Koedinger 2007: skills need ~7 reps but many are over-practiced; SM-2 "ease hell" spirals review load until decks are abandoned | retire a rung when progress slope flattens (TSCL); cap reps; do not ratchet difficulty down on every stumble |
| Gaming the metric (Goodhart) | Duolingo: long streaks and cleared mastery with no conversational ability (HN 19825632); Baker 2004: gamers learn 2/3 as much | make the competence signal expensive to fake; test on novel work; separate producer from certifier |

The Duolingo case is the load-bearing warning: a cheap signal
(completion, streak, "tests pass") will be satisfied without the
understanding the ladder was built to certify.

## Thread C (TRIZ): cross-domain convergence on the gate design

Five high-stakes apprenticeship domains independently resolved
"graduate the operator to higher autonomy only when proven, without
stalling and without faked readiness":

1. **Per-capability, not global.** Medical EPAs score each task on a
   1-5 supervision scale; driver licensing restricts by context (no
   night driving) rather than one global dial. Map ambition as a
   vector of capability-specific levels, simple capabilities advanced
   first.
2. **Externally judged artifact.** The guild masterpiece, ABRSM's
   visiting examiner, and EPA observed milestones all separate the
   producer from the certifier. This is the four-eyes principle and
   the universal anti-gaming device: readiness cannot be
   self-attested.
3. **Clean-record gating beats time-served.** GDL lifts restrictions
   only after a conviction-free window; one bad merge resets the
   clock and can demote a tier.
4. **Defeat faked readiness with novelty.** ABRSM sight-reading uses
   an unseen piece; medicine rejected "see one, do one, teach one"
   because confidence outran competence (28-42% of residents felt
   unsafe doing a procedure solo the first time).
5. **Guard the assistance dilemma directly.** Aviation's "children of
   the magenta": ramp autonomy faster than retained understanding and
   the operator can no longer hand-fly or override. Countermeasure:
   mandatory periodic hand-flying.

Dominant TRIZ principles: #15 dynamics, #16 partial action
(deliberately under-automate to keep the human in the loop), #23
feedback, #24 intermediary, #25 self-service, #1/#3 segmentation by
stakes.

## Thread D (code): mechanisms to borrow

| Project | Mechanism | Maps to |
|---------|-----------|---------|
| CAHLR/pyBKT | posterior mastery update, advance at p>=0.95 | competence estimate with slip/guess |
| open-spaced-repetition/py-fsrs | stability grows on success, collapses on lapse | scope grows on clean increment, resets on regression |
| eaplatanios/curriculum | c(t) competence gate over difficulty CDF | the literal graduated-scope schedule |
| Feryal/automated-curriculum-rl (TSCL) | sample task by learning-progress slope | retire a rung when its slope flattens (anti-stall) |
| nizos/tdd-guard | PreToolUse block/allow state machine | runtime gate mechanism for an agent |
| Swarmia five-level autonomy | start at L3, expand as trust builds | progressive-autonomy ladder for coding agents |

## Provenance

Originally captured as research session 3dfdba53 (2026-06-02;
channels: academic, discourse, code, triz). This pass targeted the
gap that session 19c28f3c (see `assisted-mastery`
`modules/research-basis.md`) opened: a workflow should start with a
bounded, intentional implementation and ramp ambition only as the
human's understanding of the prior increment is demonstrated.

## Sources

Primary: Wilson et al. 2019 (Nature Communications 10:4646,
DOI 10.1038/s41467-019-12552-4); Bloom 1968/1984; Keller 1968;
Corbett & Anderson 1995; Platanios et al. 2019 (NAACL); Ericsson,
Krampe & Tesch-Romer 1993; Bjork & Bjork 1992; Csikszentmihalyi 1990;
Doroudi & Brunskill 2017 (EDM); Cen, Koedinger & Junker 2007 (AIED);
Baker, Corbett & Koedinger 2004 (ITS); Settles & Meeder 2016 (ACL);
Matiisen et al. 2017 (TSCL, arXiv 1707.00183). Cross-domain: AAMC
EPAs, "children of the magenta" (Van Der Burgh 1997), graduated
driver licensing, medieval guild masterpiece, ABRSM graded exams.
Code: pyBKT, py-fsrs, eaplatanios/curriculum, nizos/tdd-guard,
Swarmia autonomy levels.
