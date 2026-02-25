"""Tests for auto_promote_learnings.py.

Tests the severity-based auto-promotion that replaces reaction voting
for single-developer use. Verifies:
1. LEARNINGS.md parsing and priority scoring
2. Issue creation for high-severity items (>5.0)
3. Discussion posting for medium-severity items (2.0-5.0)
4. Deduplication via promoted_issues.json
5. Graceful failure handling
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_LEARNINGS_MD = """\
# Skill Performance Learnings

**Last Updated**: 2026-02-23 04:30:00 UTC
**Analysis Period**: Last 30 days
**Skills Analyzed**: 15
**Total Executions**: 342

---

## High-Impact Issues

Skills with significant problems requiring immediate attention.

### imbue:proof-of-work
**Type**: high_failure_rate
**Severity**: high
**Metric**: 42.3% success rate
**Detail**: 11/26 failures

### abstract:skill-auditor
**Type**: low_rating
**Severity**: medium
**Metric**: 2.8/5.0 rating
**Detail**: User evaluations indicate poor effectiveness

---

## Slow Execution

Skills exceeding 10s average execution time.

| Skill | Avg Duration | Max Duration | Executions |
|-------|--------------|--------------|------------|
| `sanctum:pr-agent` | 45.2s | 120.0s | 18 |

---

## Low User Ratings

Skills with < 3.5/5.0 average rating from evaluations.

### abstract:skill-auditor - 2.8/5.0
**Common Friction**:
- Too verbose output
- Slow execution

---

## Skill Performance Summary

