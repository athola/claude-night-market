"""Tests for src/abstract/skills_eval/auditor.py.

Feature: Skills auditing
    As a developer
    I want all branches of the SkillsAuditor tested
    So that skill quality scoring and reporting work correctly
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from abstract.skills_eval.auditor import (
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_GOOD,
    SCORE_WELL_STRUCTURED,
    SkillMetrics,
    SkillsAuditor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_SKILL = (
    "---\n"
    "name: test-skill\n"
    "description: A test skill\n"
    "---\n\n"
    "# Test Skill\n\n"
    "## Overview\nAn overview.\n\n"
    "## Quick Start\nRun it.\n"
)

FULL_SKILL = (
    "---\n"
    "name: full-skill\n"
    "description: A complete skill\n"
    "category: testing\n"
    "tags: [test]\n"
    "dependencies: []\n"
    "---\n\n"
    "# Full Skill\n\n"
    "## Overview\nOverview.\n\n"
    "## Quick Start\nStart here.\n\n"
    "## Examples\nSee below.\n\n"
    "## Resources\nLinks.\n\n"
    "## Troubleshooting\nFix it.\n\n"
    "```python\nprint('hello')\n```\n\n"
    "```bash\necho hi\n```\n\n"
    "```python\nrun()\n```\n\n"
    "1. Step one\n2. Step two\n3. Step three\n"
)


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Given a skills directory with two SKILL.md files."""
    for name, content in [("skill-a", MINIMAL_SKILL), ("skill-b", FULL_SKILL)]:
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(content)
    return tmp_path


@pytest.fixture
def empty_skills_dir(tmp_path: Path) -> Path:
    """Given an empty skills directory with no SKILL.md files."""
    return tmp_path


@pytest.fixture
def single_skill_dir(tmp_path: Path) -> Path:
    """Given a skills directory with a single minimal skill."""
    d = tmp_path / "my-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(MINIMAL_SKILL)
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: SkillMetrics dataclass
# ---------------------------------------------------------------------------


class TestSkillMetrics:
    """Feature: SkillMetrics stores skill assessment data."""

    @pytest.mark.unit
    def test_skill_metrics_creation(self) -> None:
        """Scenario: SkillMetrics can be created with all fields."""
        m = SkillMetrics(
            name="my-skill",
            path="/path/to/SKILL.md",
            score=75.0,
            issues=["issue1"],
            strengths=["strength1"],
            token_count=500,
            completeness_score=80.0,
            structure_score=70.0,
            documentation_score=75.0,
        )
        assert m.name == "my-skill"
        assert m.score == 75.0
        assert m.issues == ["issue1"]
        assert m.strengths == ["strength1"]
        assert m.token_count == 500


# ---------------------------------------------------------------------------
# Tests: SkillsAuditor.__init__ and properties
# ---------------------------------------------------------------------------


class TestSkillsAuditorInit:
    """Feature: SkillsAuditor initializes with correct attributes."""

    @pytest.mark.unit
    def test_init_sets_skills_dir(self, tmp_path: Path) -> None:
        """Scenario: Constructor sets skills_dir and skills_root."""
        auditor = SkillsAuditor(tmp_path)
        assert auditor.skills_dir == tmp_path
        assert auditor.skills_root == tmp_path

    @pytest.mark.unit
    def test_audit_metrics_loaded(self, tmp_path: Path) -> None:
        """Scenario: audit_metrics contains required keys."""
        auditor = SkillsAuditor(tmp_path)
        assert "scoring_weights" in auditor.audit_metrics
        assert "required_fields" in auditor.audit_metrics
        assert "required_sections" in auditor.audit_metrics
        assert "token_optimal" in auditor.audit_metrics

    @pytest.mark.unit
    def test_skill_files_property_empty_dir(self, empty_skills_dir: Path) -> None:
        """Scenario: skill_files returns empty list for empty directory."""
        auditor = SkillsAuditor(empty_skills_dir)
        assert auditor.skill_files == []

    @pytest.mark.unit
    def test_skill_files_property_with_skills(self, skills_dir: Path) -> None:
        """Scenario: skill_files returns SKILL.md paths."""
        auditor = SkillsAuditor(skills_dir)
        files = auditor.skill_files
        assert len(files) == 2
        assert all(f.name == "SKILL.md" for f in files)


