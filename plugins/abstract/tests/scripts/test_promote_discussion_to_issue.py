"""Tests for promote_discussion_to_issue.py.

Part of Issue #69 Phase 6c: Voting-based promotion to Issues
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from promote_discussion_to_issue import (
    DiscussionItem,
    PromotedRecord,
    PromotionConfig,
    fetch_learnings_discussions,
    format_issue_body,
    promote_discussion,
    run_promotion,
)


class TestPromotionConfig:
    """Feature: Load promotion configuration

    As a collective intelligence system
    I want to configure promotion thresholds
    So that only sufficiently-voted items become Issues
    """

    @pytest.mark.unit
    def test_default_threshold_is_three(self) -> None:
        """Scenario: Default promotion threshold
        Given no config file exists
        When I load the config
        Then the threshold is 3 fire reactions
        """
        config = PromotionConfig()
        assert config.promotion_threshold == 3
        assert config.promotion_emoji == "\U0001f525"

    @pytest.mark.unit
    def test_loads_custom_threshold(self, tmp_path: Path) -> None:
        """Scenario: Custom threshold from config
        Given a config.json with promotion_threshold=5
        When I load the config
        Then the threshold is 5
        """
        config_dir = tmp_path / "discussions"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text(json.dumps({"promotion_threshold": 5}))

        with patch(
            "promote_discussion_to_issue.get_config_dir",
            return_value=config_dir,
        ):
            config = PromotionConfig.load()

        assert config.promotion_threshold == 5


class TestPromotedRecord:
    """Feature: Track promoted discussions to avoid duplicates

    As a collective intelligence system
    I want to track which discussions have been promoted to Issues
    So that I don't create duplicate Issues
    """

    @pytest.mark.unit
    def test_empty_record_has_no_promotions(self) -> None:
        """Scenario: New record has no promotions
        Given a fresh PromotedRecord
        When I check any discussion ID
        Then it reports as not promoted
        """
        record = PromotedRecord()
        assert not record.is_promoted("D_abc123")

    @pytest.mark.unit
    def test_tracks_promoted_discussions(self) -> None:
        """Scenario: Track a promoted discussion
        Given a PromotedRecord with a recorded promotion
        When I check that discussion ID
        Then it reports as already promoted
        """
        record = PromotedRecord(promoted={"D_abc123": "https://github.com/issues/1"})
        assert record.is_promoted("D_abc123")
        assert not record.is_promoted("D_xyz789")

    @pytest.mark.unit
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Scenario: Save and reload promoted record
        Given a PromotedRecord with data
        When I save and reload it
        Then the data is preserved
        """
        config_dir = tmp_path / "discussions"
        config_dir.mkdir(parents=True)

        record = PromotedRecord(promoted={"D_abc": "https://github.com/issues/1"})

        with patch(
            "promote_discussion_to_issue.get_config_dir",
            return_value=config_dir,
        ):
            record.save()
            loaded = PromotedRecord.load()

        assert loaded.promoted == record.promoted


class TestFetchDiscussions:
    """Feature: Fetch discussions with reaction counts

    As a collective intelligence system
    I want to query GitHub Discussions for reaction counts
    So that I can identify items meeting the promotion threshold
    """

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.run_gh_graphql")
    def test_parses_discussion_with_reactions(self, mock_graphql: MagicMock) -> None:
        """Scenario: Parse discussion with fire reactions
        Given a Discussions API response with reaction data
        When I fetch learnings discussions
        Then DiscussionItems are returned with correct reaction counts
        """
        mock_graphql.return_value = {
            "data": {
                "repository": {
                    "discussions": {
                        "nodes": [
                            {
                                "id": "D_abc123",
                                "title": "[Learning] 2026-02-21",
                                "url": "https://github.com/discussions/42",
                                "body": "## Summary\nTest learning",
                                "reactions": {"totalCount": 5},
                            }
                        ]
                    }
                }
            }
        }

        items = fetch_learnings_discussions()
        assert len(items) == 1
        assert items[0].discussion_id == "D_abc123"
        assert items[0].title == "[Learning] 2026-02-21"
        assert items[0].reaction_count == 5

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.run_gh_graphql")
    def test_returns_empty_on_api_failure(self, mock_graphql: MagicMock) -> None:
        """Scenario: Handle API failure gracefully
        Given the gh API call fails
        When I fetch discussions
        Then an empty list is returned
        """
        mock_graphql.side_effect = RuntimeError("API error")
        items = fetch_learnings_discussions()
        assert items == []


