"""Tests for rollback review GitHub issue creation."""

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
