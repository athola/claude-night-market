"""Expert configurations and command resolution for War Room.

Contains EXPERT_CONFIGS, panel definitions, availability testing,
and CLI command resolution (GLM fallback, Haiku fallback).

Note: Uses asyncio.create_subprocess_exec (safe, no shell injection).
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess  # nosec B404 - Used safely with create_subprocess_exec (no shell)
from pathlib import Path

from scripts.war_room.config import (
    CLAUDE_HAIKU,
    CLAUDE_OPUS,
    CLAUDE_SONNET,
    GEMINI_FLASH,
    GEMINI_PRO,
    GLM_53,
    MINIMAX_M3,
    MINIMAX_M3_1_FLASH,
    MUSE_SPARK,
    QWEN_CODER,
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
    ),
    "chief_strategist": ExpertConfig(
        role="Chief Strategist",
        service="native",
        model=CLAUDE_SONNET,
        description="Approach generation and trade-off analysis",
        phases=["assessment", "coa"],
    ),
    "intelligence_officer": ExpertConfig(
        role="Intelligence Officer",
        service="gemini",
        model=GEMINI_PRO,
        description="Deep context analysis with 1M+ token window",
        phases=["intel"],
        command=["gemini", "--model", GEMINI_PRO, "-p"],
    ),
    "field_tactician": ExpertConfig(
        role="Field Tactician",
        service="glm",
        model=GLM_53,
        description="Implementation feasibility assessment",
        phases=["coa"],
    ),
    "scout": ExpertConfig(
        role="Scout",
        service="qwen",
        model=QWEN_CODER,
        description="Rapid reconnaissance and data gathering",
        phases=["intel"],
        command=["qwen", "--model", QWEN_CODER, "-p"],
    ),
    "red_team": ExpertConfig(
        role="Red Team Commander",
        service="gemini",
        model=GEMINI_FLASH,
        description="Adversarial challenge and failure mode identification",
        phases=["red_team", "premortem"],
        command=["gemini", "--model", GEMINI_FLASH, "-p"],
    ),
    "logistics_officer": ExpertConfig(
        role="Logistics Officer",
        service="qwen",
        model=QWEN_CODER,
        description="Resource estimation and dependency analysis",
        phases=["coa"],
        command=["qwen", "--model", QWEN_CODER, "-p"],
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
        model=MINIMAX_M3_1_FLASH,
        description="Rapid second-opinion challenge of proposed courses of action",
        phases=["red_team"],
        command=["mmx", "text", "chat", "--model", MINIMAX_M3_1_FLASH, "--message"],
        optional=True,
    ),
    # ``muse exec <prompt>`` takes the prompt positionally: Meta documents no
    # prompt flag, so the command ends at the --model value and the
    # orchestrator's trailing prompt lands in the right slot. The model is
    # passed because Muse Code's own default is the older muse-spark-1.2.
    "systems_engineer": ExpertConfig(
        role="Systems Engineer",
        service="muse",
        model=MUSE_SPARK,
        description="Repository-scale implementation review across a large codebase",
        phases=["intel", "coa"],
        command=["muse", "exec", "--model", MUSE_SPARK],
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
    are unaffected; their fallback behavior is unchanged.
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
        try:
            await asyncio.wait_for(proc.communicate(), timeout=10.0)
        except asyncio.TimeoutError:
            # wait_for cancels communicate(), not the process. Without
            # this the provider CLI outlives the probe, holding its pipes
            # for the rest of the session.
            proc.kill()
            await proc.wait()
            raise

        available = proc.returncode == 0
        _expert_availability[cache_key] = available
        return available

    # asyncio.TimeoutError became an alias of the builtin only in 3.11;
    # this plugin runs on 3.9, where catching TimeoutError alone lets the
    # probe timeout escape and take the whole panel down.
    except (asyncio.TimeoutError, TimeoutError, FileNotFoundError, RuntimeError):
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


def get_glm_command(*, skip_permissions: bool = False) -> list[str]:
    """Resolve the GLM invocation command with fallback.

    The model id comes from the ExpertConfig, not from here.

    ``--dangerously-skip-permissions`` is added only when a caller passes
    ``skip_permissions=True``. The war-room GLM expert does not: it is
    asked for an opinion through ``-p`` and uses no tools, so it has no
    permission to bypass.

    Priority:
    1. ccgd (alias) - if available in PATH
    2. claude-glm - explicit fallback
    3. ~/.local/bin/claude-glm - direct path fallback
    """
    flags = ["--dangerously-skip-permissions"] if skip_permissions else []

    if shutil.which("ccgd"):
        return ["ccgd", *flags, "-p"]

    if shutil.which("claude-glm"):
        return ["claude-glm", *flags, "-p"]

    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), *flags, "-p"]

    raise RuntimeError(
        "GLM not available. Install claude-glm or configure the ccgd alias.\n"
        "Add to ~/.bashrc: alias ccgd='claude-glm'"
    )


def get_expert_command(expert: ExpertConfig) -> list[str]:
    """Get the command to invoke an expert.

    The GLM command carries ``expert.model`` explicitly. The sealed audit
    record attributes the answer to that id through ``expert_model`` and
    the metadata hash, so the call must name the same model the record
    does.

    Statically configured experts already name the model in ``command``
    and are returned unchanged.
    """
    if expert.service == "glm":
        cmd = get_glm_command(skip_permissions=False)
        if expert.model and "--model" not in cmd:
            # Before the trailing -p, which claude reads as "print this".
            insert_at = cmd.index("-p") if "-p" in cmd else len(cmd)
            cmd[insert_at:insert_at] = ["--model", expert.model]
        return cmd
    if expert.command:
        return expert.command.copy()
    raise RuntimeError(f"No command configured for {expert.role}")
