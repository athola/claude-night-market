# Skill Validation

Before merging a skill, validate that its frontmatter parses,
its references resolve, and its activation behaves as expected.
This module covers the structural checks. For the empirical
TDD validation (does the skill actually change behavior?), see
`tdd-methodology.md` and `testing-with-subagents.md`. For the
final pre-deployment checklist that combines both, see
`deployment-checklist.md`.

## Three validation layers

| Layer | Question | Tool |
|-------|----------|------|
| Structural | Does the file parse and link correctly? | `skill_validator.py` |
| Activation | Does the skill load when expected? | `/skills` in fresh session |
| Behavioral | Does the skill change the response? | Subagent TDD |

A skill that passes structural checks but fails activation is
invisible. A skill that activates but does not change behavior
is overhead. Run all three.

## Structural validation

The minimum required artifacts:

- `SKILL.md` exists and parses as YAML frontmatter and markdown.
- All required frontmatter fields are present.
- All declared modules exist on disk.
- No circular module references.
- Line counts within limits (SKILL.md under 500, modules
  200-400).

### Run the validator

```bash
python plugins/abstract/scripts/skill_validator.py \
  plugins/<plugin>/skills/<skill>/SKILL.md
```

The validator checks frontmatter syntax, required fields,
module references, and line counts. Output is a list of
issues with line numbers.

### Required frontmatter fields

| Field | Required | Constraint |
|-------|----------|------------|
| `name` | yes | kebab-case, 64 chars max |
| `description` | recommended | quoted if it contains a colon |
| `version` | yes | semver |
| `category` | yes | valid category string |
| `tags` | yes | list of strings |
| `estimated_tokens` | yes | integer, realistic |

The full schema is documented in
the `evaluation-criteria` module of the `skills-eval` skill (under `plugins/abstract/skills/skills-eval/`).

### Module reference resolution

Every module listed in frontmatter must exist:

```bash
# Print declared modules
rg '^- modules/' plugins/<plugin>/skills/<skill>/SKILL.md

# Verify each one
for m in $(rg '^- modules/' \
  plugins/<plugin>/skills/<skill>/SKILL.md | \
  awk '{print $2}'); do
  test -f plugins/<plugin>/skills/<skill>/$m || \
    echo "MISSING: $m"
done
```

A declared module that does not exist is a silent failure.
The skill loads, the reader follows the link, and gets a
404. Fix before merge.

### Line count limits

```bash
# SKILL.md must stay under 500 lines
wc -l plugins/<plugin>/skills/<skill>/SKILL.md

# Modules should be 200-400 lines (warning, not error, outside)
wc -l plugins/<plugin>/skills/<skill>/modules/*.md
```

A SKILL.md over 500 lines should split per
`progressive-disclosure.md`. A module under 100 lines may be
inlined back into SKILL.md or merged with a sibling. A module
over 400 lines should split.

## Activation validation

Structural validity does not guarantee the skill actually
loads when expected. Test activation in a fresh session.

### Check rank for the target prompt

In a fresh Claude Code session, type the prompt that should
activate the skill. Then run `/skills` and check the rank of
the target skill.

```
User: Review my pull request and check for security issues.
Claude: [response]
User: /skills
Claude: [list of loaded skills with rank]
```

If the target skill is not in the top 3, the description does
not match the prompt strongly enough. See
`description-writing.md` for the rewrite formula.

### Check the absence case

Run a prompt that should not activate the skill. The skill
should not appear in `/skills` for that prompt. If it does,
the description is too generic.

### Check across model sizes

Activation behaves differently on Haiku vs Sonnet vs Opus.
Test the skill on the model your users actually run. A skill
that activates reliably on Opus may misfire on Haiku because
the smaller model is more keyword-dependent.

## Behavioral validation

Once the skill loads, validate that it changes the response.
This is the core TDD loop.

### Compare with-skill vs without-skill on identical prompts

For each baseline scenario in `tests/baseline/`:

1. Dispatch a fresh subagent without the skill. Capture the
   response.
2. Dispatch a fresh subagent with the skill. Capture the
   response.
3. Diff the responses against the documented failures.

The skill passes when every documented failure in the
without-skill response is absent in the with-skill response.

### Run the auditor for cross-skill consistency

```bash
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

The auditor flags structural issues, voice inconsistencies,
and missing required sections (Quick Start, Verification).
Output is a numeric score and a list of fixes.

### Compliance check

```bash
python plugins/abstract/scripts/compliance_checker.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

The compliance checker validates against the project standards
documented in
the `evaluation-criteria` module of the `skills-eval` skill (under `plugins/abstract/skills/skills-eval/`).
A score under 70 is a blocker. A score 70-89 is shippable
with a note. A score 90+ is production-ready.

## Pre-merge checklist

Use this checklist before opening a PR for a new or modified
skill.

```markdown
## Skill Validation Checklist

Structural:
- [ ] `python skill_validator.py SKILL.md` exits zero
- [ ] All declared modules exist
- [ ] SKILL.md under 500 lines
- [ ] Each module 200-400 lines
- [ ] No circular references
- [ ] Frontmatter description quoted if it contains colons

Activation:
- [ ] Skill ranks in top 3 for target prompt in fresh session
- [ ] Skill does not load for unrelated prompts
- [ ] Tested on the model the user actually runs

Behavioral:
- [ ] At least 3 RED scenarios under `tests/baseline/`
- [ ] All RED failures fixed in `tests/with-skill/`
- [ ] At least 3 REFACTOR scenarios with no rationalization
- [ ] `skills_auditor.py` score above 70

Documentation:
- [ ] Slop scan passes (`Skill(scribe:slop-detector)`)
- [ ] Slop words flagged by `Skill(scribe:slop-detector)` removed
- [ ] Markdown wraps at 80 chars per project rules
- [ ] Cross-references resolve to real targets
```

## Anti-patterns

### Validating only the structure

A skill with perfect frontmatter that never activates is
worse than no skill at all. Always check activation.

### Validating only with the author's prompts

The author has a mental model of what should trigger the
skill. Real users phrase requests differently. Pull a real
transcript and validate against it.

### Treating a high score as proof of quality

The scoring system catches structural and content issues. It
does not measure whether the skill solves the right problem.
Empirical TDD is the proof, not the score.

### Skipping validation for "small" changes

A typo fix in a description can change activation rank
dramatically. Re-validate activation after any
description change.

### Validating after merge

Validation that runs after merge does not block bad skills
from reaching users. Run pre-merge.

## Continuous validation

Skills drift. A skill that passed validation six months ago
may now reference a renamed file, cite a deprecated tool, or
overlap with a newer skill. Re-validate periodically:

```bash
# Audit all skills in a plugin
for skill in plugins/<plugin>/skills/*/SKILL.md; do
  python plugins/abstract/scripts/skills_auditor.py \
    --skill "$skill"
done
```

The output is a per-skill score. Skills that dropped below
70 are due for a refresh.

Cross-reference: see `Skill(abstract:skills-eval)` for the
full evaluation framework, `deployment-checklist.md` for the
final merge gates, and `Skill(abstract:skill-graph-audit)`
for cross-skill reference validation across the corpus.
