---
name: adaptive-constraints
description: >-
  Dynamically adjust constraint loading based on
  task complexity. Simple tasks get minimal
  governance; complex tasks get full enforcement.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 180
---

# Adaptive Constraints (Nen-Free Zones)

## Problem

All missions load the same governance weight
regardless of complexity. Past 150 soft rules,
compliance drops for all rules. A focused 50-line
CLAUDE.md beats an unfocused 300-line one; bad
context performs worse than none. SWE-agent mini
proves 100 lines of focused code reaches 74% on
SWE-bench Verified. Simple tasks need less
governance, not the same governance.

## Constraint Profiles

| Profile | Task Type | Constraints Loaded | Governance |
|---------|-----------|-------------------|------------|
| Minimal | quickfix, single-file changes | Core safety only (no `--no-verify`, no secrets) | No war-room, no scope-guard, no plan review |
| Standard | tactical missions, multi-file | Core safety + scope-guard + proof-of-work | Plan review, single checkpoint |
| Full | full/standard missions, architecture changes | All constraints + war-room + extended thinking | Full checkpoints, iteration governor |

## Profile Selection

### By Mission Type

| Mission Type | Default Profile |
|-------------|----------------|
| `quickfix` | Minimal |
| `tactical` | Standard |
| `standard` | Full |
| `full` | Full |

### Manual Override

Override with `--constraints=minimal|standard|full`.
The override bypasses mission-type defaults and
risk upgrades (always wins).

### Risk Upgrade

`leyline:risk-classification` can upgrade (never
downgrade) the profile:

| Risk Level | Effect |
|------------|--------|
| GREEN/YELLOW | Use mission-type default |
| ORANGE | Upgrade to Standard minimum |
| RED | Upgrade to Full |

Selection order: mission-type default, then risk
upgrade, then manual override.

## What Each Profile Strips

### Minimal (vs Full)

Stripped:

- scope-guard worthiness evaluation
- war-room checkpoint
- plan-review iteration loop
- backlog triage (issue creation from Out of Scope)
- additive-bias-defense check

Kept:

- proof-of-work evidence (always required)
- Iron Law enforcement (always active)
- Pre-commit hooks (always run)
- Destructive operation confirmation (always prompt)

### Standard (vs Full)

Stripped:

- war-room checkpoint
- additive-bias-defense audit
- Plan review limited to single pass (no iteration
  governor, no multi-round revision)

Kept:

- scope-guard worthiness evaluation
- proof-of-work evidence
- Single checkpoint per critical phase
- Pre-commit hooks
- Iron Law enforcement
- Destructive operation confirmation

## Safety Floor

These constraints are never stripped regardless of
profile, forming the absolute minimum governance:

1. **Pre-commit hooks** always run. No path through
   adaptive-constraints disables `--no-verify`
   protection.
2. **proof-of-work evidence** is always required.
   Every mission must produce verifiable artifacts.
3. **Hard vows from vow-enforcement** are always
   enforced. Soft vows may be relaxed by profile.
4. **Destructive operation confirmation** always
   prompts. No silent `rm -rf`, `git push --force`,
   or `DROP TABLE`.

Any code path bypassing the safety floor is a bug.
The floor is not configurable.

## Token Savings

| Profile | Modules Skipped | Tokens Saved |
|---------|----------------|--------------|
| Minimal | 4 (scope-guard, war-room, plan-review, additive-bias-defense) | ~2000 per mission |
| Standard | 2 (war-room, additive-bias-defense) | ~800 per mission |
| Full | 0 (baseline) | 0 |

Savings compound: 5 quickfixes save ~10k tokens.

## Integration with Phase Routing

The `phase-routing.md` module consults adaptive-
constraints before each phase transition:

1. At mission start, the orchestrator determines the
   constraint profile and records it in
   `.attune/mission-state.json` under
   `constraint_profile`.

2. Before each phase, phase-routing checks the
   active profile against the phase's governance
   requirements.

3. If the profile says "skip checkpoint for this
   phase," phase-routing auto-continues without
   presenting the checkpoint prompt.

4. The profile is locked at mission start. No mid-
   mission changes. If risk escalates, the
   orchestrator logs a warning; the user can abort
   and restart with a higher profile.

### Phase-Routing Decision Table

| Phase Transition | Minimal | Standard | Full |
|-----------------|---------|----------|------|
| brainstorm to specify | auto-continue | auto-continue | checkpoint |
| specify to plan | auto-continue | checkpoint | checkpoint + backlog triage |
| plan to execute | auto-continue | single-pass review | full review loop + war-room |
| post-execute | proof-of-work only | proof-of-work + scope check | proof-of-work + scope + bias audit |
