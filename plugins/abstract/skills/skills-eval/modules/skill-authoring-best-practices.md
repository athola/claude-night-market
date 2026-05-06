# Skill-Authoring Best Practices Distilled From Evaluation

This module captures the patterns that consistently score above
85 in `skills-eval` audits, contrasted with the patterns that
score below 50. The best practices are distilled from evaluating
the corpus of skills shipped in this repo and tracking which
shapes survive contact with real users. For the full evaluation
rubric, see `evaluation-criteria.md`. For the authoring process
itself, see `Skill(abstract:skill-authoring)`.

## The headline finding

Small, focused, tested skills outperform monolithic ones across
every metric the auditor measures.

| Metric | Small focused skill | Monolithic skill |
|--------|---------------------|------------------|
| Activation precision | 85-95% | 30-50% |
| Token cost per use | 600-1500 | 4000-8000 |
| Edit safety (regression rate) | low | high |
| Test coverage | typically full | typically none |
| Audit score | 80-95 | 40-65 |

The pattern repeats across 20+ skills audited. The cause is
not subtle. A skill with one job, one description, and three
test scenarios is easy to keep correct. A skill with five jobs
drifts in five directions and breaks under any of them.

## Practice 1: one job per skill

The single most predictive trait of a high-scoring skill is
that its description names exactly one job.

### Good (single job)

```yaml
description: 'Audit a codebase using three escalation tiers:
  git history analysis, targeted deep-dives, and full
  codebase review with gating.'
```

The skill `Skill(pensive:tiered-audit)` does one thing:
escalate audit depth. The description says so. The skill
activates when the user wants an audit and stays out of the
way otherwise.

### Bad (many jobs)

```yaml
description: 'A general development guide that covers testing,
  deployment, security, performance, documentation, and code
  review best practices.'
```

This description matches everything and nothing. Activation
rank is poor because more specific skills outscore it. Token
cost is high because every load pulls a large file.

### How to audit

Read the description aloud. If you find the word "and" linking
unrelated capabilities ("testing and deployment"), the skill
has two jobs. Split.

## Practice 2: progressive disclosure with real spokes

High-scoring skills use the hub-and-spoke pattern documented
in the `progressive-disclosure` module of the
`skill-authoring` skill (under `plugins/abstract/`).

### What works

- SKILL.md under 500 lines, containing overview, quick start,
  and one example.
- Modules in `modules/` sized 200-400 lines, each focused on
  one topic.
- Module references in SKILL.md point to spokes the user can
  load on demand.

### What does not work

- SKILL.md at 1500+ lines covering everything.
- Modules that exist only to satisfy a frontmatter list, with
  one paragraph of content each.
- Cross-module chains where reading one module requires
  reading three others.

### Audit signal

The auditor checks `wc -l` against the limits and flags both
oversize hubs and undersize spokes. A spoke under 100 lines
that is referenced from only one place should usually inline
back into the hub.

## Practice 3: TDD evidence on disk

Skills that ship with `tests/baseline/`, `tests/with-skill/`,
and `tests/rationalization/` directories outscore skills
without them by 20+ points on average. The presence of test
artifacts predicts:

- The author thought about failure modes before writing.
- The skill addresses a documented problem, not an imagined
  one.
- Future maintainers can re-run the tests after edits.

The auditor does not currently grade test artifacts directly
but the correlation with quality is strong enough to treat as
a leading indicator.

### What good test artifacts look like

```
plugins/<plugin>/skills/<skill>/tests/
├── baseline/
│   ├── scenario-1-quick-fix.md
│   ├── scenario-2-internal-tool.md
│   └── scenario-3-prototype.md
├── with-skill/
│   └── (same scenarios, with-skill responses)
└── rationalization/
    └── (pressure scenarios, with documented counters)
```

Each file contains the dispatch prompt verbatim, the response
verbatim, and a notes section listing failures observed.

## Practice 4: directive language, no hedges

