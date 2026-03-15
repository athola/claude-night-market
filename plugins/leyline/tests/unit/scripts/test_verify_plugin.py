"""Tests for the verify_plugin CLI and trust assessment logic.

Feature: Plugin Behavioral Contract Verification

    As a plugin consumer
    I want to verify a plugin's trust history via ERC-8004
    So that I can make informed installation decisions
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from verify_plugin import (  # noqa: I001
    LevelScore,
    _choose_recommendation,
    _compute_level_scores,
    _format_human,
    build_parser,
    main,
    verify_plugin,
    verify_plugin_offline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_records(
    l1_pass: int = 0,
    l1_fail: int = 0,
    l2_pass: int = 0,
    l2_fail: int = 0,
    l3_pass: int = 0,
    l3_fail: int = 0,
) -> list[dict[str, object]]:
    """Build a list of assertion records with given pass/fail counts."""
    records: list[dict[str, object]] = []
    for _ in range(l1_pass):
        records.append({"level": "L1", "passed": True})
    for _ in range(l1_fail):
        records.append({"level": "L1", "passed": False})
    for _ in range(l2_pass):
        records.append({"level": "L2", "passed": True})
    for _ in range(l2_fail):
        records.append({"level": "L2", "passed": False})
    for _ in range(l3_pass):
        records.append({"level": "L3", "passed": True})
    for _ in range(l3_fail):
        records.append({"level": "L3", "passed": False})
    return records


# ---------------------------------------------------------------------------
# Level score computation
# ---------------------------------------------------------------------------


class TestComputeLevelScores:
    """Feature: Compute per-level pass rates from assertion records.

    As a verification system
    I want accurate pass-rate calculations per level
    So that trust assessments reflect actual contract history.
    """

    @pytest.mark.unit
    def test_all_passing_returns_100_percent(self) -> None:
        """Scenario: All assertions pass.

        Given 10 passing L1 assertions
        When computing level scores
        Then L1 rate is 1.0 and L2/L3 rates are 0.0.
        """
        records = _make_records(l1_pass=10)
        scores = _compute_level_scores(records)

        assert scores["L1"].rate == 1.0
        assert scores["L1"].total == 10  # noqa: PLR2004
        assert scores["L1"].passed == 10  # noqa: PLR2004
        assert scores["L2"].total == 0
        assert scores["L3"].total == 0

    @pytest.mark.unit
    def test_mixed_pass_fail(self) -> None:
        """Scenario: Some assertions fail.

        Given 8 passing and 2 failing L1 assertions
        When computing level scores
        Then L1 rate is 0.8.
        """
        records = _make_records(l1_pass=8, l1_fail=2)
        scores = _compute_level_scores(records)

        assert scores["L1"].rate == pytest.approx(0.8)
        assert scores["L1"].total == 10  # noqa: PLR2004
        assert scores["L1"].passed == 8  # noqa: PLR2004

    @pytest.mark.unit
    def test_multiple_levels(self) -> None:
        """Scenario: Records span multiple levels.

        Given assertions at L1, L2, and L3
        When computing level scores
        Then each level has independent pass rates.
        """
        records = _make_records(l1_pass=10, l2_pass=9, l2_fail=1, l3_pass=7, l3_fail=3)
        scores = _compute_level_scores(records)

        assert scores["L1"].rate == 1.0
        assert scores["L2"].rate == pytest.approx(0.9)
        assert scores["L3"].rate == pytest.approx(0.7)

    @pytest.mark.unit
    def test_empty_records_returns_zero_totals(self) -> None:
        """Scenario: No assertion history.

        Given an empty record list
        When computing level scores
        Then all levels have 0 total and 0.0 rate.
        """
        scores = _compute_level_scores([])

        for lvl in ("L1", "L2", "L3"):
            assert scores[lvl].total == 0
            assert scores[lvl].rate == 0.0


# ---------------------------------------------------------------------------
# Recommendation logic
# ---------------------------------------------------------------------------


class TestChooseRecommendation:
    """Feature: Derive trust recommendation from pass rates.

    As a plugin consumer
    I want a clear trusted/caution/untrusted label
    So that I can quickly assess plugin safety.
    """

    @pytest.mark.unit
    def test_high_score_returns_trusted(self) -> None:
        """Scenario: Pass rate exceeds threshold.

        Given L1 pass rate of 0.95 and threshold of 0.8
        When choosing recommendation
        Then recommendation is "trusted".
        """
        scores = {"L1": LevelScore(level="L1", total=20, passed=19, rate=0.95)}
        assert _choose_recommendation(scores, "L1", 0.8) == "trusted"

    @pytest.mark.unit
    def test_moderate_score_returns_caution(self) -> None:
        """Scenario: Pass rate is below threshold but above 70% of it.

        Given L1 pass rate of 0.65 and threshold of 0.8
        When choosing recommendation
        Then recommendation is "caution" (0.65 >= 0.8*0.7=0.56).
        """
        scores = {"L1": LevelScore(level="L1", total=20, passed=13, rate=0.65)}
        assert _choose_recommendation(scores, "L1", 0.8) == "caution"

    @pytest.mark.unit
    def test_low_score_returns_untrusted(self) -> None:
        """Scenario: Pass rate far below threshold.

        Given L1 pass rate of 0.3 and threshold of 0.8
        When choosing recommendation
        Then recommendation is "untrusted" (0.3 < 0.8*0.7=0.56).
        """
        scores = {"L1": LevelScore(level="L1", total=10, passed=3, rate=0.3)}
        assert _choose_recommendation(scores, "L1", 0.8) == "untrusted"

    @pytest.mark.unit
    def test_zero_records_returns_untrusted(self) -> None:
        """Scenario: Level has no records.

        Given L2 has 0 records
        When choosing recommendation for L2
        Then recommendation is "untrusted".
        """
        scores = {"L2": LevelScore(level="L2", total=0, passed=0, rate=0.0)}
        assert _choose_recommendation(scores, "L2", 0.8) == "untrusted"

    @pytest.mark.unit
    def test_missing_level_returns_untrusted(self) -> None:
        """Scenario: Requested level not present in scores.

        Given scores only contain L1
        When checking L3
        Then recommendation is "untrusted".
        """
        scores = {"L1": LevelScore(level="L1", total=10, passed=10, rate=1.0)}
        assert _choose_recommendation(scores, "L3", 0.8) == "untrusted"

    @pytest.mark.unit
    def test_exact_threshold_returns_trusted(self) -> None:
        """Scenario: Pass rate exactly matches threshold.

        Given L1 pass rate of 0.8 and threshold of 0.8
        When choosing recommendation
        Then recommendation is "trusted".
        """
        scores = {"L1": LevelScore(level="L1", total=10, passed=8, rate=0.8)}
        assert _choose_recommendation(scores, "L1", 0.8) == "trusted"


# ---------------------------------------------------------------------------
# Offline verification (no RPC)
# ---------------------------------------------------------------------------


class TestVerifyPluginOffline:
    """Feature: Offline trust verification from pre-fetched records.

    As a developer running tests
    I want to verify trust without an RPC connection
    So that verification logic is testable in isolation.
    """

    @pytest.mark.unit
    def test_all_passing_plugin_is_trusted(self) -> None:
        """Scenario: Plugin with all assertions passing.

        Given 20 passing L1 assertions
        When verifying offline with min_score 0.8
        Then result is trusted and meets threshold.
        """
        records = _make_records(l1_pass=20)
        result = verify_plugin_offline("good-plugin", records, level="L1")

        assert result["plugin_name"] == "good-plugin"
        assert result["recommendation"] == "trusted"
        assert result["meets_threshold"] is True
        assert result["error"] is None

    @pytest.mark.unit
    def test_some_failures_returns_caution(self) -> None:
        """Scenario: Plugin with some failures.

        Given 6 passing and 4 failing L1 assertions
        When verifying offline with min_score 0.8
        Then recommendation is "caution" (0.6 >= 0.56).
        """
        records = _make_records(l1_pass=6, l1_fail=4)
        result = verify_plugin_offline("risky-plugin", records, level="L1")

        assert result["recommendation"] == "caution"
        assert result["meets_threshold"] is False

    @pytest.mark.unit
    def test_no_history_returns_untrusted(self) -> None:
        """Scenario: Plugin with no assertion history.

        Given empty assertion records
        When verifying offline
        Then recommendation is "untrusted" with error message.
        """
        result = verify_plugin_offline("unknown-plugin", [])

        assert result["recommendation"] == "untrusted"
        assert result["meets_threshold"] is False
        assert "No assertion history" in result["error"]

    @pytest.mark.unit
    def test_invalid_level_returns_error(self) -> None:
        """Scenario: Invalid assertion level specified.

        Given any records
        When verifying with level "L9"
        Then result has error and recommendation "unknown".
        """
        records = _make_records(l1_pass=10)
        result = verify_plugin_offline("test", records, level="L9")

        assert result["recommendation"] == "unknown"
        assert "Invalid level" in result["error"]

    @pytest.mark.unit
    def test_high_min_score_threshold(self) -> None:
        """Scenario: Strict threshold makes good plugin untrusted.

        Given 85% L1 pass rate
        When verifying with min_score 0.95
        Then recommendation is "caution" (0.85 >= 0.95*0.7=0.665).
        """
        records = _make_records(l1_pass=17, l1_fail=3)
        result = verify_plugin_offline(
            "decent-plugin", records, level="L1", min_score=0.95
        )

        assert result["recommendation"] == "caution"
        assert result["meets_threshold"] is False

    @pytest.mark.unit
    def test_l3_verification(self) -> None:
        """Scenario: Verify at L3 level.

        Given records at all three levels
        When verifying at L3 with min_score 0.9
        Then assessment is based on L3 pass rate.
        """
        records = _make_records(l1_pass=10, l2_pass=10, l3_pass=19, l3_fail=1)
        result = verify_plugin_offline(
            "advanced-plugin", records, level="L3", min_score=0.9
        )

        assert result["recommendation"] == "trusted"
        assert result["meets_threshold"] is True
        # Confirm L3 score is 95%
        l3_score = [s for s in result["level_scores"] if s["level"] == "L3"][0]
        assert l3_score["rate"] == pytest.approx(0.95)

    @pytest.mark.unit
    def test_history_truncated_to_20(self) -> None:
        """Scenario: Large history is truncated in output.

        Given 50 assertion records
        When verifying offline
        Then assertion_history contains at most 20 records.
        """
        records = _make_records(l1_pass=50)
        result = verify_plugin_offline("big-plugin", records, level="L1")

        assert len(result["assertion_history"]) <= 20  # noqa: PLR2004


# ---------------------------------------------------------------------------
# Online verification (mocked RPC)
# ---------------------------------------------------------------------------


class TestVerifyPluginOnline:
    """Feature: Online trust verification via ERC-8004 registry.

    As a plugin consumer
    I want to query on-chain reputation data
    So that I get real-time trust assessments.
    """

    @pytest.mark.unit
    def test_erc8004_unavailable_returns_unknown(self) -> None:
        """Scenario: web3 not installed.

        Given the erc8004 package cannot be imported
        When calling verify_plugin
        Then result has recommendation "unknown" and helpful error.
        """
        with patch("verify_plugin._try_import_erc8004", return_value=None):
            result = verify_plugin("some-plugin")

        assert result["recommendation"] == "unknown"
        assert "not available" in result["error"]

    @pytest.mark.unit
    def test_registry_query_succeeds(self) -> None:
        """Scenario: Successful registry query.

        Given a mock ERC-8004 client returning passing records
        When calling verify_plugin
        Then result reflects the on-chain data.
        """
        mock_erc8004 = MagicMock(name="erc8004_module")
        mock_client = MagicMock(name="ERC8004Client")
        mock_erc8004.ERC8004Client.return_value = mock_client
        mock_client.reputation.get_assertion_history.return_value = _make_records(
            l1_pass=10
        )

        with patch(
            "verify_plugin._try_import_erc8004",
            return_value=mock_erc8004,
        ):
            result = verify_plugin("good-plugin", level="L1", min_score=0.8)

        assert result["recommendation"] == "trusted"
        assert result["meets_threshold"] is True

    @pytest.mark.unit
    def test_registry_query_exception(self) -> None:
        """Scenario: Registry query raises an exception.

        Given a mock client that raises ConnectionError
        When calling verify_plugin
        Then result has recommendation "unknown" with error detail.
        """
        mock_erc8004 = MagicMock(name="erc8004_module")
        mock_erc8004.ERC8004Client.side_effect = ConnectionError("RPC down")

        with patch(
            "verify_plugin._try_import_erc8004",
            return_value=mock_erc8004,
        ):
            result = verify_plugin("broken-plugin")

        assert result["recommendation"] == "unknown"
        assert "Failed to query" in result["error"]

    @pytest.mark.unit
    def test_empty_registry_returns_untrusted(self) -> None:
        """Scenario: Plugin has no on-chain history.

        Given a mock client returning empty records
        When calling verify_plugin
        Then result is untrusted with no-history error.
        """
        mock_erc8004 = MagicMock(name="erc8004_module")
        mock_client = MagicMock(name="ERC8004Client")
        mock_erc8004.ERC8004Client.return_value = mock_client
        mock_client.reputation.get_assertion_history.return_value = []

        with patch(
            "verify_plugin._try_import_erc8004",
            return_value=mock_erc8004,
        ):
            result = verify_plugin("new-plugin")

        assert result["recommendation"] == "untrusted"
        assert "No assertion history" in result["error"]

    @pytest.mark.unit
    def test_invalid_level_rejected(self) -> None:
        """Scenario: Invalid level is rejected before any RPC call.

        Given level "INVALID"
        When calling verify_plugin
        Then result has error without touching the registry.
        """
        result = verify_plugin("any-plugin", level="INVALID")

        assert result["recommendation"] == "unknown"
        assert "Invalid level" in result["error"]


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestCLIParsing:
    """Feature: Command-line interface for verify_plugin.

    As a developer
    I want a CLI with clear arguments
    So that I can verify plugins from the terminal.
    """

    @pytest.mark.unit
    def test_minimal_args(self) -> None:
        """Scenario: Only plugin name provided.

        Given just a plugin name argument
        When parsing CLI args
        Then defaults apply: level=L1, min_score=0.8.
        """
        parser = build_parser()
        args = parser.parse_args(["my-plugin"])

        assert args.plugin_name == "my-plugin"
        assert args.level == "L1"
        assert args.min_score == 0.8  # noqa: PLR2004
        assert args.json_output is False

    @pytest.mark.unit
    def test_all_args(self) -> None:
        """Scenario: All arguments provided.

        Given plugin name, level, min-score, and json flag
        When parsing CLI args
        Then all values are captured correctly.
        """
        parser = build_parser()
        args = parser.parse_args(
            ["sanctum", "--level", "L3", "--min-score", "0.9", "--json"]
        )

        assert args.plugin_name == "sanctum"
        assert args.level == "L3"
        assert args.min_score == 0.9  # noqa: PLR2004
        assert args.json_output is True

    @pytest.mark.unit
    def test_invalid_level_rejected_by_parser(self) -> None:
        """Scenario: Invalid level caught by argparse.

        Given level "L9"
        When parsing CLI args
        Then argparse raises SystemExit.
        """
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["plugin", "--level", "L9"])


# ---------------------------------------------------------------------------
# CLI main() exit codes
# ---------------------------------------------------------------------------


class TestCLIMain:
    """Feature: CLI exit codes reflect trust status.

    As a CI pipeline
    I want non-zero exit for untrusted plugins
    So that I can gate deployments on trust.
    """

    @pytest.mark.unit
    def test_trusted_returns_zero(self) -> None:
        """Scenario: Trusted plugin returns exit code 0.

        Given verify_plugin returns trusted
        When running main()
        Then exit code is 0.
        """
        with patch("verify_plugin.verify_plugin") as mock_verify:
            mock_verify.return_value = {
                "plugin_name": "good",
                "recommendation": "trusted",
                "meets_threshold": True,
                "level_scores": [],
                "assertion_history": [],
                "error": None,
            }
            code = main(["good"])

        assert code == 0

    @pytest.mark.unit
    def test_untrusted_returns_one(self) -> None:
        """Scenario: Untrusted plugin returns exit code 1.

        Given verify_plugin returns untrusted
        When running main()
        Then exit code is 1.
        """
        with patch("verify_plugin.verify_plugin") as mock_verify:
            mock_verify.return_value = {
                "plugin_name": "bad",
                "recommendation": "untrusted",
                "meets_threshold": False,
                "level_scores": [],
                "assertion_history": [],
                "error": None,
            }
            code = main(["bad"])

        assert code == 1

    @pytest.mark.unit
    def test_error_returns_two(self) -> None:
        """Scenario: Error condition returns exit code 2.

        Given verify_plugin returns unknown with error
        When running main()
        Then exit code is 2.
        """
        with patch("verify_plugin.verify_plugin") as mock_verify:
            mock_verify.return_value = {
                "plugin_name": "broken",
                "recommendation": "unknown",
                "meets_threshold": False,
                "level_scores": [],
                "assertion_history": [],
                "error": "SDK not available",
            }
            code = main(["broken"])

        assert code == 2  # noqa: PLR2004

    @pytest.mark.unit
    def test_json_output_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Scenario: JSON flag produces valid JSON output.

        Given --json flag
        When running main()
        Then stdout contains valid JSON.
        """
        with patch("verify_plugin.verify_plugin") as mock_verify:
            mock_verify.return_value = {
                "plugin_name": "test",
                "recommendation": "trusted",
                "meets_threshold": True,
                "level_scores": [],
                "assertion_history": [],
                "error": None,
            }
            main(["test", "--json"])

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["plugin_name"] == "test"


