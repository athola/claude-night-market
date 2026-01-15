"""Tests for quota tracking utilities."""

import time
from pathlib import Path

import pytest

from leyline import quota_tracker
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

    @pytest.mark.bdd
    def test_quota_status_healthy_when_usage_low(self, tmp_path: Path) -> None:
        """Scenario: Low usage results in healthy status.

        Given low request and token usage
        When checking quota status
        Then it should return healthy level with no warnings.
        """
        config = QuotaConfig(
            tokens_per_minute=1000,
            requests_per_minute=60,
            requests_per_day=1000,
        )
        tracker = QuotaTracker(
            service="test-healthy",
            config=config,
            storage_dir=tmp_path,
        )

        tracker.record_request(tokens=10)

        level, warnings = tracker.get_quota_status()

        assert level == "healthy"
        assert len(warnings) == 0

    @pytest.mark.bdd
    def test_quota_status_critical_at_high_usage(self, tmp_path: Path) -> None:
        """Scenario: Very high usage triggers critical status.

        Given usage above 95% threshold
        When checking quota status
        Then it should return critical level.
        """
        config = QuotaConfig(tokens_per_minute=100, requests_per_minute=10)
        tracker = QuotaTracker(
            service="test-critical",
            config=config,
            storage_dir=tmp_path,
        )

        # Record enough to exceed 95%
        tracker.record_request(tokens=96)

        level, warnings = tracker.get_quota_status()

        assert level == "critical"

    @pytest.mark.bdd
    def test_quota_status_warns_on_high_rpm(self, tmp_path: Path) -> None:
        """Scenario: High RPM usage triggers warning.

        Given requests per minute above 80%
        When checking quota status
        Then it should include RPM warning.
        """
        config = QuotaConfig(requests_per_minute=10, tokens_per_minute=10000)
        tracker = QuotaTracker(
            service="test-rpm",
            config=config,
            storage_dir=tmp_path,
        )

        # Record 9 requests to hit 90% RPM
        for _ in range(9):
            tracker.record_request(tokens=1)

        level, warnings = tracker.get_quota_status()

        assert level in ("warning", "critical")
        assert any("RPM" in w for w in warnings)

    @pytest.mark.bdd
    def test_quota_status_warns_on_high_daily_requests(self, tmp_path: Path) -> None:
        """Scenario: High daily request count triggers warning.

        Given daily requests above 80%
        When checking quota status
        Then it should include daily request warning.
        """
        config = QuotaConfig(
            requests_per_day=10,
            requests_per_minute=1000,
            tokens_per_minute=100000,
        )
        tracker = QuotaTracker(
            service="test-daily",
            config=config,
            storage_dir=tmp_path,
        )

        # Manually set daily usage high (with recent timestamp to avoid cleanup)
        tracker.usage.requests_today = 9
        tracker.usage.last_request_time = time.time()
        tracker._save_usage()

        level, warnings = tracker.get_quota_status()

        assert any("Daily" in w for w in warnings)

    @pytest.mark.bdd
    def test_can_handle_task_flags_daily_token_overage(self, tmp_path: Path) -> None:
        """Scenario: Task would exceed daily token limit.

        Given high daily token usage
        When checking if task can be handled
        Then it should flag daily limit exceeded.
        """
        config = QuotaConfig(tokens_per_day=100, tokens_per_minute=10000)
        tracker = QuotaTracker(
            service="test-daily-tokens",
            config=config,
            storage_dir=tmp_path,
        )

        # Set high usage with recent timestamp to avoid cleanup
        tracker.usage.tokens_today = 90
        tracker.usage.last_request_time = time.time()
        tracker._save_usage()

        can_proceed, issues = tracker.can_handle_task(20)

        assert can_proceed is False
        assert any("daily token limit" in issue for issue in issues)

    @pytest.mark.bdd
    def test_can_handle_task_flags_rpm_limit_reached(self, tmp_path: Path) -> None:
        """Scenario: RPM limit already reached.

        Given requests this minute at limit
        When checking if task can be handled
        Then it should flag RPM limit.
        """
        config = QuotaConfig(requests_per_minute=5)
        tracker = QuotaTracker(
            service="test-rpm-limit",
            config=config,
            storage_dir=tmp_path,
        )

        # Set limit reached with recent timestamp to avoid cleanup
        tracker.usage.requests_this_minute = 5
        tracker.usage.last_request_time = time.time()
        tracker._save_usage()

        can_proceed, issues = tracker.can_handle_task(10)

        assert can_proceed is False
        assert any("RPM limit" in issue for issue in issues)

    @pytest.mark.bdd
    def test_can_handle_task_flags_daily_request_limit(self, tmp_path: Path) -> None:
        """Scenario: Daily request limit reached.

        Given daily requests at limit
        When checking if task can be handled
        Then it should flag daily request limit.
        """
        config = QuotaConfig(requests_per_day=10)
        tracker = QuotaTracker(
            service="test-daily-limit",
            config=config,
            storage_dir=tmp_path,
        )

        # Set limit reached with recent timestamp to avoid cleanup
        tracker.usage.requests_today = 10
        tracker.usage.last_request_time = time.time()
        tracker._save_usage()

        can_proceed, issues = tracker.can_handle_task(10)

        assert can_proceed is False
        assert any("Daily request limit" in issue for issue in issues)

    @pytest.mark.bdd
    def test_get_current_usage_returns_stats(self, tmp_path: Path) -> None:
        """Scenario: Getting current usage after recording requests.

        Given recorded requests
        When getting current usage
        Then it should return accurate statistics.
        """
        tracker = QuotaTracker(service="test-usage", storage_dir=tmp_path)

        tracker.record_request(tokens=50)
        tracker.record_request(tokens=30)

        usage = tracker.get_current_usage()

        assert usage.requests_this_minute == 2  # noqa: PLR2004
        assert usage.tokens_this_minute == 80  # noqa: PLR2004

    @pytest.mark.bdd
    def test_estimate_file_tokens_nonexistent_file(self, tmp_path: Path) -> None:
        """Scenario: Estimating tokens for non-existent file.

        Given a file path that doesn't exist
        When estimating file tokens
        Then it should return 0.
        """
        tracker = QuotaTracker(service="test-estimate", storage_dir=tmp_path)

        result = tracker.estimate_file_tokens(tmp_path / "nonexistent.py")

        assert result == 0


