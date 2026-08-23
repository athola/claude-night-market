---
name: skill-library-mission
description: "Build a project skill library in .claude/skills/ via discovery, parallel authoring, and review. Use when packaging tribal knowledge. Do not use for one skill."
alwaysApply: false
category: workflow-orchestration
tags:
- skill-library
- knowledge-transfer
- succession
- mission
- multi-agent
dependencies:
- attune:mission-orchestrator
- abstract:skill-authoring
- imbue:proof-of-work
tools: []
provides:
  workflow:
  - skill-library-authoring
  - knowledge-transfer
  - succession-planning
usage_patterns:
- repo-succession
- onboarding-library
- institutional-memory
complexity: advanced
model_hint: deep
estimated_tokens: 700
progressive_loading: true
modules:
- modules/taxonomy.md
- modules/authoring-rules.md
- modules/review-protocol.md
references:
- references/mission-prompt.md
role: entrypoint
---

# Skill Library Mission

## Overview

A retiring distinguished fellow's final task: package everything the
project knows into a skill library under `.claude/skills/`, so that
cheaper sessions and newer engineers can carry the project forward at
the same standard. This skill turns that one-off exercise into a
repeatable mission with three gated phases: discover, author, review.

The mission produced its first library in this repository on
2026-07-02 (15 skills, mission `skill-library-2026-07-02`). The
generalized dispatch prompt distilled from that run is preserved
verbatim in `references/mission-prompt.md`.

## When To Use

- A repository has deep tribal knowledge and no `.claude/skills/`
  library, and future sessions (human or model) must operate without
  the current expert.
- An existing project library has drifted and needs a full
  re-discovery and re-review pass.
- Onboarding cost is high: the same questions get re-answered and the
  same dead ends get re-fought across sessions.

## When NOT To Use

| Situation | Use instead |
|-----------|-------------|
| Authoring or improving one skill | `Skill(abstract:skill-authoring)` |
| Skills shipped inside a plugin | `Skill(plugin-dev:skill-development)` |
| Auditing existing skills only | `Skill(abstract:skills-eval)` |
| Full project lifecycle (code, not knowledge) | `Skill(attune:mission-orchestrator)` |

## Mission Shape

Run as an attune mission with custom phases so the run survives
interruption and records user directives:

```json
{
  "mission_id": "skill-library-YYYY-MM-DD",
  "type": "custom",
  "phases": ["discover", "author", "review", "report"],
  "artifacts": { "library_root": ".claude/skills/" }
}
```

Save this to `.attune/mission-state.json`, advance `current_phase` at
each gate, and record every user decision and override in
`decisions` / `directive_overrides`. A later session must be able to
resume from the state file alone.

## Phase 1: Discover

No authoring happens in this phase. Investigate like an incoming
principal engineer:

- [ ] README, manifest, contributor docs
- [ ] Build system and how tests actually run (not how docs claim)
- [ ] CI config and quality gates
- [ ] Git history: what changed, what got reverted, what stalled
- [ ] TODO/FIXME hotspots and issue-shaped artifacts
- [ ] Generated-data, deploy, and artifact conventions
- [ ] Any project memory available (discussions, ADRs, journals)

Then ask the user at most five questions, only for what the repo
cannot tell you. The canonical five: the hardest live problem,
unwritten discipline rules, the audience and what it lacks, the most
expensive past failures, and what "beyond state of the art" means
here. Fold the answers into every later phase.

## Phase 2: Author

`workflows/skill-library.js` runs authoring and review as one
pipeline, so each skill's review starts when that skill is written
rather than when the slowest one is. It runs only when asked for, and
it returns review findings instead of applying them, because fixing
edits files that already exist. Without it, dispatch by hand:

Dispatch one authoring agent per skill, in parallel, following the
taxonomy in `modules/taxonomy.md` (adapt it: merge thin categories,
split deep ones, add domain categories). Aim for 10 to 16 skills.
Every agent prompt embeds the rules in `modules/authoring-rules.md`;
the non-negotiables are ground-truth-only claims, a "Provenance and
maintenance" section per skill, and a write fence limiting agents to
`.claude/skills/`.

## Phase 3: Review

After all skills exist, run the three-reviewer-plus-fixer protocol in
`modules/review-protocol.md`: factual, doctrine, and usability lenses
in parallel, then one fixer applying blocking and important findings.
Finish with the report: skill inventory with one-line descriptions,
what was spot-checked, and what remains uncertain.

## Red Flags

Stop if you catch yourself thinking any of these:

| Thought | Reality |
|---------|---------|
| "The repo is small, skip discovery" | Discovery is where the five questions come from. Run it. |
| "I know this codebase, skip verification" | Ground truth only. Wrong runbooks are worse than none. |
| "The library looks complete, skip review" | Authoring agents cannot see each other's contradictions. |
| "This claim is probably still true" | Date-stamp it and add a re-verification command. |

## Exit Criteria

- [ ] `.attune/mission-state.json` exists with the custom phase list
  and reaches `report` with all prior phases completed.
- [ ] `.claude/skills/` contains 10 to 16 skill directories, each
  with a SKILL.md whose frontmatter has `name` and a trigger-rich
  `description`.
- [ ] Every skill ends with a "Provenance and maintenance" section
  containing one-line re-verification commands.
- [ ] All three review lenses ran and every blocking or important
  finding is either applied or skipped with a recorded reason.
- [ ] The final report lists the inventory, spot-check evidence, and
  remaining uncertainties.

## Provenance and Maintenance

- Origin: mission `skill-library-2026-07-02` in claude-night-market;
  generalized prompt captured 2026-07-03.
- Verify the reference prompt still matches this skill's phases:
  `rg -c "Phase" plugins/attune/skills/skill-library-mission/references/mission-prompt.md`
- Verify the first library still exists where this skill claims:
  `ls .claude/skills/ | head -5`