# ---------------------------------------------------------------------------
# Human-readable formatting
# ---------------------------------------------------------------------------


class TestFormatHuman:
    """Feature: Human-readable output formatting.

    As a developer reading terminal output
    I want clear, readable trust summaries
    So that I understand the assessment at a glance.
    """

    @pytest.mark.unit
    def test_format_includes_plugin_name(self) -> None:
        """Scenario: Output contains plugin name.

        Given a trust assessment for "my-plugin"
        When formatting for human output
        Then the plugin name appears in the output.
        """
        result = {
            "plugin_name": "my-plugin",
            "recommendation": "trusted",
            "meets_threshold": True,
            "level_scores": [],
            "assertion_history": [],
            "error": None,
        }
        output = _format_human(result)
        assert "my-plugin" in output
        assert "trusted" in output

    @pytest.mark.unit
    def test_format_includes_level_scores(self) -> None:
        """Scenario: Output contains level-by-level scores.

        Given scores for L1 and L2
        When formatting for human output
        Then both level pass rates appear.
        """
        result = {
            "plugin_name": "test",
            "recommendation": "trusted",
            "meets_threshold": True,
            "level_scores": [
                {"level": "L1", "total": 10, "passed": 10, "rate": 1.0},
                {"level": "L2", "total": 5, "passed": 4, "rate": 0.8},
            ],
            "assertion_history": [],
            "error": None,
        }
        output = _format_human(result)
        assert "L1" in output
        assert "100.0%" in output
        assert "L2" in output
        assert "80.0%" in output

    @pytest.mark.unit
    def test_format_includes_error_note(self) -> None:
        """Scenario: Error message shown as note.

        Given an assessment with error
        When formatting for human output
        Then the error appears as a Note.
        """
        result = {
            "plugin_name": "broken",
            "recommendation": "unknown",
            "meets_threshold": False,
            "level_scores": [],
            "assertion_history": [],
            "error": "SDK not available",
        }
        output = _format_human(result)
        assert "Note:" in output
        assert "SDK not available" in output
