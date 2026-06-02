# Research: Coupling Implementation Ambition to Demonstrated Competence

**Session:** 3dfdba53-a9a4-4177-b94f-1a9c6acd2449
**Date:** 2026-06-02
**Channels:** academic, discourse, code, triz
**Domain:** architecture / learning-science / human-automation systems

## Thesis

Round 1 (session 19c28f3c) built the verification spine against
blind trust of agent output. It covered five of the six
principles that study recommended. This pass targets the gap the
follow-up opened: a workflow should start with a bounded,
intentional implementation and ramp ambition up a notch only as
the human's understanding of the prior increment is demonstrated.

That is the same move the learning sciences made for novices:
not "ban the tool," but force graduated practice where the next
challenge is coupled to proven competence on the last one. The
design question is therefore: what is the advancement criterion,
and how is it protected from being faked?

## Thread A: the advancement number is real and converges

Five independent literatures land on the same target band: keep
the learner where they succeed most of the time but not all of
it, and move the difficulty to hold that point.

| Source | Mechanism | Encodable criterion |
|--------|-----------|---------------------|
| Wilson et al. 2019, Nature Comms 10:4646 | optimal training error for gradient learners | success rate ~85% (error 15.87%); above -> advance, below -> hold |
| Bloom 1968 / Keller 1968 (PSI) | mastery learning, formative gate per unit | advance a unit at >=90% (Keller: 9/10) on a fresh check |
| Corbett & Anderson 1995 (BKT) | latent mastery HMM, slip/guess noise model | advance when p(mastery) >= 0.95 |
| Platanios et al. 2019 (NAACL) | competence-based curriculum | only attempt tasks with difficulty CDF <= c(t); c(t)=sqrt(t(1-c0^2)/T + c0^2) |
| Ericsson et al. 1993 | deliberate practice at edge of ability | advance the target on reliable success; isolate the weak rep otherwise |
| Vygotsky 1978 / Csikszentmihalyi 1990 | ZPD / flow channel | succeed with support, fade support, move the zone on unsupported success |

The 85% rule is the quantitative spine: it is the same number
the ZPD boundary, the edge of ability, and the flow channel all
gesture at, derived formally rather than by analogy.

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
"graduate the operator to higher autonomy only when proven,
without stalling and without faked readiness":

1. **Per-capability, not global.** Medical EPAs score each task
   on a 1-5 supervision scale; driver licensing restricts by
   context (no night driving) rather than one global dial. Map
   ambition as a vector of capability-specific levels, simple
   capabilities advanced first.
2. **Externally judged artifact.** The guild masterpiece, ABRSM's
   visiting examiner, and EPA observed milestones all separate
   the producer from the certifier. This is the four-eyes
   principle and the universal anti-gaming device: readiness
   cannot be self-attested.
3. **Clean-record gating beats time-served.** GDL lifts
   restrictions only after a conviction-free window; one bad
   merge resets the clock and can demote a tier.
4. **Defeat faked readiness with novelty.** ABRSM sight-reading
   uses an unseen piece; medicine rejected "see one, do one,
   teach one" because confidence outran competence (28-42% of
   residents felt unsafe doing a procedure solo the first time).
5. **Guard the assistance dilemma directly.** Aviation's
   "children of the magenta": ramp autonomy faster than retained
   understanding and the operator can no longer hand-fly or
   override. Countermeasure: mandatory periodic hand-flying.

Dominant TRIZ principles: #15 dynamics, #16 partial action
(deliberately under-automate to keep the human in the loop), #23
feedback, #24 intermediary, #25 self-service, #1/#3 segmentation
by stakes.

## Thread D (code): mechanisms to borrow

| Project | Mechanism | Maps to |
|---------|-----------|---------|
| CAHLR/pyBKT | posterior mastery update, advance at p>=0.95 | competence estimate with slip/guess |
| open-spaced-repetition/py-fsrs | stability grows on success, collapses on lapse | scope grows on clean increment, resets on regression |
| eaplatanios/curriculum | c(t) competence gate over difficulty CDF | the literal graduated-scope schedule |
| Feryal/automated-curriculum-rl (TSCL) | sample task by learning-progress slope | retire a rung when its slope flattens (anti-stall) |
| nizos/tdd-guard | PreToolUse block/allow state machine | runtime gate mechanism for an agent |
| Swarmia five-level autonomy | start at L3, expand as trust builds | progressive-autonomy ladder for coding agents |

## What this means for night-market

The codebase already has the verification spine and, from Round
1, `imbue:assisted-mastery` (visible reasoning, explain/produce
modes, fading) and `leyline:risk-classification` automation
tiers. The missing piece is the *ramp*: nothing couples the
ambition of the next increment to demonstrated understanding of
the last one. assisted-mastery fades scaffolding; this ramps
challenge. They are the two directions of the same axis.

## Recommended principles for the workflow improvement

1. Start at the smallest intentional increment; do not design
   the whole system up front.
2. The advancement gate is demonstrated understanding of the
   prior increment, sized to its blast radius, not its
   completion. Target the ~85% band: ramp on clean
   demonstration, hold and re-scaffold below it, ramp faster
   when the human clears it trivially (anti over-drill).
3. The producing agent may not certify the human's readiness to
   ramp (four-eyes); for high-stakes rungs the check uses a
   novel question about the actual change, not a rehearsed one.
4. Ambition is per-capability and per-stakes, not a single dial.
   Lift restrictions on a clean record; a regression resets the
   clock and can demote a rung.
5. Periodically force the human to hand-fly: explain the last
   increment unaided. If they cannot, drop the tier rather than
   ramp it (the magenta guard).
6. Retire a rung when progress flattens; never-advancing is as
   much a failure as advancing too fast.

## Sources

Primary: Wilson et al. 2019 (Nature Communications 10:4646,
DOI 10.1038/s41467-019-12552-4); Bloom 1968/1984; Keller 1968;
Corbett & Anderson 1995; Platanios et al. 2019 (NAACL); Ericsson,
Krampe & Tesch-Romer 1993; Bjork & Bjork 1992; Csikszentmihalyi
1990; Doroudi & Brunskill 2017 (EDM); Cen, Koedinger & Junker
2007 (AIED); Baker, Corbett & Koedinger 2004 (ITS); Settles &
Meeder 2016 (ACL); Matiisen et al. 2017 (TSCL, arXiv 1707.00183).
Cross-domain: AAMC EPAs, "children of the magenta" (Van Der Burgh
1997), graduated driver licensing, medieval guild masterpiece,
ABRSM graded exams. Code: pyBKT, py-fsrs, eaplatanios/curriculum,
nizos/tdd-guard, Swarmia autonomy levels.