| Skill | Executions | Success Rate | Avg Duration | Rating |
|-------|------------|--------------|--------------|--------|
| `imbue:proof-of-work` | 26 | 42.3% | 5.2s | 3.0/5.0 |
| `sanctum:pr-agent` | 18 | 88.9% | 45.2s | 4.2/5.0 |
| `abstract:skill-auditor` | 12 | 91.7% | 8.1s | 2.8/5.0 |
| `conserve:bloat-scan` | 8 | 100.0% | 3.4s | 4.5/5.0 |
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def promote_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Import auto_promote_learnings with paths redirected."""
    if "auto_promote_learnings" in sys.modules:
        del sys.modules["auto_promote_learnings"]

    import auto_promote_learnings  # noqa: PLC0415

    monkeypatch.setattr(
        auto_promote_learnings,
        "get_learnings_path",
        lambda: tmp_path / "LEARNINGS.md",
    )
    monkeypatch.setattr(
        auto_promote_learnings,
        "get_promoted_record_path",
        lambda: tmp_path / "promoted_issues.json",
    )
    return auto_promote_learnings


@pytest.fixture()
def learnings_file(tmp_path: Path) -> Path:
    """Create a sample LEARNINGS.md file."""
    path = tmp_path / "LEARNINGS.md"
    path.write_text(SAMPLE_LEARNINGS_MD)
    return path


# ---------------------------------------------------------------------------
# Priority scoring tests
# ---------------------------------------------------------------------------


class TestPriorityScoring:
    """Test the (Frequency × Impact) / Ease priority formula."""

    def test_high_failure_rate_scores_high(self, promote_module) -> None:
        """Given: A skill with high failure rate and many executions
        When: calculate_priority() is called
        Then: Score should be > 5.0 (auto-promote threshold)
        """
        item = {
            "skill": "imbue:proof-of-work",
            "type": "high_failure_rate",
            "severity": "high",
            "executions": 26,
            "success_rate": 42.3,
        }
        score = promote_module.calculate_priority(item)
        assert score > 5.0, f"Expected >5.0, got {score}"

    def test_low_rating_with_few_executions_scores_medium(self, promote_module) -> None:
        """Given: A skill with low rating and very few executions
        When: calculate_priority() is called
        Then: Score should be between 2.0 and 5.0 (discuss threshold)
        """
        item = {
            "skill": "abstract:skill-auditor",
            "type": "low_rating",
            "severity": "medium",
            "executions": 3,
            "avg_rating": 3.2,
        }
        score = promote_module.calculate_priority(item)
        assert 2.0 <= score <= 5.0, f"Expected 2.0-5.0, got {score}"

    def test_healthy_skill_scores_low(self, promote_module) -> None:
        """Given: A skill with good metrics
        When: calculate_priority() is called
        Then: Score should be < 2.0 (skip threshold)
        """
        item = {
            "skill": "conserve:bloat-scan",
            "type": "none",
            "severity": "low",
            "executions": 8,
            "success_rate": 100.0,
            "avg_rating": 4.5,
        }
        score = promote_module.calculate_priority(item)
        assert score < 2.0, f"Expected <2.0, got {score}"

    def test_slow_execution_scores_correctly(self, promote_module) -> None:
        """Given: A skill with slow execution
        When: calculate_priority() is called
        Then: Score reflects execution time severity
        """
        item = {
            "skill": "sanctum:pr-agent",
            "type": "slow_execution",
            "severity": "medium",
            "executions": 18,
            "avg_duration_ms": 45200,
        }
        score = promote_module.calculate_priority(item)
        assert score > 0, f"Expected positive score, got {score}"


# ---------------------------------------------------------------------------
# LEARNINGS.md parsing tests
# ---------------------------------------------------------------------------


class TestLearningsParsing:
    """Test parsing LEARNINGS.md into promotable items."""

    def test_extracts_high_impact_issues(
        self, promote_module, learnings_file: Path
    ) -> None:
        """Given: LEARNINGS.md with high-impact issues
        When: parse_improvement_items() is called
        Then: Returns items with correct skill names and types
        """
        items = promote_module.parse_improvement_items(learnings_file.read_text())
        skills = [i["skill"] for i in items]
        assert "imbue:proof-of-work" in skills

    def test_extracts_slow_skills(self, promote_module, learnings_file: Path) -> None:
        """Given: LEARNINGS.md with slow execution section
        When: parse_improvement_items() is called
        Then: Includes slow skills in results
        """
        items = promote_module.parse_improvement_items(learnings_file.read_text())
        slow_items = [i for i in items if i.get("type") == "slow_execution"]
        assert len(slow_items) > 0

    def test_extracts_low_rated_skills(
        self, promote_module, learnings_file: Path
    ) -> None:
        """Given: LEARNINGS.md with low-rated skills
        When: parse_improvement_items() is called
        Then: Includes low-rated skills in results
        """
        items = promote_module.parse_improvement_items(learnings_file.read_text())
        low_rated = [i for i in items if i.get("type") == "low_rating"]
        assert len(low_rated) > 0

    def test_returns_empty_for_missing_file(self, promote_module) -> None:
        """Given: No LEARNINGS.md content
        When: parse_improvement_items() is called with empty string
        Then: Returns empty list
        """
        items = promote_module.parse_improvement_items("")
        assert items == []


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


class TestDeduplication:
    """Test that items aren't promoted twice."""

    def test_skips_already_promoted_items(self, promote_module, tmp_path: Path) -> None:
        """Given: An item was previously promoted (in promoted_issues.json)
        When: should_promote() is called for that item
        Then: Returns False
        """
        record_path = tmp_path / "promoted_issues.json"
        record_path.write_text(
            json.dumps(
                {
                    "promoted": {
                        "imbue:proof-of-work:high_failure_rate": "https://github.com/athola/claude-night-market/issues/999"
                    }
                }
            )
        )

        record = promote_module.PromotedIssueRecord.load(record_path)
        assert record.is_promoted("imbue:proof-of-work:high_failure_rate")

    def test_allows_new_items(self, promote_module, tmp_path: Path) -> None:
        """Given: An item has never been promoted
        When: should_promote() is called
        Then: Returns True
        """
        record_path = tmp_path / "promoted_issues.json"
        record = promote_module.PromotedIssueRecord.load(record_path)
        assert not record.is_promoted("new:skill:issue_type")

    def test_record_persists_to_disk(self, promote_module, tmp_path: Path) -> None:
        """Given: A promotion is recorded
        When: Record is saved and reloaded
        Then: The promotion is still tracked
        """
        record_path = tmp_path / "promoted_issues.json"
        record = promote_module.PromotedIssueRecord.load(record_path)
        record.add("test:skill:type", "https://example.com/issue/1")
        record.save(record_path)

        reloaded = promote_module.PromotedIssueRecord.load(record_path)
        assert reloaded.is_promoted("test:skill:type")


# ---------------------------------------------------------------------------
# Issue creation tests
# ---------------------------------------------------------------------------


