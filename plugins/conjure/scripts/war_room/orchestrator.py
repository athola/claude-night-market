"""Main War Room orchestrator class.

Slim coordinator that delegates to phase, expert, persistence, and delphi modules.

Note: Uses asyncio.create_subprocess_exec (safe, no shell injection).
"""

from __future__ import annotations

import asyncio
import functools
import subprocess  # nosec B404 - Used safely with create_subprocess_exec (no shell)
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.war_room import experts as _experts_mod
from scripts.war_room.config import CLAUDE_HAIKU
from scripts.war_room.delphi import (
    compute_convergence,
    convene_delphi,
    delphi_revision_round,
)
from scripts.war_room.experts import (
    EXPERT_CONFIGS,
    _haiku_fallback_notices,
    clear_availability_cache,
    get_expert_command,
    get_fallback_notice,
    get_haiku_command,
)
from scripts.war_room.hooks import should_suggest_war_room as _should_suggest_war_room
from scripts.war_room.models import ExpertInfo, MerkleDAG, WarRoomSession
from scripts.war_room.persistence import (
    archive_session,
    list_sessions,
    load_session,
    persist_session,
)
from scripts.war_room.phases import (
    compute_borda_scores,
    escalate,
    phase_assessment,
    phase_coa_development,
    phase_intel,
    phase_premortem,
    phase_red_team,
    phase_synthesis,
    phase_voting,
    should_escalate,
)

# Written as 120.0 at two call sites and as the literal "120s" in four
# messages before this, so changing it meant editing six places.
_SUBPROCESS_TIMEOUT_SECONDS = 120.0


# Built once at import rather than on every attribute miss. Phase methods
# are reached through __getattr__ so the class stays thin; the cost is that
# a typo in a phase name is a runtime AttributeError, not a static error.
_ORCH_BOUND: dict[str, Any] = {
    "_phase_intel": phase_intel,
    "_phase_assessment": phase_assessment,
    "_phase_coa_development": phase_coa_development,
    "_phase_red_team": phase_red_team,
    "_phase_voting": phase_voting,
    "_phase_premortem": phase_premortem,
    "_phase_synthesis": phase_synthesis,
    "_escalate": escalate,
    "_delphi_revision_round": delphi_revision_round,
}
_PLAIN: dict[str, Any] = {
    "_should_escalate": should_escalate,
    "_compute_convergence": compute_convergence,
    "_compute_borda_scores": compute_borda_scores,
}