class TestFormatIssueBody:
    """Feature: Format a promoted Issue body

    As a collective intelligence system
    I want to format promoted discussion content as an Issue
    So that the team can triage and act on it
    """

    @pytest.mark.unit
    def test_includes_discussion_link(self) -> None:
        """Scenario: Include link to original discussion
        Given a DiscussionItem with a URL
        When I format the issue body
        Then the discussion URL is linked
        """
        item = DiscussionItem(
            discussion_id="D_abc",
            title="[Learning] 2026-02-21",
            url="https://github.com/discussions/42",
            body="Test body",
            reaction_count=5,
        )
        body = format_issue_body(item)
        assert "https://github.com/discussions/42" in body
        assert "5" in body

    @pytest.mark.unit
    def test_includes_vote_count(self) -> None:
        """Scenario: Include vote count in issue body
        Given a DiscussionItem with 7 reactions
        When I format the issue body
        Then the reaction count is shown
        """
        item = DiscussionItem(
            discussion_id="D_abc",
            title="Test",
            url="https://example.com",
            body="Body",
            reaction_count=7,
        )
        body = format_issue_body(item)
        assert "7" in body


class TestPromoteDiscussion:
    """Feature: Promote a single discussion to an Issue

    As a collective intelligence system
    I want to create a GitHub Issue from a highly-voted Discussion
    So that it enters the team's triage workflow
    """

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.run_gh_graphql")
    def test_creates_issue_with_correct_title(self, mock_graphql: MagicMock) -> None:
        """Scenario: Create issue with prefixed title
        Given a DiscussionItem meeting the threshold
        When I promote it
        Then an Issue is created with [Community Learning] prefix
        """
        mock_graphql.return_value = {
            "data": {"createIssue": {"issue": {"url": "https://github.com/issues/99"}}}
        }

        item = DiscussionItem(
            discussion_id="D_abc",
            title="[Learning] 2026-02-21",
            url="https://github.com/discussions/42",
            body="Test body",
            reaction_count=5,
        )
        url = promote_discussion("R_repo123", item)
        assert url == "https://github.com/issues/99"

        # Verify the mutation was called with correct title
        call_args = mock_graphql.call_args
        kw_vars = call_args[1].get("variables", {})
        positional = call_args[0][1] if len(call_args[0]) > 1 else {}
        variables = kw_vars or positional
        assert "[Community Learning]" in variables.get("title", "")


class TestRunPromotion:
    """Feature: End-to-end promotion workflow

    As a collective intelligence system
    I want to scan discussions and promote qualifying items
    So that high-impact community learnings become actionable Issues
    """

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.promote_discussion")
    @patch("promote_discussion_to_issue.get_repo_node_id")
    @patch("promote_discussion_to_issue.fetch_learnings_discussions")
    def test_promotes_items_above_threshold(
        self,
        mock_fetch: MagicMock,
        mock_repo_id: MagicMock,
        mock_promote: MagicMock,
    ) -> None:
        """Scenario: Promote discussions above threshold
        Given discussions with 5 and 1 reactions (threshold=3)
        When I run promotion
        Then only the 5-reaction discussion is promoted
        """
        mock_fetch.return_value = [
            DiscussionItem("D_high", "High votes", "url1", "body1", 5),
            DiscussionItem("D_low", "Low votes", "url2", "body2", 1),
        ]
        mock_repo_id.return_value = "R_test"
        mock_promote.return_value = "https://github.com/issues/99"

        record = PromotedRecord()
        record.save = MagicMock()

        with (
            patch(
                "promote_discussion_to_issue.PromotionConfig.load",
                return_value=PromotionConfig(promotion_threshold=3),
            ),
            patch(
                "promote_discussion_to_issue.PromotedRecord.load",
                return_value=record,
            ),
        ):
            results = run_promotion()

        assert len(results) == 1
        assert "issues/99" in results[0]
        mock_promote.assert_called_once()

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.fetch_learnings_discussions")
    def test_skips_already_promoted(self, mock_fetch: MagicMock) -> None:
        """Scenario: Skip already-promoted discussions
        Given a discussion that was already promoted
        When I run promotion
        Then it is skipped even if above threshold
        """
        mock_fetch.return_value = [
            DiscussionItem("D_already", "Already done", "url1", "b", 10),
        ]

        record = PromotedRecord(promoted={"D_already": "https://github.com/issues/1"})
        record.save = MagicMock()

        with (
            patch(
                "promote_discussion_to_issue.PromotionConfig.load",
                return_value=PromotionConfig(),
            ),
            patch(
                "promote_discussion_to_issue.PromotedRecord.load",
                return_value=record,
            ),
        ):
            results = run_promotion()

        assert len(results) == 0

    @pytest.mark.unit
    @patch("promote_discussion_to_issue.fetch_learnings_discussions")
    def test_handles_no_discussions(self, mock_fetch: MagicMock) -> None:
        """Scenario: No discussions to check
        Given the Discussions query returns empty
        When I run promotion
        Then an empty result list is returned
        """
        mock_fetch.return_value = []

        with (
            patch(
                "promote_discussion_to_issue.PromotionConfig.load",
                return_value=PromotionConfig(),
            ),
            patch(
                "promote_discussion_to_issue.PromotedRecord.load",
                return_value=PromotedRecord(),
            ),
        ):
            results = run_promotion()

        assert results == []


# ---------------------------------------------------------------------------
# Error paths at the gh and config-file boundaries
# ---------------------------------------------------------------------------

import promote_discussion_to_issue as promote_module  # noqa: E402 - path set above