class TestIssueCreation:
    """Test GitHub issue creation for high-severity items."""

    def test_creates_issue_for_high_priority_item(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: An item with priority > 5.0
        When: promote_to_issue() is called
        Then: gh CLI is invoked to create an issue
        """
        mock_run = MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout="https://github.com/athola/claude-night-market/issues/100\n",
            )
        )
        monkeypatch.setattr("subprocess.run", mock_run)

        item = {
            "skill": "imbue:proof-of-work",
            "type": "high_failure_rate",
            "metric": "42.3% success rate",
            "detail": "11/26 failures",
        }
        url = promote_module.promote_to_issue(item)
        assert url is not None
        mock_run.assert_called_once()

        # Verify the gh command structure
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd[0]
        assert "issue" in cmd
        assert "create" in cmd

    def test_issue_has_correct_label(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: An item being promoted to issue
        When: promote_to_issue() is called
        Then: Issue has improvement:auto-promoted label
        """
        mock_run = MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout="https://github.com/test/issues/1\n",
            )
        )
        monkeypatch.setattr("subprocess.run", mock_run)

        item = {
            "skill": "test:skill",
            "type": "high_failure_rate",
            "metric": "50% success rate",
            "detail": "details",
        }
        promote_module.promote_to_issue(item)

        cmd = mock_run.call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "improvement:auto-promoted" in cmd_str


# ---------------------------------------------------------------------------
# Discussion posting tests (medium severity)
# ---------------------------------------------------------------------------


