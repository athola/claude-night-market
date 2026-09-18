# ADR-0024: Tome Channel Cards and a Record-Based Stop Decision

**Date**: 2026-09-17
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0020 (positive controls, which this builds on),
OctoTools (arXiv 2502.11271, repo commit `fddbc9d`)

## Context

Tome is a toolset workflow. A research session picks channels, sends
each to an agent, and decides whether it has enough. OctoTools frames
that same shape for tool-using agents and reports a 9.3 point average
gain over zero-shot GPT-4o across 16 benchmarks. Two of its parts have
no counterpart in tome:

- **Tool cards.** Each tool carries its input and output contract,
  demonstrations, limitations and best practices. The planner and the
  verifier read the card instead of knowing the tool by name.
- **A context verifier.** After each step it judges completeness,
  unused tools, inconsistencies, verification needs and ambiguities,
  then answers STOP or CONTINUE, inside a step budget.

In tome the facts a card would hold were spread across four places:
`models._VALID_CHANNELS`, an if-ladder in `research_planner.plan`, the
Step 4 table in the research skill, and prose in ADR-0020. None of the
limitations reached an agent's prompt. The parts of a stop decision
existed separately (`channel_outcomes`, `canary_outcomes`,
`frontier_verdict`, `replan`) and nothing combined them: the skill ran
one pass and `replan` had no caller.

The survey behind this ADR ran through tome itself, as three agents:
two on the academic channel (OctoTools' successors, and TRIZ-adjacent
problem-solving frameworks) and one on the triz channel (distant fields
that already solved channel selection, card drift and stopping). The
code and discourse channels were not sent. The topic is methodology,
and the new code card's `when` field records that code search is weak
there. That call was made by hand. The card's `when` field now records it
where the next orchestrator reads it.

## Decision

1. **Channel cards** (`tome.channels.cards`). A frozen dataclass per
   channel: kind (`retrieval` or `generative`), agent, minimum depth,
   whether it runs a positive control, what its prompt must include,
   when it fits, limitations, best practices. The planner gates on
   `min_depth`. `render_card` produces the block each dispatch prompt
   embeds.
2. **Typed fields.** OctoTools keeps limitations in a free
   `user_metadata` dict, and its shipped tools spell the key four ways
   (`limitation`, `limitations`, `best_practice`, `best_practices`). A
   dataclass turns that drift into a `TypeError`. Construction also
   rejects a card with no limitations, and a generative card that
   claims a control.
3. **Cards are pinned to the code they restate.**
   `tests/unit/test_channel_cards.py` fails when the retrieval cards
   differ from `RETRIEVAL_CHANNELS`, when the controlled cards differ
   from `CANARY_TARGETS`, when an agent file is missing, or when a card
   names a query builder that does not exist. The skill's Step 4 table
   is checked against the cards as well.
4. **The stop decision reads records, not judgment**
   (`tome.synthesis.verifier.verify_context`). Each OctoTools criterion
   maps to something no agent graded. The mapping is in
   `skills/research/modules/stop-verifier.md`. A failed criterion names
   channels to `rerun`, `reformulate` or `add`. The pass budget defaults
   to 2: OctoTools averaged 2.56 of 10 steps with GPT-4o, and one tome
   pass sends up to four agents.
5. **Two ideation methods**, each opening a category the catalog lacked
   and each with a controlled study behind it: devil's advocacy and
   multiple working hypotheses. Both are graded `mixed`.
6. **`parse_envelope` reads a top-level `queries` list** when
   `metadata.queries` is absent. See the dogfood findings below.

## Why the verifier does not ask a model

OctoTools asks an LLM. Two later results argue against doing that for a
stop decision. VRR-Stop (arXiv 2607.17641) measured a verifier's
acceptance rate rising while true validity fell, and improved final
validity by 60.6 points over fixed five-round repair on a GSM8K
stress setting by stopping on expected marginal gain.
arXiv 2607.24300 found self-authored
verification unreliable in self-improving agents. ADR-0020 already put
tome's coverage verdict on positive controls for the same reason. The
verifier extends that choice to the loop.

## Dogfood findings

The survey's envelopes were run through `parse_envelope`,
`merge_findings`, `rank_findings`, `frontier_verdict` and then the new
verifier. Four problems came up:

| # | What happened | Disposition |
|---|---------------|-------------|
| F1 | A topic about TRIZ frameworks classified `general` at 0.33, so the plan dropped `triz` | Fixed in pass 2: a `methodology` domain (deep, academic and triz weighted) and agent-framework terms under `ai-agents`. The topic now refines to both at deep depth |
| F2 | The dispatch prompt dictated `{"findings", "queries"}`, the agent obeyed it over its own file, and 27 query records, a canary among them, collapsed into one synthesized log | Fixed twice: the rendered card points at the agent's documented envelope, and the parser reads a top-level `queries` list |
| F3 | An agent put relevance notes in `error`, so working queries counted as failed and the channel read `degraded` | Parser left strict, since the error runs toward INCONCLUSIVE. The card now says `error` is for failed queries only |
| F4 | The triz helper fell back to "flexibility vs complexity" for all four real contradictions | Fixed in pass 2: four workflow pairs in the catalogue with principles from the triz pass, and `formulate_contradictions` returns ranked candidates |

