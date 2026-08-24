"""Tests for delphi.py convergence computation and revision rounds.

Targets uncovered paths in compute_convergence and
delphi_revision_round to raise delphi.py coverage above 80%.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from scripts.war_room import WarRoomOrchestrator
from scripts.war_room.delphi import compute_convergence, delphi_revision_round
from scripts.war_room.models import ExpertInfo, WarRoomSession

# -------------------------------------------------------------------
# compute_convergence
# -------------------------------------------------------------------


class TestComputeConvergence:
    """Test compute_convergence edge cases for full branch coverage."""

    @pytest.mark.parametrize(
        ("borda_scores", "expected"),
        [
            ({}, 0.0),
            ({"A": 5}, 0.0),
            ({"A": 0, "B": 0}, 0.0),
            ({"A": 0, "B": 0, "C": 0}, 0.0),
        ],
        ids=[
            "empty-scores",
            "single-score",
            "two-zeros",
            "three-zeros",
        ],
    )
    def test_convergence_returns_zero_for_degenerate_inputs(
        self,
        borda_scores: dict[str, int],
        expected: float,
    ) -> None:
        """Degenerate inputs yield zero convergence."""
        session = WarRoomSession(
            session_id="conv-test",
            problem_statement="Test",
        )
        session.artifacts["voting"] = {"borda_scores": borda_scores}

        assert compute_convergence(session) == expected

    def test_convergence_no_voting_artifact(self) -> None:
        """Missing voting artifact yields zero convergence."""
        session = WarRoomSession(
            session_id="no-vote",
            problem_statement="Test",
        )
        # No voting artifact at all
        assert compute_convergence(session) == 0.0

    def test_convergence_clear_winner(self) -> None:
        """Clear winner (high spread) produces high convergence."""
        session = WarRoomSession(
            session_id="clear-winner",
            problem_statement="Test",
        )
        session.artifacts["voting"] = {
            "borda_scores": {"A": 100, "B": 1},
        }

        result = compute_convergence(session)
        # Large spread relative to mean indicates high convergence
        assert 0.5 < result <= 1.0

    def test_convergence_equal_scores(self) -> None:
        """Equal scores (no spread) produce zero convergence."""
        session = WarRoomSession(
            session_id="equal-scores",
            problem_statement="Test",
        )
        session.artifacts["voting"] = {
            "borda_scores": {"A": 5, "B": 5, "C": 5},
        }

        result = compute_convergence(session)
        assert result == 0.0

    def test_convergence_two_options_moderate_spread(self) -> None:
        """Two options with moderate spread yield intermediate value."""
        session = WarRoomSession(
            session_id="moderate",
            problem_statement="Test",
        )
        session.artifacts["voting"] = {
            "borda_scores": {"A": 8, "B": 4},
        }

        result = compute_convergence(session)
        assert 0.0 < result <= 1.0

    def test_convergence_capped_at_one(self) -> None:
        """Convergence is capped at 1.0 even with extreme spread."""
        session = WarRoomSession(
            session_id="extreme",
            problem_statement="Test",
        )
        session.artifacts["voting"] = {
            "borda_scores": {"A": 1000, "B": 1},
        }

        result = compute_convergence(session)
        assert result <= 1.0


# -------------------------------------------------------------------
# delphi_revision_round
# -------------------------------------------------------------------


class TestDelphiRevisionRound:
    """Test delphi_revision_round for uncovered branches."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> WarRoomOrchestrator:
        """Create orchestrator with temp path."""
        return WarRoomOrchestrator(strategeion_path=tmp_path)

    @pytest.mark.asyncio
    async def test_revision_round_updates_coas(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """Revision round calls _invoke_parallel and updates artifacts."""
        session = WarRoomSession(
            session_id="rev-test",
            problem_statement="Revise decision",
            mode="full_council",
        )
        session.artifacts["red_team"] = {"challenges": "Challenge text"}
        session.artifacts["coa"] = {
            "raw_coas": {
                "chief_strategist": "Original A",
                "field_tactician": "Original B",
            },
        }
        # Add a node so get_anonymized_view returns something
        session.merkle_dag.add_contribution(
            content="Original A",
            phase="coa",
            round_number=1,
            expert=ExpertInfo(role="Chief Strategist", model="model"),
        )

        with patch.object(
            orchestrator,
            "_invoke_parallel",
            new_callable=AsyncMock,
        ) as mock_parallel:
            mock_parallel.return_value = {
                "chief_strategist": "Revised A",
                "field_tactician": "Revised B",
            }

            await delphi_revision_round(orchestrator, session, 2)

        # Verify updated artifacts
        assert session.artifacts["coa"]["delphi_round"] == 2
        assert session.artifacts["coa"]["raw_coas"]["chief_strategist"] == "Revised A"
        assert session.artifacts["coa"]["raw_coas"]["field_tactician"] == "Revised B"
        # Verify _invoke_parallel was called with correct phase
        mock_parallel.assert_called_once()
        call_args = mock_parallel.call_args
        assert call_args.args[3] == "coa"  # phase argument

    @pytest.mark.asyncio
    async def test_revision_round_skips_commander_and_red_team(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """Revision excludes supreme_commander and red_team."""
        session = WarRoomSession(
            session_id="skip-test",
            problem_statement="Test",
            mode="full_council",
        )
        session.artifacts["red_team"] = {"challenges": "feedback"}
        session.artifacts["coa"] = {
            "raw_coas": {
                "supreme_commander": "SC decision",
                "red_team": "RT review",
                "chief_strategist": "CS approach",
            },
        }

        with patch.object(
            orchestrator,
            "_invoke_parallel",
            new_callable=AsyncMock,
        ) as mock_parallel:
            mock_parallel.return_value = {
                "chief_strategist": "Revised CS",
            }

            await delphi_revision_round(orchestrator, session, 3)

        # Only chief_strategist should be in the expert list
        expert_keys = mock_parallel.call_args.args[0]
        assert "supreme_commander" not in expert_keys
        assert "red_team" not in expert_keys
        assert "chief_strategist" in expert_keys

    @pytest.mark.asyncio
    async def test_revision_round_empty_previous_coas(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """Revision round handles empty previous COAs gracefully."""
        session = WarRoomSession(
            session_id="empty-coa",
            problem_statement="Test",
            mode="full_council",
        )
        session.artifacts["red_team"] = {"challenges": "feedback"}
        session.artifacts["coa"] = {"raw_coas": {}}

        with patch.object(
            orchestrator,
            "_invoke_parallel",
            new_callable=AsyncMock,
        ) as mock_parallel:
            mock_parallel.return_value = {}

            await delphi_revision_round(orchestrator, session, 2)

        # No experts to revise, so parallel should be called with empty
        expert_keys = mock_parallel.call_args.args[0]
        assert len(expert_keys) == 0
        assert session.artifacts["coa"]["delphi_round"] == 2

    @pytest.mark.asyncio
    async def test_revision_round_missing_red_team_artifact(
        self,
        orchestrator: WarRoomOrchestrator,
    ) -> None:
        """Revision round defaults to 'N/A' when red_team missing."""
        session = WarRoomSession(
            session_id="no-rt",
            problem_statement="Test",
            mode="full_council",
        )
        # No red_team artifact at all
        session.artifacts["coa"] = {
            "raw_coas": {"chief_strategist": "approach"},
        }

        with patch.object(
            orchestrator,
            "_invoke_parallel",
            new_callable=AsyncMock,
        ) as mock_parallel:
            mock_parallel.return_value = {
                "chief_strategist": "Revised",
            }

            await delphi_revision_round(orchestrator, session, 2)

        assert session.artifacts["coa"]["delphi_round"] == 2


class TestAUnanimousPanelCanActuallyConverge:
    """The scale has to reach the threshold the loop stops on.

    The raw coefficient of variation of Borda counts is bounded by
    `2*sqrt((n+1)/(12*(n-1)))`: 0.816 at three COAs, 0.707 at five,
    falling toward 0.577. The default `convergence_threshold` is 0.85,
    so a unanimous panel could not clear it for any COA count above two
    and every Delphi run paid for `max_rounds`.
    """

    DEFAULT_THRESHOLD = 0.85

    @staticmethod
    def _convergence(scores: dict[str, float]) -> float:
        session = WarRoomSession(session_id="s", problem_statement="p")
        session.artifacts["voting"] = {"borda_scores": scores}
        return compute_convergence(session)

    @pytest.mark.parametrize("count", [2, 3, 4, 5, 8])
    def test_a_unanimous_panel_scores_one(self, count: int) -> None:
        """Unanimous ranking is 1.0 whatever the number of COAs."""
        scores = {chr(97 + i): float(count - 1 - i) for i in range(count)}

        assert self._convergence(scores) == pytest.approx(1.0)

    @pytest.mark.parametrize("count", [3, 4, 5, 8])
    def test_a_unanimous_panel_clears_the_default_threshold(self, count: int) -> None:
        """The case that burned every paid round."""
        scores = {chr(97 + i): float(count - 1 - i) for i in range(count)}

        assert self._convergence(scores) >= self.DEFAULT_THRESHOLD

    def test_uniform_scores_are_still_zero(self) -> None:
        """Normalizing must not turn disagreement into agreement."""
        assert self._convergence({"A": 2.0, "B": 2.0, "C": 2.0}) == 0.0

    def test_partial_agreement_lands_between(self) -> None:
        """A narrower spread scores below a unanimous one."""
        partial = self._convergence({"A": 3.0, "B": 2.0, "C": 1.0})
        unanimous = self._convergence({"A": 2.0, "B": 1.0, "C": 0.0})

        assert 0.0 < partial < unanimous

    def test_the_result_never_exceeds_one(self) -> None:
        """A spread wider than any ranking can produce is still capped."""
        assert self._convergence({"A": 100.0, "B": 0.0, "C": 0.0}) <= 1.0
