"""Tests for review scout -- learns techniques from exemplar projects."""

from __future__ import annotations

import base64
import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from scout import (
    ExemplarProject,
    ReviewTechnique,
    classify_technique,
    default_exemplars,
    extract_techniques_from_guidelines,
    fetch_contributing_guide,
    format_discussion_body,
    parse_contributing_guide,
    post_discussion,
    run_scout,
)


class TestExemplarProjects:
    """Curated list of projects to study."""

    def test_default_exemplars_exist(self) -> None:
        """Default list has at least 5 exemplar projects."""
        exemplars = default_exemplars()
        assert len(exemplars) >= 5

    def test_exemplars_have_required_fields(self) -> None:
        """Each exemplar has owner, repo, and language."""
        for e in default_exemplars():
            assert e.owner, f"Missing owner for {e}"
            assert e.repo, f"Missing repo for {e}"
            assert e.language, f"Missing language for {e}"

    def test_exemplars_cover_python(self) -> None:
        """At least one Python exemplar exists."""
        langs = {e.language for e in default_exemplars()}
        assert "python" in langs

    def test_full_name_format(self) -> None:
        """Given an exemplar, when accessing full_name, then returns owner/repo."""
        e = ExemplarProject(owner="org", repo="lib", language="python")
        assert e.full_name == "org/lib"


class TestParseContributing:
    """Extract review rules from CONTRIBUTING.md content."""

    def test_extracts_review_checklist(self) -> None:
        """Detect checklist items from contributing guides."""
        content = (
            "## Code Review\n\n"
            "Before merging, ensure:\n"
            "- [ ] Tests pass\n"
            "- [ ] No lint warnings\n"
            "- [ ] Changelog updated\n"
        )
        sections = parse_contributing_guide(content)
        assert "review" in sections
        assert len(sections["review"]) >= 3

    def test_extracts_style_rules(self) -> None:
        """Detect code style requirements."""
        content = (
            "## Style Guide\n\n"
            "- Use type hints for all public functions\n"
            "- Maximum line length is 88 characters\n"
            "- Import sorting via isort\n"
        )
        sections = parse_contributing_guide(content)
        assert "style" in sections

    def test_handles_empty_content(self) -> None:
        """Empty content returns empty sections."""
        sections = parse_contributing_guide("")
        assert sections == {}

    def test_handles_no_review_section(self) -> None:
        """Content without review section returns no review key."""
        content = "# Contributing\n\nJust send a PR!\n"
        sections = parse_contributing_guide(content)
        assert "review" not in sections


class TestExtractTechniques:
    """Extract concrete review techniques from parsed guidelines."""

    def test_extracts_from_review_checklist(self) -> None:
        """Checklist items become techniques."""
        sections = {
            "review": [
                "Tests pass",
                "No lint warnings",
                "Changelog updated",
            ]
        }
        techniques = extract_techniques_from_guidelines(
            sections, source="fastapi/fastapi"
        )
        assert len(techniques) >= 1
        assert all(t.source == "fastapi/fastapi" for t in techniques)

    def test_technique_has_category(self) -> None:
        """Each technique is categorized."""
        sections = {
            "review": ["All tests must pass before merge"],
            "style": ["Use black for formatting"],
        }
        techniques = extract_techniques_from_guidelines(sections, source="test/repo")
        categories = {t.category for t in techniques}
        assert len(categories) >= 1

    def test_review_section_gets_higher_confidence(self) -> None:
        """Given a review section item, when extracted, then confidence is 0.7."""
        sections = {"review": ["Run all unit tests before merge"]}
        techniques = extract_techniques_from_guidelines(sections, source="org/repo")
        assert techniques[0].confidence == 0.7

    def test_non_review_section_gets_lower_confidence(self) -> None:
        """Given a style section item, when extracted, then confidence is 0.5."""
        sections = {"style": ["Use black for formatting"]}
        techniques = extract_techniques_from_guidelines(sections, source="org/repo")
        assert techniques[0].confidence == 0.5


