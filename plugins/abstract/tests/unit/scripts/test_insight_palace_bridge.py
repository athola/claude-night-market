"""Tests for the insight-palace bridge.

Covers: score_finding, finding_to_markdown, ingest_findings,
query_palace_insights.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path so we can import the bridge
_scripts = Path(__file__).resolve().parents[3] / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

import hashlib

from insight_palace_bridge import (
    finding_to_markdown,
    ingest_findings,
    query_palace_insights,
    score_finding,
)
from insight_types import AnalysisContext, Finding

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def high_finding() -> Finding:
    """High-severity finding with related files and skill."""
    return Finding(
        type="Trend",
        severity="high",
        skill="abstract:skill-improver",
        summary="Success rate declining over 7 days",
        evidence="Dropped from 95% to 78%",
        recommendation="Investigate recent changes",
        source="trend_lens",
        related_files=["plugins/abstract/agents/skill-improver.md"],
    )


@pytest.fixture()
def info_finding() -> Finding:
    """Info-severity finding with no skill or related files."""
    return Finding(
        type="Health Check",
        severity="info",
        skill="",
        summary="3 skills unused in 30 days",
        evidence="Skills X, Y, Z had zero executions",
        recommendation="Consider deprecation",
        source="health_lens",
    )


@pytest.fixture()
def medium_finding_no_files() -> Finding:
    """Medium-severity finding with skill but no related files."""
    return Finding(
        type="Pattern",
        severity="medium",
        skill="pensive:code-reviewer",
        summary="Shared timeout pattern across 4 skills",
        evidence="Common timeout at 30s boundary",
        recommendation="Extract shared timeout config",
        source="pattern_lens",
    )


# ---------------------------------------------------------------------------
# T2: score_finding
# ---------------------------------------------------------------------------


class TestScoreFinding:
    """Score_finding applies severity mapping + bonuses."""

    def test_high_with_files_and_skill(self, high_finding: Finding) -> None:
        # high=75, +10 related_files, +5 skill = 90
        assert score_finding(high_finding) == 90

    def test_info_no_bonuses(self, info_finding: Finding) -> None:
        # info=20, no bonuses
        assert score_finding(info_finding) == 20

    def test_medium_skill_only(self, medium_finding_no_files: Finding) -> None:
        # medium=55, +5 skill = 60
        assert score_finding(medium_finding_no_files) == 60

    def test_cap_at_100(self, high_finding: Finding) -> None:
        # Manually set severity to something that would exceed 100
        high_finding.severity = "high"
        # high=75 + 10 + 5 = 90, within cap
        assert score_finding(high_finding) <= 100

    def test_unknown_severity_defaults_to_zero(self) -> None:
        f = Finding(
            type="Bug Alert",
            severity="unknown",
            skill="",
            summary="test",
            evidence="",
            recommendation="",
            source="test",
        )
        assert score_finding(f) == 0

    def test_low_with_files(self) -> None:
        f = Finding(
            type="Improvement",
            severity="low",
            skill="",
            summary="test",
            evidence="",
            recommendation="",
            source="test",
            related_files=["a.py"],
        )
        # low=35 + 10 files = 45
        assert score_finding(f) == 45


# ---------------------------------------------------------------------------
# T1: AnalysisContext palace_insights field
# ---------------------------------------------------------------------------


class TestAnalysisContextExtension:
    """AnalysisContext has a palace_insights field."""

    def test_default_empty_list(self) -> None:
        ctx = AnalysisContext(
            metrics={},
            previous_snapshot=None,
            performance_history=None,
            improvement_memory=None,
        )
        assert ctx.palace_insights == []

    def test_accepts_palace_insights(self) -> None:
        data = [{"title": "test", "severity": "high"}]
        ctx = AnalysisContext(
            metrics={},
            previous_snapshot=None,
            performance_history=None,
            improvement_memory=None,
            palace_insights=data,
        )
        assert ctx.palace_insights == data


# ---------------------------------------------------------------------------
# T3: finding_to_markdown
# ---------------------------------------------------------------------------


class TestFindingToMarkdown:
    """finding_to_markdown produces frontmatter + body."""

    def test_has_yaml_frontmatter(self, high_finding: Finding) -> None:
        md = finding_to_markdown(high_finding)
        assert md.startswith("---\n")
        assert "\n---\n" in md[4:]  # closing frontmatter

    def test_frontmatter_source(self, high_finding: Finding) -> None:
        md = finding_to_markdown(high_finding)
        assert "source: insight-engine" in md

    def test_frontmatter_fields(self, high_finding: Finding) -> None:
        md = finding_to_markdown(high_finding)
        assert "finding_type: Trend" in md
        assert "severity: high" in md
        assert 'skill: "abstract:skill-improver"' in md
        assert "finding_hash:" in md
        assert "importance_score: 90" in md

    def test_body_sections(self, high_finding: Finding) -> None:
        md = finding_to_markdown(high_finding)
        assert "## Finding" in md
        assert "## Evidence" in md
        assert "## Recommended Action" in md
        assert "## Related Files" in md

    def test_no_skill_omits_skill_line(self, info_finding: Finding) -> None:
        md = finding_to_markdown(info_finding)
        assert "skill:" not in md.split("---")[1]

    def test_no_related_files_omits_section(self, info_finding: Finding) -> None:
        md = finding_to_markdown(info_finding)
        assert "## Related Files" not in md


# ---------------------------------------------------------------------------
# T4: ingest_findings
# ---------------------------------------------------------------------------


class TestIngestFindings:
    """ingest_findings writes staging files and updates index."""

    def test_returns_zero_when_no_palace(self, high_finding: Finding) -> None:
        with patch("insight_palace_bridge._HAS_PALACE", False):
            assert ingest_findings([high_finding]) == 0

    def test_returns_zero_when_empty(self) -> None:
        assert ingest_findings([]) == 0

    def test_skips_when_budget_low(self, high_finding: Finding) -> None:
        assert ingest_findings([high_finding], budget_remaining=0.5) == 0

    def test_ingests_finding_to_staging(
        self, high_finding: Finding, tmp_path: Path
    ) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch("insight_palace_bridge._PALACE_STAGING", staging),
            patch("insight_palace_bridge.is_known", return_value=False),
            patch(
                "insight_palace_bridge.get_content_hash",
                return_value="sha256:abc123",
            ),
            patch("insight_palace_bridge.update_index") as mock_idx,
        ):
            count = ingest_findings([high_finding])

        assert count == 1
        files = list(staging.glob("insight-*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "source: insight-engine" in content
        mock_idx.assert_called_once()
        call_kwargs = mock_idx.call_args
        assert call_kwargs[1]["maturity"] == "seedling"
        assert call_kwargs[1]["routing_type"] == "meta"
        assert "insight://" in call_kwargs[1]["url"]

    def test_skips_known_findings(self, high_finding: Finding, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch("insight_palace_bridge._PALACE_STAGING", staging),
            patch("insight_palace_bridge.is_known", return_value=True),
        ):
            count = ingest_findings([high_finding])

        assert count == 0
        assert len(list(staging.glob("*.md"))) == 0

    def test_caps_at_10_findings(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        findings = [
            Finding(
                type="Trend",
                severity="low",
                skill=f"skill-{i}",
                summary=f"finding {i}",
                evidence="",
                recommendation="",
                source="test",
            )
            for i in range(15)
        ]

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch("insight_palace_bridge._PALACE_STAGING", staging),
            patch("insight_palace_bridge.is_known", return_value=False),
            patch(
                "insight_palace_bridge.get_content_hash",
                return_value="sha256:x",
            ),
            patch("insight_palace_bridge.update_index"),
        ):
            count = ingest_findings(findings)

        assert count == 10


# ---------------------------------------------------------------------------
# T5: query_palace_insights
# ---------------------------------------------------------------------------


class TestQueryPalaceInsights:
    """query_palace_insights reads insight entries from index."""

    def test_returns_empty_when_no_palace(self) -> None:
        with patch("insight_palace_bridge._HAS_PALACE", False):
            assert query_palace_insights() == []

    def test_filters_insight_entries(self) -> None:
        mock_index = {
            "entries": {
                "insight://abc123": {
                    "title": "[Trend] test finding",
                    "importance_score": 75,
                    "last_updated": "2026-04-13T00:00:00Z",
                    "maturity": "seedling",
                    "finding_type": "Trend",
                    "severity": "high",
                    "skill": "abstract:test",
                },
                "https://example.com": {
                    "title": "Not an insight",
                    "importance_score": 50,
                },
            },
            "hashes": {},
        }

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch(
                "insight_palace_bridge._load_index",
                return_value=mock_index,
            ),
        ):
            results = query_palace_insights()

        assert len(results) == 1
        assert results[0]["key"] == "insight://abc123"
        assert results[0]["title"] == "[Trend] test finding"
        assert results[0]["severity"] == "high"

    def test_returns_empty_on_exception(self) -> None:
        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch(
                "insight_palace_bridge._load_index",
                side_effect=RuntimeError("broken"),
            ),
        ):
            assert query_palace_insights() == []


# ---------------------------------------------------------------------------
# T8: Integration (round-trip ingest then query)
# ---------------------------------------------------------------------------


class TestIntegrationRoundTrip:
    """End-to-end: ingest findings, then query them back."""

    def test_ingest_then_query_round_trip(
        self,
        high_finding: Finding,
        info_finding: Finding,
        medium_finding_no_files: Finding,
        tmp_path: Path,
    ) -> None:
        """Scenario: Ingest 3 findings, then query returns all 3.
        Given 3 findings of different types/severities
        When ingest_findings writes them to staging
        And the index is populated
        Then query_palace_insights returns 3 entries
        And each entry has correct metadata
        """

        staging = tmp_path / "staging"
        staging.mkdir()

        # Use a real in-memory index instead of mocks
        index_state: dict = {"entries": {}, "hashes": {}}

        def fake_is_known(
            content_hash=None,
            url=None,
            path=None,
        ):
            if url and url in index_state["entries"]:
                return True
            return False

        def fake_get_content_hash(content):
            if isinstance(content, str):
                content = content.encode()
            return f"sha256:{hashlib.sha256(content).hexdigest()[:16]}"

        def fake_update_index(*, content_hash, stored_at, importance_score, **fields):
            key = fields.get("url") or fields.get("path")
            index_state["entries"][key] = {
                "content_hash": content_hash,
                "stored_at": stored_at,
                "importance_score": importance_score,
                "title": fields.get("title"),
                "maturity": fields.get("maturity"),
                "routing_type": fields.get("routing_type"),
            }

        findings = [high_finding, info_finding, medium_finding_no_files]

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch("insight_palace_bridge._PALACE_STAGING", staging),
            patch("insight_palace_bridge.is_known", side_effect=fake_is_known),
            patch(
                "insight_palace_bridge.get_content_hash",
                side_effect=fake_get_content_hash,
            ),
            patch(
                "insight_palace_bridge.update_index",
                side_effect=fake_update_index,
            ),
        ):
            count = ingest_findings(findings)

        # All 3 ingested
        assert count == 3
        assert len(list(staging.glob("insight-*.md"))) == 3

        # Verify staging files have frontmatter
        for md_file in staging.glob("insight-*.md"):
            content = md_file.read_text()
            assert content.startswith("---\n")
            assert "source: insight-engine" in content

        # Verify index entries use insight:// keys
        insight_keys = [k for k in index_state["entries"] if k.startswith("insight://")]
        assert len(insight_keys) == 3

        # Now query: mock _load_index to return our state
        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch(
                "insight_palace_bridge._load_index",
                return_value=index_state,
            ),
        ):
            results = query_palace_insights()

        assert len(results) == 3
        titles = {r["title"] for r in results}
        assert any("Trend" in t for t in titles)
        assert any("Health Check" in t for t in titles)
        assert any("Pattern" in t for t in titles)

        # Verify scores
        scores = {r["title"]: r["importance_score"] for r in results}
        for title, score in scores.items():
            if "Trend" in title:
                assert score == 90  # high + files + skill
            elif "Health Check" in title:
                assert score == 20  # info, no bonuses
            elif "Pattern" in title:
                assert score == 60  # medium + skill

    def test_dedup_prevents_double_ingest(
        self,
        high_finding: Finding,
        tmp_path: Path,
    ) -> None:
        """Scenario: Same finding ingested twice is skipped.
        Given a finding already in the index
        When ingest_findings is called again
        Then it returns 0 (skipped)
        """

        staging = tmp_path / "staging"
        staging.mkdir()

        with (
            patch("insight_palace_bridge._HAS_PALACE", True),
            patch("insight_palace_bridge._PALACE_STAGING", staging),
            patch("insight_palace_bridge.is_known", return_value=True),
        ):
            count = ingest_findings([high_finding])

        assert count == 0
