"""Tests for post_learnings_to_discussions.py.

Covers parsing, formatting, GraphQL helpers, and the main post_learnings
pipeline with all external I/O mocked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import post_learnings_to_discussions as pld

# ---------------------------------------------------------------------------
# _extract_metadata_field / _extract_bold_field
# ---------------------------------------------------------------------------


class TestExtractFields:
    """Regex extraction helpers."""

    @pytest.mark.unit
    def test_extract_metadata_field_found(self):
        """Returns the value after a bold label."""
        content = "**Last Updated**: 2024-01-15"
        assert pld._extract_metadata_field(content, "Last Updated") == "2024-01-15"

    @pytest.mark.unit
    def test_extract_metadata_field_missing(self):
        """Returns empty string when label not present."""
        assert pld._extract_metadata_field("no label here", "Missing") == ""

    @pytest.mark.unit
    def test_extract_bold_field_found(self):
        """Returns value from bold field in a text block."""
        text = "**Type**: high_failure_rate"
        assert pld._extract_bold_field(text, "Type") == "high_failure_rate"

    @pytest.mark.unit
    def test_extract_bold_field_missing(self):
        """Returns empty string when field not present."""
        assert pld._extract_bold_field("no type here", "Type") == ""


# ---------------------------------------------------------------------------
# _extract_section
# ---------------------------------------------------------------------------


class TestExtractSection:
    """_extract_section isolates content between headings."""

    @pytest.mark.unit
    def test_section_found(self):
        """Returns content between heading and next ## heading."""
        content = "## High-Impact Issues\nsome content\n## Next\nother"
        result = pld._extract_section(content, "## High-Impact Issues")
        assert result is not None
        assert "some content" in result

    @pytest.mark.unit
    def test_section_not_found(self):
        """Returns None when heading not present."""
        assert pld._extract_section("# Title\ncontent", "## Missing") is None

    @pytest.mark.unit
    def test_section_at_end_of_file(self):
        """Returns section content when it's at the end of the file."""
        content = "## Last Section\ncontent at end"
        result = pld._extract_section(content, "## Last Section")
        assert result == "content at end"


# ---------------------------------------------------------------------------
# parse_learnings_md
# ---------------------------------------------------------------------------


SAMPLE_LEARNINGS = """# Skill Performance Learnings

**Last Updated**: 2024-01-15 12:00:00 UTC
**Analysis Period**: Last 30 days
**Skills Analyzed**: 5
**Total Executions**: 100

---

## High-Impact Issues

### abstract:skill-auditor
**Type**: high_failure_rate
**Severity**: high
**Metric**: 20.0% success rate
**Detail**: 8/10 failures

---

## Slow Execution

| Skill | Avg Duration | Max Duration | Executions |
|-------|--------------|--------------|------------|
| `abstract:slow-skill` | 15.0s | 30.0s | 5 |

---

## Low User Ratings

### abstract:bad-skill - 2.5/5.0
**Common Friction**:
- unclear output

---
"""


