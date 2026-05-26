# Skill Description Guide

Source: Anthropic official best practices, ADR-0004, and obra/superpowers
patterns. Governs the `description:` field in every `SKILL.md`.

## Hard Constraints

- **Max 160 chars** per description (enforced by pre-commit hook)
- **Third person only**: no "I" or "you"
- **No surrounding quotes needed**: use `description: text` not
  `description: 'text'`
- Current total: ~70,000 chars with overhead (validator ceiling: 60,000;
  1M context allows ~80,000). Growth is intentional per ADR-0004.
  Run `python3 plugins/abstract/scripts/validate_budget.py` to check.

## Format Template

```
[Verb phrase] [domain]. Use when [trigger condition].
[Optional: Do not use when [negative]; use [alternative] instead.]
```

## Categories and Patterns

### User-invoked process skills

Skills users trigger by describing what they're about to do.

```
Guides [process]. Use when [action the user is about to take].
```

Examples:
- `Guides TDD cycle. Use when implementing any feature or bugfix, before
  writing implementation code.`
- `Orchestrates systematic debugging. Use when encountering any bug, test
  failure, or unexpected behavior.`

### Domain-conditional skills

Skills that activate on file type, import pattern, or technology context.

```
[Capability]. Use when [file/import/language pattern] or [user phrase].
Do not use when [false-positive scenario].
```

Examples:
- `Async Python patterns for I/O-bound apps. Use when code uses asyncio,
  aiohttp, or the user asks about concurrency. Do not use for CPU-bound tasks.`
- `Architecture paradigm for [domain]. Use when selecting or designing [arch].`

### Review/audit skills

Skills invoked to assess quality of existing work.

```
[Reviews/audits/analyzes] [subject] for [dimensions]. Use when [review
trigger — before PR, after writing, on request].
```

Examples:
- `Audits Makefiles for build correctness and recipe duplication. Use when
  reviewing a Makefile or before committing Makefile changes.`
- `Hunts bugs with evidence trails. Use when investigating unexpected behavior
  or before merging code that could have hidden defects.`

### Utility/library skills

Skills called by other skills, not directly by users.

```
[Shared capability] for [plugin] skills. Use when composing or extending
[plugin] skills.
```

### Orchestrator/lifecycle skills

Skills that coordinate a multi-step workflow.

```
Orchestrates [lifecycle/workflow]. Use when starting [project type] or
resuming [workflow] from saved state.
```

## Examples: Before and After

| Skill | Before (noun-phrase) | After (action-oriented) |
|-------|---------------------|------------------------|
| `hookify:writing-rules` | `Create markdown-based behavioral rules to prevent unwanted actions.` | `Creates behavioral rules in markdown to block dangerous commands or restrict AI behavior. Use when adding safety guardrails or preventing specific commands.` |
| `hookify:rule-catalog` | `Browse the rule catalog and guide installation.` | `Browse hookify's pre-built rule catalog. Use when installing standard rules or browsing available categories. Do not use when writing custom rules.` |
| `pensive:makefile-review` | `Audit Makefiles for build correctness and recipe duplication.` | `Audits Makefiles for build correctness and recipe duplication. Use when reviewing a Makefile or before committing Makefile changes.` |
| `imbue:rigorous-reasoning` | `Anti-sycophancy reasoning checklist.` | `Anti-sycophancy reasoning checklist. Use when analyzing contested claims, resolving disagreements, or detecting sycophantic self-correction patterns.` |
| `attune:brainstorm` | `Guide project ideation through Socratic questioning...` | `Guides project ideation via Socratic questioning. Use before any creative work — features, components, behavior changes — before writing code.` |

## Common Mistakes

- **No trigger**: `'Audit Makefiles for build correctness.'` Tells Claude WHAT
  but not WHEN to invoke it.
- **Over-long**: descriptions > 160 chars fail the pre-commit hook
- **First-person**: `'I help you...'` or `'You can use this...'`: use third
  person
- **Vague trigger**: `'Use when needed.'` Must name specific situations.
- **Missing "Do not use when"**: for skills with similar alternatives, add the
  negative condition to prevent mis-activation

## Running the Validator

```bash
python3 plugins/abstract/scripts/validate_budget.py
```

Pass condition: all descriptions ≤ 160 chars and total overhead under 60k.

## Related

- ADR-0004: `docs/adr/0004-skill-description-budget-optimization.md`
- Anthropic best practices:
  fetched from `obra/superpowers/skills/writing-skills/anthropic-best-practices.md`
- Pre-commit hook: `validate-description-budget` in `.pre-commit-config.yaml`