class WarRoomOrchestrator:
    """Orchestrates multi-LLM deliberation sessions.

    Responsibilities:
    - Expert panel management
    - Phase sequencing
    - Parallel dispatch
    - Response aggregation
    - Merkle-DAG maintenance
    - Strategeion persistence
    """

    def __init__(self, strategeion_path: Path | None = None) -> None:
        """Initialize orchestrator with Strategeion storage path."""
        self.strategeion = strategeion_path or (
            Path.home() / ".claude" / "memory-palace" / "strategeion"
        )
        self.strategeion.mkdir(parents=True, exist_ok=True)

    async def convene(
        self,
        problem: str,
        context_files: list[str] | None = None,
        mode: str = "lightweight",
    ) -> WarRoomSession:
        """Convene a new War Room session.

        Args:
            problem: The problem/decision to deliberate
            context_files: Optional file globs for context
            mode: "lightweight" or "full_council"

        Returns:
            Completed WarRoomSession with decision

        """
        # Clear availability cache for fresh session
        clear_availability_cache()

        session = self._initialize_session(problem, mode)
        session.metrics["start_time"] = datetime.now().isoformat()

        try:
            # Phase 1: Intelligence
            await self._phase_intel(session, context_files)

            # Phase 2: Assessment
            await self._phase_assessment(session)

            # Phase 3: COA Development
            await self._phase_coa_development(session)

            # Escalation check
            if mode == "lightweight" and await self._should_escalate(session):
                session.escalated = True
                session.mode = "full_council"
                await self._escalate(session, context_files)

            # Phase 4: Red Team
            await self._phase_red_team(session)

            # Phase 5: Voting
            await self._phase_voting(session)

            # Phase 6: Premortem
            await self._phase_premortem(session)

            # Phase 7: Synthesis
            await self._phase_synthesis(session)

            session.status = "completed"

        except Exception as e:
            session.status = f"failed: {e}"
            raise

        finally:
            session.metrics["end_time"] = datetime.now().isoformat()
            # Capture any fallback notices
            fallback_notice = get_fallback_notice()
            if fallback_notice:
                session.artifacts["fallback_notice"] = fallback_notice
            self._persist_session(session)

        return session

    def _initialize_session(self, problem: str, mode: str) -> WarRoomSession:
        """Create new session with unique ID."""
        session_id = f"war-room-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return WarRoomSession(
            session_id=session_id,
            problem_statement=problem,
            mode=mode,
            merkle_dag=MerkleDAG(session_id),
        )

    async def _invoke_expert(
        self,
        expert_key: str,
        prompt: str,
        session: WarRoomSession,
        phase: str,
    ) -> str:
        """Invoke a single expert and record contribution.

        For external LLMs (Gemini, Qwen, GLM), tests availability first.
        Falls back to Haiku if external LLM is unavailable.
        """
        expert = EXPERT_CONFIGS[expert_key]
        actual_model = expert.model

        if expert.service == "native":
            # Native experts (Opus, Sonnet) handled by orchestrating Claude
            result = f"[Native expert {expert.role} response placeholder]"
        elif await _experts_mod.check_expert_availability(expert):
            # External expert is available - invoke directly
            result = await self._invoke_external(expert, prompt)
        else:
            # Fallback to Haiku
            actual_model = CLAUDE_HAIKU
            notice = (
                f"{expert.role} ({expert.model}) unavailable, using Haiku as fallback"
            )
            if notice not in _haiku_fallback_notices:
                _haiku_fallback_notices.append(notice)
            result = await self._invoke_haiku_fallback(expert, prompt)

        # Record in Merkle-DAG
        session.merkle_dag.add_contribution(
            content=result,
            phase=phase,
            round_number=len(session.phases_completed) + 1,
            expert=ExpertInfo(role=expert.role, model=actual_model),
        )

        return result

    async def _run_subprocess(self, cmd: list[str], label: str, not_found: str) -> str:
        """Run ``cmd`` and return its stdout, or a bracketed failure note.

        Both invocation paths share this: the same create_subprocess_exec
        call, the same timeout, the same returncode check and the same three
        failure modes. Only the wording differs, which is what ``label`` and
        ``not_found`` carry.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=_SUBPROCESS_TIMEOUT_SECONDS,
            )
            if proc.returncode != 0:
                return f"[{label} failed: {stderr.decode()[:500]}]"
            return stdout.decode()
        except TimeoutError:
            return f"[{label} timed out after {_SUBPROCESS_TIMEOUT_SECONDS:.0f}s]"
        except FileNotFoundError:
            return not_found
        except Exception as e:
            return f"[{label} error: {e}]"

    async def _invoke_haiku_fallback(self, expert: Any, prompt: str) -> str:
        """Invoke Haiku as fallback for unavailable external expert.

        Prefixes prompt with role context to maintain expert perspective.
        """
        role_prefix = (
            f"You are acting as the {expert.role} in a strategic War Room.\n"
            f"Your expertise: {expert.description}\n\n"
        )
        full_prompt = role_prefix + prompt

        try:
            cmd = get_haiku_command()
        except Exception as e:
            return f"[{expert.role} (Haiku fallback) error: {e}]"
        cmd.append(full_prompt)
        return await self._run_subprocess(
            cmd,
            f"{expert.role} (Haiku fallback)",
            f"[{expert.role} fallback failed: Claude CLI not found]",
        )

    async def _invoke_external(self, expert: Any, prompt: str) -> str:
        """Invoke external expert via CLI.

        Uses asyncio.create_subprocess_exec (safe, no shell injection).
        Arguments passed as list, not through shell.
        """
        cmd = get_expert_command(expert)
        cmd.append(prompt)
        return await self._run_subprocess(
            cmd,
            expert.role,
            f"[{expert.role} command not found: {cmd[0]}]",
        )

    async def _invoke_parallel(
        self,
        expert_keys: list[str],
        prompts: dict[str, str],
        session: WarRoomSession,
        phase: str,
    ) -> dict[str, str]:
        """Invoke multiple experts in parallel."""
        tasks = {
            key: self._invoke_expert(
                key, prompts.get(key, prompts.get("default", "")), session, phase
            )
            for key in expert_keys
            if key in EXPERT_CONFIGS
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        output: dict[str, str] = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, BaseException):
                output[key] = f"[Error: {result}]"
            elif isinstance(result, str):
                output[key] = result
            else:
                output[key] = str(result)
        return output

    def __getattr__(self, name: str) -> Any:
        """Delegate phase and utility method lookups to module-level functions."""
        if name in _ORCH_BOUND:
            return functools.partial(_ORCH_BOUND[name], self)
        if name in _PLAIN:
            return _PLAIN[name]
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    # --- Persistence delegations ---

    def _persist_session(self, session: WarRoomSession) -> None:
        """Save session to Strategeion."""
        persist_session(self.strategeion, session)

    def load_session(self, session_id: str) -> WarRoomSession | None:
        """Load session from Strategeion."""
        return load_session(self.strategeion, session_id)

    def archive_session(
        self, session_id: str, project: str | None = None
    ) -> Path | None:
        """Archive completed session."""
        return archive_session(self.strategeion, session_id, project)

    def list_sessions(self, include_archived: bool = False) -> list[dict[str, Any]]:
        """List all War Room sessions."""
        return list_sessions(self.strategeion, include_archived)

    # --- Delphi mode delegation ---

    async def convene_delphi(
        self,
        problem: str,
        context_files: list[str] | None = None,
        max_rounds: int = 5,
        convergence_threshold: float = 0.85,
    ) -> WarRoomSession:
        """Convene Delphi-style War Room with iterative convergence.

        Delegates to delphi.convene_delphi to avoid code duplication.

        Args:
            problem: The problem/decision to deliberate
            context_files: Optional file globs for context
            max_rounds: Maximum Delphi rounds (default 5)
            convergence_threshold: Agreement threshold to stop (default 0.85)

        Returns:
            Completed WarRoomSession with Delphi convergence data

        """
        return await convene_delphi(
            self, problem, context_files, max_rounds, convergence_threshold
        )

    # --- Hook delegation ---

    @staticmethod
    def should_suggest_war_room(
        user_message: str,
        complexity_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """Determine if War Room should be suggested based on message analysis."""
        return _should_suggest_war_room(user_message, complexity_threshold)
