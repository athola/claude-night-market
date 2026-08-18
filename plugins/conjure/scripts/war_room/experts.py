"""Expert configurations and command resolution for War Room.

Contains EXPERT_CONFIGS, panel definitions, availability testing,
and CLI command resolution (GLM fallback, Haiku fallback).

Note: Uses asyncio.create_subprocess_exec (safe, no shell injection).
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess  # nosec B404 - Used safely with create_subprocess_exec (no shell)
from collections.abc import Callable
from pathlib import Path

from scripts.war_room.config import (
    CLAUDE_HAIKU,
    CLAUDE_OPUS,
    CLAUDE_SONNET,
    GEMINI_3_FLASH,
    GEMINI_3_PRO,
    GLM_53,
    MINIMAX_M2_7,
    MINIMAX_M3,
    MUSE_SPARK,
    QWEN_MAX,
    QWEN_TURBO,
)
from scripts.war_room.models import ExpertConfig

# ---------------------------------------------------------------------------
# Expert Configuration
# ---------------------------------------------------------------------------

EXPERT_CONFIGS: dict[str, ExpertConfig] = {
    "supreme_commander": ExpertConfig(
        role="Supreme Commander",
        service="native",
        model=CLAUDE_OPUS,
        description="Final decision authority and synthesis",
        phases=["synthesis"],
        dangerous=False,
    ),
    "chief_strategist": ExpertConfig(
        role="Chief Strategist",
        service="native",
        model=CLAUDE_SONNET,
        description="Approach generation and trade-off analysis",
        phases=["assessment", "coa"],
        dangerous=False,
    ),
    "intelligence_officer": ExpertConfig(
        role="Intelligence Officer",
        service="gemini",
        model=GEMINI_3_PRO,
        description="Deep context analysis with 1M+ token window",
        phases=["intel"],
        command=["gemini", "--model", GEMINI_3_PRO, "-p"],
    ),
    "field_tactician": ExpertConfig(
        role="Field Tactician",
        service="glm",
        model=GLM_53,
        description="Implementation feasibility assessment",
        phases=["coa"],
        command_resolver="get_glm_command",
    ),
    "scout": ExpertConfig(
        role="Scout",
        service="qwen",
        model=QWEN_TURBO,
        description="Rapid reconnaissance and data gathering",
        phases=["intel"],
        command=["qwen", "--model", QWEN_TURBO, "-p"],
    ),
    "red_team": ExpertConfig(
        role="Red Team Commander",
        service="gemini",
        model=GEMINI_3_FLASH,
        description="Adversarial challenge and failure mode identification",
        phases=["red_team", "premortem"],
        command=["gemini", "--model", GEMINI_3_FLASH, "-p"],
    ),
    "logistics_officer": ExpertConfig(
        role="Logistics Officer",
        service="qwen",
        model=QWEN_MAX,
        description="Resource estimation and dependency analysis",
        phases=["coa"],
        command=["qwen", "--model", QWEN_MAX, "-p"],
    ),
    # ``mmx text chat --message`` is the official MiniMax CLI contract; the
    # orchestrator appends the prompt as the final argv element, so the
    # message flag has to be last.
    "operational_advisor": ExpertConfig(
        role="Operational Advisor",
        service="minimax",
        model=MINIMAX_M3,
        description="Operational trade-off analysis with a large context window",
        phases=["intel", "coa"],
        command=["mmx", "text", "chat", "--model", MINIMAX_M3, "--message"],
        optional=True,
    ),
    "skeptical_analyst": ExpertConfig(
        role="Skeptical Analyst",
        service="minimax",
        model=MINIMAX_M2_7,
        description="Rapid second-opinion challenge of proposed courses of action",
        phases=["red_team"],
        command=["mmx", "text", "chat", "--model", MINIMAX_M2_7, "--message"],
        optional=True,
    ),
    # ``muse exec <prompt>`` takes the prompt positionally: Meta documents no
    # prompt flag, so the command ends at the subcommand and the orchestrator's
    # trailing prompt lands in the right slot. No --model flag is documented
    # for exec either, so the model here records what Muse Code runs on rather
    # than selecting it.
    "systems_engineer": ExpertConfig(
        role="Systems Engineer",
        service="muse",
        model=MUSE_SPARK,
        description="Repository-scale implementation review across a large codebase",
        phases=["intel", "coa"],
        command=["muse", "exec"],
        optional=True,
    ),
}

LIGHTWEIGHT_PANEL = ["supreme_commander", "chief_strategist", "red_team"]
FULL_COUNCIL = list(EXPERT_CONFIGS.keys())


def active_panel(panel: list[str]) -> list[str]:
    """Drop opt-in experts whose CLI is not installed.

    An expert that is configured but unreachable does not sit out: it votes
    through the Haiku fallback, so an uninstalled provider adds duplicate
    ballots to the Borda count. Gating keeps opt-in providers from changing
    a deliberation for users who never installed them. Established experts
    are unaffected; their fallback behaviour is unchanged.
    """
    active: list[str] = []
    for key in panel:
        expert = EXPERT_CONFIGS.get(key)
        if expert is None:
            continue
        if expert.optional and not _optional_expert_installed(expert):
            continue
        active.append(key)
    return active


def _optional_expert_installed(expert: ExpertConfig) -> bool:
    """Report whether an opt-in expert's CLI is on PATH."""
    if not expert.command:
        return True
    return shutil.which(expert.command[0]) is not None


# Track which experts have been tested and their availability
_expert_availability: dict[str, bool] = {}
_haiku_fallback_notices: list[str] = []


# ---------------------------------------------------------------------------
# Command Resolution
# ---------------------------------------------------------------------------

# Registry of command resolvers (used by get_expert_command). Typed as the
# callable it actually holds: every registered resolver is a zero-argument
# function returning the argv list. Declaring it as object made the resolver
# call below unverifiable, which is the whole reason the registry exists.
_COMMAND_RESOLVERS: dict[str, Callable[[], list[str]]] = {}


def get_haiku_command() -> list[str]:
    """Get command to invoke Claude Haiku as fallback.

    Used when external LLMs (Gemini, Qwen, GLM) are unavailable.
    Provides diversity through smaller/faster Claude model.
    """
    if shutil.which("claude"):
        return ["claude", "--model", CLAUDE_HAIKU, "-p"]
    raise FileNotFoundError("Claude CLI not found in PATH; cannot use Haiku fallback")


async def check_expert_availability(expert: ExpertConfig) -> bool:
    """Test if an external expert is available with a lightweight probe.

    Returns True if expert responds successfully, False otherwise.
    Results are cached to avoid repeated probes.
    """
    cache_key = f"{expert.service}:{expert.model}"

    # Check cache first
    if cache_key in _expert_availability:
        return _expert_availability[cache_key]

    # Native experts are always available
    if expert.service == "native":
        _expert_availability[cache_key] = True
        return True

    try:
        cmd = get_expert_command(expert)
        # Use minimal probe prompt
        probe_cmd = cmd + ["respond with 'ok'"]

        proc = await asyncio.create_subprocess_exec(
            *probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10.0)

        available = proc.returncode == 0
        _expert_availability[cache_key] = available
        return available

    except (TimeoutError, FileNotFoundError, RuntimeError):
        _expert_availability[cache_key] = False
        return False


def get_fallback_notice() -> str:
    """Get accumulated fallback notices for user display."""
    if not _haiku_fallback_notices:
        return ""
    notices = "\n".join(f"  - {n}" for n in _haiku_fallback_notices)
    return f"\n⚠️ External LLM Fallbacks:\n{notices}\n"


def clear_availability_cache() -> None:
    """Clear the expert availability cache (useful for testing)."""
    _expert_availability.clear()
    _haiku_fallback_notices.clear()


def get_glm_command() -> list[str]:
    """Resolve the GLM invocation command with fallback.

    The model id comes from the ExpertConfig, not from here.

    Priority:
    1. ccgd (alias) - if available in PATH
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    3. ~/.local/bin/claude-glm - direct path fallback
    """
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM not available. Install claude-glm or configure the ccgd alias.\n"
        "Add to ~/.bashrc: alias ccgd='claude-glm --dangerously-skip-permissions'"
    )


# Register resolvers
_COMMAND_RESOLVERS["get_glm_command"] = get_glm_command


def get_expert_command(expert: ExpertConfig) -> list[str]:
    """Get the command to invoke an expert."""
    if expert.command_resolver:
        resolver = _COMMAND_RESOLVERS.get(expert.command_resolver)
        if resolver is None:
            raise RuntimeError(f"Unknown command resolver: {expert.command_resolver}")
        cmd = resolver()
        if not isinstance(cmd, list):
            raise RuntimeError(
                f"Resolver {expert.command_resolver} did not return list"
            )
        return cmd
    if expert.command:
        return expert.command.copy()
    raise RuntimeError(f"No command configured for {expert.role}")