class TestClassifyTechnique:
    """Classify extracted techniques into review categories."""

    @pytest.mark.parametrize(
        ("description", "expected_category"),
        [
            ("All tests must pass", "testing"),
            ("No lint warnings allowed", "linting"),
            ("Update the changelog", "documentation"),
            ("Use type hints for public functions", "style"),
            ("Check for security vulnerabilities", "security"),
            ("Be nice to reviewers", "general"),
        ],
        ids=[
            "testing",
            "linting",
            "documentation",
            "style",
            "security",
            "general-fallback",
        ],
    )
    def test_classifies_correctly(
        self, description: str, expected_category: str
    ) -> None:
        """Given a description, when classifying, then returns expected category."""
        assert classify_technique(description) == expected_category


class TestFormatDiscussion:
    """Format techniques as a GitHub Discussion post."""

    def test_includes_source_attribution(self) -> None:
        """Discussion body credits the source project."""
        techniques = [
            ReviewTechnique(
                description="Tests must pass",
                category="testing",
                source="fastapi/fastapi",
                confidence=0.9,
            )
        ]
        body = format_discussion_body(techniques)
        assert "fastapi/fastapi" in body

    def test_groups_by_category(self) -> None:
        """Techniques are grouped by category with headers."""
        techniques = [
            ReviewTechnique(
                description="Tests must pass",
                category="testing",
                source="repo/a",
                confidence=0.9,
            ),
            ReviewTechnique(
                description="Use black",
                category="style",
                source="repo/b",
                confidence=0.8,
            ),
        ]
        body = format_discussion_body(techniques)
        assert "## Testing" in body or "## testing" in body.lower()
        assert "## Style" in body or "## style" in body.lower()

    def test_includes_applicability_note(self) -> None:
        """Body includes note about human review needed."""
        techniques = [
            ReviewTechnique(
                description="Run mypy",
                category="linting",
                source="repo/x",
                confidence=0.7,
            )
        ]
        body = format_discussion_body(techniques)
        assert "review" in body.lower() or "oversight" in body.lower()

    def test_empty_techniques_returns_minimal_body(self) -> None:
        """No techniques produces a minimal note."""
        body = format_discussion_body([])
        assert "no" in body.lower() or "none" in body.lower()

    def test_includes_sources_section(self) -> None:
        """Given techniques, when formatting, then includes Sources heading."""
        techniques = [
            ReviewTechnique(
                description="Use ruff",
                category="linting",
                source="astral-sh/ruff",
            )
        ]
        body = format_discussion_body(techniques)
        assert "## Sources" in body
        assert "astral-sh/ruff" in body


class TestFetchContributingGuide:
    """Test fetching CONTRIBUTING.md from GitHub via gh api."""

    @patch("subprocess.run")
    def test_returns_decoded_content_on_success(self, mock_run: MagicMock) -> None:
        """Given gh api returns base64 content, when fetching, then decodes it."""
        raw_content = "# Contributing\n\nPlease read this guide.\n"
        encoded = base64.b64encode(raw_content.encode()).decode()
        mock_run.return_value = MagicMock(returncode=0, stdout=encoded + "\n")

        result = fetch_contributing_guide("org", "repo")

        assert result is not None
        assert "Contributing" in result
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "repos/org/repo/contents/CONTRIBUTING.md" in " ".join(cmd)

    @patch("subprocess.run")
    def test_returns_none_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        """Given gh api returns error, when fetching, then returns None."""
        mock_run.return_value = MagicMock(returncode=1)
        result = fetch_contributing_guide("org", "repo")
        assert result is None

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
    )
    def test_returns_none_on_timeout(self, mock_run: MagicMock) -> None:
        """Given gh api times out, when fetching, then returns None."""
        result = fetch_contributing_guide("org", "repo")
        assert result is None

    @patch("subprocess.run", side_effect=OSError("no gh"))
    def test_returns_none_on_os_error(self, mock_run: MagicMock) -> None:
        """Given OS error, when fetching, then returns None."""
        result = fetch_contributing_guide("org", "repo")
        assert result is None