F3 also shows the verifier doing its job: on that session it returned
CONTINUE with `rerun academic`, which is correct for the record it was
given.

## Alternatives rejected or deferred

**Port the OctoTools loop into Python.** Tome's LLM work happens in the
session through skills and agents. A Python planner and executor would
duplicate the harness.

**Cards in YAML.** The ideation catalog is YAML, but a card is read by
code. YAML would need a strict-key parser to get what the dataclass
constructor gives for free.

**Greedy toolset optimization (OctoTools Algorithm 1).** Deferred, and
nothing is built for it. It needs a validation set scored per channel.
The retrieval gold set is synthetic and records no channel, and the
frontier corpus has no recorded envelopes. When the data exists, do not
copy Algorithm 1 as written. It scores each tool alone against the base
and unions every positive one, which ignores overlap between tools
(named as a limitation by HYSET, arXiv 2607.25718). Choose by marginal
gain over the channels already chosen, divided by cost: budgeted
submodular greedy (Krause, Singh and Guestrin, JMLR 2008). The OctoTools
numbers show why that matters. The optimized set scored 58.9 on
validation, and the full set scored 57.4.

**Recall-based stopping.** Deferred. The knee and target methods from
technology-assisted review (arXiv 2106.09871, arXiv 2108.12746), and
species-discovery estimates such as STADS (arXiv 1803.02130), would let
the verifier say how much a clean channel probably missed. All three
need the index of the query that first surfaced each finding. The
query log records a count per query and no attribution. That field is
the prerequisite.

**Capture-recapture across channels.** Already rejected in ADR-0020.
The triz channel proposed it again from Kastner et al. (J Clin
Epidemiol 2009). Its independence assumption does not hold here:
discourse threads link to repositories.

**An embedding router for channel choice.** ToolRet (arXiv 2503.01763)
found strong text retrievers perform poorly at tool selection. With
four channels, explicit card fields are cheaper and inspectable.

**Card calibration intervals.** The metrology bridge (ILAC-G24 / OIML
D 10) suggests giving each card a calibrated-at date that expires. The
drift tests are stronger for facts the code owns, since CI fails the
same day. Calibration fits the facts the code cannot check, such as a
source going dead. The canaries already cover that.

## Framework survey

Candidates for the ideation catalog. The bar was a controlled study and
a category the catalog lacked. Grades were checked against the primary
source where the agent's summary was doubtful, and two were corrected
downward: dialectical inquiry, and the Evaporating Cloud.

| Framework | Evidence found | Grade | Verdict |
|-----------|----------------|-------|---------|
| Devil's advocacy | Schwenk 1990 meta-analysis: beat the expert-plan approach | mixed | Added (`adversarial`) |
| Dialectical inquiry | Same meta-analysis: no advantage over expert plans on ill-structured tasks | weak | Not added |
| Multiple working hypotheses (light form) | Lord, Lepper and Preston 1984, two experiments | mixed | Added (`hypothesis`) |
| Analysis of competing hypotheses (matrix) | Dhami, Belton and Mandel 2019 RCT, 50 analysts: no accuracy gain | weak | Not added, and the added prompt avoids a matrix |
| Strong inference (Platt 1964) | Argued from labs' own output, no experiment | anecdotal | Folded into the light hypotheses method |
| Evaporating Cloud (Goldratt) | One canonical action-research study (Decision 53, 2026), no control group | anecdotal | Not added. First candidate for the contradiction category if a controlled study appears |
| C-K theory | Industrial case studies | anecdotal | Not added |
| Axiomatic design (Suh) | Axioms asserted, case studies | anecdotal | Not added |
| Design Heuristics (Yilmaz, Daly, Seifert) | Classroom comparisons: more diverse concepts, less fixation | mixed | Not added, since `transformation` exists. Candidate to replace SCAMPER (`weak`) |
| WordTree (Linsey, Markman and Wood) | One controlled experiment (J Mech Des 2012): more analogies, more from outside the domain | mixed | Not added, since `analogical` exists. Candidate step for the cross-domain analogy prompt |
| Six Thinking Hats | Classroom RCT on critical-thinking scores, not ideation | weak | Not added |
| Polya's heuristics | Math-education quasi-experiments | weak | Not added |
| USIT, ASIT, BioTRIZ, Synectics | Case studies. Lineage already in SIT and TRIZ entries | anecdotal | Not added |
| Pugh, Delphi, QFD, DSM | Selection and structuring tools, not generation | n/a | Out of scope for ideation |
| Kepner-Tregoe | No independent evaluation found | anecdotal | Not added |
| SELF-DISCOVER, Meta-Reasoning Prompting | Single-paper benchmark gains from choosing reasoning modules per task | mixed | Not a method. The catalog's `when` field could drive such a choice later |

