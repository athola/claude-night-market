---
name: ideate
description: Generate diverse solution candidates with category-spanning ideation methods and rotation. Use when stuck on a design or fighting repetitive LLM output.
category: research
tags:
  - ideation
  - creativity
  - diversity
  - mode-collapse
  - problem-solving
estimated_tokens: 500
model_hint: standard
---

# Ideation: Diverse Methods With Rotation

**Diversity is a selection problem, not a volume problem.**

Generating ten ideas from one mental frame yields ten variations
of the same idea. The fix is to ideate from different categories of
method, then rotate methods across passes so the next round does not
repeat the last. This is the documented lever against LLM mode
collapse, not a brainstorming ritual.

## When NOT To Use

- Surveying what already exists (use `tome:research`)
- Cross-domain analogies specifically (use `tome:triz`)

## The one design rule

Structure the reasoning, not the output.

"The Price of Format" (arXiv 2505.18949) found that rigid output
templates collapse output diversity, while reasoning scaffolds raise
it. So each method hands you a reasoning prompt. Do not force the
ideas into a fixed schema while generating; impose structure only when
reporting the final set.

## Catalog

Seven methods that port to technical problem-solving, each tagged with
an honest evidence grade (see Sources below):

| Method | Category | Evidence |
|--------|----------|----------|
| SCAMPER | transformation | weak |
| SIT task unification | transformation | mixed |
| Morphological analysis | decomposition | mixed |
| SIT subtraction | decomposition | mixed |
| Cross-domain analogy (TRIZ) | analogical | mixed |
| Inversion (pre-mortem) | inversion | anecdotal |
| Constraint provocation | perturbation | anecdotal |

The grades are deliberately conservative. Individual-method evidence
is thin; the value is the diverse-selection-plus-rotation pattern, not
any single method. For the structured analogical form, use
`Skill(tome:triz)`. For finding an implied-but-empty cell in a
concept space, map the field and its hidden optimization axis first,
then apply generation methods to fill the gap.

## Workflow

1. Pick how many approaches you want (3 to 5 is the useful range).
2. Select methods spanning distinct categories:
   `select_methods(n)` from `tome.channels.ideation` returns methods
   from different categories by construction.
3. Apply each method's reasoning prompt to the problem. Generate ideas
   freely; do not normalize them into a schema yet.
4. On a second pass, rotate: `select_methods(n, exclude=used_ids)` or
   `rotation_plan(passes, n_per_pass)` so no method repeats until the
   catalog is exhausted.
5. Score the candidates with `score_idea` (weighted criteria per
   `Skill(leyline:evaluation-framework)`). Novelty claimed without
   evidence is capped, so "novel" must be earned, not asserted.
6. Report the final set with rationale and scores.

## Scoring

`score_idea(scores, novelty_evidence=False)` applies weighted criteria
(novelty 0.25, fit 0.20, feasibility 0.20, simplicity 0.15,
reversibility 0.10, impact 0.10) and an anti-inflation rule: a novelty
score of 8 or higher without supporting evidence is capped to 7. Pass
`novelty_evidence=True` only when you have checked for prior art and
found the idea genuinely new.

## Anti-goals

- Do not generate many ideas from one method and call it diverse.
- Do not impose a rigid output schema during generation; it collapses
  diversity.
- Do not present anecdotal-evidence methods as proven; cite the grade.
- Do not import the full 20-method bundle; the catalog is curated on
  purpose.

## Sources

The diversity rationale and method evidence grades draw on:

- Verbalized Sampling (arXiv 2510.01171): distributional prompting for
  1.6 to 2.1x diversity gains, training-free.
- The Price of Format (arXiv 2505.18949): rigid output schemas collapse
  generation diversity. This is the basis for the
  reasoning-prompt-not-schema rule above.
- Barriers to Diversity in LLM-Generated Ideas (arXiv 2602.20408):
  chain-of-thought reduces fixation; diverse personas restore collective
  diversity.
- The originality and SCAMPER / morphological-analysis education
  literature underpins the per-method evidence grades.
- Innovation Paradox (Shi et al., Design Science 2024): patent
  analysis of 4M+ concepts found originality declined 31% from
  1981-2016 as concept space expanded. Cognitive burden drives
  clustering near familiar terrain rather than the edge.

## Exit Criteria

- [ ] At least 3 candidate approaches were generated, each from a
      method in a distinct category (verifiable: the methods used span
      `>= 3` categories from `list_categories()`).
- [ ] A second pass, if run, used `exclude` or `rotation_plan` so no
      method repeated before the catalog was exhausted.
- [ ] Each candidate carries a weighted score from `score_idea`, with
      any uncapped novelty backed by an explicit prior-art check.
- [ ] The final report structures the output; generation did not.
