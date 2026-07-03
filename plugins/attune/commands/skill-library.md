---
name: skill-library
description: "Build a project skill library under .claude/skills/ as a resumable mission: discover, author in parallel, review adversarially."
---

# Attune Skill Library Command

Build (or rebuild) a project skill library under `.claude/skills/`
so junior engineers and Sonnet-class models can carry the project
forward: debug it, extend it, validate it, and advance it at the
departing expert's standard.

## When To Use

Use this command when you need to:

- Package a repository's institutional knowledge before the person
  or session holding it moves on
- Bootstrap `.claude/skills/` in a repo that has none
- Re-run discovery and review over a drifted project library

## When NOT To Use

Avoid this command if:

- You are authoring or improving a single skill (use
  `/abstract:create-skill`)
- The skills belong inside a plugin, not the project (use
  `Skill(plugin-dev:skill-development)`)
- You only want an audit of existing skills (use
  `/abstract:skills-eval`)

## Usage

```bash
# Full mission: discover, author, review, report
/attune:skill-library

# Resume an interrupted mission from .attune/mission-state.json
/attune:skill-library --resume

# Constrain the library size (default: adapt within 10-16)
/attune:skill-library --max-skills 12
```

## What This Command Does

1. Invokes `Skill(attune:skill-library-mission)` and creates a
   custom mission in `.attune/mission-state.json` with phases
   `discover, author, review, report`
2. **Discover**: investigates the repo like an incoming principal
   engineer, then asks the user at most five questions the repo
   cannot answer
3. **Author**: dispatches one authoring agent per skill from the
   adapted taxonomy, each carrying the non-negotiable authoring
   rules and a write fence limited to `.claude/skills/`
4. **Review**: runs factual, doctrine, and usability reviewers in
   parallel, then one fixer applying blocking and important findings
5. **Report**: delivers the skill inventory, spot-check evidence,
   and remaining uncertainties

## Arguments

| Argument | Description |
|----------|-------------|
| `--resume` | Continue from saved mission state |
| `--max-skills <n>` | Cap the adapted taxonomy at `n` skills |
| `--skip-questions` | Proceed with repo evidence only; record assumptions in mission state |

## Related Commands

- `/attune:mission` - General lifecycle orchestration with the same
  state and resume machinery
- `/abstract:create-skill` - Author one skill with TDD methodology
- `/abstract:skills-eval` - Audit existing skill quality

## Related Skills

- `Skill(attune:skill-library-mission)` - The mission methodology
  this command dispatches
- `Skill(attune:mission-orchestrator)` - State persistence and
  phase routing
- `Skill(imbue:proof-of-work)` - The evidence discipline reviewers
  enforce
