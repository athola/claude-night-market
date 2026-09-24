---
name: triz
description: Applies TRIZ cross-domain analogical reasoning to find solutions from adjacent fields. Use when stuck on a problem and needing inventive perspectives.
alwaysApply: false
category: research
tags:
  - triz
  - cross-domain
  - innovation
  - analogy
  - altshuller
estimated_tokens: 450
model_hint: standard
---
# TRIZ Cross-Domain Analysis

## When To Use

- Stuck on a problem and need perspectives from other domains
- Exploring cross-domain analogies for inventive solutions

## When NOT To Use

- Standard code search or literature review (use other
  tome channels)
- Problems with obvious, well-known solutions

Apply Altshuller's Theory of Inventive Problem Solving
to find solutions from adjacent fields.

## Depth Levels

| Depth | Fields | Analysis |
|-------|--------|----------|
| light | 1 | Ideality and contradiction |
| medium | 2 | Ideality, contradiction, field mapping |
| deep | 3 | Adds principle suggestions and separation |
| maximum | 5 | Adds distant fields and optional matrix lookup |

## Workflow

1. State the Ideal Final Result: the function delivered
   without the system existing. Ask what would make the
   system unnecessary while the function still happens.
2. Formulate the technical contradiction: improving X
   worsens Y. Every record carries `matched`: `keyword` when
   a catalogue row named the topic, `fallback` when none did.
   Treat a fallback as unformulated: call
   `near_resolutions(topic)` for the rows within one or two
   edits of the topic's words, and restate the topic in a
   row's terms or keep the fallback with a reason. For a
   physical contradiction (one parameter pulled toward two
   opposite values; `physical_contradiction(record)` names
   the known ones), apply separation in time, space,
   condition, or system/scale instead of compromise.
   `separation_strategies` lists the axis the system
   description points at first, with the words that put it
   there in `why`.
3. Probe the statement before searching:
   `reformulation_probes(contradiction)` returns five fixed
   probes, each with its principle and a dated source. Swap
   the sides (#13), relax the equality into a range (#16),
   name the parameter and direction that would surface a
   near-solution (#35), promote a constant to a variable
   (#15), and ask whether any value satisfies both demands.
   The swap probe carries both principle sets and
   `principle_set_differs`. Show the inverted form only when
   it is true. Answer each in a line or dismiss it with a
   reason. When
   nothing satisfies both, stop searching harder: separate
   the demands or state the ideal final result.
4. Map to adjacent fields using the field taxonomy.
5. Search for solved analogues in those fields.
6. Build bridge mappings with rationale and a confidence
   score.

## Field Mapping Strategy

- Software architecture: civil engineering, biology
- Data structures: logistics, materials science
- Algorithms: operations research, genetics
- Security: military strategy, immunology
- Financial: game theory, ecology

## Related

TRIZ is the analogical method in the broader ideation catalog.
For diverse, category-spanning ideation with rotation, see
`Skill(tome:ideate)`.

## Limitations

- The built-in contradiction catalog maps common software
  trade-offs to principles. It is a convenience mapping
  rather than part of the classical TRIZ Body of Knowledge, which is
  scoped to technological systems.
- The optional canonical matrix is a sparse subset of
  Altshuller's 39x39 engineering-parameter table. It has
  been frozen since 1985 and uses engineering, not software,
  parameters. Treat it as a cross-check, not the primary
  source.
- An empty matrix cell does not mean "no solution". By the
  empty-box convention, any of the 40 principles may apply.
- The strongest, most portable parts of TRIZ are the 40
  principles as a divergence checklist and Ideality as a
  framing question. ARIZ, Substance-Field analysis, the 76 standard
  solutions, the Laws of Technical Systems Evolution (S-curves), and
  Function-Oriented Search (FOS) are out of scope here.

## Sources

- TRIZ Body of Knowledge (MATRIZ) and the classical
  contradiction matrix (matriz.org).
- AutoTRIZ (arXiv 2403.13002, 2024): LLM-driven TRIZ ideation.
- TRIZ Agents (arXiv 2506.18783, 2025): multi-agent LLM orchestration
  across TRIZ steps; companion to AutoTRIZ.
- Madrigal, "The Shadows Lurking in the Equations" (gods.art, 2025)
  and the literature the reformulation probes cite: Chinneck,
  Feasibility and Infeasibility in Optimization (2008); Allgower and
  Georg, Numerical Continuation Methods (1990); Liberti,
  Reformulations in Mathematical Programming (2009); Duncker, On
  Problem-Solving (1945); Hipple, TRIZ Separation Principles (2012).
  ADR-0026.
- The vendored canonical 39x39 matrix subset comes from
  NickScherbakov/Heinrich-The-Inventing-Machine (Apache-2.0);
  see `src/tome/channels/triz_data/NOTICE` for attribution and
  the exact vendored scope.

## Exit Criteria

- [ ] An Ideal Final Result statement is produced before the
      search begins.
- [ ] A technical contradiction is stated as "improving X
      worsens Y" (or a physical contradiction is named with a
      separation axis).
- [ ] A `fallback` record is either restated in a catalogue
      row's terms via `near_resolutions` or kept with a stated
      reason. It is never reported as a keyword match.
- [ ] Each of the five reformulation probes is answered in a
      line or dismissed with a reason. An infeasible verdict
      routes to separation or the ideal final result and no
      analogy search follows it.
- [ ] At least one cross-domain bridge with a confidence
      score is returned per active adjacent field, or the
      field is explicitly reported as yielding nothing.
- [ ] When the canonical matrix is consulted, an empty cell
      is reported as "any of the 40 may apply", not as "no
      solution".
