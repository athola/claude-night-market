# Annotated Examples of Well-Authored Skills

Annotated walk-throughs of skills that ship in this repo.
Each example highlights one or two authoring decisions worth
copying. Read these after `tdd-methodology.md` and
`progressive-disclosure.md`. Citations are to real files; you
can `Read` any path below to see the full source.

## Example 1: a focused technique skill

**Skill**: `Skill(superpowers:test-driven-development)`
**Path**: not in this repo (ships from a separate marketplace)
**What it does**: enforces the red/green/refactor cycle for
implementation work.

This skill is worth studying for one reason: the description
field uses the formula `WHAT + WHEN + TRIGGERS` and earns its
activation rank without any keyword stuffing. The skill loads
when the user says "implement X" or "fix bug Y" and stays out
of the way otherwise.

The lesson: a skill with one job, named after that job, with a
description that names the job again, will activate reliably.

## Example 2: a tiered audit skill

**Skill**: `Skill(pensive:tiered-audit)`
**Path**:
`/home/alext/claude-night-market/plugins/pensive/skills/tiered-audit/SKILL.md`

What to copy from this skill:

1. **Explicit escalation tiers**. The skill defines Tier 1
   (git history), Tier 2 (targeted deep-dive), and Tier 3
   (full codebase). Each tier names what it costs and what it
   produces. The user (or the orchestrator) picks the tier.

2. **Default to the cheapest tier**. The skill says "default
   to Tier 1" and requires explicit approval to escalate. This
   counters the rationalization "I'll do a thorough job by
   running Tier 3 just in case." See `anti-rationalization.md`.

3. **Output contract per tier**. Tier 1 produces a different
   artifact than Tier 3. The skill names both. The reader
   knows what to expect before paying the cost.

The pattern generalizes: any skill with a cost gradient
(quick/thorough, local/global, draft/final) should expose
tiers explicitly rather than letting Claude pick.

## Example 3: a TDD-for-skills meta-skill

**Skill**: `Skill(abstract:subagent-testing)`
**Path**:
`/home/alext/claude-night-market/plugins/abstract/skills/subagent-testing/SKILL.md`

This skill exists because `skill-authoring` requires baseline
tests in fresh subagents. Rather than restating the testing
methodology in every skill that needs it, `skill-authoring`
defers to this skill.

What to copy:

1. **Single-purpose deference**. `skill-authoring/SKILL.md`
   contains one line: "Testing with Subagents: See
   `abstract:subagent-testing` skill for pressure testing
   methodology." That is the right amount. The testing skill
   owns the testing content.

2. **Token budget declared**. The frontmatter sets
   `token_budget: 30`, signaling the skill itself is small.
   Most of its content is in the `subagent-testing` skill's
   testing-patterns module, loaded only when needed.

3. **Hub Table of Contents**. The hub starts with a TOC. For
   skills above 100 lines, the TOC pays for itself in
   navigation. The `skills-eval` rubric penalizes skills above
   100 lines that lack one (see `evaluation-criteria.md`).

## Example 4: an enforcement skill

**Skill**: `Skill(imbue:proof-of-work)`
**Path**:
`/home/alext/claude-night-market/plugins/imbue/skills/proof-of-work/SKILL.md`

This skill enforces evidence before "done." It is referenced
by `skill-authoring/SKILL.md` as the source of detailed
enforcement patterns: "Detailed enforcement patterns for
adversarial verification and coverage gates are available in
`imbue:proof-of-work`."

What to copy:

1. **Negative space**. The skill is mostly about what
   completion claims to refuse. The positive content (what
   counts as evidence) takes less room than the refusals. This
   matches how Claude actually fails. It rarely fails to do
   work; it fails to verify the work it did.

2. **Explicit acceptance criteria template**. The skill
   provides a template the user can paste into any
   acceptance-criteria document. Templates outperform
   exhortation: "use these criteria" works better than "be
   thorough about acceptance."

3. **Cross-plugin reuse**. `proof-of-work` is referenced from
   `abstract:skill-authoring`, `sanctum:do-issue`, and
   `egregore:quality-gate`. Skills designed to be called by
   other skills should keep their interface narrow. This skill
   exposes a small set of named patterns rather than a single
   monolithic procedure.

## Example 5: a slop-detection skill

**Skill**: `Skill(scribe:slop-detector)`
**Path**:
`/home/alext/claude-night-market/plugins/scribe/skills/slop-detector/SKILL.md`

What to copy:

1. **Sub-modules as the unit of recommendation**. The skill
   exposes `wrapping-rules`, `identity-and-voice-leaks`,
   `hallucination-detection`, and others as nameable modules.
   Other documents reference specific modules
   (`Skill(scribe:slop-detector) module document-economy.md`)
   rather than the whole skill. This makes the skill
   composable.

2. **Detection commands paired with fixes**. Each pattern in
   the skill comes with a command (`grep -o '—' file.md | wc
   -l`) and a fix. The reader is not left with "find slop";
   they are given a way to find it and a way to fix it.

## Example 6: a structural skill graph audit

**Skill**: `Skill(abstract:skill-graph-audit)`
**Path**:
`/home/alext/claude-night-market/plugins/abstract/skills/skill-graph-audit/SKILL.md`

What to copy:

1. **Operates on the corpus, not on a single skill**. Skills
   that audit the skill graph itself need a different shape:
   they take a directory, walk it, and emit a report. The
   skill makes this explicit in its description: "Map
   `Skill()` refs across plugins; detect hubs, isolates, and
   dangling targets."

2. **Output is data, not prose**. The skill produces a graph
   structure other tools can consume, rather than a narrative
   only humans can read. Skills that produce machine-readable
   output multiply in value when chained.

## What every example has in common

| Trait | Why it matters |
|-------|----------------|
| Single sentence in description names the job | Activation rank |
| SKILL.md hub stays under 500 lines | Initial load cost |
| Modules sized 200-400 lines, focused | Just-in-time loading |
| Cross-references use `plugin:skill` form | Resolves regardless of install |
| Refers to other skills rather than duplicating | No drift |
| Includes a verification or test step | Closes the loop |

## Anti-pattern: the kitchen-sink skill

A real example, anonymized: a skill named
`development-best-practices` with a 3,200-line SKILL.md
covering testing, deployment, security, performance, and
documentation. Activation was unreliable (the description
matched everything and nothing). Token cost was high (every
load pulled the entire file). Nobody could safely edit it (a
change to the testing section risked breaking the deployment
section).

The fix was to split it into five focused skills, each with
its own description and frontmatter. Activation rank improved
on every measured query. Token cost on initial load dropped
by 80%. Edits became localized.

Lesson: when in doubt, split. A skill is the wrong unit if it
needs more than one paragraph to describe its job.

## Verification

To check that an example you are copying is still current:

```bash
# Confirm the skill exists at the path
ls plugins/<plugin>/skills/<skill>/SKILL.md

# Confirm the description still matches the example
head -10 plugins/<plugin>/skills/<skill>/SKILL.md

# Run the skills-eval auditor against the example
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

If a skill cited above has changed shape, update this module
rather than copying an outdated pattern.

Cross-reference: see `Skill(abstract:skill-graph-audit)` for
the corpus-level view of how these skills reference each
other and where the hubs and isolates live.