# ---------------------------------------------------------------------------
# Tests: audit_skills
# ---------------------------------------------------------------------------


class TestAuditSkills:
    """Feature: audit_skills returns summary of all skills."""

    @pytest.mark.unit
    def test_empty_dir_returns_zero_total(self, empty_skills_dir: Path) -> None:
        """Scenario: Empty directory returns 0 total_skills."""
        auditor = SkillsAuditor(empty_skills_dir)
        result = auditor.audit_skills()
        assert result["total_skills"] == 0
        assert result["average_score"] == 0.0
        assert result["well_structured"] == 0
        assert result["needs_improvement"] == 0
        assert "No skills found" in result["recommendations"][0]

    @pytest.mark.unit
    def test_with_skills_returns_correct_count(self, skills_dir: Path) -> None:
        """Scenario: Directory with skills returns correct total."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_skills()
        assert result["total_skills"] == 2
        assert "skill_metrics" in result
        assert len(result["skill_metrics"]) == 2

    @pytest.mark.unit
    def test_average_score_is_float(self, skills_dir: Path) -> None:
        """Scenario: average_score is a float between 0 and 100."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_skills()
        assert isinstance(result["average_score"], float)
        assert 0.0 <= result["average_score"] <= 100.0

    @pytest.mark.unit
    def test_well_structured_count_is_correct(self, skills_dir: Path) -> None:
        """Scenario: well_structured counts skills meeting SCORE_WELL_STRUCTURED."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_skills()
        metrics = result["skill_metrics"]
        expected = sum(1 for m in metrics if m.score >= SCORE_WELL_STRUCTURED)
        assert result["well_structured"] == expected

    @pytest.mark.unit
    def test_needs_improvement_count(self, skills_dir: Path) -> None:
        """Scenario: needs_improvement counts skills below SCORE_ACCEPTABLE."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_skills()
        metrics = result["skill_metrics"]
        expected = sum(1 for m in metrics if m.score < SCORE_ACCEPTABLE)
        assert result["needs_improvement"] == expected


# ---------------------------------------------------------------------------
# Tests: _analyze_skill_file
# ---------------------------------------------------------------------------


