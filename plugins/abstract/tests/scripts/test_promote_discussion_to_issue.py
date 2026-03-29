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