class TestParseLearningsMd:
    """parse_learnings_md extracts structured data from LEARNINGS.md content."""

    @pytest.mark.unit
    def test_metadata_extracted(self):
        """Metadata fields are parsed from header."""
        summary = pld.parse_learnings_md(SAMPLE_LEARNINGS)
        assert summary.last_updated == "2024-01-15 12:00:00 UTC"
        assert summary.skills_analyzed == 5
        assert summary.total_executions == 100

    @pytest.mark.unit
    def test_high_impact_issues_parsed(self):
        """High-impact issues section is parsed into list."""
        summary = pld.parse_learnings_md(SAMPLE_LEARNINGS)
        assert len(summary.high_impact_issues) == 1
        issue = summary.high_impact_issues[0]
        assert issue["skill"] == "abstract:skill-auditor"
        assert issue["severity"] == "high"

    @pytest.mark.unit
    def test_slow_skills_parsed(self):
        """Slow execution table rows are parsed."""
        summary = pld.parse_learnings_md(SAMPLE_LEARNINGS)
        assert len(summary.slow_skills) >= 1
        slow = summary.slow_skills[0]
        assert slow["skill"] == "abstract:slow-skill"
        assert slow["executions"] == 5

    @pytest.mark.unit
    def test_low_rated_skills_parsed(self):
        """Low user ratings section is parsed."""
        summary = pld.parse_learnings_md(SAMPLE_LEARNINGS)
        assert len(summary.low_rated_skills) >= 1
        low = summary.low_rated_skills[0]
        assert low["skill"] == "abstract:bad-skill"
        assert low["rating"] == pytest.approx(2.5)

    @pytest.mark.unit
    def test_empty_content_returns_defaults(self):
        """Empty content yields zero counts."""
        summary = pld.parse_learnings_md("")
        assert summary.skills_analyzed == 0
        assert summary.total_executions == 0
        assert summary.high_impact_issues == []

    @pytest.mark.unit
    def test_non_digit_skills_analyzed_yields_zero(self):
        """Non-numeric Skills Analyzed field yields 0."""
        content = "**Skills Analyzed**: N/A"
        summary = pld.parse_learnings_md(content)
        assert summary.skills_analyzed == 0


# ---------------------------------------------------------------------------
# format_discussion_body
# ---------------------------------------------------------------------------


class TestFormatDiscussionBody:
    """format_discussion_body produces a markdown discussion post."""

    @pytest.mark.unit
    def test_contains_summary_stats(self):
        """Output includes the Summary Stats section."""
        summary = pld.LearningSummary(
            last_updated="2024-01-15",
            analysis_period="Last 30 days",
            skills_analyzed=3,
            total_executions=30,
        )
        body = pld.format_discussion_body(summary)
        assert "## Summary Stats" in body
        assert "Skills Analyzed" in body

    @pytest.mark.unit
    def test_top_issues_section_when_present(self):
        """High impact issues appear in Top Issues section."""
        summary = pld.LearningSummary(
            high_impact_issues=[
                {
                    "skill": "p:s",
                    "severity": "high",
                    "metric": "20%",
                    "type": "high_failure_rate",
                }
            ]
        )
        body = pld.format_discussion_body(summary)
        assert "## Top Issues" in body
        assert "p:s" in body

    @pytest.mark.unit
    def test_top_issues_capped_at_5(self):
        """Only first 5 issues are included."""
        issues = [
            {"skill": f"p:{i}", "severity": "high", "metric": f"{i}%", "type": "x"}
            for i in range(10)
        ]
        summary = pld.LearningSummary(high_impact_issues=issues)
        body = pld.format_discussion_body(summary)
        # Count occurrences of "p:" in body lines for issue section
        issue_lines = [ln for ln in body.split("\n") if ln.startswith("- **p:")]
        assert len(issue_lines) <= 5

    @pytest.mark.unit
    def test_slow_skills_section_when_present(self):
        """Slow skills section appears when data is present."""
        summary = pld.LearningSummary(
            slow_skills=[
                {
                    "skill": "p:slow",
                    "avg_duration": "15.0s",
                    "max_duration": "30.0s",
                    "executions": 5,
                }
            ]
        )
        body = pld.format_discussion_body(summary)
        assert "## Slow Execution Patterns" in body

    @pytest.mark.unit
    def test_low_rated_section_when_present(self):
        """Low-rated skills section appears when data is present."""
        summary = pld.LearningSummary(
            low_rated_skills=[{"skill": "p:bad", "rating": 2.0}]
        )
        body = pld.format_discussion_body(summary)
        assert "## Low-Rated Skills" in body

    @pytest.mark.unit
    def test_footer_present(self):
        """Footer attribution is always included."""
        body = pld.format_discussion_body(pld.LearningSummary())
        assert "Phase 6a" in body


# ---------------------------------------------------------------------------
# DiscussionConfig.load
# ---------------------------------------------------------------------------


