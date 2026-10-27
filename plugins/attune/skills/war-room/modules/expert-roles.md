---
name: expert-roles
description: Configuration and invocation patterns for War Room expert panel members
category: war-room-module
tags: [experts, delegation, multi-llm]
dependencies: [conjure:delegation-core]
estimated_tokens: 600
---

# Expert Roles Configuration

## Expert Registry

The source of truth is `EXPERT_CONFIGS` in
`plugins/conjure/scripts/war_room/experts.py`; each entry is an
`ExpertConfig` (role, service, model, description, phases, and an
optional `command` and `optional` flag). An expert with no `command`
runs natively, except `field_tactician`, whose command comes from
`get_glm_command()`. Optional experts join a panel only when their CLI
is installed.

| Key | Role | Service | Phases | Optional |
|-----|------|---------|--------|----------|
| `supreme_commander` | Supreme Commander | native | synthesis | no |
| `chief_strategist` | Chief Strategist | native | assessment, coa | no |
| `intelligence_officer` | Intelligence Officer | gemini | intel | no |
| `field_tactician` | Field Tactician | glm | coa | no |
| `scout` | Scout | qwen | intel | no |
| `red_team` | Red Team Commander | gemini | red_team, premortem | no |
| `logistics_officer` | Logistics Officer | qwen | coa | no |
| `operational_advisor` | Operational Advisor | minimax | intel, coa | yes |
| `skeptical_analyst` | Skeptical Analyst | minimax | red_team | yes |
| `systems_engineer` | Systems Engineer | muse | intel, coa | yes |

## Prosecution Counsel Role

The Prosecution Counsel is a mandatory panelist when
reviewing implementation plans. Their sole job is to
argue against additions using the scrutiny questions
from `leyline:additive-bias-defense`:

1. Is this a deviation from the current priority?
2. Is it critical to implement at this juncture?
3. Does a simpler or more elegant solution exist?
4. What evidence proves this is needed?
5. What breaks if we do not add this?

**Prompt template for Prosecution Counsel:**

> You are the Prosecution Counsel. Your job is to
> challenge every proposed addition in this plan.
> For each new component, abstraction, or capability,
> apply the 5 scrutiny questions. If the proposer
> cannot provide concrete evidence for questions 4
> and 5, recommend removal.
>
> Default stance: this addition should not exist.
> Prove me wrong.

**When active:** Always active for plan reviews.
Optional for other war-room sessions (activated when
`leyline:additive-bias-defense` findings are provided
as input).

## Panel Configurations

`LIGHTWEIGHT_PANEL` is `supreme_commander`, `chief_strategist` and
`red_team`, for quick decisions with lower complexity. `FULL_COUNCIL`
is every key in `EXPERT_CONFIGS`, for complex, high-stakes decisions.
`active_panel()` drops optional experts whose CLI is missing, because
an unreachable expert would still vote through the Haiku fallback.

The Prosecution Counsel above is a prompt role, not a registry entry,
so neither panel constant lists it.

## GLM Command Resolution

`get_glm_command()` tries the `ccgd` alias, then `claude-glm` on PATH,
then `~/.local/bin/claude-glm`, and raises when none exists. The
war-room expert calls it without `skip_permissions`: it answers through
`-p` and uses no tools, so it never receives
`--dangerously-skip-permissions`.

## Expert Capabilities

| Expert | Context | Speed | Reasoning | Best For |
|--------|---------|-------|-----------|----------|
| Opus | Standard | Slow | Highest | Final synthesis, complex reasoning |
| Sonnet | Standard | Medium | High | Strategy, analysis |
| Gemini 3.1 Pro | 1M | Medium | High | Large codebase analysis |
| GLM-5.3 | Standard | Medium | High | Implementation details |
| Gemini 3.8 Flash | 1M | Fast | Medium | Rapid challenges |
| Qwen `coder-model` | Standard | Medium | Medium-High | Data gathering and estimation |

## Phase-to-Expert Mapping

| Phase | Primary Expert(s) | Secondary |
|-------|-------------------|-----------|
| Intelligence | Scout, Intel Officer | - |
| Assessment | Chief Strategist | - |
| COA Development | Strategist, Tactician, Logistics | All available |
| Red Team | Red Team Commander | - |
| Voting | All active experts | - |
| Premortem | All active experts | - |
| Synthesis | Supreme Commander | - |

## Agent Teams Member Mapping

When using `--agent-teams`, experts map to Claude Code teammates. External LLM diversity is traded for real-time inter-expert messaging.

```python
AGENT_TEAMS_MEMBERS = {
    "supreme_commander": {
        "agent_name": "supreme-commander",
        "model": "opus",
        "role": "Lead agent (not spawned — IS the lead)",
    },
    "chief_strategist": {
        "agent_name": "chief-strategist",
        "model": "sonnet",
        "color": "#4ECDC4",
    },
    "intelligence_officer": {
        "agent_name": "intel-officer",
        "model": "sonnet",
        "color": "#45B7D1",
    },
    "field_tactician": {
        "agent_name": "field-tactician",
        "model": "sonnet",
        "color": "#96CEB4",
    },
    "scout": {
        "agent_name": "scout",
        "model": "haiku",
        "color": "#FFEAA7",
    },
    "red_team": {
        "agent_name": "red-team",
        "model": "sonnet",
        "color": "#FF6B6B",
    },
    "logistics_officer": {
        "agent_name": "logistics",
        "model": "haiku",
        "color": "#DDA0DD",
    },
}
```

### Model Selection Rationale

- **Opus** for Supreme Commander: highest reasoning for final synthesis
- **Sonnet** for Strategist, Intel, Tactician, Red Team: strong reasoning at moderate cost
- **Haiku** for Scout, Logistics: speed-critical roles with simpler reasoning needs

### Spawning Example

```bash
# Lead spawns chief-strategist teammate
tmux split-window -h "CLAUDECODE=1 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
  claude --agent-id chief-strategist@war-room-20260208 \
         --agent-name chief-strategist \
         --team-name war-room-20260208 \
         --agent-color '#4ECDC4' \
         --parent-session-id $SESSION_ID \
         --model sonnet"
```

## Invocation Safety

All external experts are invoked using `asyncio.create_subprocess_exec` which:
- Does NOT use shell interpretation (no injection risk)
- Passes arguments as a list (safe)
- Captures stdout/stderr separately
- Handles timeouts gracefully

Agent teams teammates are invoked via `tmux split-window` with CLI identity flags: the same safety model applies (no shell interpretation of user input).