@pytest.mark.unit
class TestQuotaTrackerStorage:
    """Feature: Quota tracker storage and persistence."""

    @pytest.mark.bdd
    def test_load_usage_handles_corrupt_json(self, tmp_path: Path) -> None:
        """Scenario: Loading corrupt usage file falls back to empty stats.

        Given a corrupt JSON usage file
        When creating tracker
        Then it should initialize with empty stats.
        """
        usage_file = tmp_path / "corrupt-service_usage.json"
        usage_file.write_text("not valid json {{{")

        tracker = QuotaTracker(service="corrupt-service", storage_dir=tmp_path)

        assert tracker.usage.requests_this_minute == 0
        assert tracker.usage.tokens_today == 0

    @pytest.mark.bdd
    def test_load_usage_handles_invalid_data_types(self, tmp_path: Path) -> None:
        """Scenario: Loading usage file with wrong types falls back to empty.

        Given a JSON file with invalid data types
        When creating tracker
        Then it should initialize with empty stats.
        """
        usage_file = tmp_path / "badtypes-service_usage.json"
        usage_file.write_text('{"requests_this_minute": "not-a-number"}')

        tracker = QuotaTracker(service="badtypes-service", storage_dir=tmp_path)

        assert tracker.usage.requests_this_minute == 0

    @pytest.mark.bdd
    def test_load_usage_from_existing_file(self, tmp_path: Path) -> None:
        """Scenario: Loading valid usage file restores stats.

        Given a valid usage JSON file
        When creating tracker
        Then it should restore the saved statistics.
        """
        usage_file = tmp_path / "existing-service_usage.json"
        usage_file.write_text(
            f'{{"requests_this_minute": 5, "requests_today": 10, '
            f'"tokens_this_minute": 100, "tokens_today": 500, '
            f'"last_request_time": {time.time()}}}'
        )

        tracker = QuotaTracker(service="existing-service", storage_dir=tmp_path)

        assert tracker.usage.requests_this_minute == 5  # noqa: PLR2004
        assert tracker.usage.requests_today == 10  # noqa: PLR2004


@pytest.mark.unit
class TestQuotaTrackerCLI:
    """Feature: Quota tracker CLI interface."""

    @pytest.mark.bdd
    def test_main_check_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Scenario: CLI check mode queries quota status.

        Given CLI invoked with --check flag
        When running main
        Then it should check quota status without error.
        """
        monkeypatch.setattr("sys.argv", ["quota_tracker", "test-cli", "--check"])
        # Override storage to use tmp_path
        original_init = QuotaTracker.__init__

        def patched_init(self, service, config=None, storage_dir=None):
            original_init(self, service, config, storage_dir=tmp_path)

        monkeypatch.setattr(QuotaTracker, "__init__", patched_init)

        # Should not raise
        quota_tracker.main()

    @pytest.mark.bdd
    def test_main_estimate_mode(self, tmp_path: Path, monkeypatch) -> None:
        """Scenario: CLI estimate mode calculates tokens for files.

        Given CLI invoked with --estimate and file paths
        When running main
        Then it should estimate tokens without error.
        """
        test_file = tmp_path / "sample.py"
        test_file.write_text("print('hello')")

        monkeypatch.setattr(
            "sys.argv",
            ["quota_tracker", "test-estimate-cli", "--estimate", str(test_file)],
        )

        original_init = QuotaTracker.__init__

        def patched_init(self, service, config=None, storage_dir=None):
            original_init(self, service, config, storage_dir=tmp_path)

        monkeypatch.setattr(QuotaTracker, "__init__", patched_init)

        # Should not raise
        quota_tracker.main()

    @pytest.mark.bdd
    def test_main_estimate_with_issues(self, tmp_path: Path, monkeypatch) -> None:
        """Scenario: CLI estimate shows issues when quota exceeded.

        Given CLI invoked with --estimate when quota would be exceeded
        When running main
        Then it should show issues without error.
        """
        test_file = tmp_path / "large.py"
        test_file.write_text("x" * 10000)

        monkeypatch.setattr(
            "sys.argv",
            ["quota_tracker", "test-issues-cli", "--estimate", str(test_file)],
        )

        # Create tracker with very low limits
        original_init = QuotaTracker.__init__

        def patched_init(self, service, config=None, storage_dir=None):
            low_config = QuotaConfig(tokens_per_minute=10, tokens_per_day=10)
            original_init(self, service, config=low_config, storage_dir=tmp_path)

        monkeypatch.setattr(QuotaTracker, "__init__", patched_init)

        # Should not raise
        quota_tracker.main()
