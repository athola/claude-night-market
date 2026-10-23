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
last_updated: 2026-10-23
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
2026-10-21 it listed 78 names. A review read them on 2026-10-22 and
found 26 to be competing models of one concern. The rest were protocol
names such as `_build_parser`, unrelated functions sharing a generic
verb, and thin wrappers over a single model.

Among the 26 were two copies of a version ordering, in minister and
memory-palace, that sorted `1.10.1-rc1` below `1.10.0`. leyline's
vendored ordering already got it right. Both now use it, and the census
lists 71 names on `plugins/` and 81 from the repository root.
`parse_frontmatter` still has four bodies beside leyline's vendored
parser.

## Rules the skills carry

The skills use one term, *model of a concern*: one way the codebase
does one job. `abstract:escalation-governance` says implementation,
because model there means an LLM tier. The census reports the same
thing as competing implementations.

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
| Before reusing a model, compare its contract with the stdlib, platform or installed dependency, and raise a departure with no recorded reason | `conserve:elegant-code` rung 2, `conserve:decisive-action` | Departure disclosure in financial reporting (added by hand, not from the TRIZ pass) |

## How far the repository's models depart from the standard

Reusing the repository's model only beats the standard when the two
agree, or when the difference has a reason someone wrote down. On
2026-10-23 the four concerns this page already discusses compared as
follows.

| Concern | Repository model | Standard | Departure | Recorded reason | Outcome |
|---------|------------------|----------|-----------|-----------------|---------|
| Version ordering | leyline `version_key` | PEP 440, `packaging.version` | `1.10.0.post1` sorted below `1.10.0` | Stdlib-only, in the `sibling_plugins.py` docstring. The post-release order was not recorded | Raised, then fixed in `9140ab23f` |
| Atomic file write | Temp file in the same directory, then `os.replace` (four writers) | The same, with `os.fsync` on the file before the rename and on the directory after | None of the four flushed. A crash before the data reached disk could lose the write | None | Raised, then fixed in `b064bb5fc` and the directory sync after it |
| Frontmatter parsing | leyline `frontmatter.py`, PyYAML optional | `yaml.safe_load` on the fenced block | Parses with PyYAML absent | Hooks and pre-commit run on the system `python3` (`scripts/sync_vendored.py`, `skill_graph.py`) | Reuse, cite |
| Token estimation | leyline `tokens.py`, `tiktoken` when installed | A tokenizer such as `tiktoken` | A size heuristic when `tiktoken` is absent | The `tokens.py` module docstring | Reuse, cite |

Raise means the departure is named to a person, who decides whether to
record a reason or move to the standard. Both raised cases moved to
the standard. The version key now orders post-releases as PEP 440 does
and stays stdlib-only. The four writers call `os.fsync` on the temp
file before the rename and on the parent directory after it.

## Limits

- No migration-share threshold is set. Building codes pick one for
  life safety, and software has no basis for a number yet. The rules
  ask for the count and leave the call to the person.
- No departure threshold is set either. A departure is an input the two
  models treat differently, named rather than scored.
- The census matches names and can miss a second model saved under a
  new name. A practitioner report describes exactly that: an agent
  rebuilt a helper under another name. Here, atomic file writes sit
  under 4 names at 7 sites and the census lists 3 of them as unrelated
  entries. Frontmatter parsing has about 15 module-level functions under
  11 names, and the census lists 2.
- Bodies are compared without docstrings or argument annotations, and
  with argument names. A renamed parameter counts as a different body,
  and so does a wrapper that differs only in a constant, such as a log
  label.
