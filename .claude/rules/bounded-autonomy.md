**Give the model a map and a destination, not turn-by-turn
directions!**

Every skill, command, agent, and hook in this repository is written to
a session that can already reason. Its job is to supply what that
session cannot know: the destination, the boundaries, and the local
facts. The route between them is the model's to choose, because the
model can see the situation and the author could not.

This rule inverts a doctrine this repository used to hold. The old
`persuasion-principles` module argued for maximizing compliance,
citing a study in which persuasive phrasing raised instruction
adherence from 33% to 72%. That study measured compliance, not
correctness. Doubling adherence helps only where the instruction fits
the situation in front of it, and doubles the damage where it does
not.

## What to write instead

Three parts, in this order:

- **Intent**: what a good outcome looks like, and why it matters
- **Constraints**: the boundaries that must hold, and what is behind
  each one
- **Exit criteria**: how anyone can check afterward that it worked

Then stop. Do not narrate the steps between. A twelve-step procedure
fails whole when step four meets a repository the author did not
imagine, and it fails silently, because the instructions were
followed.

## The strength budget

| Strength | For | Test |
|----------|-----|------|
| Invariant | Unrecoverable if wrong | Trust boundary, credential, destructive command, safety-critical contract |
| Default | This repo's pick among defensible options | A reader may deviate with a stated reason |
| Map | Everything else | Local facts the model cannot derive |

Most content belongs in the third row. An invariant needs a named
failure this repository actually hit, with a linked issue or journal
entry. "A model might get this wrong" is not evidence.

## Retired patterns

Do not add these, and remove them when editing a file that has them:

- **Rationalization tables** pairing a thought with why it is wrong.
  They foreclose the case where the thought was correct, which is the
  only case that matters.
- **"Cannot be overridden by other skills, hooks, or
  rationalization."** Unfalsifiable by construction: it recasts every
  disagreement as bad faith, including the ones where the instruction
  is simply wrong about the situation.
- **"If you think this doesn't apply, reconsider - it probably does."**
  Instructs a session to distrust its own read in favour of an author
  who never saw it.
- **Intensity ladders** that escalate phrasing by skill category. If a
  skill is passed over where it applies, the description is wrong.
  Pressure language hides that bug rather than fixing it.
- **Ceremonial declarations** required before work begins. They
  produce the announcement, not the behavior, and cost context either
  way.

## Where this rule does not apply

- **Trust boundaries.** Validating untrusted input, handling secrets,
  and blocking destructive commands stay imperative. Being loose there
  is not judgment, it is a vulnerability.
- **Safety-critical code.** `Skill(pensive:safety-critical-patterns)`
  requires defensive checks by design. When the two conflict,
  safety-critical wins.
- **Deterministic machine contracts.** Hook exit codes, JSON schemas,
  and CLI argv are specifications, not advice. Precision there is not
  over-prescription.
- **Recorded failures.** A constraint tracing to a real incident keeps
  its force. Cite the incident.

## Pruning is part of the job

Skills accumulate sediment: people add and never remove. A stale skill
does not sit inert, it is read, believed, and acted on. Deleting one
that no longer matches the codebase is maintenance, not lost
capability.

Before adding a skill, ask whether it carries something a competent
session could not derive. If it restates a general practice, it is a
reminder competing for context with the repository's actual secrets.

## Why this rule exists

The concern is not stylistic. Instruction load measurably degrades
reasoning, and reasoning models are hit hardest.

| Source | Finding |
|--------|---------|
| "Prompt Complexity Dilutes Structured Reasoning" ([arXiv 2603.13351](https://arxiv.org/pdf/2603.13351)) | Beyond roughly 15 simultaneous constraints, nearly all models show a distinct drop in compliance; the effect is more pronounced for reasoning models |
| "On the Paradoxical Interference between Instruction-Following and Task Solving" ([arXiv 2601.22047](https://arxiv.org/pdf/2601.22047)) | Explicit instruction-following pressure trades off against task-solving accuracy |
| "When Built-in Thinking Helps and Hurts" ([arXiv 2606.09662](https://arxiv.org/pdf/2606.09662)) | Format-restricting instructions cause measurable reasoning degradation, worse under stricter constraints |
| "When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following" ([OpenReview](https://openreview.net/forum?id=w5uUvxp81b)) | Instruction-following and reasoning interfere rather than compose |
| Matt Pocock, [mattpocock/skills](https://github.com/mattpocock/skills) | Skills should be "small, easy to adapt, and composable"; the reader is invited to "hack around with them, make them your own" |
| Matt Pocock, "The Missing Manual: How to Write Great Skills" ([talk](https://youtu.be/UNzCG3lw6O0)) | Names pruning as one of four things separating good skill sets from bad: sediment accumulates when people add and never remove |

The arXiv results are independent of Pocock and were not authored in
response to any skill framework. They corroborate the mechanism rather
than the framing.

Read the last row against this repository's own numbers: 217 skills,
163 commands, 56 agents, 169 hooks. The constraint ceiling in the
first row is a per-prompt count, and a session that loads several
skills plus injected session-start policy passes it easily.

## Sibling rules

- `prefer-invariants-over-fallbacks.md`: the same instinct applied to
  defensive code. Both say: do not build machinery for a case you
  cannot name.
- `ceremony-requires-need.md`: the same instinct applied to structure.
- `.claude/rules/skill-exit-criteria.md`: exit criteria are the third
  part of the shape above, and are required.

## References

- `plugins/abstract/skills/skill-authoring/modules/persuasion-principles.md`
- `plugins/abstract/shared-modules/skill-selection-judgment.md`
- `plugins/abstract/skills/modular-skills/modules/enforcement-patterns.md`