## Consequences

- A fifth channel needs a card, and the tests list what else must
  change with it. `Finding` still validates against `_VALID_CHANNELS`.
  The cards restate that set rather than own it, so `models` does not
  import the card module.
- A session can run a second pass, and the reason for it is written
  down. A pass cut off by the budget reports its gaps.
- The rendered card adds 100 to 130 words (about 210 tokens) to each
  dispatch prompt.
- F1 and F4 were vocabulary gaps in keyword tables. Pass 2 filled
  them. The cards did not, and could not, fix them.

## Pass 2 (2026-09-18)

The verifier asked for a second pass, and the first pass had never
sent the code and discourse channels. Pass 2 sent code, discourse and
academic, each prompt carrying its rendered card. This is what the
cards were built to do, so the pass doubled as their first measurement.

**What the card changed, measured.** With the card pointing at the
agent's envelope file, the code agent returned prose and no envelope;
the discourse and academic agents returned the documented envelope. One
in three. The code agent also built fourteen of its fifteen queries as
free text against the card's best practice. A pointer is not an
instruction, so `render_card` now states the output contract inline:
the final message is one fenced JSON block. That is the second fix for
F2, and unlike the first it follows an observed failure. The query
construction finding is open. Two other findings came from reading the
records: WebFetch refuses `old.reddit.com` in Claude Code, so the
discourse card now names Reddit as a dead source, and Unpaywall answers
422 to tome's placeholder address, so `build_unpaywall_url` now needs a
real one from `TOME_CONTACT_EMAIL`.

**Session record.** Six envelopes over two passes, 95 findings merged
to 92, every control passed, discourse and academic both `degraded`
(Reddit and Semantic Scholar refused). The verifier stopped on the
budget with both listed as gaps. Verdict `INCONCLUSIVE`, which is the
correct reading of a run with two half-blind channels.

**What the channels found.**

The code channel found no card field that earns a place. MCP's four
annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`,
`openWorldHint`) would be constant across tome's read-only channels.
smolagents' `output_type` and AutoGen's typed termination conditions
have their counterparts in the envelope contract and the verifier's
named checks. The agent's star counts were not verified and are not
cited.

The discourse channel returned the case against TRIZ in software from
Hacker News: "a cargo cult, painting by numbers for engineers", and
that applying the principles to software takes enough creativity that
they work "only as a form of provocation like Eno's oblique
strategies". Scores measure attention, and the card says so, but the
claim matches the academic record below, so the triz card's `when`
stands and the ADR states the position: tome's TRIZ channel is a
provocation source, and the ideation catalog grades it `mixed` on the
strength of design-by-analogy experiments, not of TRIZ trials.

The academic channel found no controlled study of TRIZ training on
ideation fluency or novelty. The most cited review (Ilevbare, Probert
and Phaal, Technovation 2013) has none to synthesize, and Spreafico and
Russo's critical survey (Procedia CIRP 2016) exists to grade the case
studies offered in place of one. ARIZ, Su-Field analysis and the
nine-windows operator returned nothing on arXiv with a passing control.
Nothing was added to the ideation catalog from this pass.

Two LLM-plus-TRIZ results changed code. TRIZ-GPT (arXiv 2408.05897,
ASME IDETC 2024) measured GPT-4 mapping free text onto contradiction
parameters at recall 0.69 and precision 0.31, about three candidates
per correct pair, so `formulate_contradictions` now returns the ranked
few and the triz agent searches from each that fits. Terwiesch et al.
(arXiv 2607.27553) found LLM idea sets less diverse than human sets
across three prior datasets, with structural prompt variation restoring
part of the gap, which is the finding behind the ideate skill's design
and a second reason to hand the agent several candidates.
AutoTRIZ (arXiv 2403.13002; Adv. Eng. Informatics 2025) reproduced
textbook contradictions in 7 of 10 cases with no plain-prompt baseline,
and TRIZ-RAGNER (arXiv 2602.23656) reached F1 84.2 on patent
contradiction extraction, which measures reading of existing text.
Both are noted, neither changed code.

**Open after pass 2.** `workflows/research.js` dispatches with its own
briefs and no card, so nothing on that path sees the Reddit limitation
or the inline output contract; its agent files carry the Reddit fact
instead. Card best practices did not change how the code agent built
queries (n=1). Whether the inline output contract holds is
unmeasured until the next dispatch. The two degraded channels are gaps
in the record, not in the field.
