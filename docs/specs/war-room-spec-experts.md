# War Room Specification: Expert Panel

**Part of**: [War Room Specification](war-room-spec-overview.md)

---

## Default Panel (Lightweight Mode)

| Role | LLM | Invocation | Purpose |
|------|-----|------------|---------|
| **Supreme Commander** | Claude Opus | Native session | Final synthesis, escalation decisions |
| **Chief Strategist** | Claude Sonnet | Native session | Approach generation, trade-off analysis |
| **Red Team** | Gemini Flash | `gemini --model gemini-2.0-flash-exp -p "..."` | Adversarial challenge, failure modes |

## Full Council (Escalated Mode)

| Role | LLM | Invocation | Purpose |
|------|-----|------------|---------|
| **Supreme Commander** | Claude Opus | Native session | Final synthesis |
| **Chief Strategist** | Claude Sonnet | Native session | Approach generation |
| **Intelligence Officer** | Gemini 2.5 Pro | `gemini --model gemini-2.5-pro-exp -p "..."` | Large context analysis (1M+ tokens) |
| **Field Tactician** | GLM-4.7 | `ccgd -p "..."` | Implementation feasibility |
| **Scout** | Qwen Turbo | `qwen --model qwen-turbo -p "..."` | Quick data gathering |
| **Red Team Commander** | Gemini Flash | `gemini --model gemini-2.0-flash-exp -p "..."` | Adversarial challenge |
| **Logistics Officer** | Qwen Max | `qwen --model qwen-max -p "..."` | Resource estimation |

---

## Expert Invocation Code

```python
EXPERT_CONFIGS = {
    "supreme_commander": {
        "role": "Supreme Commander",
        "service": "native",  # Uses current Claude session
        "model": "claude-opus-4",
        "dangerous": False,   # Native session, no subprocess
    },
    "chief_strategist": {
        "role": "Chief Strategist",
        "service": "native",
        "model": "claude-sonnet-4",
        "dangerous": False,
    },
    "intelligence_officer": {
        "role": "Intelligence Officer",
        "service": "gemini",
        "model": "gemini-2.5-pro-exp",
        "command": ["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
        "dangerous": True,    # No interactive prompts
    },
    "field_tactician": {
        "role": "Field Tactician",
        "service": "glm",
        "model": "glm-4.7",
        "command_resolver": "get_glm_command",  # Dynamic resolution
        "preferred_alias": "ccgd",
        "fallback_command": ["claude-glm", "--dangerously-skip-permissions", "-p"],
        "dangerous": True,
    },
    "scout": {
        "role": "Scout",
        "service": "qwen",
        "model": "qwen-turbo",
        "command": ["qwen", "--model", "qwen-turbo", "-p"],
        "dangerous": True,
    },
    "red_team": {
        "role": "Red Team Commander",
        "service": "gemini",
        "model": "gemini-2.0-flash-exp",
        "command": ["gemini", "--model", "gemini-2.0-flash-exp", "-p"],
        "dangerous": True,
    },
    "logistics_officer": {
        "role": "Logistics Officer",
        "service": "qwen",
        "model": "qwen-max",
        "command": ["qwen", "--model", "qwen-max", "-p"],
        "dangerous": True,
    },
}
```

---

## GLM Command Fallback Logic

```python
def get_glm_command() -> list[str]:
    """
    Get GLM-4.7 invocation command with fallback.

    Priority:
    1. ccgd (alias) - fastest, if available
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    """
    import shutil

    # Check if ccgd alias is available
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    # Fallback to explicit command
    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    # Last resort: check common locations
    from pathlib import Path
    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM-4.7 not available. Install claude-glm or configure ccgd alias.\n"
        "See: ~/.local/bin/claude-glm or add to ~/.bashrc:\n"
        "  alias ccgd='claude-glm --dangerously-skip-permissions'"
    )
```

---

## Escalation Protocol

The Supreme Commander evaluates after Phase 3 (COA Development):

```python
def should_escalate(lightweight_coas: list[COA]) -> tuple[bool, str]:
    """
    Supreme Commander decides if full council is needed.

    Escalation triggers:
    - High complexity detected (multiple architectural trade-offs)
    - Significant disagreement between initial experts
    - Novel problem domain requiring specialized analysis
    - User explicitly requested full council
    - Stakes are high (irreversible decisions)
    """
    # Returns (should_escalate, justification)
```

---

**Next**: See [Protocol](war-room-spec-protocol.md) for deliberation phases and prompt templates.