class TestDiscussionConfigLoad:
    """DiscussionConfig.load reads config from disk."""

    @pytest.mark.unit
    def test_defaults_when_no_config_file(self, tmp_path, monkeypatch):
        """When config file is absent, returns default config."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        config = pld.DiscussionConfig.load()
        assert config.auto_post_learnings is True
        assert config.target_repo == ""

    @pytest.mark.unit
    def test_loads_from_config_file(self, tmp_path, monkeypatch):
        """Config values are read from JSON file."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        config_data = {
            "auto_post_learnings": False,
            "target_repo": "owner/repo",
            "promotion_threshold": 5,
        }
        (tmp_path / "config.json").write_text(json.dumps(config_data))
        config = pld.DiscussionConfig.load()
        assert config.auto_post_learnings is False
        assert config.target_repo == "owner/repo"

    @pytest.mark.unit
    def test_bad_json_falls_back_to_defaults(self, tmp_path, monkeypatch):
        """When config JSON is malformed, defaults are returned."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        (tmp_path / "config.json").write_text("NOT JSON")
        config = pld.DiscussionConfig.load()
        assert config.auto_post_learnings is True


# ---------------------------------------------------------------------------
# PostedRecord
# ---------------------------------------------------------------------------


class TestPostedRecord:
    """PostedRecord persists previously posted discussion titles."""

    @pytest.mark.unit
    def test_new_record_is_empty(self, tmp_path, monkeypatch):
        """When no record file exists, posted dict is empty."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord.load()
        assert record.posted == {}

    @pytest.mark.unit
    def test_is_posted_returns_false_when_title_absent(self, tmp_path, monkeypatch):
        """is_posted returns False for unknown title."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord.load()
        assert not record.is_posted("[Learning] 2024-01-15")

    @pytest.mark.unit
    def test_save_and_reload(self, tmp_path, monkeypatch):
        """Saved record is reloaded correctly on next load."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord.load()
        record.posted["[Learning] 2024-01-15"] = "https://example.com/1"
        record.save()

        reloaded = pld.PostedRecord.load()
        assert reloaded.is_posted("[Learning] 2024-01-15")
        assert reloaded.posted["[Learning] 2024-01-15"] == "https://example.com/1"

    @pytest.mark.unit
    def test_malformed_record_file_returns_empty(self, tmp_path, monkeypatch):
        """When record JSON is malformed, empty record is returned."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        (tmp_path / "posted.json").write_text("INVALID")
        record = pld.PostedRecord.load()
        assert record.posted == {}

    @pytest.mark.unit
    def test_record_saves_repo_node_id(self, tmp_path, monkeypatch):
        """repo_node_id is persisted and reloaded."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord(repo_node_id="MDEwOlJlcG8x")
        record.save()

        reloaded = pld.PostedRecord.load()
        assert reloaded.repo_node_id == "MDEwOlJlcG8x"


# ---------------------------------------------------------------------------
# detect_target_repo
# ---------------------------------------------------------------------------