class TestAnalyzeSkillFile:
    """Feature: _analyze_skill_file produces correct SkillMetrics."""

    @pytest.mark.unit
    def test_analyze_returns_skill_metrics(self, single_skill_dir: Path) -> None:
        """Scenario: _analyze_skill_file returns a SkillMetrics instance."""
        auditor = SkillsAuditor(single_skill_dir)
        skill_file = single_skill_dir / "my-skill" / "SKILL.md"
        result = auditor._analyze_skill_file(skill_file)
        assert isinstance(result, SkillMetrics)

    @pytest.mark.unit
    def test_analyze_uses_frontmatter_name(self, single_skill_dir: Path) -> None:
        """Scenario: name field comes from frontmatter when present."""
        auditor = SkillsAuditor(single_skill_dir)
        skill_file = single_skill_dir / "my-skill" / "SKILL.md"
        result = auditor._analyze_skill_file(skill_file)
        assert result.name == "test-skill"

    @pytest.mark.unit
    def test_analyze_falls_back_to_dir_name(self, tmp_path: Path) -> None:
        """Scenario: name falls back to parent dir name when frontmatter has no name."""
        d = tmp_path / "fallback-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("No frontmatter here.\n")
        auditor = SkillsAuditor(tmp_path)
        result = auditor._analyze_skill_file(d / "SKILL.md")
        assert result.name == "fallback-skill"

    @pytest.mark.unit
    def test_analyze_unreadable_file_returns_error_metrics(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Unreadable file returns SkillMetrics with error issue."""
        d = tmp_path / "bad-skill"
        d.mkdir()
        skill_file = d / "SKILL.md"
        skill_file.write_text("content")
        auditor = SkillsAuditor(tmp_path)
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = auditor._analyze_skill_file(skill_file)
        assert result.score == 0.0
        assert any("Error reading" in issue for issue in result.issues)

    @pytest.mark.unit
    def test_analyze_score_between_0_and_100(self, single_skill_dir: Path) -> None:
        """Scenario: Overall score is always within [0, 100]."""
        auditor = SkillsAuditor(single_skill_dir)
        skill_file = single_skill_dir / "my-skill" / "SKILL.md"
        result = auditor._analyze_skill_file(skill_file)
        assert 0.0 <= result.score <= 100.0


# ---------------------------------------------------------------------------
# Tests: _calculate_completeness_score
# ---------------------------------------------------------------------------


class TestCalculateCompletenessScore:
    """Feature: _calculate_completeness_score scores frontmatter completeness."""

    @pytest.mark.unit
    def test_all_fields_present_returns_high_score(self, tmp_path: Path) -> None:
        """Scenario: All required and recommended fields yield high score."""
        auditor = SkillsAuditor(tmp_path)
        frontmatter = {
            "name": "my-skill",
            "description": "desc",
            "category": "test",
            "tags": ["a"],
            "dependencies": [],
        }
        score = auditor._calculate_completeness_score(frontmatter, "")
        assert score > 80.0

    @pytest.mark.unit
    def test_empty_frontmatter_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Empty frontmatter yields 0 score."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_completeness_score({}, "")
        assert score == 0.0

    @pytest.mark.unit
    def test_none_value_fields_not_counted(self, tmp_path: Path) -> None:
        """Scenario: Fields present but None are not counted."""
        auditor = SkillsAuditor(tmp_path)
        frontmatter = {"name": None, "description": None}
        score = auditor._calculate_completeness_score(frontmatter, "")
        assert score == 0.0

    @pytest.mark.unit
    def test_required_only_partial_score(self, tmp_path: Path) -> None:
        """Scenario: Only required fields gives partial score."""
        auditor = SkillsAuditor(tmp_path)
        frontmatter = {"name": "skill", "description": "desc"}
        score = auditor._calculate_completeness_score(frontmatter, "")
        assert 0.0 < score < 100.0


# ---------------------------------------------------------------------------
# Tests: _calculate_structure_score
# ---------------------------------------------------------------------------


class TestCalculateStructureScore:
    """Feature: _calculate_structure_score measures content structure."""

    @pytest.mark.unit
    def test_full_structure_yields_high_score(self, tmp_path: Path) -> None:
        """Scenario: All required and recommended sections yield high score."""
        auditor = SkillsAuditor(tmp_path)
        content = (
            "## Overview\n## Quick Start\n## Examples\n"
            "## Resources\n## Troubleshooting\n"
            "# h1\n## h2\n## h3\n## h4\n"
        )
        score = auditor._calculate_structure_score(content)
        assert score > 75.0

    @pytest.mark.unit
    def test_empty_content_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Empty content yields 0 score."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_structure_score("")
        assert score == 0.0

    @pytest.mark.unit
    def test_headings_bonus_applied(self, tmp_path: Path) -> None:
        """Scenario: Content with 4+ headings gets bonus points."""
        auditor = SkillsAuditor(tmp_path)
        many_headings = "## Overview\n## Quick Start\n## H3\n## H4\n## H5\n"
        score_many = auditor._calculate_structure_score(many_headings)
        few_headings = "## Overview\n## Quick Start\n"
        score_few = auditor._calculate_structure_score(few_headings)
        assert score_many >= score_few


# ---------------------------------------------------------------------------
# Tests: _calculate_documentation_score
# ---------------------------------------------------------------------------


class TestCalculateDocumentationScore:
    """Feature: _calculate_documentation_score measures docs quality."""

    @pytest.mark.unit
    def test_full_docs_scores_100(self, tmp_path: Path) -> None:
        """Scenario: 3+ code blocks, 3+ numbered steps, examples = max score."""
        auditor = SkillsAuditor(tmp_path)
        content = (
            "## Examples\n"
            "```python\ncode\n```\n"
            "```bash\ncode\n```\n"
            "```python\nmore\n```\n"
            "1. Step one\n2. Step two\n3. Step three\n"
        )
        score = auditor._calculate_documentation_score(content)
        assert score == 100.0

    @pytest.mark.unit
    def test_no_docs_returns_zero_unless_example_word(self, tmp_path: Path) -> None:
        """Scenario: Content with no code blocks or lists scores low."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_documentation_score("Just some text.")
        # 'example' not in text, no code blocks, no numbered list
        assert score == 0.0

    @pytest.mark.unit
    def test_example_word_adds_points(self, tmp_path: Path) -> None:
        """Scenario: Content containing 'example' gets documentation points."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_documentation_score("See this example.")
        assert score == 25.0

    @pytest.mark.unit
    def test_one_code_block_adds_25(self, tmp_path: Path) -> None:
        """Scenario: Single code block pair adds 25 points."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_documentation_score("```python\ncode\n```\n")
        assert score >= 25.0


# ---------------------------------------------------------------------------
# Tests: _calculate_token_score
# ---------------------------------------------------------------------------


class TestCalculateTokenScore:
    """Feature: _calculate_token_score returns correct efficiency score."""

    @pytest.mark.unit
    def test_within_optimal_returns_100(self, tmp_path: Path) -> None:
        """Scenario: Token count at or below optimal returns 100."""
        auditor = SkillsAuditor(tmp_path)
        assert auditor._calculate_token_score(100) == 100
        assert auditor._calculate_token_score(1500) == 100

    @pytest.mark.unit
    def test_between_optimal_and_acceptable_returns_80(self, tmp_path: Path) -> None:
        """Scenario: Token count between optimal and acceptable returns 80."""
        auditor = SkillsAuditor(tmp_path)
        assert auditor._calculate_token_score(2000) == 80

    @pytest.mark.unit
    def test_above_acceptable_returns_reduced_score(self, tmp_path: Path) -> None:
        """Scenario: Very high token count returns reduced (minimum 20) score."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_token_score(10000)
        assert score >= 20
        assert score < 80

    @pytest.mark.unit
    def test_extreme_token_count_floors_at_20(self, tmp_path: Path) -> None:
        """Scenario: Extreme token count floors at 20."""
        auditor = SkillsAuditor(tmp_path)
        score = auditor._calculate_token_score(1_000_000)
        assert score == 20


# ---------------------------------------------------------------------------
# Tests: _generate_issues
# ---------------------------------------------------------------------------


class TestGenerateIssues:
    """Feature: _generate_issues identifies skill problems."""

    @pytest.mark.unit
    def test_missing_frontmatter_issue(self, tmp_path: Path) -> None:
        """Scenario: Content without frontmatter gets 'Missing YAML' issue."""
        auditor = SkillsAuditor(tmp_path)
        issues = auditor._generate_issues({}, "No frontmatter content.", 100)
        assert any("Missing YAML frontmatter" in i for i in issues)

    @pytest.mark.unit
    def test_missing_required_field_reported(self, tmp_path: Path) -> None:
        """Scenario: Missing required field appears in issues."""
        auditor = SkillsAuditor(tmp_path)
        issues = auditor._generate_issues(
            {"name": "x"},  # missing 'description'
            "---\nname: x\n---\ncontent",
            100,
        )
        assert any("description" in i for i in issues)

    @pytest.mark.unit
    def test_missing_recommended_field_reported(self, tmp_path: Path) -> None:
        """Scenario: Missing recommended field appears in issues."""
        auditor = SkillsAuditor(tmp_path)
        issues = auditor._generate_issues(
            {"name": "x", "description": "d"},
            "---\nname: x\ndescription: d\n---\ncontent",
            100,
        )
        assert any("category" in i or "tags" in i for i in issues)

    @pytest.mark.unit
    def test_compact_convention_not_flagged_for_overview(self, tmp_path: Path) -> None:
        """Scenario: A skill using the compact paragraph-after-H1 convention
        (no '## Overview' heading, but content present) should not be flagged
        with a 'Missing required section: Overview' issue.

        Background: 7 cartograph and 14 archetypes skills follow this style
        intentionally; the previous schema treated this as a bug.
        """
        auditor = SkillsAuditor(tmp_path)
        compact_content = (
            "---\nname: x\ndescription: d\n---\n\n"
            "# X\n\n"
            "A short intro paragraph that describes what the skill does.\n\n"
            "## When To Use\n\n- Foo\n- Bar\n\n"
            "## Workflow\n\n"
            "1. Step one\n2. Step two\n3. Step three\n\n"
            "```bash\necho hello\n```\n"
        )
        issues = auditor._generate_issues(
            {"name": "x", "description": "d"}, compact_content, 100
        )
        assert not any("required section: Overview" in i for i in issues), (
            f"Compact convention skills should not be flagged: {issues}"
        )

    @pytest.mark.unit
    def test_high_token_count_reported(self, tmp_path: Path) -> None:
        """Scenario: Token count above acceptable limit triggers issue."""
        auditor = SkillsAuditor(tmp_path)
        issues = auditor._generate_issues(
            {"name": "x", "description": "d"},
            "---\nname: x\ndescription: d\n---\ncontent",
            5000,
        )
        assert any("token" in i.lower() for i in issues)

    @pytest.mark.unit
    def test_missing_code_examples_reported(self, tmp_path: Path) -> None:
        """Scenario: No code blocks triggers missing examples issue."""
        auditor = SkillsAuditor(tmp_path)
        issues = auditor._generate_issues(
            {"name": "x", "description": "d"},
            "---\nname: x\ndescription: d\n---\ncontent",
            100,
        )
        assert any("code" in i.lower() for i in issues)

    @pytest.mark.unit
    def test_explicitly_configured_required_section_reported(
        self, tmp_path: Path
    ) -> None:
        """Scenario: When required_sections is explicitly populated (e.g. via
        config), missing sections still appear as issues.

        Background: 2026-04-25 schema change moved Overview/Quick Start to
        recommended; this test guards the still-functional required-section
        path for opt-in stricter scoring.
        """
        auditor = SkillsAuditor(tmp_path)
        auditor.audit_metrics["required_sections"] = ["Custom"]
        issues = auditor._generate_issues(
            {"name": "x", "description": "d"},
            "---\nname: x\ndescription: d\n---\ncontent",
            100,
        )
        assert any("Custom" in i for i in issues)


# ---------------------------------------------------------------------------
# Tests: _generate_strengths
# ---------------------------------------------------------------------------


class TestGenerateStrengths:
    """Feature: _generate_strengths identifies skill qualities."""

    @pytest.mark.unit
    def test_excellent_completeness_strength(self, tmp_path: Path) -> None:
        """Scenario: Excellent completeness score adds strength."""
        auditor = SkillsAuditor(tmp_path)
        strengths = auditor._generate_strengths(SCORE_EXCELLENT, 50, 50, 100)
        assert any("completeness" in s.lower() for s in strengths)

    @pytest.mark.unit
    def test_good_completeness_strength(self, tmp_path: Path) -> None:
        """Scenario: Good completeness score adds 'Good' strength."""
        auditor = SkillsAuditor(tmp_path)
        strengths = auditor._generate_strengths(SCORE_GOOD, 50, 50, 100)
        assert any("Good" in s for s in strengths)

    @pytest.mark.unit
    def test_excellent_structure_strength(self, tmp_path: Path) -> None:
        """Scenario: Excellent structure score adds structure strength."""
        auditor = SkillsAuditor(tmp_path)
        strengths = auditor._generate_strengths(50, SCORE_EXCELLENT, 50, 100)
        assert any("structure" in s.lower() for s in strengths)

    @pytest.mark.unit
    def test_excellent_documentation_strength(self, tmp_path: Path) -> None:
        """Scenario: Excellent documentation score adds documentation strength."""
        auditor = SkillsAuditor(tmp_path)
        strengths = auditor._generate_strengths(50, 50, SCORE_EXCELLENT, 100)
        assert any("documentation" in s.lower() for s in strengths)

    @pytest.mark.unit
    def test_optimal_token_count_strength(self, tmp_path: Path) -> None:
        """Scenario: Token count within optimal limit adds efficiency strength."""
        auditor = SkillsAuditor(tmp_path)
        optimal = auditor.audit_metrics["token_optimal"]
        strengths = auditor._generate_strengths(50, 50, 50, optimal)
        assert any("token" in s.lower() or "efficiency" in s.lower() for s in strengths)

    @pytest.mark.unit
    def test_acceptable_token_count_strength(self, tmp_path: Path) -> None:
        """Scenario: Token count in acceptable range adds 'Acceptable' strength."""
        auditor = SkillsAuditor(tmp_path)
        acceptable = auditor.audit_metrics["token_acceptable"] - 1
        strengths = auditor._generate_strengths(50, 50, 50, acceptable)
        assert any("Acceptable" in s for s in strengths)

    @pytest.mark.unit
    def test_low_scores_return_no_strengths(self, tmp_path: Path) -> None:
        """Scenario: Low scores across all dimensions yield empty strengths."""
        auditor = SkillsAuditor(tmp_path)
        strengths = auditor._generate_strengths(10, 10, 10, 999999)
        assert strengths == []


# ---------------------------------------------------------------------------
# Tests: _generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    """Feature: _generate_recommendations returns actionable advice."""

    @pytest.mark.unit
    def test_empty_metrics_returns_empty_list(self, tmp_path: Path) -> None:
        """Scenario: Empty metrics list returns empty recommendations."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor._generate_recommendations([])
        assert result == []

    @pytest.mark.unit
    def test_low_completeness_triggers_recommendations(self, tmp_path: Path) -> None:
        """Scenario: Low completeness average generates frontmatter recommendations."""
        auditor = SkillsAuditor(tmp_path)
        metrics = [
            SkillMetrics(
                name="s",
                path="p",
                score=50.0,
                issues=[],
                strengths=[],
                token_count=100,
                completeness_score=20.0,
                structure_score=80.0,
                documentation_score=80.0,
            )
        ]
        recs = auditor._generate_recommendations(metrics)
        assert any("frontmatter" in r.lower() or "name" in r.lower() for r in recs)

    @pytest.mark.unit
    def test_low_structure_triggers_recommendations(self, tmp_path: Path) -> None:
        """Scenario: Low structure average generates structure recommendations."""
        auditor = SkillsAuditor(tmp_path)
        metrics = [
            SkillMetrics(
                name="s",
                path="p",
                score=50.0,
                issues=[],
                strengths=[],
                token_count=100,
                completeness_score=80.0,
                structure_score=20.0,
                documentation_score=80.0,
            )
        ]
        recs = auditor._generate_recommendations(metrics)
        assert any("structure" in r.lower() for r in recs)

    @pytest.mark.unit
    def test_high_token_usage_triggers_recommendations(self, tmp_path: Path) -> None:
        """Scenario: High average token count generates optimization recommendations."""
        auditor = SkillsAuditor(tmp_path)
        token_acceptable = auditor.audit_metrics["token_acceptable"]
        metrics = [
            SkillMetrics(
                name="s",
                path="p",
                score=50.0,
                issues=[],
                strengths=[],
                token_count=token_acceptable + 1000,
                completeness_score=80.0,
                structure_score=80.0,
                documentation_score=80.0,
            )
        ]
        recs = auditor._generate_recommendations(metrics)
        assert any("token" in r.lower() or "optim" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# Tests: audit_all_skills (legacy method)
# ---------------------------------------------------------------------------


class TestAuditAllSkills:
    """Feature: audit_all_skills returns legacy-compatible structure."""

    @pytest.mark.unit
    def test_returns_skills_list(self, skills_dir: Path) -> None:
        """Scenario: audit_all_skills returns a 'skills' key with list."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_all_skills()
        assert "skills" in result
        assert isinstance(result["skills"], list)

    @pytest.mark.unit
    def test_returns_summary(self, skills_dir: Path) -> None:
        """Scenario: audit_all_skills returns a 'summary' key with metrics."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_all_skills()
        assert "summary" in result
        summary = result["summary"]
        assert "average_completeness" in summary
        assert "average_overall" in summary
        assert "skills_needing_improvement" in summary
        assert "high_priority_issues" in summary

    @pytest.mark.unit
    def test_empty_dir_summary_zeros(self, empty_skills_dir: Path) -> None:
        """Scenario: Empty directory results in zero-value summary."""
        auditor = SkillsAuditor(empty_skills_dir)
        result = auditor.audit_all_skills()
        assert result["summary"]["average_overall"] == 0.0
        assert result["summary"]["skills_needing_improvement"] == 0

    @pytest.mark.unit
    def test_skills_have_issues_key(self, skills_dir: Path) -> None:
        """Scenario: Each skill in 'skills' list has 'issues' as list of dicts."""
        auditor = SkillsAuditor(skills_dir)
        result = auditor.audit_all_skills()
        for skill in result["skills"]:
            assert "issues" in skill
            for issue in skill["issues"]:
                assert "type" in issue
                assert "description" in issue


# ---------------------------------------------------------------------------
# Tests: audit_skill
# ---------------------------------------------------------------------------


class TestAuditSkill:
    """Feature: audit_skill audits a single skill by name."""

    @pytest.mark.unit
    def test_skill_not_found_returns_error(self, empty_skills_dir: Path) -> None:
        """Scenario: Missing skill returns error dict."""
        auditor = SkillsAuditor(empty_skills_dir)
        result = auditor.audit_skill("nonexistent")
        assert "error" in result
        assert result["overall_score"] == 0

    @pytest.mark.unit
    def test_existing_skill_returns_scores(self, single_skill_dir: Path) -> None:
        """Scenario: Existing skill returns dict with all score fields."""
        auditor = SkillsAuditor(single_skill_dir)
        result = auditor.audit_skill("my-skill")
        assert "overall_score" in result
        assert "completeness_score" in result
        assert "structure_score" in result
        assert "documentation_score" in result
        assert "token_count" in result

    @pytest.mark.unit
    def test_typed_issues_returned(self, tmp_path: Path) -> None:
        """Scenario: Issues are returned as typed dicts with 'type' key."""
        d = tmp_path / "bare-skill"
        d.mkdir()
        # Write a skill that will have issues
        (d / "SKILL.md").write_text("No frontmatter at all.\n")
        auditor = SkillsAuditor(tmp_path)
        result = auditor.audit_skill("bare-skill")
        for issue in result["issues"]:
            assert "type" in issue
            assert "description" in issue

    @pytest.mark.unit
    def test_issue_type_size_large_for_token_issue(self, tmp_path: Path) -> None:
        """Scenario: Token usage issue gets 'size_large' type."""
        d = tmp_path / "big-skill"
        d.mkdir()
        # Create skill with lots of tokens
        big_content = "---\nname: big\ndescription: big skill\n---\n\n" + "word " * 5000
        (d / "SKILL.md").write_text(big_content)
        auditor = SkillsAuditor(tmp_path)
        result = auditor.audit_skill("big-skill")
        types = [i["type"] for i in result["issues"]]
        assert "size_large" in types

    @pytest.mark.unit
    def test_issue_type_missing_description(self, tmp_path: Path) -> None:
        """Scenario: Missing description issue gets 'missing_description' type."""
        d = tmp_path / "nodesc-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: nodesc\n---\ncontent\n")
        auditor = SkillsAuditor(tmp_path)
        result = auditor.audit_skill("nodesc-skill")
        types = [i["type"] for i in result["issues"]]
        assert "missing_description" in types


# ---------------------------------------------------------------------------
# Tests: generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Feature: generate_report produces markdown report string."""

    @pytest.mark.unit
    def test_report_contains_header(self, skills_dir: Path) -> None:
        """Scenario: Report starts with Skills Audit Report header."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        report = auditor.generate_report(audit_results)
        assert "# Skills Audit Report" in report

    @pytest.mark.unit
    def test_report_contains_total_skills(self, skills_dir: Path) -> None:
        """Scenario: Report includes total skills count."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        report = auditor.generate_report(audit_results)
        assert "Total Skills" in report

    @pytest.mark.unit
    def test_report_with_summary_includes_averages(self, skills_dir: Path) -> None:
        """Scenario: Report includes average scores when summary present."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        report = auditor.generate_report(audit_results)
        assert "Average Completeness" in report
        assert "Average Overall" in report

    @pytest.mark.unit
    def test_report_lists_skills(self, skills_dir: Path) -> None:
        """Scenario: Report contains skill names in Skills section."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        report = auditor.generate_report(audit_results)
        assert "## Skills" in report

    @pytest.mark.unit
    def test_report_without_summary_key(self, empty_skills_dir: Path) -> None:
        """Scenario: Report handles missing summary key gracefully."""
        auditor = SkillsAuditor(empty_skills_dir)
        result = {"total_skills": 0, "skills": []}
        report = auditor.generate_report(result)
        assert "# Skills Audit Report" in report


# ---------------------------------------------------------------------------
# Tests: export_results
# ---------------------------------------------------------------------------


class TestExportResults:
    """Feature: export_results writes JSON to file."""

    @pytest.mark.unit
    def test_export_creates_json_file(self, skills_dir: Path, tmp_path: Path) -> None:
        """Scenario: export_results writes valid JSON to export_path."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        export_path = tmp_path / "results.json"
        auditor.export_results(audit_results, export_path)
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert "total_skills" in data

    @pytest.mark.unit
    def test_export_contains_skills_list(
        self, skills_dir: Path, tmp_path: Path
    ) -> None:
        """Scenario: Exported JSON contains skills list."""
        auditor = SkillsAuditor(skills_dir)
        audit_results = auditor.audit_all_skills()
        export_path = tmp_path / "results.json"
        auditor.export_results(audit_results, export_path)
        data = json.loads(export_path.read_text())
        assert "skills" in data


# ---------------------------------------------------------------------------
# Tests: filter_skills
# ---------------------------------------------------------------------------


class TestFilterSkills:
    """Feature: filter_skills applies score and issue filters."""

    @pytest.fixture
    def sample_audit_results(self) -> dict:
        return {
            "skills": [
                {"name": "a", "overall_score": 90.0, "issues": []},
                {"name": "b", "overall_score": 60.0, "issues": [{"type": "x"}]},
                {"name": "c", "overall_score": 75.0, "issues": []},
            ]
        }

    @pytest.mark.unit
    def test_filter_by_min_score(self, tmp_path: Path, sample_audit_results) -> None:
        """Scenario: Filter by min_overall_score removes low-scoring skills."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor.filter_skills(sample_audit_results, min_overall_score=75.0)
        assert result["total_skills"] == 2
        assert all(s["overall_score"] >= 75.0 for s in result["skills"])

    @pytest.mark.unit
    def test_filter_with_issues_true(
        self, tmp_path: Path, sample_audit_results
    ) -> None:
        """Scenario: has_high_priority_issues=True returns only skills with issues."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor.filter_skills(
            sample_audit_results, has_high_priority_issues=True
        )
        assert result["total_skills"] == 1
        assert result["skills"][0]["name"] == "b"

    @pytest.mark.unit
    def test_filter_with_issues_false(
        self, tmp_path: Path, sample_audit_results
    ) -> None:
        """Scenario: has_high_priority_issues=False returns only skills without issues."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor.filter_skills(
            sample_audit_results, has_high_priority_issues=False
        )
        assert result["total_skills"] == 2
        assert all(len(s["issues"]) == 0 for s in result["skills"])

    @pytest.mark.unit
    def test_filter_no_criteria_returns_all(
        self, tmp_path: Path, sample_audit_results
    ) -> None:
        """Scenario: No filter criteria returns all skills."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor.filter_skills(sample_audit_results)
        assert result["total_skills"] == 3

    @pytest.mark.unit
    def test_filter_combined_criteria(
        self, tmp_path: Path, sample_audit_results
    ) -> None:
        """Scenario: Combined min_score and no-issues filter yields intersection."""
        auditor = SkillsAuditor(tmp_path)
        result = auditor.filter_skills(
            sample_audit_results,
            min_overall_score=75.0,
            has_high_priority_issues=False,
        )
        # a (90, no issues) and c (75, no issues) pass both filters
        assert result["total_skills"] == 2


# ---------------------------------------------------------------------------
# Tests: discover_skills
# ---------------------------------------------------------------------------


class TestDiscoverSkills:
    """Feature: discover_skills returns skill names."""

    @pytest.mark.unit
    def test_empty_dir_returns_empty_list(self, empty_skills_dir: Path) -> None:
        """Scenario: Empty directory returns empty skill names list."""
        auditor = SkillsAuditor(empty_skills_dir)
        names = auditor.discover_skills()
        assert names == []

    @pytest.mark.unit
    def test_returns_correct_names(self, skills_dir: Path) -> None:
        """Scenario: Returns parent directory names of all SKILL.md files."""
        auditor = SkillsAuditor(skills_dir)
        names = auditor.discover_skills()
        assert set(names) == {"skill-a", "skill-b"}
