# ADR-0026: TRIZ Records Carry Their Residual

**Date**: 2026-09-18
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0024 (tome channel cards and record-based stop, which
added the research-workflow rows to the contradiction catalogue),
ADR-0025 (fan-outs report what they dropped)

## Context

Caleb Madrigal's "The Shadows Lurking in the Equations" (gods.art,
2025-11-05) plots `|left - right|^k` in place of the exact equality and
names three structures the zero set hides: underwater islands
(near-solutions that surface when `sin(2.7y)` becomes `sin(2.8y)`),
black holes (regions with no solution and strong topography, as in
`1/(x^2+y^2) = 0`), and shadow lines (structure visible only in the
inverted or divided arrangement). Two Hacker News threads discussed it.
On the 2025 thread (45823141, 308 points, 86 comments) the consensus
was that the mathematics is not new: rustybolt and andrewflnr pointed
out that the graph is by definition the zero set and that the picture
is a level set, semi-extrinsic that PDE visualization has done this
since the 1960s, and the author (calebm) conceded the opening sentence
was hyperbolic. On the 2026 thread (49721507, 50 points, 9 comments)
rcxdude observed that the visualization is an artifact of how the
equation is arranged, since moving a term across the equals sign
changes the picture without changing the line, Enginerrrd read it as
the constant-as-variable generalization `f(x, y) = z`, and aeve890
linked it to f(R) gravity and to TRIZ, "trying to find assumptions or
constraints and playing with variations of them".

The mission was to read the article as TRIZ and improve tome's triz
channel with whatever survived. Five tome channels ran (academic,
discourse, triz, code, web) with cards embedded and positive controls
in place. Fifty-six findings merged to forty-eight. The frontier
verdict was INCONCLUSIVE and the verifier stopped at the pass budget
with reruns outstanding: Semantic Scholar returned HTTP 429 on three
queries in pass 1 and on two of them again on retry in pass 2,
WebFetch cannot reach Reddit from this environment, and one web page
timed out. Those are gaps in the run and are recorded as such in the
session reports under `docs/research/` (machine-local; gitignored).
The triz analyst reached the article at
`gods.art/articles/equation_shadows.html` on its second attempt after
a 404 on the URL it was first given.

Every bridge the research proposed was checked against what TRIZ
already holds. The verdicts:

| Article structure | TRIZ counterpart | Verdict |
|-------------------|------------------|---------|
| Shadow lines in the inverted form | ARIZ-85C step 1.1 writes both technical contradictions (TC-1 and TC-2) and step 1.4 chooses one; principle 13 | Already in TRIZ; tome never ran it |
| Black hole: no solution, strong topography | ARIZ-85C step 3.3 triage to a physical contradiction; separation principles; ideal final result | Already in TRIZ; the trigger for it was missing |
| Underwater islands | Numerical continuation (Allgower and Georg 1990): a near-solution is a solution branch at a nearby parameter | The measure is new to tome; the idea is 1990 |
| Constant promoted to a variable | Principle 35, the Feynman parameter trick, f(R) gravity | Least novel; already a probe |
| The fuzzy graph itself | Level sets (Osher and Sethian 1988), domain coloring (Farris 1998), marching squares | Not new; the web channel confirmed no TRIZ source frames contradiction resolution as a continuum (Oxford Creativity presents four discrete separation categories) |

Two defects in the existing channel came out of the same reading:

- `formulate_contradictions` fell back to `flexibility` versus
  `complexity` whenever no catalogue keyword matched, and the fallback
  record was indistinguishable from a matched one. The analyst noticed
  it on this very session's topic, which scores zero hits against all
  nine populated rows. That is the equality-only picture: a topic
  either matched or the function invented one, with nothing in between
  and no mark on the invented record.
- `FIELD_ADJACENCY` had no rows for `methodology` or `ai-agents`, two
  of the ten domains the classifier emits, so both fell through to the
  `general` list.

## Decision

Four mechanisms, each with a source that names the operation and a
test that fails without it.

1. **Every contradiction record carries `matched`**, `keyword` when a
   catalogue row named the topic and `fallback` when none did. The
   skill and the agent treat a fallback as unformulated.

2. **`near_resolutions(topic)` keeps the residual.** For each row with
   no exact hit it reports the smallest edit distance between one of
   the row's keywords and one of the topic's words, returning up to
   three rows within two edits, best first. Widening is satisficing
   (Simon 1956): nothing is returned when an exact match exists, radius
   one is tried before radius two, and the search stops at the first
   radius that yields anything. Words under four letters are ignored
   because two edits from three letters reach everything. The exact
   predicate is one function shared with `formulate_contradictions`,
   and a test asserts the two agree over every catalogue keyword.

3. **`physical_contradiction(record)` routes before the principle
   search.** True when the pair is in a small table of two demands on
   one quantity (early stopping and completeness, coverage and cost,
   consistency and availability) or when the two labels share a word.
   The skill routes a true result to separation or to the ideal final
   result. `separation_strategies` now ranks the four axes by hint
   words in the system description (schedule and lifecycle point at
   time, boundary and layer at space, flag and mode at condition,
   cluster and subsystem at scale) and says in `why` which words put an
   axis first. Whole words only, so "model" does not read as "mode".
   Ties keep the canonical order.

4. **The swap probe reports its principle delta.** The first
   reformulation probe now carries `principles`, `swapped_principles`,
   and `principle_set_differs`. The display rule for a reader: show the
   inverted form only when its principle set differs, which is what
   makes ARIZ step 1.4's choice cheap.

`FIELD_ADJACENCY` gains rows for `methodology` and `ai-agents`, and a
test now asserts every classifier domain has its own row.

## Consequences

- A session whose topic no catalogue row describes now says so. The
  agent either restates the topic in a near row's terms or keeps the
  fallback with a reason, and the exit criteria require one or the
  other.
- The near-miss search is syntactic. Edit distance over keywords
  finds a typo or an inflection and nothing deeper, and the docstring
  says so. A semantic near miss is the agent's job.
- The physical-contradiction table is three pairs. It will grow as
  rows do, and a pair that is vacuous for semantic reasons passes
  through unflagged. An empty matrix cell is still never the signal.
- The equality-versus-continuum reading extends TRIZ. The web channel
  looked for a source that frames contradiction resolution as a
  continuum and found none.
  The skill's Sources section cites the mathematics behind the probes
  and this ADR, and does not claim TRIZ provenance for the continuum.
- Discourse attributions were checked against the raw thread JSON
  under `.attune/research/` (machine-local; gitignored), since the
  discourse scanner's envelope swapped two commenters and misattributed
  the TRIZ remark. Any quote in this ADR comes from the raw thread.

## Sources

- Madrigal, "The Shadows Lurking in the Equations", gods.art, 2025.
- Hacker News 45823141 (2025-11) and 49721507 (2026-09-16).
- Altshuller, ARIZ-85C, steps 1.1, 1.4, 3.3.
- Allgower and Georg, Numerical Continuation Methods, 1990.
- Chinneck, Feasibility and Infeasibility in Optimization, 2008.
- Liberti, Reformulations in Mathematical Programming, 2009.
- Duncker, On Problem-Solving, 1945; Knoblich, Ohlsson, Haider and
  Rhenius, "Constraint relaxation and chunk decomposition in insight
  problem solving", 1999.
- Simon, "Rational choice and the structure of the environment", 1956.
- Hipple, "TRIZ Separation Principles", 2012; Oxford Creativity, "What
  are Contradictions?".
- Osher and Sethian, "Fronts propagating with curvature-dependent
  speed", 1988; Farris, domain coloring, 1998.