class TestDetectTargetRepo:
    """detect_target_repo resolves the (owner, name) tuple."""

    @pytest.mark.unit
    def test_uses_config_file_override(self, tmp_path, monkeypatch):
        """When config has target_repo, it is used without calling gh."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        config_data = {"target_repo": "myowner/myrepo"}
        (tmp_path / "config.json").write_text(json.dumps(config_data))

        result = pld.detect_target_repo()
        assert result == ("myowner", "myrepo")

    @pytest.mark.unit
    def test_falls_back_to_gh_repo_view(self, tmp_path, monkeypatch):
        """When no config override, gh repo view is called."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "owner/repo\n"
        with patch("subprocess.run", return_value=mock_result):
            result = pld.detect_target_repo()

        assert result == ("owner", "repo")

    @pytest.mark.unit
    def test_returns_none_when_gh_fails(self, tmp_path, monkeypatch):
        """When gh command fails, returns None."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = pld.detect_target_repo()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_gh_not_found(self, tmp_path, monkeypatch):
        """When gh CLI is not installed, returns None."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = pld.detect_target_repo()

        assert result is None

    @pytest.mark.unit
    def test_config_repo_without_slash_ignored(self, tmp_path, monkeypatch):
        """Config target_repo without slash is not used; falls back to gh."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        config_data = {"target_repo": "noslashhere"}
        (tmp_path / "config.json").write_text(json.dumps(config_data))

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "fallback/repo\n"
        with patch("subprocess.run", return_value=mock_result):
            result = pld.detect_target_repo()

        assert result == ("fallback", "repo")


# ---------------------------------------------------------------------------
# run_gh_graphql
# ---------------------------------------------------------------------------


class TestRunGhGraphql:
    """run_gh_graphql executes gh api graphql and parses JSON."""

    @pytest.mark.unit
    def test_returns_parsed_json_on_success(self):
        """Returns parsed response on returncode 0."""
        payload = {"data": {"repository": {"id": "MDEw"}}}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(payload)
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = pld.run_gh_graphql("query {}")

        assert result == payload

    @pytest.mark.unit
    def test_raises_runtime_error_on_failure(self):
        """Raises RuntimeError when gh command returns non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "auth error"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="gh api graphql failed"):
                pld.run_gh_graphql("query {}")

    @pytest.mark.unit
    def test_variables_passed_as_f_flags(self):
        """Variables are passed as -f key=value flags."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "{}"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            pld.run_gh_graphql("query {}", variables={"owner": "o", "repo": "r"})

        call_args = mock_run.call_args[0][0]
        joined = " ".join(call_args)
        assert "owner=o" in joined
        assert "repo=r" in joined


# ---------------------------------------------------------------------------
# resolve_category_id
# ---------------------------------------------------------------------------


class TestResolveCategoryId:
    """resolve_category_id fetches the category node ID by slug."""

    @pytest.mark.unit
    def test_returns_category_id_when_found(self):
        """Returns ID when slug matches."""
        payload = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": [
                            {"id": "CAT1", "slug": "learnings"},
                            {"id": "CAT2", "slug": "general"},
                        ]
                    }
                }
            }
        }
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.resolve_category_id("owner", "repo", "learnings")

        assert result == "CAT1"

    @pytest.mark.unit
    def test_returns_none_when_slug_not_found(self):
        """Returns None when slug not in response."""
        payload = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": [{"id": "CAT1", "slug": "general"}]
                    }
                }
            }
        }
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.resolve_category_id("owner", "repo", "learnings")

        assert result is None

    @pytest.mark.unit
    def test_returns_none_on_graphql_error(self):
        """Returns None when run_gh_graphql raises RuntimeError."""
        with patch.object(pld, "run_gh_graphql", side_effect=RuntimeError("api error")):
            result = pld.resolve_category_id("owner", "repo", "learnings")

        assert result is None


# ---------------------------------------------------------------------------
# get_repo_node_id
# ---------------------------------------------------------------------------


class TestGetRepoNodeId:
    """get_repo_node_id retrieves and caches the repository node ID."""

    @pytest.mark.unit
    def test_uses_cached_id_when_available(self, tmp_path, monkeypatch):
        """When record already has repo_node_id, GraphQL is not called."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord(repo_node_id="CACHED_ID")

        with patch.object(pld, "run_gh_graphql") as mock_gql:
            result = pld.get_repo_node_id(record, "owner", "repo")

        assert result == "CACHED_ID"
        mock_gql.assert_not_called()

    @pytest.mark.unit
    def test_fetches_and_caches_id(self, tmp_path, monkeypatch):
        """When record has no repo_node_id, it is fetched and cached."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        record = pld.PostedRecord()

        payload = {"data": {"repository": {"id": "NEW_REPO_ID"}}}
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.get_repo_node_id(record, "owner", "repo")

        assert result == "NEW_REPO_ID"
        assert record.repo_node_id == "NEW_REPO_ID"


# ---------------------------------------------------------------------------
# check_existing_discussion
# ---------------------------------------------------------------------------


class TestCheckExistingDiscussion:
    """check_existing_discussion searches for pre-existing discussions."""

    @pytest.mark.unit
    def test_returns_url_when_found(self):
        """Returns URL when title matches a search result."""
        title = "[Learning] 2024-01-15"
        payload = {
            "data": {
                "search": {"nodes": [{"title": title, "url": "https://github.com/d/1"}]}
            }
        }
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.check_existing_discussion(title, "owner", "repo")

        assert result == "https://github.com/d/1"

    @pytest.mark.unit
    def test_returns_none_when_no_match(self):
        """Returns None when no node title matches."""
        payload = {
            "data": {
                "search": {
                    "nodes": [
                        {"title": "Different Title", "url": "https://github.com/d/2"}
                    ]
                }
            }
        }
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.check_existing_discussion(
                "[Learning] 2024-01-15", "owner", "repo"
            )

        assert result is None

    @pytest.mark.unit
    def test_returns_none_on_error(self):
        """Returns None when GraphQL call raises."""
        with patch.object(
            pld, "run_gh_graphql", side_effect=RuntimeError("network error")
        ):
            result = pld.check_existing_discussion(
                "[Learning] 2024-01-15", "owner", "repo"
            )

        assert result is None


# ---------------------------------------------------------------------------
# create_discussion
# ---------------------------------------------------------------------------


class TestCreateDiscussion:
    """create_discussion creates a GitHub Discussion via mutation."""

    @pytest.mark.unit
    def test_returns_discussion_url(self):
        """Returns URL from mutation response."""
        payload = {
            "data": {
                "createDiscussion": {
                    "discussion": {"url": "https://github.com/discussions/42"}
                }
            }
        }
        with patch.object(pld, "run_gh_graphql", return_value=payload):
            result = pld.create_discussion("REPO_ID", "CAT_ID", "Title", "Body")

        assert result == "https://github.com/discussions/42"


# ---------------------------------------------------------------------------
# _load_and_validate_learnings
# ---------------------------------------------------------------------------


class TestLoadAndValidateLearnings:
    """_load_and_validate_learnings validates LEARNINGS.md before posting."""

    @pytest.mark.unit
    def test_missing_file_returns_none(self, tmp_path, capsys):
        """When file does not exist, returns None and prints warning."""
        result = pld._load_and_validate_learnings(tmp_path / "LEARNINGS.md")
        assert result is None
        out = capsys.readouterr().err
        assert "not found" in out.lower() or "Warning" in out

    @pytest.mark.unit
    def test_empty_file_returns_none(self, tmp_path, capsys):
        """When file is empty, returns None."""
        f = tmp_path / "LEARNINGS.md"
        f.write_text("   ")
        result = pld._load_and_validate_learnings(f)
        assert result is None

    @pytest.mark.unit
    def test_no_data_returns_none(self, tmp_path, capsys):
        """When parsed summary has zero skills and executions, returns None."""
        f = tmp_path / "LEARNINGS.md"
        f.write_text("**Skills Analyzed**: 0\n**Total Executions**: 0\n")
        result = pld._load_and_validate_learnings(f)
        assert result is None

    @pytest.mark.unit
    def test_valid_file_returns_summary(self, tmp_path):
        """When file has valid content, returns LearningSummary."""
        f = tmp_path / "LEARNINGS.md"
        f.write_text(SAMPLE_LEARNINGS)
        result = pld._load_and_validate_learnings(f)
        assert result is not None
        assert result.skills_analyzed == 5


# ---------------------------------------------------------------------------
# post_learnings (main pipeline)
# ---------------------------------------------------------------------------


class TestPostLearnings:
    """post_learnings orchestrates the full pipeline."""

    @pytest.mark.unit
    def test_returns_none_when_disabled(self, tmp_path, monkeypatch, capsys):
        """When auto_post_learnings is False, returns None immediately."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        config_json = {"auto_post_learnings": False}
        (tmp_path / "config.json").write_text(json.dumps(config_json))

        result = pld.post_learnings()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_repo_undetectable(self, tmp_path, monkeypatch):
        """When repo detection fails, returns None."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        with patch.object(pld, "detect_target_repo", return_value=None):
            result = pld.post_learnings()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_no_learnings_category(self, tmp_path, monkeypatch):
        """When repo has no 'learnings' discussion category, returns None."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)
        with (
            patch.object(pld, "detect_target_repo", return_value=("o", "r")),
            patch.object(pld, "resolve_category_id", return_value=None),
        ):
            result = pld.post_learnings()

        assert result is None

    @pytest.mark.unit
    def test_returns_existing_url_when_already_posted(self, tmp_path, monkeypatch):
        """When title already in posted record, returns cached URL."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)

        # Prepare LEARNINGS.md
        learnings_path = tmp_path / "LEARNINGS.md"
        learnings_path.write_text(SAMPLE_LEARNINGS)

        # Patch title creation to return a known value
        from datetime import datetime, timezone

        fixed_date = "2024-01-15"
        title = f"[Learning] {fixed_date}"

        # Pre-populate posted record
        posted_record = pld.PostedRecord(
            posted={title: "https://existing.com/discussion/1"}
        )

        with (
            patch.object(pld, "detect_target_repo", return_value=("o", "r")),
            patch.object(pld, "resolve_category_id", return_value="CAT_ID"),
            patch.object(pld, "PostedRecord") as mock_cls,
        ):
            # Make PostedRecord.load() return our pre-populated record
            mock_cls.load.return_value = posted_record

            with patch("post_learnings_to_discussions.datetime") as mock_dt:
                mock_dt.now.return_value.strftime.return_value = fixed_date
                mock_dt.now.return_value = datetime(2024, 1, 15, tzinfo=timezone.utc)

                result = pld.post_learnings(learnings_path=learnings_path)

        assert result == "https://existing.com/discussion/1"

    @pytest.mark.unit
    def test_creates_new_discussion_when_not_posted(self, tmp_path, monkeypatch):
        """When not yet posted, creates a new discussion and returns URL."""
        monkeypatch.setattr(pld, "get_config_dir", lambda: tmp_path)

        learnings_path = tmp_path / "LEARNINGS.md"
        learnings_path.write_text(SAMPLE_LEARNINGS)

        new_url = "https://github.com/discussions/99"

        with (
            patch.object(pld, "detect_target_repo", return_value=("o", "r")),
            patch.object(pld, "resolve_category_id", return_value="CAT_ID"),
            patch.object(pld, "check_existing_discussion", return_value=None),
            patch.object(pld, "get_repo_node_id", return_value="REPO_ID"),
            patch.object(pld, "create_discussion", return_value=new_url),
        ):
            result = pld.post_learnings(learnings_path=learnings_path)

        assert result == new_url


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


class TestMain:
    """main() is a graceful CLI entry point."""

    @pytest.mark.unit
    def test_main_exits_0_on_file_not_found(self, monkeypatch):
        """FileNotFoundError (no gh) exits 0 rather than crashing."""
        with patch.object(pld, "post_learnings", side_effect=FileNotFoundError):
            with pytest.raises(SystemExit) as exc_info:
                pld.main()
        assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_exits_0_on_runtime_error(self, monkeypatch):
        """RuntimeError exits 0 (graceful failure)."""
        with patch.object(pld, "post_learnings", side_effect=RuntimeError("api down")):
            with pytest.raises(SystemExit) as exc_info:
                pld.main()
        assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_prints_url_on_success(self, capsys):
        """When URL returned, it is printed to stdout."""
        with patch.object(
            pld, "post_learnings", return_value="https://example.com/d/1"
        ):
            pld.main()

        captured = capsys.readouterr().out
        assert "https://example.com/d/1" in captured
