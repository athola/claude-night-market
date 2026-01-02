"""Tests for skills auditing functionality."""

import json

import pytest

from abstract.skills_eval import SkillsAuditor

# Test constants
EXPECTED_TOTAL_SKILLS = 3
WELL_STRUCTURED_MIN_SCORE = 80
NEEDS_IMPROVEMENT_MAX_SCORE = 70
MAX_SCORE = 100


class TestSkillsAuditor:
    """Test cases for SkillsAuditor."""

    @pytest.fixture
    def sample_skills_dir(self, tmp_path):
        """Create a temporary directory with multiple skill files."""
        skills_data = {
            "well-structured-skill": """---
name: well-structured-skill
description: A properly structured skill
category: testing
dependencies: []
---

# Well Structured Skill

## Overview
This skill follows best practices.

## Quick Start
Use it by running the command.

## Detailed Resources
More information available.
""",
            "needs-improvement-skill": """---
name: needs-improvement-skill
---

# Needs Improvement Skill

This skill needs work on structure and completeness.
""",
            "large-skill": """---
name: large-skill
description: A very large skill
category: detailed
---

# Large Skill

"""
            + "This skill has a lot of content that makes it hard to manage "
            "effectively. " * 150,
        }

        for skill_name, content in skills_data.items():
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(content)

        return tmp_path

    def test_auditor_initialization(self, sample_skills_dir) -> None:
        """Test auditor initializes correctly."""
        auditor = SkillsAuditor(sample_skills_dir)
        assert auditor.skills_root == sample_skills_dir
        assert len(auditor.skill_files) == EXPECTED_TOTAL_SKILLS

    def test_discover_skills(self, sample_skills_dir) -> None:
        """Test skill discovery."""
        auditor = SkillsAuditor(sample_skills_dir)
        discovered_skills = auditor.discover_skills()

        assert len(discovered_skills) == EXPECTED_TOTAL_SKILLS
        # discover_skills returns a list of skill names (strings), not dictionaries
        assert "well-structured-skill" in discovered_skills
        assert "needs-improvement-skill" in discovered_skills
        assert "large-skill" in discovered_skills

    def test_audit_all_skills(self, sample_skills_dir) -> None:
        """Test detailed auditing of all skills."""
        auditor = SkillsAuditor(sample_skills_dir)
        audit_results = auditor.audit_all_skills()

        assert "total_skills" in audit_results
        assert "skill_metrics" in audit_results
        assert audit_results["total_skills"] == EXPECTED_TOTAL_SKILLS
        assert len(audit_results["skill_metrics"]) == EXPECTED_TOTAL_SKILLS

    def test_audit_single_skill(self, sample_skills_dir) -> None:
        """Test auditing a single skill."""
        auditor = SkillsAuditor(sample_skills_dir)
        skill_audit = auditor.audit_skill("well-structured-skill")

        assert "name" in skill_audit
        assert "completeness_score" in skill_audit
        assert "structure_score" in skill_audit
        assert "overall_score" in skill_audit
        assert "issues" in skill_audit
        assert "recommendations" in skill_audit
        assert skill_audit["name"] == "well-structured-skill"

    def test_calculate_completeness_scores(self, sample_skills_dir) -> None:
        """Test completeness scoring."""
        auditor = SkillsAuditor(sample_skills_dir)

        # Well structured skill should have high completeness
        well_structured = auditor.audit_skill("well-structured-skill")
        assert well_structured["completeness_score"] >= WELL_STRUCTURED_MIN_SCORE

        # Needs improvement skill should have lower completeness
        needs_improvement = auditor.audit_skill("needs-improvement-skill")
        assert needs_improvement["completeness_score"] < NEEDS_IMPROVEMENT_MAX_SCORE

    def test_calculate_structure_scores(self, sample_skills_dir) -> None:
        """Test structure scoring."""
        auditor = SkillsAuditor(sample_skills_dir)

        well_structured = auditor.audit_skill("well-structured-skill")
        needs_improvement = auditor.audit_skill("needs-improvement-skill")

        # Well structured should score higher on structure
        assert well_structured["structure_score"] > needs_improvement["structure_score"]

    def test_detect_common_issues(self, sample_skills_dir) -> None:
        """Test detection of common skill issues."""
        auditor = SkillsAuditor(sample_skills_dir)

        # Check for missing description in needs-improvement skill
        needs_improvement = auditor.audit_skill("needs-improvement-skill")
        issue_descriptions = [issue["type"] for issue in needs_improvement["issues"]]
        assert "missing_description" in issue_descriptions

        # Check for large size in large-skill
        large_skill = auditor.audit_skill("large-skill")
        issue_descriptions = [issue["type"] for issue in large_skill["issues"]]
        assert "size_large" in issue_descriptions

    def test_generate_recommendations(self, sample_skills_dir) -> None:
        """Test recommendation generation."""
        auditor = SkillsAuditor(sample_skills_dir)

        # Skill with issues should get recommendations
        needs_improvement = auditor.audit_skill("needs-improvement-skill")
        assert len(needs_improvement["recommendations"]) > 0

        # Recommendations should be actionable
        for rec in needs_improvement["recommendations"]:
            assert "action" in rec
            assert "priority" in rec
            assert rec["priority"] in ["high", "medium", "low"]

    def test_generate_audit_report(self, sample_skills_dir) -> None:
        """Test detailed audit report generation."""
        auditor = SkillsAuditor(sample_skills_dir)
        audit_results = auditor.audit_all_skills()
        report = auditor.generate_report(audit_results)

        assert "Skills Audit Report" in report
        assert "Total Skills" in report
        assert "Summary" in report
        assert "well-structured-skill" in report
        assert "needs-improvement-skill" in report

    def test_calculate_overall_metrics(self, sample_skills_dir) -> None:
        """Test calculation of overall audit metrics."""
        auditor = SkillsAuditor(sample_skills_dir)
        audit_results = auditor.audit_all_skills()

        summary = audit_results["summary"]
        assert "average_completeness" in summary
        assert "average_structure" in summary
        assert "average_overall" in summary
        assert "skills_needing_improvement" in summary
        assert "high_priority_issues" in summary

        # Metrics should be in valid ranges
        assert 0 <= summary["average_completeness"] <= MAX_SCORE
        assert 0 <= summary["average_structure"] <= MAX_SCORE
        assert 0 <= summary["average_overall"] <= MAX_SCORE

    def test_export_audit_results(self, sample_skills_dir, tmp_path) -> None:
        """Test exporting audit results to file."""
        auditor = SkillsAuditor(sample_skills_dir)
        audit_results = auditor.audit_all_skills()

        export_file = tmp_path / "audit_results.json"
        auditor.export_results(audit_results, export_file)

        assert export_file.exists()

        # Verify exported data
        with open(export_file) as f:
            exported_data = json.load(f)

        assert "total_skills" in exported_data
        assert exported_data["total_skills"] == EXPECTED_TOTAL_SKILLS
        assert "skills" in exported_data
        assert "summary" in exported_data

    def test_filter_skills_by_criteria(self, sample_skills_dir) -> None:
        """Test filtering skills by various criteria."""
        auditor = SkillsAuditor(sample_skills_dir)
        audit_results = auditor.audit_all_skills()

        # Filter by overall score
        high_quality = auditor.filter_skills(audit_results, min_overall_score=70)
        assert len(high_quality["skills"]) <= audit_results["total_skills"]

        # Filter by priority issues
        critical_issues = auditor.filter_skills(
            audit_results,
            has_high_priority_issues=True,
        )
        assert len(critical_issues["skills"]) <= audit_results["total_skills"]

    def test_track_improvement_over_time(self, tmp_path) -> None:
        """Test tracking skill improvements across multiple audits."""
        # Create initial audit
        initial_skills_dir = tmp_path / "initial"
        initial_skills_dir.mkdir()

        skill_dir = initial_skills_dir / "improving-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: improving-skill
---

# Improving Skill
Basic content.
""")

        auditor = SkillsAuditor(initial_skills_dir)
        initial_audit = auditor.audit_all_skills()

        # Simulate improvement
        improved_content = """---
name: improving-skill
description: Improved skill
category: testing
---

# Improving Skill

## Overview
This skill has been improved.

## Quick Start
Usage instructions.

## Detailed Resources
More details.
"""
        (skill_dir / "SKILL.md").write_text(improved_content)

        improved_audit = auditor.audit_all_skills()

        # Overall scores should improve
        initial_score = next(s["overall_score"] for s in initial_audit["skills"])
        improved_score = next(s["overall_score"] for s in improved_audit["skills"])
        assert improved_score > initial_score
