"""Model ID constants for War Room expert configuration.

Single source of truth for all LLM model identifiers used by War Room.
Prevents silent misconfiguration from drift between EXPERT_CONFIGS entries
and their corresponding CLI command arguments.
"""

from __future__ import annotations

# Native Claude models (served by the orchestrating Claude process)
#
# Named by tier rather than generation on purpose. The previous names
# encoded the version (CLAUDE_OPUS_48, CLAUDE_SONNET_46), which meant
# every model release either forced a rename across every consumer or
# left a constant whose name contradicted its value.
#
# Refreshed by Skill(night-market-model-and-harness-updates).
CLAUDE_OPUS = "claude-opus-5"
CLAUDE_SONNET = "claude-sonnet-5"

# Gemini models (served via gemini CLI)
GEMINI_3_PRO = "gemini-3-pro"
GEMINI_3_FLASH = "gemini-3-flash"

# Qwen models (served via qwen CLI)
QWEN_TURBO = "qwen-turbo"
QWEN_MAX = "qwen-max"

# MiniMax models (served via the official mmx CLI)
MINIMAX_M3 = "MiniMax-M3"
MINIMAX_M2_7 = "MiniMax-M2.7"

# Meta Muse models. muse-spark-1.2 is served by the muse CLI; the Glimmer
# weights are Apache 2.0 and run locally, served here through ollama.
MUSE_SPARK = "muse-spark-1.2"
MUSE_GLIMMER = "muse-glimmer:30b"

# GLM models, served through ccgd / claude-glm or the glm delegation service
# against Z.ai's Anthropic-compatible endpoint. GLM-5.2 stays defined: 5.3 was
# still rolling out when it was added, so a caller pinning the older id is
# making a deliberate choice rather than lagging behind.
GLM_52 = "glm-5.2"
GLM_53 = "glm-5.3"

# Haiku fallback (used when external LLMs are unavailable)
CLAUDE_HAIKU = "claude-haiku-4-5"


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


# Self-check: the War Room expert CLI commands are built from these
# constants, so an accidental empty value would silently break expert
# invocation. Validate at import time so the failure is loud.
validate_model_ids(
    {
        "CLAUDE_OPUS": CLAUDE_OPUS,
        "CLAUDE_SONNET": CLAUDE_SONNET,
        "GEMINI_3_PRO": GEMINI_3_PRO,
        "GEMINI_3_FLASH": GEMINI_3_FLASH,
        "QWEN_TURBO": QWEN_TURBO,
        "QWEN_MAX": QWEN_MAX,
        "MINIMAX_M3": MINIMAX_M3,
        "MINIMAX_M2_7": MINIMAX_M2_7,
        "MUSE_SPARK": MUSE_SPARK,
        "MUSE_GLIMMER": MUSE_GLIMMER,
        "GLM_52": GLM_52,
        "GLM_53": GLM_53,
        "CLAUDE_HAIKU": CLAUDE_HAIKU,
    }
)
