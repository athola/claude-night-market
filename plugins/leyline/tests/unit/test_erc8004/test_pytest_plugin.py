"""Tests for the ERC-8004 pytest plugin.

Feature: Automatic content assertion capture during test runs

As a CI pipeline
I want pytest to automatically capture assertion results
So that they can be published to the Reputation Registry
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from leyline.erc8004 import pytest_plugin
from leyline.erc8004.pytest_plugin import _detect_level, _get_git_commit_hash
from leyline.erc8004.reputation import AssertionResult

# Sample test node IDs
README_NODEID = "tests/test_readme.py::ReadmeContent::test_exists"
QUALITY_NODEID = "tests/test_quality.py::test_no_fixmes"
HELPER_NODEID = "tests/test_util.py::test_helper"
SAMPLE_TIMESTAMP = 1700000000


@pytest.fixture(autouse=True)
def _clear_captured_assertions() -> None:
    """Clear captured assertions before and after each test."""
    pytest_plugin._captured_assertions.clear()
    yield  # type: ignore[misc]
    pytest_plugin._captured_assertions.clear()


@pytest.mark.unit
class TestLevelDetection:
    """Feature: Detect assertion levels from markers and class names."""

    @pytest.mark.bdd
    def test_detect_level_from_l1_marker(self) -> None:
        """Scenario: Test with @pytest.mark.l1 marker.

        Given a test item with an l1 marker
        When detecting the assertion level
        Then it should return "L1".
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.side_effect = (
            lambda name: MagicMock() if name == "l1" else None
        )

        assert _detect_level(item) == "L1"

    @pytest.mark.bdd
    def test_detect_level_from_l2_marker(self) -> None:
        """Scenario: Test with @pytest.mark.l2 marker.

        Given a test item with an l2 marker
        When detecting the assertion level
        Then it should return "L2".
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.side_effect = (
            lambda name: MagicMock() if name == "l2" else None
        )

        assert _detect_level(item) == "L2"

    @pytest.mark.bdd
    def test_detect_level_from_l3_marker(self) -> None:
        """Scenario: Test with @pytest.mark.l3 marker.

        Given a test item with an l3 marker
        When detecting the assertion level
        Then it should return "L3".
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.side_effect = (
            lambda name: MagicMock() if name == "l3" else None
        )

        assert _detect_level(item) == "L3"

    @pytest.mark.bdd
    def test_detect_level_from_content_class_name(self) -> None:
        """Scenario: Test class whose name ends with Content.

        Given a test item in a class named FooContent
        When detecting the assertion level
        Then it should return "L1" as the default for Content classes.
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.return_value = None
        item.cls = type("ReadmeContent", (), {})

        assert _detect_level(item) == "L1"

    @pytest.mark.bdd
    def test_detect_level_returns_none_for_regular_test(self) -> None:
        """Scenario: Regular test without markers or Content class.

        Given a test item with no assertion markers
        And not in a Content-suffixed class
        When detecting the assertion level
        Then it should return None.
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.return_value = None
        item.cls = None

        assert _detect_level(item) is None

    @pytest.mark.bdd
    def test_detect_level_returns_none_for_non_content_class(
        self,
    ) -> None:
        """Scenario: Test in a class that does not end with Content.

        Given a test item in a class named TestFoo
        And no assertion markers
        When detecting the assertion level
        Then it should return None.
        """
        item = MagicMock(name="test_item")
        item.get_closest_marker.return_value = None
        item.cls = type("TestFoo", (), {})

        assert _detect_level(item) is None


