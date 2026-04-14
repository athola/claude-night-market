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

```python
EXPERT_CONFIGS = {
    "supreme_commander": {
        "role": "Supreme Commander",
        "service": "native",
        "model": "claude-opus-4",
        "description": "Final decision authority and synthesis",
        "phases": ["synthesis"],
        "dangerous": False,
    },
    "chief_strategist": {
        "role": "Chief Strategist",
        "service": "native",
        "model": "claude-sonnet-4",
        "description": "Approach generation and trade-off analysis",
        "phases": ["assessment", "coa_development"],
        "dangerous": False,
    },
    "intelligence_officer": {
        "role": "Intelligence Officer",
        "service": "gemini",
        "model": "gemini-2.5-pro-exp",
        "command": ["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
        "description": "Deep context analysis with 1M+ token window",
        "phases": ["intel"],
        "dangerous": True,
    },
    "field_tactician": {
        "role": "Field Tactician",
        "service": "glm",
        "model": "glm-4.7",
        "command_resolver": "get_glm_command",
        "preferred_alias": "ccgd",
        "fallback_command": ["claude-glm", "--dangerously-skip-permissions", "-p"],
        "description": "Implementation feasibility assessment",
        "phases": ["coa_development"],
        "dangerous": True,
    },
    "scout": {
        "role": "Scout",
        "service": "qwen",
        "model": "qwen-turbo",
        "command": ["qwen", "--model", "qwen-turbo", "-p"],
        "description": "Rapid reconnaissance and data gathering",
        "phases": ["intel"],
        "dangerous": True,
    },
    "prosecution_counsel": {
        "role": "Prosecution Counsel",
        "service": "native",
        "model": "claude-sonnet-4",
        "description": "Challenges every addition using additive-bias-defense scrutiny questions",
        "phases": ["red_team", "coa_development"],
        "dangerous": False,
    },
    "red_team": {
        "role": "Red Team Commander",
        "service": "gemini",
        "model": "gemini-2.0-flash-exp",
        "command": ["gemini", "--model", "gemini-2.0-flash-exp", "-p"],
        "description": "Adversarial challenge and failure mode identification",
        "phases": ["red_team", "premortem"],
        "dangerous": True,
    },
    "logistics_officer": {
        "role": "Logistics Officer",
        "service": "qwen",
        "model": "qwen-max",
        "command": ["qwen", "--model", "qwen-max", "-p"],
        "description": "Resource estimation and dependency analysis",
        "phases": ["coa_development"],
        "dangerous": True,
    },
}
```

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

### Lightweight Panel

For quick decisions with lower complexity:

```python
LIGHTWEIGHT_PANEL = [
    "supreme_commander",
    "chief_strategist",
    "prosecution_counsel",
    "red_team",
]
```

### Full Council

For complex, high-stakes decisions:

```python
FULL_COUNCIL = [
    "supreme_commander",
    "chief_strategist",
    "intelligence_officer",
    "prosecution_counsel",
    "field_tactician",
    "scout",
    "red_team",
    "logistics_officer",
]
```

## GLM-4.7 Command Resolution

```python
def get_glm_command() -> list[str]:
    """
    Resolve GLM-4.7 invocation command with fallback.

    Priority:
    1. ccgd (alias) - if available in PATH
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    3. ~/.local/bin/claude-glm - direct path fallback
    """
    import shutil
    from pathlib import Path

    # Check for alias
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    # Check for script in PATH
    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    # Direct path fallback
    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM-4.7 not available. Install claude-glm or configure ccgd alias.\n"
        "Add to ~/.bashrc: alias ccgd='claude-glm --dangerously-skip-permissions'"
    )
```

## Expert Capabilities

| Expert | Context | Speed | Reasoning | Best For |
|--------|---------|-------|-----------|----------|
| Opus | Standard | Slow | Highest | Final synthesis, complex reasoning |
| Sonnet | Standard | Medium | High | Strategy, analysis |
| Gemini Pro | 1M+ | Medium | High | Large codebase analysis |
| GLM-4.7 | Standard | Medium | High | Implementation details |
| Qwen Turbo | Standard | Fast | Medium | Quick data gathering |
| Gemini Flash | Standard | Fast | Medium | Rapid challenges |
| Qwen Max | Standard | Medium | Medium-High | Thorough estimation |

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

- **Opus** for Supreme Commander — highest reasoning for final synthesis
- **Sonnet** for Strategist, Intel, Tactician, Red Team — strong reasoning at moderate cost
- **Haiku** for Scout, Logistics — speed-critical roles with simpler reasoning needs

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

Agent teams teammates are invoked via `tmux split-window` with CLI identity flags — the same safety model applies (no shell interpretation of user input).
