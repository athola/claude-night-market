"""Model ID constants for War Room expert configuration.

Single source of truth for all LLM model identifiers used by War Room.
Prevents silent misconfiguration from drift between EXPERT_CONFIGS entries
and their corresponding CLI command arguments.
"""

from __future__ import annotations

# Native Claude models (served by the orchestrating Claude process)
CLAUDE_OPUS_4 = "claude-opus-4"
CLAUDE_SONNET_4 = "claude-sonnet-4"

# Gemini models (served via gemini CLI)
GEMINI_25_PRO = "gemini-2.5-pro-exp"
GEMINI_20_FLASH = "gemini-2.0-flash-exp"

# Qwen models (served via qwen CLI)
QWEN_TURBO = "qwen-turbo"
QWEN_MAX = "qwen-max"

# GLM models (served via ccgd / claude-glm)
GLM_47 = "glm-4.7"

# Haiku fallback (used when external LLMs are unavailable)
CLAUDE_HAIKU_3 = "claude-haiku-3"


def validate_model_ids(model_ids: dict[str, str]) -> None:
    """Raise ValueError if any model ID is an empty string.

    Args:
        model_ids: Mapping of constant name to model ID value.

    Raises:
        ValueError: If any value is an empty string.

    """
    empty = [name for name, value in model_ids.items() if value == ""]
    if empty:
        raise ValueError(
            f"Model ID constants must not be empty strings: {', '.join(empty)}"
        )
