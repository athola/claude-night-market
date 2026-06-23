"""TDD tests for CJR behavioral findings.

CJR-001: Model IDs must be named constants with startup validation.
CJR-002: verify_service auth probe must narrow exception to subprocess types.
CJR-003: load_configurations must narrow exception to json/OS types.
CJR-004: compute_borda_scores must produce identical output after O(n²) refactor.
CJR-007: convene() must call module-level phase functions directly.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# CJR-001: Named model ID constants + startup validation
# ---------------------------------------------------------------------------


class TestModelIdConstants:
    """Model IDs must be named constants, not inline strings."""

    def test_constants_exist_in_config_module(self) -> None:
        """All 8 model IDs must be importable named constants."""
        from scripts.war_room.config import (
            CLAUDE_HAIKU_3,
            CLAUDE_OPUS_4,
            CLAUDE_SONNET_4,
            GEMINI_20_FLASH,
            GEMINI_25_PRO,
            GLM_47,
            QWEN_MAX,
            QWEN_TURBO,
        )

        assert CLAUDE_OPUS_4 == "claude-opus-4"
        assert CLAUDE_SONNET_4 == "claude-sonnet-4"
        assert GEMINI_25_PRO == "gemini-2.5-pro-exp"
        assert GLM_47 == "glm-4.7"
        assert QWEN_TURBO == "qwen-turbo"
        assert GEMINI_20_FLASH == "gemini-2.0-flash-exp"
        assert QWEN_MAX == "qwen-max"
        assert CLAUDE_HAIKU_3 == "claude-haiku-3"

    def test_validate_model_ids_rejects_empty_string(self) -> None:
        """Validation must raise ValueError for any empty model ID."""
        from scripts.war_room.config import validate_model_ids

        with pytest.raises(ValueError, match="empty"):
            validate_model_ids({"MODEL_A": ""})

    def test_validate_model_ids_accepts_valid_ids(self) -> None:
        """Validation must pass silently for non-empty strings."""
        from scripts.war_room.config import validate_model_ids

        # Must not raise
        validate_model_ids({"CLAUDE_OPUS_4": "claude-opus-4", "GLM": "glm-4.7"})

    def test_experts_uses_constants_not_inline_strings(self) -> None:
        """experts.py must reference config constants, not duplicate literals."""
        import ast
        from pathlib import Path

        experts_path = (
            Path(__file__).parent.parent / "scripts" / "war_room" / "experts.py"
        )
        source = experts_path.read_text()
        tree = ast.parse(source)

        # Collect all string literals in the file
        string_literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]

        banned_model_ids = {
            "claude-opus-4",
            "claude-sonnet-4",
            "gemini-2.5-pro-exp",
            "glm-4.7",
            "qwen-turbo",
            "gemini-2.0-flash-exp",
            "qwen-max",
            "claude-haiku-3",
        }
        found = banned_model_ids & set(string_literals)
        assert not found, (
            f"experts.py still has inline model ID strings: {found}. "
            "Use constants from scripts.war_room.config."
        )


# ---------------------------------------------------------------------------
# CJR-002: verify_service narrow exception
# ---------------------------------------------------------------------------


class TestVerifyServiceNarrowException:
    """Auth probe must not swallow unexpected exceptions."""

    def test_unexpected_exception_propagates_from_auth_probe(
        self, tmp_path: Path
    ) -> None:
        """RuntimeError from auth probe must propagate, not be swallowed."""
        from scripts.delegation_executor import Delegator

        delegator = Delegator(config_dir=tmp_path)

        # --version call succeeds, auth status raises unexpected error
        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[ok_result, RuntimeError("unexpected auth failure")],
        ):
            with pytest.raises(RuntimeError, match="unexpected auth failure"):
                delegator.verify_service("qwen")

    def test_timeout_is_caught_as_issue(self, tmp_path: Path) -> None:
        """TimeoutExpired from auth probe must be caught and reported as issue."""
        from scripts.delegation_executor import Delegator

        delegator = Delegator(config_dir=tmp_path)

        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[
                ok_result,
                subprocess.TimeoutExpired(cmd=["qwen", "auth", "status"], timeout=10),
            ],
        ):
            is_available, issues = delegator.verify_service("qwen")
            assert not is_available
            assert any("auth" in i.lower() for i in issues)

    def test_file_not_found_is_caught_as_issue(self, tmp_path: Path) -> None:
        """FileNotFoundError from auth probe must be caught and reported as issue."""
        from scripts.delegation_executor import Delegator

        delegator = Delegator(config_dir=tmp_path)

        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[ok_result, FileNotFoundError("qwen not found")],
        ):
            is_available, issues = delegator.verify_service("qwen")
            assert not is_available
            assert any("auth" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# CJR-003: load_configurations narrow exception
# ---------------------------------------------------------------------------


class TestLoadConfigurationsNarrowException:
    """Config load must not swallow unexpected exceptions."""

    def test_type_error_propagates_from_bad_service_config(
        self, tmp_path: Path
    ) -> None:
        """TypeError from malformed service config must propagate."""
        from scripts.delegation_executor import Delegator

        config_file = tmp_path / "config.json"
        # Valid JSON, valid "services" dict, but ServiceConfig(**{"bad": 1})
        # will raise TypeError for unknown field.
        config_file.write_text(
            json.dumps({"services": {"newsvc": {"bad_field": "value"}}})
        )

        with pytest.raises(TypeError):
            Delegator(config_dir=tmp_path)

    def test_json_decode_error_is_swallowed(self, tmp_path: Path) -> None:
        """JSONDecodeError from malformed config file must be silently skipped."""
        from scripts.delegation_executor import Delegator

        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        # Must not raise — JSONDecodeError is expected to be swallowed
        delegator = Delegator(config_dir=tmp_path)
        # Default services should still be present
        assert "gemini" in delegator.services

    def test_os_error_is_swallowed(self, tmp_path: Path) -> None:
        """OSError (e.g., permission denied) must be silently skipped."""
        from scripts.delegation_executor import Delegator

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"services": {}}))

        with patch("builtins.open", side_effect=OSError("permission denied")):
            delegator = Delegator(config_dir=tmp_path)
            assert "gemini" in delegator.services


# ---------------------------------------------------------------------------
# CJR-004: Borda score O(n²) refactor — output must be identical
# ---------------------------------------------------------------------------


class TestBordaScoresCharacterization:
    """compute_borda_scores output must be identical after O(n²) refactor."""

    def _original_borda(
        self, votes: dict[str, str], coa_labels: list[str]
    ) -> dict[str, int]:
        """Reference copy of the original O(n³) algorithm for comparison."""
        scores: dict[str, int] = dict.fromkeys(coa_labels, 0)
        n = len(coa_labels)
        for vote_text in votes.values():
            for label in coa_labels:
                for rank in range(1, n + 1):
                    if f"{rank}." in vote_text and label in vote_text:
                        pos = vote_text.find(label)
                        rank_pos = vote_text.find(f"{rank}.")
                        if 0 <= rank_pos < pos < rank_pos + 200:
                            scores[label] += n - rank + 1
                            break
        return scores

    def test_normal_ballot(self) -> None:
        """Standard ballot produces same scores as original algorithm."""
        from scripts.war_room.phases import compute_borda_scores

        labels = ["Alpha", "Beta", "Gamma"]
        votes = {
            "expert1": "1. Alpha is best\n2. Beta is second\n3. Gamma is third",
            "expert2": "1. Beta is top\n2. Gamma follows\n3. Alpha is last",
        }
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_label_absent_from_ballot(self) -> None:
        """Label not mentioned in ballot gets 0 additional score."""
        from scripts.war_room.phases import compute_borda_scores

        labels = ["Alpha", "Beta", "Zeta"]
        votes = {"expert1": "1. Alpha wins\n2. Beta second\n3. Delta not in list"}
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_rank_marker_far_from_label(self) -> None:
        """Label more than 200 chars after rank marker gets 0 score."""
        from scripts.war_room.phases import compute_borda_scores

        labels = ["Alpha"]
        # Put Alpha 300 chars after "1."
        padding = "x" * 250
        votes = {"expert1": f"1. {padding} Alpha is here"}
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_empty_votes(self) -> None:
        """Empty votes dict returns all-zero scores."""
        from scripts.war_room.phases import compute_borda_scores

        labels = ["Alpha", "Beta"]
        expected = self._original_borda({}, labels)
        assert compute_borda_scores({}, labels) == expected

    def test_large_n_produces_same_output(self) -> None:
        """n=20 labels, 5 ballots: optimized output matches reference."""
        from scripts.war_room.phases import compute_borda_scores

        labels = [f"COA_{i}" for i in range(20)]
        votes = {}
        for ballot_idx in range(5):
            lines = []
            for rank_idx, label in enumerate(labels):
                lines.append(f"{rank_idx + 1}. {label} is rank {rank_idx + 1}")
            votes[f"expert{ballot_idx}"] = "\n".join(lines)

        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected
