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

## Panel Configurations

### Lightweight Panel

For quick decisions with lower complexity:

```python
LIGHTWEIGHT_PANEL = [
    "supreme_commander",
    "chief_strategist",
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

## Invocation Safety

All external experts are invoked using `asyncio.create_subprocess_exec` which:
- Does NOT use shell interpretation (no injection risk)
- Passes arguments as a list (safe)
- Captures stdout/stderr separately
- Handles timeouts gracefully