def _gh_error(message: str) -> Exception:
    """A GhCommandError as leyline.git_platform raises it."""
    return promote_module.GhCommandError(message, cmd=["gh", "api", "graphql"])


class TestConfigFileErrors:
    """Unreadable config files fall back to defaults instead of crashing."""

    @pytest.mark.unit
    def test_corrupt_config_falls_back_to_defaults_and_warns(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A config.json that is not JSON yields the defaults and a warning."""
        (tmp_path / "config.json").write_text("{not json")
        with patch("promote_discussion_to_issue.get_config_dir", return_value=tmp_path):
            config = PromotionConfig.load()
        assert config == PromotionConfig()
        assert "Could not load config" in capsys.readouterr().err

    @pytest.mark.unit
    def test_corrupt_promoted_record_loads_empty(self, tmp_path: Path) -> None:
        """A promoted.json that is not JSON yields an empty record."""
        (tmp_path / "promoted.json").write_text("{not json")
        with patch("promote_discussion_to_issue.get_config_dir", return_value=tmp_path):
            record = PromotedRecord.load()
        assert record.promoted == {}


class TestGhBoundary:
    """gh failures surface as RuntimeError, the type callers handle."""

    @pytest.mark.unit
    def test_gh_failure_is_reraised_as_runtime_error(self) -> None:
        """GhCommandError from leyline becomes RuntimeError with its message."""
        with patch(
            "promote_discussion_to_issue.gh_graphql",
            side_effect=_gh_error("HTTP 502"),
        ):
            with pytest.raises(RuntimeError, match="HTTP 502"):
                promote_module.run_gh_graphql("query { x }")

    @pytest.mark.unit
    def test_repo_node_id_is_read_from_the_response(self) -> None:
        """get_repo_node_id returns data.repository.id as a string."""
        with patch(
            "promote_discussion_to_issue.gh_graphql",
            return_value={"data": {"repository": {"id": "R_kgDO"}}},
        ):
            assert promote_module.get_repo_node_id() == "R_kgDO"

    @pytest.mark.unit
    def test_long_body_is_truncated_with_a_notice(self) -> None:
        """A body over BODY_PREVIEW_LIMIT is cut and marked as truncated."""
        limit = promote_module.BODY_PREVIEW_LIMIT
        item = DiscussionItem("D_1", "t", "u", "x" * (limit + 10), 4)
        body = format_issue_body(item)
        assert "x" * limit in body
        assert "x" * (limit + 1) not in body
        assert "Content truncated" in body

    @pytest.mark.unit
    def test_one_failed_promotion_does_not_stop_the_rest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An issue-creation failure is warned about and the loop continues."""
        discussions = {
            "data": {
                "repository": {
                    "discussions": {
                        "nodes": [
                            {
                                "id": f"D_{n}",
                                "title": f"T{n}",
                                "url": f"https://x/{n}",
                                "body": "b",
                                "reactions": {"totalCount": 5},
                            }
                            for n in (1, 2)
                        ]
                    }
                }
            }
        }
        created = {"data": {"createIssue": {"issue": {"url": "https://x/issues/9"}}}}

        def fake_gh(query: str, variables: dict | None = None) -> dict:
            if "createIssue" in query:
                if variables and variables["title"].endswith("T1"):
                    raise _gh_error("rate limited")
                return created
            if "discussions" in query:
                return discussions
            return {"data": {"repository": {"id": "R_1"}}}

        with (
            patch("promote_discussion_to_issue.gh_graphql", side_effect=fake_gh),
            patch("promote_discussion_to_issue.get_config_dir", return_value=tmp_path),
        ):
            urls = run_promotion()

        assert urls == ["https://x/issues/9"]
        assert "Could not promote 'T1'" in capsys.readouterr().err
        saved = json.loads((tmp_path / "promoted.json").read_text())
        assert saved == {"promoted": {"D_2": "https://x/issues/9"}}


class TestMain:
    """main never fails the session: every error exits 0 with a warning."""

    @pytest.mark.unit
    def test_prints_each_promoted_url(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch(
            "promote_discussion_to_issue.run_promotion",
            return_value=["https://x/issues/1"],
        ):
            promote_module.main()
        out = capsys.readouterr().out
        assert "Promoted 1 discussion(s)" in out
        assert "https://x/issues/1" in out

    @pytest.mark.unit
    def test_reports_when_nothing_was_promoted(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("promote_discussion_to_issue.run_promotion", return_value=[]):
            promote_module.main()
        assert "No discussions promoted." in capsys.readouterr().out

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("error", "message"),
        [
            (RuntimeError("boom"), "Promotion failed: boom"),
            (FileNotFoundError("gh"), "gh CLI not found"),
        ],
        ids=["gh-failure", "gh-missing"],
    )
    def test_errors_exit_zero_with_a_warning(
        self,
        error: Exception,
        message: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with patch("promote_discussion_to_issue.run_promotion", side_effect=error):
            with pytest.raises(SystemExit) as exc:
                promote_module.main()
        assert exc.value.code == 0
        assert message in capsys.readouterr().err