@pytest.mark.unit
class TestAssertionCapture:
    """Feature: Capture test results as assertion data."""

    @pytest.mark.bdd
    def test_logreport_captures_passing_test(self) -> None:
        """Scenario: Passing test in Content class is captured.

        Given a test report for a passing test in a Content class
        When pytest_runtest_logreport processes it
        Then an AssertionResult with status "pass" should be captured.
        """
        report = MagicMock(name="report")
        report.when = "call"
        report.passed = True
        report.failed = False
        report.nodeid = README_NODEID
        report.get_closest_marker.return_value = None
        report.cls = type("ReadmeContent", (), {})

        pytest_plugin.pytest_runtest_logreport(report)

        assert len(pytest_plugin._captured_assertions) == 1
        captured = pytest_plugin._captured_assertions[0]
        assert captured.status == "pass"
        assert captured.level == "L1"
        assert captured.test_name == README_NODEID

    @pytest.mark.bdd
    def test_logreport_captures_failing_test(self) -> None:
        """Scenario: Failing test with L2 marker is captured.

        Given a test report for a failing test with l2 marker
        When pytest_runtest_logreport processes it
        Then an AssertionResult with "fail" and "L2" is captured.
        """
        report = MagicMock(name="report")
        report.when = "call"
        report.passed = False
        report.failed = True
        report.nodeid = QUALITY_NODEID
        report.get_closest_marker.side_effect = (
            lambda name: MagicMock() if name == "l2" else None
        )
        report.cls = None

        pytest_plugin.pytest_runtest_logreport(report)

        assert len(pytest_plugin._captured_assertions) == 1
        captured = pytest_plugin._captured_assertions[0]
        assert captured.status == "fail"
        assert captured.level == "L2"

    @pytest.mark.bdd
    def test_logreport_skips_setup_teardown_phases(self) -> None:
        """Scenario: Setup and teardown phases are not captured.

        Given a test report from the "setup" phase
        When pytest_runtest_logreport processes it
        Then nothing should be captured.
        """
        report = MagicMock(name="report")
        report.when = "setup"

        pytest_plugin.pytest_runtest_logreport(report)

        assert len(pytest_plugin._captured_assertions) == 0

    @pytest.mark.bdd
    def test_logreport_skips_non_assertion_tests(self) -> None:
        """Scenario: Regular tests without markers are not captured.

        Given a test report for a non-assertion test
        When pytest_runtest_logreport processes it
        Then nothing should be captured.
        """
        report = MagicMock(name="report")
        report.when = "call"
        report.passed = True
        report.failed = False
        report.nodeid = HELPER_NODEID
        report.get_closest_marker.return_value = None
        report.cls = None

        pytest_plugin.pytest_runtest_logreport(report)

        assert len(pytest_plugin._captured_assertions) == 0


@pytest.mark.unit
class TestSessionFinish:
    """Feature: Publish captured assertions at session end."""

    @pytest.mark.bdd
    def test_session_finish_skips_when_no_assertions(self) -> None:
        """Scenario: No assertions were captured.

        Given no assertion results were captured during the session
        When the session finishes
        Then no publish attempt should be made.
        """
        session = MagicMock(name="session")

        # Should not raise even without ERC8004_PUBLISH set
        pytest_plugin.pytest_sessionfinish(session, exitstatus=0)

    @pytest.mark.bdd
    def test_session_finish_skips_when_publish_not_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Assertions captured but publishing not enabled.

        Given assertions were captured
        But ERC8004_PUBLISH is not set
        When the session finishes
        Then assertions should not be published on-chain.
        """
        pytest_plugin._captured_assertions.append(
            AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP)
        )

        monkeypatch.delenv("ERC8004_PUBLISH", raising=False)
        session = MagicMock(name="session")

        pytest_plugin.pytest_sessionfinish(session, exitstatus=0)

    @pytest.mark.bdd
    def test_session_finish_clears_assertions_after_publish(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Assertions are cleared after publish attempt.

        Given assertions were captured and ERC8004_PUBLISH is set
        When the session finishes
        Then captured assertions should be cleared.
        """
        pytest_plugin._captured_assertions.append(
            AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP)
        )

        monkeypatch.setenv("ERC8004_PUBLISH", "1")
        monkeypatch.setenv("ERC8004_PLUGIN_TOKEN_ID", "42")

        session = MagicMock(name="session")

        # ERC8004Client is imported lazily inside the function,
        # so we patch at the source module.
        with patch("leyline.erc8004.client.ERC8004Client") as mock_cls:
            mock_client = MagicMock(name="client")
            mock_cls.from_env.return_value = mock_client
            mock_client.reputation.publish_assertions.return_value = "0xtxhash"

            pytest_plugin.pytest_sessionfinish(session, exitstatus=0)

        assert len(pytest_plugin._captured_assertions) == 0


@pytest.mark.unit
class TestGitCommitHash:
    """Feature: Retrieve git commit hash for assertion records."""

    @pytest.mark.bdd
    def test_get_git_commit_hash_returns_hash(self) -> None:
        """Scenario: Git is available and returns a commit hash.

        Given git is installed and the working directory is a repo
        When getting the git commit hash
        Then it should return a non-empty string.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="abc1234\n")
            result = _get_git_commit_hash()

        assert result == "abc1234"

    @pytest.mark.bdd
    def test_get_git_commit_hash_returns_unknown_on_failure(
        self,
    ) -> None:
        """Scenario: Git is not available.

        Given git is not installed or the directory is not a repo
        When getting the git commit hash
        Then it should return "unknown".
        """
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _get_git_commit_hash()

        assert result == "unknown"
