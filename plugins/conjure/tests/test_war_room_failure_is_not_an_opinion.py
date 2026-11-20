"""A provider failure never reaches the phases or the audit DAG as an answer.

Each test drives one path by which an error text used to be recorded as
an expert's contribution, or one way the user lost the reason an expert
fell back to Haiku.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room import (
    WarRoomOrchestrator,
    WarRoomSession,
    clear_availability_cache,
    get_fallback_notice,
    phases,
)
from scripts.war_room.experts import EXPERT_CONFIGS, check_expert_availability
from scripts.war_room.models import MerkleDAG
from scripts.war_room.orchestrator import ExpertFailureNote


class _FakeProc:
    def __init__(self, stdout: bytes, stderr: bytes = b"", returncode: int = 0):
        self._out = (stdout, stderr)
        self.returncode = returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._out


@pytest.fixture
def orchestrator(tmp_path: Path) -> WarRoomOrchestrator:
    """Orchestrator with a clean availability cache on both sides."""
    clear_availability_cache()
    yield WarRoomOrchestrator(strategeion_path=tmp_path)
    clear_availability_cache()


@pytest.fixture
def session() -> WarRoomSession:
    """Session with an empty DAG to count contributions in."""
    return WarRoomSession(
        session_id="s", problem_statement="p", merkle_dag=MerkleDAG("s")
    )


async def test_haiku_fallback_without_claude_cli_is_a_failure_not_an_opinion(
    orchestrator: WarRoomOrchestrator, session: WarRoomSession
) -> None:
    """A missing `claude` CLI made every external expert's 'opinion' an error."""
    with (
        patch(
            "scripts.war_room.experts.check_expert_availability",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "scripts.war_room.orchestrator.get_haiku_command",
            side_effect=FileNotFoundError("claude CLI not on PATH"),
        ),
    ):
        output = await orchestrator._invoke_parallel(
            ["intelligence_officer", "field_tactician"],
            {"default": "p"},
            session,
            "intel",
        )

    assert output == {}
    assert set(session.artifacts["expert_failures"]) == {
        "intel:intelligence_officer",
        "intel:field_tactician",
    }
    assert len(session.merkle_dag.nodes) == 0


async def test_red_team_provider_failure_is_not_handed_to_the_phases(
    orchestrator: WarRoomOrchestrator, session: WarRoomSession
) -> None:
    """A direct `_invoke_expert` caller stored a 401 note as the challenges."""
    note = ExpertFailureNote("[Red Team Commander failed: 401 bad key]")
    with (
        patch(
            "scripts.war_room.experts.check_expert_availability",
            new=AsyncMock(return_value=True),
        ),
        patch.object(orchestrator, "_run_subprocess", new=AsyncMock(return_value=note)),
    ):
        await phases.phase_red_team(orchestrator, session)

    assert "401" not in str(session.artifacts["red_team"].get("challenges"))
    assert "401" in session.artifacts["expert_failures"]["red_team:red_team"]
    assert len(session.merkle_dag.nodes) == 0


async def test_refused_credential_with_exit_zero_is_a_failure(
    orchestrator: WarRoomOrchestrator, session: WarRoomSession
) -> None:
    """The qwen CLI prints its 401 and exits 0; that text is not the Scout's report."""
    proc = _FakeProc(b"[API Error: 401 Incorrect API key provided]\n")
    with (
        patch(
            "scripts.war_room.experts.check_expert_availability",
            new=AsyncMock(return_value=True),
        ),
        patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)),
    ):
        result = await orchestrator._invoke_expert("scout", "p", session, "intel")

    assert result is None
    assert "401" in session.artifacts["expert_failures"]["intel:scout"]
    assert len(session.merkle_dag.nodes) == 0


async def test_glm_expert_does_not_inherit_the_anthropic_key(
    orchestrator: WarRoomOrchestrator,
    session: WarRoomSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The GLM wrapper sends to Z.ai; an inherited Anthropic key goes with it."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-secret")
    spawn = AsyncMock(return_value=_FakeProc(b"feasible\n"))
    with (
        patch(
            "scripts.war_room.experts.check_expert_availability",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "scripts.war_room.experts.get_glm_command",
            return_value=["claude-glm", "-p"],
        ),
        patch("asyncio.create_subprocess_exec", new=spawn),
    ):
        result = await orchestrator._invoke_expert(
            "field_tactician", "p", session, "coa"
        )

    assert result == "feasible\n"
    env: dict[str, Any] = spawn.call_args.kwargs["env"]
    assert "ANTHROPIC_API_KEY" not in env
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
    assert env.get("PATH")


async def test_fallback_notice_names_why_the_expert_is_unavailable(
    orchestrator: WarRoomOrchestrator, session: WarRoomSession
) -> None:
    """A missing binary, a missing key and a refused key all read the same."""
    reason = "Command 'gemini' not found. Install with: npm i -g x"
    with (
        patch(
            "scripts.war_room.experts.verify_service",
            return_value=(False, [reason]),
        ),
        patch.object(
            orchestrator,
            "_invoke_haiku_fallback",
            new=AsyncMock(return_value="haiku answer"),
        ),
    ):
        await orchestrator._invoke_expert("intelligence_officer", "p", session, "intel")

    assert reason in get_fallback_notice()


async def test_raising_availability_check_is_logged_as_a_warning_with_reason(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A raising check went only to debug, and the notice lost the cause."""
    clear_availability_cache()
    expert = EXPERT_CONFIGS["intelligence_officer"]
    with patch(
        "scripts.war_room.experts.verify_service",
        side_effect=OSError("probe exploded"),
    ):
        available = await check_expert_availability(expert)

    assert available is False
    assert any(
        r.levelname == "WARNING" and "probe exploded" in r.getMessage()
        for r in caplog.records
    )
    clear_availability_cache()