The auditor flags hedging language ("consider," "might want
to," "you can") as a quality issue. High-scoring skills use
imperative or declarative forms.

| Hedge (low score) | Directive (high score) |
|-------------------|------------------------|
| "Consider adding validation" | "Add input validation" |
| "You might want to test this" | "Run the test scenarios" |
| "It would be good to use..." | "Use..." |
| "Try to keep it under 500 lines" | "Keep it under 500 lines" |

The reason is behavioral. Claude treats "consider" as
optional. Optional requirements get skipped under pressure.
See the `anti-rationalization` module of the `skill-authoring`
skill (under `plugins/abstract/`) for the full pattern.

## Practice 5: concrete commands in Quick Start

Skills with abstract Quick Starts ("configure pytest and run
the tests") score worse than skills with literal commands
("run `pytest --cov=src` to generate the coverage report").

### Good

```markdown
## Quick Start

\`\`\`bash
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
\`\`\`

The output is a list of issues with line numbers.
```

### Bad

```markdown
## Quick Start

Run the auditor against your skill to identify issues.
```

The bad form forces the reader to figure out where the
auditor lives. The good form is copy-pasteable.

The auditor flags this as the "cargo cult anti-pattern." See
`evaluation-criteria.md` for the full check.

## Practice 6: cross-references use `plugin:skill` form

Skills that reference other skills with full
`Skill(plugin:skill)` form work regardless of where the user
installed the marketplace. Skills that use relative paths
break when the directory structure differs from the author's
machine.

### Good

```markdown
For the testing methodology, see
`Skill(abstract:subagent-testing)`.
```

### Bad

```markdown
For the testing methodology, see
`../subagent-testing/SKILL.md`.
```

The relative path may not exist in the user's install. The
`Skill()` form resolves through the harness.

## Practice 7: voice consistency

Third person throughout. No "you" or "your." This is not a
style preference. It is an activation issue. Skills written
in second person ("you should validate inputs") read as
direct address and Claude treats them as user-facing
documentation rather than instructions to itself.

### Good

```markdown
Every endpoint must validate inputs. The validation step
checks type, length, and format.
```

### Bad

```markdown
You should validate your inputs. Make sure to check the type,
length, and format of your data.
```

The auditor flags second-person voice. Fix before merge.

## Practice 8: ship with an `Verification` section

High-scoring skills end with a section the user can run to
verify the skill produced the expected outcome. This closes
the loop: produce output, verify output, then declare done.

### Pattern

```markdown
## Verification

After running the skill:

\`\`\`bash
# Confirm the artifact exists
ls path/to/expected/output

# Confirm the artifact is valid
python validate.py path/to/expected/output
\`\`\`

If either check fails, see troubleshooting.md.
```

Without a verification section, the skill ends in narrative
("the work is complete") and Claude rationalizes incomplete
output as complete. See
`Skill(imbue:proof-of-work)` for the underlying pattern.

## Anti-patterns to avoid

These are the patterns that consistently score below 50.

| Anti-pattern | Symptom | Fix |
|--------------|---------|-----|
| Multi-job skill | Activation rank below 5 | Split |
| Monolithic SKILL.md | Token cost above 4000 | Apply hub-and-spoke |
| Vague description | Activates on unrelated prompts | Rewrite per formula |
| No test artifacts | Regressions on every edit | Add baseline/ tests |
| Hedging language | Bypassed under pressure | Use directives |
| Abstract Quick Start | Reader cannot copy-paste | Use literal commands |
| Relative cross-refs | Breaks across installs | Use `Skill()` form |
| Second-person voice | Treated as user docs | Convert to third person |
| No verification section | Claude declares done early | Add explicit checks |
| Stale cited paths | Hallucinated content | Re-verify on each release |

## How to use this module

When auditing an existing skill, run through the eight
practices above and the anti-pattern table. Each violation
maps to a specific improvement. The improvement-suggester
script (`plugins/abstract/scripts/improvement_suggester.py`)
ranks issues by impact:

```bash
python plugins/abstract/scripts/improvement_suggester.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

The output is a prioritized list. Fix the highest-impact
items first.

When authoring a new skill, treat the eight practices as a
pre-flight checklist. The
`plugins/abstract/skills/skills-eval/modules/authoring-checklist.md`
module provides the form.

## Verification

To confirm a skill follows these practices:

```bash
# Score against the full rubric
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md

# Check compliance with project standards
python plugins/abstract/scripts/compliance_checker.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md
```

A score above 85 indicates the practices are mostly applied.
A score below 70 means at least three of the practices are
violated; the auditor output names which.

Cross-reference: see `evaluation-criteria.md` for the full
scoring rubric, `Skill(abstract:skill-authoring)` for the
authoring methodology, and `authoring-checklist.md` for the
quick-reference form of these practices.
