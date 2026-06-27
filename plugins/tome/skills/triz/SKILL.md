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
   worsens Y. For a physical contradiction (one parameter
   pulled toward two opposite values), apply separation in
   time, space, condition, or system/scale instead of
   compromise.
3. Map to adjacent fields using the field taxonomy.
4. Search for solved analogues in those fields.
5. Build bridge mappings with rationale and a confidence
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
- [ ] At least one cross-domain bridge with a confidence
      score is returned per active adjacent field, or the
      field is explicitly reported as yielding nothing.
- [ ] When the canonical matrix is consulted, an empty cell
      is reported as "any of the 40 may apply", not as "no
      solution".
