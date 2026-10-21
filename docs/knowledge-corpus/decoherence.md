---
id: decoherence
title: Decoherence and Competing Models in Agent-Written Code
maturity: seedling
importance_score: 70
routing_type: both
tags:
  - code-quality
  - ai-generated-code
  - migrations
  - documentation
  - decision-making
sources:
  - https://maevyn.codes/decoherence
  - https://arxiv.org/abs/2511.04427
  - https://arxiv.org/abs/2603.28592
  - https://fion.ac/jellyfish.pdf
  - https://arxiv.org/abs/2606.21804
  - https://arxiv.org/abs/2605.21384
  - https://arxiv.org/abs/2409.10781
  - https://arxiv.org/abs/2511.00215
  - https://arxiv.org/abs/1701.05472
related_artifacts:
  - plugins/conserve/skills/elegant-code/SKILL.md
  - plugins/conserve/scripts/detect_duplicates.py
  - plugins/imbue/skills/karpathy-principles/SKILL.md
  - plugins/conserve/skills/decisive-action/SKILL.md
  - plugins/abstract/skills/escalation-governance/SKILL.md
  - plugins/leyline/skills/evaluation-framework/SKILL.md
  - plugins/scribe/skills/doc-generator/SKILL.md
last_updated: 2026-10-21
---

# Decoherence and Competing Models in Agent-Written Code

Reader: practitioner maintaining night-market skills, rules and hooks.

A second way of doing something the codebase already does is the
change to refuse. Each model is locally valid. The cost lands on every
later change, which has to translate between them. This page holds the
evidence the skills cite, and each number is stated here once.

## The claim

Kristen Maevyn's essay "The Decoherence Trap" (2026-10-14, CC BY 4.0)
defines decoherence as "the accumulation of locally valid but mutually
incompatible or redundant models within a system, such that the cost
of change is dominated by translating among those models and
preventing unintended side-effects." Four claims from it shape the
skills:

1. Decoherence grows with change, and stays put while a system is left
   alone. Agents raise the rate of change.
2. Under pressure an expert stops the analysis earlier and adds "extra
   safeguards, just in case". The next change then costs more.
3. Starting a second transition before the first finishes is the worst
   case, because the combinations multiply.
4. A measurable proxy optimized as a target drifts from the goal
   (Goodhart). Coherence can only be checked against real use.

## What is measured and what is argued

The core claim, that coexisting models of one concern raise the cost
of change, is argument. Two tome research passes (arXiv, then
OpenAlex; Semantic Scholar was rate-limited both times) found no study
that measures it. The nearest result covers redundancy only.

| Source | Status | Finding |
|--------|--------|---------|
| He et al., MSR '26, arXiv 2511.04427 | peer reviewed, full text read | 806 repos adopting Cursor vs 1,380 matched. Lines added rose 3-5x in month one and returned to baseline within two months. Static-analysis warnings +30.3% and complexity +41.6% persisted. The paper also reports +25.1% for complexity, unreconciled |
| Liu et al., arXiv 2603.28592 | preprint, full text read | 9.1% of 302,579 AI-authored commits introduce at least one issue. 22.7% of tracked issues survive at HEAD, flat across age cohorts. Broad exception handling is the most common issue (8.5%). No human baseline |
| Chen and Stratton, Harvard working paper, 2026-08-04 | unreviewed, full text read | Agent adoption across about 700 firms: lines +30%, resolved issues not significantly higher (rules out more than 12%). Time to review a PR +49%. Share of PRs with changes requested 0.13 to 0.25. PR size unchanged |
| Juergens et al., ICSE 2009, arXiv 1701.05472 | peer reviewed, full text read | 5 systems, 1,427 clone groups, 724 changed inconsistently. 107 of those were faults confirmed by the systems' developers |
| Patel et al., arXiv 2606.21804 | preprint, abstract only | An agent extending agent-written code resolves up to 13.1% fewer tasks. Traditional maintainability metrics explain little of the gap |
| SpecBench, arXiv 2605.21384 | preprint, abstract only | The gap between visible and held-out test pass rates grows 28 points per tenfold increase in code size |
| Radmanesh et al., arXiv 2409.10781 | preprint, abstract only | Code changes left inconsistent with their comments are about 1.5x more likely to introduce a bug |
| DocPrism, arXiv 2511.00215 | preprint, abstract only | An unfiltered LLM checker flagged 98% of code-doc pairs as inconsistent. Filtering cut that to 14% |

None of the three studies the essay cites measures decoherence. He et
al. name velocity to size to debt. Chen and Stratton name a review
bottleneck. Liu et al. name debt that persists. All three agree with
the essay's direction, and none tests it.

## What this repository shows

`python3 plugins/conserve/scripts/detect_duplicates.py plugins`
reports module-level functions that share a name but not a body. On
2026-10-21, with vendored `.uv-cache` trees set aside, it listed 75
names. Protocol names such as `_build_parser` lead the list and are
expected. Competing models of one concern sit among them:
`parse_frontmatter` in 4 plugins, `estimate_tokens` in 3 with 4
bodies, and the vendored `_version_key`, which has drifted to 3 bodies
across 14 plugins.

## Rules the skills carry

Each rule is written into the skill that makes the decision. The analogies come
from a TRIZ pass and are not evidence. They give the shape of a rule
that other fields already enforce.

| Rule | Skill | Analogy |
|------|-------|---------|
| Reuse the model the codebase uses for a concern before the stdlib | `conserve:elegant-code` rung 2 | Switching-cost control: change only past a threshold |
| A second model retires the first in the same change, or records why both stand | `conserve:elegant-code`, `conserve:decisive-action` | Statute law presumes against implied repeal |
| During a migration, new code uses the target and never copies the superseded variant | `conserve:elegant-code`, `imbue:karpathy-principles` | Building codes for existing buildings: each alteration leaves the building no less compliant |
| Count how many ways the codebase models a concern before escalating | `abstract:escalation-governance` | Cascading organizational change |
| Pair a gating score with a check outside the score | `leyline:evaluation-framework` | Goodhart's law |
| One authorized term per concept, and one home per fact | `scribe:doc-generator` | Library authority files |
| The superseded document points forward and states its status | `scribe:doc-generator` | The RFC index records "Obsoleted by" |

## Limits

- No migration-share threshold is set. Building codes pick one for
  life safety, and software has no basis for a number yet. The rules
  ask for the count and leave the call to the person.
- The census matches names and can miss a second model saved under a
  new name. A practitioner report describes exactly that: an agent
  rebuilt a helper under another name.
- Bodies are compared without docstrings and with arguments. A
  renamed parameter counts as a different body.
