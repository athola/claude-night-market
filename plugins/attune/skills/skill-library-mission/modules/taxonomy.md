# Skill Library Taxonomy

Sixteen categories, adapted to what Phase 1 discovery found. Merge
categories that are thin in the target repo, split ones that are
deep, and add domain categories the taxonomy does not imagine. Aim
for 10 to 16 skills total. Placeholders: `<project>` is the repo's
short name, `<domain>` is its technical field.

## Core Categories

Every project has these twelve.

| # | Skill | Contents |
|---|-------|----------|
| 1 | `<project>-change-control` | How changes are classified, gated, and reviewed here; the non-negotiables with the rationale and the historical incident behind each. |
| 2 | `<project>-debugging-playbook` | Symptom-to-triage table for this project's failure modes; the traps that cost real time, each with its story; discriminating experiments. |
| 3 | `<project>-failure-archaeology` | The chronicle: every major investigation, dead end, rejected fix, and revert, as symptom, root cause, evidence, and status, so no one re-fights a settled battle. Mine git history and docs hard. |
| 4 | `<project>-architecture-contract` | The load-bearing design decisions and why; the invariants that must hold; the known-weak points, stated plainly. |
| 5 | `<domain>-reference` | The domain-theory knowledge pack a mid-level person lacks: the field's math, protocols, and standards as they apply HERE, not a textbook. |
| 6 | `<project>-config-and-flags` | Catalog of every configuration axis: options, defaults, production vs experimental, guards; how to add one (checklist); re-verification commands, since flags drift. |
| 7 | `<project>-build-and-env` | Recreate the environment from scratch; known traps. |
| 8 | `<project>-run-and-operate` | Running and deploying the thing: command anatomy, data and artifact conventions, what output lands where. |
| 9 | `<project>-diagnostics-and-tooling` | How to MEASURE instead of eyeball: diagnostic tools with interpretation guides; ship real scripts in the skill's `scripts/` dir. |
| 10 | `<project>-validation-and-qa` | What counts as evidence here; acceptance-threshold discipline; the certified or golden inventory; how to add tests. |
| 11 | `<project>-docs-and-writing` | Maintaining the docs of record; templates; house style. |
| 12 | `<project>-external-positioning` | Papers, releases, ecosystem: what is novel vs known, what must be proven before claiming, reproducibility standards. |

## Advanced Categories

The layer that makes juniors dangerous, in the good way.

| # | Skill | Contents |
|---|-------|----------|
| 13 | `<project>-<hardest-problem>-campaign` | An executable, decision-gated campaign for the hardest live problem from Phase 1: numbered phases, exact commands, expected observations and numbers at every gate ("if you see X instead, branch to Y"), the solution menu ranked with theory obligations, known wrong paths fenced off, and a validation-and-promotion protocol that routes through change control. Success must be measurable, never judged by eye. |
| 14 | `<project>-proof-and-analysis-toolkit` | The first-principles analysis methods of this domain (whatever "prove it, don't just install it" means here), each as a recipe with a worked example from the repo's history. |
| 15 | `<project>-research-frontier` | Open problems where this project could advance the state of the art: why current approaches fail, this project's specific asset, the first three concrete steps IN THIS REPO, and a falsifiable "you have a result when" milestone. |
| 16 | `<project>-research-methodology` | The discipline that turns a hunch into an accepted result: the evidence bar (one mechanism must explain ALL observations including negatives, and survive assigned adversarial refutation), hypothesis-predicts-numbers-before-running, the idea lifecycle from experiment flag to adopted change or documented retirement, and where good ideas historically came from. |

## Adaptation Rules

- Merge when discovery finds a category thin: the first run in this
  repo folded run-and-operate, build tooling, and release steps into
  one `operations` skill because they shared a Makefile.
- Split when a category is deep enough to exceed one skill's token
  budget; prefer a hub skill plus modules over two overlapping
  skills.
- Add a `collective-memory` category when the project keeps memory in
  discussions, ADRs, or journals: searching memory before
  re-investigating is its own discipline.
- One home per fact. When two categories want the same fact, pick
  the owner and cross-reference from the other.
