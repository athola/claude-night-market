"""Tests for rollback review GitHub issue creation."""

import subprocess
from unittest.mock import patch

from abstract.rollback_reviewer import RollbackReviewer


class TestIssueBodyGeneration:
    """Test GitHub issue body generation."""

    def test_should_generate_issue_body(self) -> None:
        """Given regression data, when body generated, then all fields present."""
        reviewer = RollbackReviewer()
        body = reviewer.generate_issue_body(
            skill_name="abstract:test-skill",
            baseline_gap=0.15,
            current_gap=0.35,
            improvement_diff="Added error handling for edge cases",
            rollback_command="git revert abc123",
        )
        assert "abstract:test-skill" in body
        assert "0.15" in body
        assert "0.35" in body
        assert "git revert abc123" in body
        assert "Added error handling" in body

    def test_should_generate_issue_title(self) -> None:
        """Given skill name, when title generated, then formatted correctly."""
        reviewer = RollbackReviewer()
        title = reviewer.generate_issue_title("abstract:test-skill")
        assert "abstract:test-skill" in title
        assert "regression" in title.lower()


class TestRollbackCommand:
    """Test rollback command generation."""

    def test_should_generate_revert_command(self) -> None:
        """Given a commit hash, when command generated, then valid git revert."""
        reviewer = RollbackReviewer()
        cmd = reviewer.generate_rollback_command("abc123def")
        assert "git revert" in cmd
        assert "abc123def" in cmd


class TestCreateGithubIssue:
    """Test GitHub issue creation via gh CLI."""

    ISSUE_KWARGS = {
        "skill_name": "abstract:test-skill",
        "baseline_gap": 0.15,
        "current_gap": 0.35,
        "improvement_diff": "Changed error handling",
        "rollback_command": "git revert abc123",
    }

    @patch("abstract.rollback_reviewer.subprocess.run")
    @patch("abstract.rollback_reviewer.shutil.which", return_value="/usr/bin/gh")
    def test_should_return_url_on_success(self, _mock_which, mock_run) -> None:
        """Given gh CLI available, when issue created, then return URL."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="https://github.com/org/repo/issues/42\n"
        )
        reviewer = RollbackReviewer()
        url = reviewer.create_github_issue(**self.ISSUE_KWARGS)
        assert url == "https://github.com/org/repo/issues/42"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/gh"
        assert "issue" in call_args
        assert "--label" in call_args

    @patch("abstract.rollback_reviewer.shutil.which", return_value=None)
    def test_should_return_none_when_gh_not_found(self, _mock_which) -> None:
        """Given gh CLI not installed, when issue created, then return None."""
        reviewer = RollbackReviewer()
        result = reviewer.create_github_issue(**self.ISSUE_KWARGS)
        assert result is None

    @patch("abstract.rollback_reviewer.subprocess.run")
    @patch("abstract.rollback_reviewer.shutil.which", return_value="/usr/bin/gh")
    def test_should_return_none_on_nonzero_exit(self, _mock_which, mock_run) -> None:
        """Given gh command fails, when issue created, then return None."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="auth required"
        )
        reviewer = RollbackReviewer()
        result = reviewer.create_github_issue(**self.ISSUE_KWARGS)
        assert result is None

    @patch("abstract.rollback_reviewer.subprocess.run", side_effect=FileNotFoundError)
    @patch("abstract.rollback_reviewer.shutil.which", return_value="/usr/bin/gh")
    def test_should_return_none_on_file_not_found(self, _mock_which, _mock_run) -> None:
        """Given gh binary disappears at runtime, when called, then return None."""
        reviewer = RollbackReviewer()
        result = reviewer.create_github_issue(**self.ISSUE_KWARGS)
        assert result is None

    @patch(
        "abstract.rollback_reviewer.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
    )
    @patch("abstract.rollback_reviewer.shutil.which", return_value="/usr/bin/gh")
    def test_should_return_none_on_timeout(self, _mock_which, _mock_run) -> None:
        """Given gh command hangs, when timeout reached, then return None."""
        reviewer = RollbackReviewer()
        result = reviewer.create_github_issue(**self.ISSUE_KWARGS)
        assert result is None
