"""TDD tests for CJR behavioral findings.

CJR-001: Model IDs must be named constants with startup validation.
CJR-002: verify_service auth probe must narrow exception to subprocess types.
CJR-003: load_configurations must narrow exception to json/OS types.
CJR-004: compute_borda_scores must produce identical output after O(n²) refactor.
CJR-007: convene() must call module-level phase functions directly.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.delegation_executor import Delegator
from scripts.war_room.config import (
    CLAUDE_HAIKU,
    CLAUDE_OPUS,
    CLAUDE_SONNET,
    GEMINI_3_FLASH,
    GEMINI_3_PRO,
    GLM_52,
    QWEN_MAX,
    QWEN_TURBO,
    validate_model_ids,
)
from scripts.war_room.phases import compute_borda_scores

# ---------------------------------------------------------------------------
# CJR-001: Named model ID constants + startup validation
# ---------------------------------------------------------------------------


class TestModelIdConstants:
    """Model IDs must be named constants, not inline strings."""

    def test_constants_exist_in_config_module(self) -> None:
        """Expose all eight model IDs as importable named constants.

        GIVEN the war_room config module
        WHEN the model ID constants are imported
        THEN each constant equals its canonical model ID string
        AND all eight expected models are present
        """
        assert CLAUDE_OPUS == "claude-opus-5"
        assert CLAUDE_SONNET == "claude-sonnet-5"
        assert GEMINI_3_PRO == "gemini-3-pro"
        assert GLM_52 == "glm-5.2"
        assert QWEN_TURBO == "qwen-turbo"
        assert GEMINI_3_FLASH == "gemini-3-flash"
        assert QWEN_MAX == "qwen-max"
        assert CLAUDE_HAIKU == "claude-haiku-4-5"

    def test_validate_model_ids_rejects_empty_string(self) -> None:
        """Reject an empty model ID with a ValueError.

        GIVEN a model ID mapping containing an empty string
        WHEN validate_model_ids inspects it
        THEN a ValueError is raised
        AND the message identifies the value as empty
        """
        with pytest.raises(ValueError, match="empty"):
            validate_model_ids({"MODEL_A": ""})

    def test_validate_model_ids_accepts_valid_ids(self) -> None:
        """Accept non-empty model IDs without raising.

        GIVEN a mapping of non-empty model ID strings
        WHEN validate_model_ids inspects it
        THEN no exception is raised
        AND the validator returns None on the success path
        """
        outcome = validate_model_ids({"CLAUDE_OPUS": "claude-opus-5", "GLM": "glm-5.2"})
        assert outcome is None

    def test_experts_uses_constants_not_inline_strings(self) -> None:
        """Reference config constants instead of inline model strings.

        GIVEN the experts.py source parsed into an AST
        WHEN its string literals are collected
        THEN no banned inline model ID literal appears
        AND model IDs are sourced from the config constants
        """
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
            "claude-opus-4-8",
            "claude-sonnet-4-6",
            "gemini-3-pro",
            "glm-5.2",
            "qwen-turbo",
            "gemini-3-flash",
            "qwen-max",
            "claude-haiku-4-5",
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
        """Propagate an unexpected error raised by the auth probe.

        GIVEN a version check that succeeds and an auth probe that
            raises RuntimeError
        WHEN verify_service runs
        THEN the RuntimeError propagates
        AND it is not swallowed as a normal issue
        """
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
        """Report an auth-probe timeout as a service issue.

        GIVEN a version check that succeeds and an auth probe that
            raises TimeoutExpired
        WHEN verify_service runs
        THEN the service is reported unavailable
        AND an auth-related issue is included
        """
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
        """Report a missing auth binary as a service issue.

        GIVEN a version check that succeeds and an auth probe that
            raises FileNotFoundError
        WHEN verify_service runs
        THEN the service is reported unavailable
        AND an auth-related issue is included
        """
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
        """Propagate a TypeError from a malformed service config.

        GIVEN a config whose new service entry has an unknown field
        WHEN the Delegator loads configurations
        THEN a TypeError propagates from the construction
        AND the malformed config is not silently swallowed
        """
        config_file = tmp_path / "config.json"
        # Valid JSON, valid "services" dict, but ServiceConfig(**{"bad": 1})
        # will raise TypeError for unknown field.
        config_file.write_text(
            json.dumps({"services": {"newsvc": {"bad_field": "value"}}})
        )

        with pytest.raises(TypeError):
            Delegator(config_dir=tmp_path)

    def test_json_decode_error_is_swallowed(self, tmp_path: Path) -> None:
        """Swallow a JSONDecodeError from a malformed config file.

        GIVEN a config file containing invalid JSON
        WHEN the Delegator loads configurations
        THEN no exception is raised
        AND the default services remain present
        """
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        # Must not raise — JSONDecodeError is expected to be swallowed
        delegator = Delegator(config_dir=tmp_path)
        # Default services should still be present
        assert "gemini" in delegator.services

    def test_os_error_is_swallowed(self, tmp_path: Path) -> None:
        """Swallow an OSError raised while reading the config.

        GIVEN a config read that raises OSError (permission denied)
        WHEN the Delegator loads configurations
        THEN no exception is raised
        AND the default services remain present
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"services": {}}))

        with patch("builtins.open", side_effect=OSError("permission denied")):
            delegator = Delegator(config_dir=tmp_path)
            assert "gemini" in delegator.services

    def test_incomplete_service_skipped_but_valid_sibling_loads(
        self, tmp_path: Path
    ) -> None:
        """Skip an incomplete service while loading its valid siblings.

        GIVEN a config with one incomplete service (missing required
            fields) and one fully-specified service
        WHEN the Delegator loads configurations
        THEN the incomplete service is skipped per-entry
        AND the valid sibling defined in the same config still loads

        Encodes the invariant that a single incomplete entry is dropped
        in isolation rather than aborting the whole config load. If this
        breaks, the loop reverts to all-or-nothing behavior and one bad
        entry silently drops every later service.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "services": {
                        "incomplete": {"name": "incomplete"},
                        "fullsvc": {
                            "name": "fullsvc",
                            "command": "fs",
                            "auth_method": "cli",
                        },
                    }
                }
            )
        )

        delegator = Delegator(config_dir=tmp_path)

        assert "incomplete" not in delegator.services
        assert "fullsvc" in delegator.services
        assert delegator.services["fullsvc"].command == "fs"
        assert "gemini" in delegator.services


# ---------------------------------------------------------------------------
# CJR-004: Borda score O(n²) refactor — output must be identical
# ---------------------------------------------------------------------------


class TestBordaScoresCharacterization:
    """compute_borda_scores output must be identical after O(n²) refactor."""

    def _original_borda(
        self, votes: dict[str, str], coa_labels: list[str]
    ) -> dict[str, int]:
        """Reproduce the original O(n³) Borda algorithm for comparison."""
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
        """Match the reference scores for a standard ballot.

        GIVEN a standard set of ranked ballots
        WHEN compute_borda_scores tallies them
        THEN the scores equal the original algorithm's output
        AND the optimized path agrees with the reference
        """
        labels = ["Alpha", "Beta", "Gamma"]
        votes = {
            "expert1": "1. Alpha is best\n2. Beta is second\n3. Gamma is third",
            "expert2": "1. Beta is top\n2. Gamma follows\n3. Alpha is last",
        }
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_label_absent_from_ballot(self) -> None:
        """Give an unmentioned label no additional score.

        GIVEN a ballot that never names a given label
        WHEN compute_borda_scores tallies the votes
        THEN that label gains zero score
        AND the result matches the reference algorithm
        """
        labels = ["Alpha", "Beta", "Zeta"]
        votes = {"expert1": "1. Alpha wins\n2. Beta second\n3. Delta not in list"}
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_rank_marker_far_from_label(self) -> None:
        """Ignore a label too far from its rank marker.

        GIVEN a label appearing more than 200 chars after the rank
            marker
        WHEN compute_borda_scores tallies the vote
        THEN that label gains zero score
        AND the result matches the reference algorithm
        """
        labels = ["Alpha"]
        # Put Alpha 300 chars after "1."
        padding = "x" * 250
        votes = {"expert1": f"1. {padding} Alpha is here"}
        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected

    def test_empty_votes(self) -> None:
        """Return all-zero scores for an empty ballot set.

        GIVEN an empty votes mapping
        WHEN compute_borda_scores tallies it
        THEN every label scores zero
        AND the result matches the reference algorithm
        """
        labels = ["Alpha", "Beta"]
        expected = self._original_borda({}, labels)
        assert compute_borda_scores({}, labels) == expected

    def test_large_n_produces_same_output(self) -> None:
        """Match the reference output at larger ballot sizes.

        GIVEN 20 labels across 5 ballots
        WHEN compute_borda_scores tallies them
        THEN the output equals the reference algorithm
        AND the O(n squared) path scales without diverging
        """
        labels = [f"COA_{i}" for i in range(20)]
        votes = {}
        for ballot_idx in range(5):
            lines = []
            for rank_idx, label in enumerate(labels):
                lines.append(f"{rank_idx + 1}. {label} is rank {rank_idx + 1}")
            votes[f"expert{ballot_idx}"] = "\n".join(lines)

        expected = self._original_borda(votes, labels)
        assert compute_borda_scores(votes, labels) == expected