class TestDiscussionPosting:
    """Test Discussion posting for medium-severity items."""

    def test_posts_discussion_for_medium_priority_item(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: An item with priority between 2.0 and 5.0
        When: post_to_discussion() is called
        Then: Delegates to post_learnings_to_discussions infrastructure
        """
        mock_post = MagicMock(return_value="https://github.com/test/discussions/1")
        monkeypatch.setattr(promote_module, "_post_single_discussion", mock_post)

        item = {
            "skill": "abstract:skill-auditor",
            "type": "low_rating",
            "metric": "2.8/5.0 rating",
            "detail": "User evaluations indicate poor effectiveness",
        }
        url = promote_module.post_to_discussion(item)
        assert url is not None
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# Graceful failure tests
# ---------------------------------------------------------------------------


class TestGracefulFailure:
    """Test that failures don't crash the hook pipeline."""

    def test_returns_empty_when_learnings_missing(
        self, promote_module, tmp_path: Path
    ) -> None:
        """Given: LEARNINGS.md doesn't exist
        When: run_auto_promote() is called
        Then: Returns empty list (no crashes)
        """
        result = promote_module.run_auto_promote()
        assert result == []

    def test_handles_gh_cli_not_found(
        self, promote_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Given: gh CLI is not installed
        When: promote_to_issue() is called
        Then: Returns None gracefully
        """
        monkeypatch.setattr(
            "subprocess.run",
            MagicMock(side_effect=FileNotFoundError("gh not found")),
        )

        item = {
            "skill": "test:skill",
            "type": "test",
            "metric": "test",
            "detail": "test",
        }
        result = promote_module.promote_to_issue(item)
        assert result is None

    def test_handles_malformed_learnings(self, promote_module, tmp_path: Path) -> None:
        """Given: LEARNINGS.md has invalid content
        When: parse_improvement_items() is called
        Then: Returns empty list
        """
        items = promote_module.parse_improvement_items("not valid markdown")
        assert items == []

    def test_returns_none_when_gh_returns_nonzero(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: gh CLI returns a non-zero exit code
        When: promote_to_issue() is called
        Then: Returns None (not a URL)
        """
        monkeypatch.setattr(
            "subprocess.run",
            MagicMock(
                return_value=MagicMock(
                    returncode=1,
                    stderr="label not found",
                )
            ),
        )

        item = {
            "skill": "test:skill",
            "type": "test",
            "metric": "test",
            "detail": "test",
        }
        result = promote_module.promote_to_issue(item)
        assert result is None

    def test_handles_generic_exception_in_promote(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: subprocess.run raises an unexpected exception
        When: promote_to_issue() is called
        Then: Returns None gracefully
        """
        monkeypatch.setattr(
            "subprocess.run",
            MagicMock(side_effect=OSError("unexpected")),
        )

        item = {
            "skill": "test:skill",
            "type": "test",
            "metric": "test",
            "detail": "test",
        }
        result = promote_module.promote_to_issue(item)
        assert result is None


# ---------------------------------------------------------------------------
# Additional priority scoring tests
# ---------------------------------------------------------------------------


class TestPriorityScoringEdgeCases:
    """Test edge cases in the priority formula."""

    def test_excessive_failures_type_has_high_fixed_impact(
        self, promote_module
    ) -> None:
        """Given: An item with type 'excessive_failures'
        When: calculate_priority() is called
        Then: Uses fixed high impact of 8.0
        """
        item = {
            "skill": "broken:skill",
            "type": "excessive_failures",
            "severity": "high",
            "executions": 10,
        }
        score = promote_module.calculate_priority(item)
        # (10 * 8.0) / 2.0 = 40.0
        assert score == pytest.approx(40.0)

    def test_unknown_type_has_minimal_impact(self, promote_module) -> None:
        """Given: An item with an unrecognized type
        When: calculate_priority() is called
        Then: Uses minimal impact (0.1)
        """
        item = {
            "skill": "some:skill",
            "type": "completely_unknown",
            "severity": "low",
            "executions": 5,
        }
        score = promote_module.calculate_priority(item)
        # (5 * 0.1) / 5.0 = 0.1
        assert score == pytest.approx(0.1)

    def test_zero_executions_treated_as_one(self, promote_module) -> None:
        """Given: An item with 0 executions
        When: calculate_priority() is called
        Then: Frequency is clamped to 1 (never zero)
        """
        item = {
            "skill": "new:skill",
            "type": "high_failure_rate",
            "severity": "high",
            "executions": 0,
            "success_rate": 0.0,
        }
        score = promote_module.calculate_priority(item)
        # frequency=1, impact=(100-0)/10=10, ease=2.0 -> 5.0
        assert score == pytest.approx(5.0)

    def test_unknown_severity_defaults_to_low_ease(self, promote_module) -> None:
        """Given: An item with an unrecognized severity
        When: calculate_priority() is called
        Then: Ease defaults to 5.0 (low)
        """
        item = {
            "skill": "test:skill",
            "type": "excessive_failures",
            "severity": "critical",  # Not in ease_map
            "executions": 1,
        }
        score = promote_module.calculate_priority(item)
        # (1 * 8.0) / 5.0 = 1.6
        assert score == pytest.approx(1.6)


# ---------------------------------------------------------------------------
# Deduplication record edge cases
# ---------------------------------------------------------------------------


class TestDeduplicationEdgeCases:
    """Test PromotedIssueRecord edge cases."""

    def test_load_with_corrupt_json(self, promote_module, tmp_path: Path) -> None:
        """Given: promoted_issues.json contains invalid JSON
        When: PromotedIssueRecord.load() is called
        Then: Returns empty record (does not crash)
        """
        record_path = tmp_path / "promoted_issues.json"
        record_path.write_text("{not valid json")

        record = promote_module.PromotedIssueRecord.load(record_path)
        assert record.promoted == {}

    def test_load_with_missing_promoted_key(
        self, promote_module, tmp_path: Path
    ) -> None:
        """Given: JSON file exists but lacks 'promoted' key
        When: PromotedIssueRecord.load() is called
        Then: Returns empty record
        """
        record_path = tmp_path / "promoted_issues.json"
        record_path.write_text(json.dumps({"other": "data"}))

        record = promote_module.PromotedIssueRecord.load(record_path)
        assert record.promoted == {}

    def test_save_creates_parent_directories(
        self, promote_module, tmp_path: Path
    ) -> None:
        """Given: Parent directory doesn't exist
        When: record.save() is called
        Then: Directories are created
        """
        record_path = tmp_path / "deep" / "nested" / "promoted_issues.json"
        record = promote_module.PromotedIssueRecord()
        record.add("test:key", "https://example.com")
        record.save(record_path)

        assert record_path.exists()
        reloaded = promote_module.PromotedIssueRecord.load(record_path)
        assert reloaded.is_promoted("test:key")


# ---------------------------------------------------------------------------
# Parsing edge cases
# ---------------------------------------------------------------------------


class TestParsingEdgeCases:
    """Test LEARNINGS.md parsing edge cases."""

    def test_deduplicates_skill_across_sections(self, promote_module) -> None:
        """Given: A skill appears in both High-Impact and Low-Rated sections
        When: parse_improvement_items() is called
        Then: Skill appears only once, with rating enriched
        """
        items = promote_module.parse_improvement_items(SAMPLE_LEARNINGS_MD)
        auditor_items = [i for i in items if i["skill"] == "abstract:skill-auditor"]
        # Should appear once from High-Impact, with rating enriched
        assert len(auditor_items) == 1
        assert auditor_items[0].get("avg_rating") == 2.8

    def test_enriches_items_with_summary_table_data(self, promote_module) -> None:
        """Given: LEARNINGS.md has a Summary table
        When: parse_improvement_items() extracts high-impact items
        Then: Items are enriched with executions from the summary table
        """
        items = promote_module.parse_improvement_items(SAMPLE_LEARNINGS_MD)
        pow_items = [i for i in items if i["skill"] == "imbue:proof-of-work"]
        assert len(pow_items) == 1
        assert pow_items[0]["executions"] == 26
        assert pow_items[0]["success_rate"] == 42.3

    def test_whitespace_only_content_returns_empty(self, promote_module) -> None:
        """Given: Content is only whitespace
        When: parse_improvement_items() is called
        Then: Returns empty list
        """
        items = promote_module.parse_improvement_items("   \n\n  ")
        assert items == []


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------


class TestRunAutoPromotePipeline:
    """Test the full run_auto_promote() pipeline."""

    def test_promotes_high_priority_items(
        self, promote_module, learnings_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: LEARNINGS.md has items scoring above 5.0
        When: run_auto_promote() is called
        Then: Creates GitHub Issues for those items
        """
        mock_issue = MagicMock(return_value="https://github.com/test/issues/1")
        mock_discuss = MagicMock(return_value="https://github.com/test/discussions/1")
        monkeypatch.setattr(promote_module, "promote_to_issue", mock_issue)
        monkeypatch.setattr(promote_module, "post_to_discussion", mock_discuss)

        urls = promote_module.run_auto_promote()
        assert len(urls) > 0
        # At least one issue should have been promoted
        assert mock_issue.called or mock_discuss.called

    def test_skips_already_promoted_items_in_pipeline(
        self,
        promote_module,
        learnings_file: Path,
        tmp_path: Path,
    ) -> None:
        """Given: All items have already been promoted
        When: run_auto_promote() is called
        Then: Returns empty list (no duplicates)
        """
        # Pre-populate all items as promoted
        items = promote_module.parse_improvement_items(SAMPLE_LEARNINGS_MD)
        record = promote_module.PromotedIssueRecord()
        for item in items:
            key = f"{item['skill']}:{item.get('type', 'unknown')}"
            record.add(key, "https://example.com/already")
        record.save(tmp_path / "promoted_issues.json")

        urls = promote_module.run_auto_promote()
        assert urls == []

    def test_returns_empty_for_empty_learnings(
        self, promote_module, tmp_path: Path
    ) -> None:
        """Given: LEARNINGS.md exists but is empty
        When: run_auto_promote() is called
        Then: Returns empty list
        """
        (tmp_path / "LEARNINGS.md").write_text("")
        urls = promote_module.run_auto_promote()
        assert urls == []


# ---------------------------------------------------------------------------
# CLI main() tests
# ---------------------------------------------------------------------------


class TestMainCLI:
    """Test the main() CLI entry point."""

    def test_main_prints_promoted_count(
        self, promote_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: Items are promoted successfully
        When: main() is called
        Then: Prints count and URLs
        """
        monkeypatch.setattr(
            promote_module,
            "run_auto_promote",
            MagicMock(return_value=["https://github.com/test/issues/1"]),
        )

        promote_module.main()

        captured = capsys.readouterr()
        assert "Promoted 1 item(s)" in captured.out

    def test_main_prints_no_items_message(
        self, promote_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: No items are promoted
        When: main() is called
        Then: Prints 'No items promoted.'
        """
        monkeypatch.setattr(
            promote_module,
            "run_auto_promote",
            MagicMock(return_value=[]),
        )

        promote_module.main()

        captured = capsys.readouterr()
        assert "No items promoted." in captured.out

    def test_main_handles_exception_gracefully(
        self, promote_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: run_auto_promote() raises an exception
        When: main() is called
        Then: Prints warning and exits cleanly (exit code 0)
        """
        monkeypatch.setattr(
            promote_module,
            "run_auto_promote",
            MagicMock(side_effect=RuntimeError("unexpected")),
        )

        with pytest.raises(SystemExit) as exc_info:
            promote_module.main()

        assert exc_info.value.code == 0