class TestPostDiscussion:
    """Test posting a GitHub Discussion via GraphQL."""

    @patch("subprocess.run")
    def test_returns_url_on_success(self, mock_run: MagicMock) -> None:
        """Given successful GraphQL calls, when posting, then returns discussion URL."""
        repo_response = json.dumps({"data": {"repository": {"id": "R_abc123"}}})
        discussion_response = json.dumps(
            {
                "data": {
                    "createDiscussion": {
                        "discussion": {
                            "url": "https://github.com/org/repo/discussions/1"
                        }
                    }
                }
            }
        )
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=repo_response),
            MagicMock(returncode=0, stdout=discussion_response),
        ]

        url = post_discussion(
            title="Test",
            body="Body",
            category_id="CAT_123",
            repo_owner="org",
            repo_name="repo",
        )

        assert url == "https://github.com/org/repo/discussions/1"
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_returns_none_when_repo_query_fails(self, mock_run: MagicMock) -> None:
        """Given repo query fails, when posting, then returns None."""
        mock_run.return_value = MagicMock(returncode=1)
        url = post_discussion(
            title="Test",
            body="Body",
            category_id="CAT_123",
            repo_owner="org",
            repo_name="repo",
        )
        assert url is None

    @patch("subprocess.run")
    def test_returns_none_when_mutation_fails(self, mock_run: MagicMock) -> None:
        """Given mutation fails, when posting, then returns None."""
        repo_response = json.dumps({"data": {"repository": {"id": "R_abc123"}}})
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=repo_response),
            MagicMock(returncode=1),
        ]
        url = post_discussion(
            title="Test",
            body="Body",
            category_id="CAT_123",
            repo_owner="org",
            repo_name="repo",
        )
        assert url is None

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
    )
    def test_returns_none_on_timeout(self, mock_run: MagicMock) -> None:
        """Given timeout on repo query, when posting, then returns None."""
        url = post_discussion(
            title="Test",
            body="Body",
            category_id="CAT_123",
            repo_owner="org",
            repo_name="repo",
        )
        assert url is None


class TestRunScout:
    """Test the full scout pipeline."""

    @patch("scout.post_discussion", return_value="https://example.com/d/1")
    @patch("scout.fetch_contributing_guide")
    def test_returns_techniques_from_exemplars(
        self,
        mock_fetch: MagicMock,
        mock_post: MagicMock,
    ) -> None:
        """Given exemplars with contributing guides, then returns techniques."""
        mock_fetch.return_value = (
            "## Code Review\n\n"
            "- [ ] All tests must pass before merging\n"
            "- [ ] Update changelog for user-facing changes\n"
        )
        exemplars = [
            ExemplarProject(owner="org", repo="lib", language="python"),
        ]

        techniques = run_scout(
            exemplars=exemplars,
            post_to_discussions=True,
        )

        assert len(techniques) >= 1
        assert all(t.source == "org/lib" for t in techniques)
        mock_fetch.assert_called_once_with("org", "lib")
        mock_post.assert_called_once()

    @patch("scout.post_discussion")
    @patch("scout.fetch_contributing_guide", return_value=None)
    def test_skips_exemplars_without_contributing_guide(
        self,
        mock_fetch: MagicMock,
        mock_post: MagicMock,
    ) -> None:
        """Given exemplar without CONTRIBUTING.md, when scouting, then skips it."""
        exemplars = [
            ExemplarProject(owner="org", repo="no-contrib", language="python"),
        ]

        techniques = run_scout(
            exemplars=exemplars,
            post_to_discussions=True,
        )

        assert techniques == []
        mock_post.assert_not_called()

    @patch("scout.fetch_contributing_guide")
    def test_skips_discussion_posting_when_disabled(
        self, mock_fetch: MagicMock
    ) -> None:
        """Given post_to_discussions=False, when scouting, then skips posting."""
        mock_fetch.return_value = "## Testing\n\n- Run pytest before each commit\n"
        exemplars = [
            ExemplarProject(owner="org", repo="lib", language="python"),
        ]

        with patch("scout.post_discussion") as mock_post:
            techniques = run_scout(
                exemplars=exemplars,
                post_to_discussions=False,
            )

        assert len(techniques) >= 1
        mock_post.assert_not_called()

    @patch("scout.fetch_contributing_guide", return_value=None)
    def test_uses_default_exemplars_when_none_provided(
        self, mock_fetch: MagicMock
    ) -> None:
        """Given no exemplars argument, when scouting, then uses defaults."""
        run_scout(exemplars=None, post_to_discussions=False)
        assert mock_fetch.call_count == len(default_exemplars())
