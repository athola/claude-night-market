"""Tests for quota tracking utilities."""

from pathlib import Path

import pytest

from leyline.quota_tracker import QuotaConfig, QuotaTracker


@pytest.mark.unit
class TestQuotaTracker:
    """Feature: Quota tracking for rate-limited services."""

    @pytest.mark.bdd
    def test_quota_status_warns_on_high_token_usage(self, tmp_path: Path) -> None:
        """Scenario: High token usage triggers warning level."""
        config = QuotaConfig(tokens_per_minute=100, requests_per_minute=60)
        tracker = QuotaTracker(
            service="test-service",
            config=config,
            storage_dir=tmp_path,
        )

        tracker.record_request(tokens=90)

        level, warnings = tracker.get_quota_status()

        assert level == "warning"
        assert any("TPM" in warning for warning in warnings)

    @pytest.mark.bdd
    def test_can_handle_task_flags_token_overage(self, tmp_path: Path) -> None:
        """Scenario: Task exceeds minute token budget."""
        config = QuotaConfig(tokens_per_minute=100, requests_per_minute=60)
        tracker = QuotaTracker(
            service="test-service",
            config=config,
            storage_dir=tmp_path,
        )

        tracker.record_request(tokens=90)

        can_proceed, issues = tracker.can_handle_task(20)

        assert can_proceed is False
        assert any("TPM limit" in issue for issue in issues)

    @pytest.mark.bdd
    def test_estimate_task_tokens_accounts_for_prompt(self, tmp_path: Path) -> None:
        """Scenario: Estimating tokens from prompt and file sizes."""
        file_path = tmp_path / "notes.txt"
        file_path.write_text("a" * 40)

        tracker = QuotaTracker(service="test-service", storage_dir=tmp_path)

        expected = 100 // 4
        expected += tracker.estimate_file_tokens(file_path)

        assert tracker.estimate_task_tokens([file_path], prompt_length=100) == expected
