# Advanced Skill-Authoring Patterns

Patterns for skill authors who have shipped a working skill and now
need to coordinate with other skills, scale across many activation
contexts, or expose conditional behavior. Read this after the core
SKILL.md and `tdd-methodology.md` modules. The Iron Law still
applies: every advanced pattern below assumes a baseline failing
test exists for the behavior being added.

## When to reach for these patterns

Most skills do not need any of this. Add an advanced pattern only
when a baseline scenario fails because of coordination, scale, or
context, not because of missing content. If the failure can be
fixed by adding a section to a single SKILL.md, do that first.

| Symptom in baseline tests | Pattern below |
|---------------------------|---------------|
| Two skills give conflicting advice on same task | Multi-skill coordination |
| One SKILL.md exceeds 500 lines and still grows | Hub-and-spoke loading |
| Skill activates on irrelevant tasks | Trigger narrowing |
| Skill must behave differently per environment | Conditional activation |
| Same module needed by 3+ skills | Shared module extraction |

## Multi-skill coordination

Skills frequently overlap. `abstract:skill-authoring` writes new
skills, `abstract:skills-eval` audits them, and
`abstract:subagent-testing` validates them. When a task touches
all three, the user does not want three skills shouting in
parallel. They want a chain.

### Establish a primary skill per task

In each SKILL.md, declare which other skills it defers to and
which it owns. Example from `abstract:skill-authoring/SKILL.md`:

```markdown
## Integration and Best Practices

Individual skills are created using `skill-authoring`, while
`modular-skills` handles the architecture of larger structures.
`skills-eval` provides ongoing quality assessment.
```

This single paragraph prevents the three skills from racing. The
user reading any one of them learns where the boundaries live.

### Cross-reference real targets, not abstractions

Use the fully qualified `plugin:skill` form so the reference
resolves regardless of which marketplace the user installed:

```markdown
For pressure testing the new skill, see
`Skill(abstract:subagent-testing)`.
```

Anti-pattern: `see the testing skill`. There are six skills with
"testing" in the name across this repo. The reader cannot route.

### Hand off, do not duplicate

When skill A needs behavior owned by skill B, link to skill B
rather than restating its content. Duplicated guidance drifts.
The version in `abstract:skill-authoring` will say one thing and
the copy in `abstract:skills-eval` will say something else after
two PRs. Pick an owner and link.

## Hub-and-spoke loading

The hub-and-spoke pattern is documented in
`progressive-disclosure.md`. The advanced variant adds two rules
that only matter once a skill has 5+ modules.

### Rule 1: the hub never loads more than two spokes

If your SKILL.md routinely says "for X, see module-a; for Y, see
module-b; for Z, see module-c," the hub is doing too much. Either
collapse the three modules into one, or split the hub into
multiple skills. A reader who must load four files to start
working has lost progressive disclosure.

### Rule 2: spokes do not chain

A spoke that says "see other-spoke.md for prerequisites" forces
sequential loading and defeats the model. If two spokes share
foundational content, extract a third spoke and have the hub
load it explicitly when needed. See
`Skill(abstract:modular-skills)` for the full chain-elimination
algorithm.

## Dynamic activation via description triggers

Skills activate by semantic match on the `description:` field.
Authors of mature skills tune triggers deliberately rather than
listing every possible synonym.

### Use specific noun phrases, not generic verbs

| Generic (low signal) | Specific (high signal) |
|----------------------|------------------------|
| Use when reviewing code | Use when reviewing PRs |
| Use when writing tests | Use when writing pytest fixtures |
| Use for optimization | Use for token budget reduction |

The generic form competes with every other skill in the category.
The specific form fires only when the user actually needs this
skill. Test specificity by running a real user prompt through
`/skills` and checking activation rank.

### Front-load the use case

The first 50 characters of `description:` carry the most weight
in semantic matching. Lead with the action and the trigger:

```yaml
description: 'Audit hooks for security and SDK compliance.
  Use when reviewing hook PRs or auditing plugin safety.'
```

Not:

```yaml
description: 'A thorough framework that helps developers think
  carefully about hook quality across many dimensions...'
```

The second form buries the trigger past the truncation point on
small context windows.

## Conditional activation

Some skills should only fire in certain environments (CI vs
local) or for certain file types. Two mechanisms exist.

### Path globs for file-scoped skills

The `paths:` field activates a skill only when the conversation
references matching files. Example for a skill that should only
load when editing Python tests:

```yaml
paths:
  - "**/test_*.py"
  - "**/tests/**/*.py"
```

This is enforced by the harness, not by Claude. A skill with a
`paths:` glob will not appear in `/skills` for unrelated edits.

### Explicit gates inside the skill

For runtime gates the harness cannot check (e.g., "only run when
a PR is open"), put a gate at the top of SKILL.md:

```markdown
## Activation Gate

This skill requires:
- A current branch other than `master`
- An open PR for the current branch (verify with `gh pr view`)

If either condition fails, stop and tell the user this skill does
not apply. Do not silently proceed.
```

The gate is a behavioral instruction. Pair it with a baseline
test that runs the skill on `master` and verifies Claude refuses.

## Shared module extraction

When three or more skills reference the same content, extract it
to `plugins/<plugin>/skills/shared-patterns/modules/` and link
from each consumer. The `abstract:shared-patterns` skill owns
this directory in the abstract plugin.

### Migration anti-pattern

The deprecated location was `skills/shared/modules/` at the
plugin root. The current evaluator
(`plugins/abstract/scripts/skills_auditor.py`) flags any
`skills/shared/` path as a structural warning. Move the file
into the consuming skill's `modules/` directory or into
`shared-patterns/modules/` with cross-references.

## Anti-patterns

These are common ways advanced patterns fail in review.

### "Skill of skills"

A SKILL.md that consists entirely of links to other skills
provides no value. The user could have run `/skills` themselves.
A hub skill must contain at least one substantive section that
adds context the linked skills cannot provide on their own.

### Trigger sprawl

Adding every keyword you can think of to `description:` to
"improve discovery" actually degrades it. Each irrelevant keyword
dilutes the signal of the relevant ones. Cap descriptions at
three trigger phrases and test activation against real prompts.

### Conditional gates without tests

A gate that says "only use in production environments" is a
behavioral promise. Without a baseline test that runs the skill
in development and verifies refusal, the gate is decoration.
Claude will rationalize past it under pressure. See
`anti-rationalization.md` for the counter pattern.

### Spoke depth creep

A spoke module that grew from 200 to 800 lines and now contains
its own subsections probably needs to become two spokes. Split
when a module has more than three top-level sections.

## Verification

Before merging an advanced pattern:

```bash
# Confirm the hub stays under 500 lines
wc -l plugins/<plugin>/skills/<skill>/SKILL.md

# Confirm activation against a real prompt (manual)
# Run the user prompt in a fresh session and check /skills
# output for rank and load order.

# Confirm the auditor sees no shared/ regressions
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

Cross-reference: see `Skill(abstract:modular-skills)` for the
full hub-and-spoke specification and chain-elimination rules.
