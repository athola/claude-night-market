"""Integration tests for continuous improvement workflow.

Tests behavioral execution of Phase 2-3, not just documentation completeness.
Addresses issue #104 from PR #100 review.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from update_plugin_registrations import PluginAuditor


class TestPhase2SkillPerformanceAnalysis:
    """Verify Phase 2 performance analysis actually executes and returns results."""

    def test_analyze_skill_performance_returns_dict(self, tmp_path):
        """Phase 2 analysis returns a dict with expected structure."""
        # Create minimal plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin", "skills": []}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.analyze_skill_performance("test-plugin")
        assert isinstance(result, dict)

    def test_analyze_skill_performance_has_expected_keys(self, tmp_path):
        """Phase 2 result contains all required analysis categories."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin", "skills": []}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.analyze_skill_performance("test-plugin")
        assert "unstable_skills" in result
        assert "recent_failures" in result
        assert "low_success_rate" in result

    def test_analyze_skill_performance_empty_when_no_logs(self, tmp_path):
        """Phase 2 returns empty lists when no log directory exists."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin", "skills": []}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.analyze_skill_performance("test-plugin")
        # Default log_dir (~/.claude/skills/logs) likely doesn't exist in test env
        assert result["unstable_skills"] == []
        assert result["recent_failures"] == []
        assert result["low_success_rate"] == []

    def test_analyze_skill_performance_with_skills(self, tmp_path):
        """Phase 2 handles plugins with actual skills."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        skill = skills_dir / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n# My Skill\nContent here.\n"
        )
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps(
                {"name": "test-plugin", "skills": ["./skills/my-skill"]}, indent=2
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.analyze_skill_performance("test-plugin")
        assert isinstance(result, dict)
        # All value lists should be lists (even if empty)
        for key in ("unstable_skills", "recent_failures", "low_success_rate"):
            assert isinstance(result[key], list)

    def test_analyze_skill_performance_with_log_data(self, tmp_path):
        """Phase 2 picks up failures from actual log files."""
        from update_plugins_modules.performance_analysis import PerformanceAnalyzer

        # Create a log directory with sample data
        # Use naive timestamp (no Z suffix) to match datetime.now() used in cutoff_date
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_entry = {
            "skill": "test-plugin:my-skill",
            "outcome": "failure",
            "timestamp": "2099-01-01T00:00:00",
            "metrics": {"stability_gap": 0.5},
        }
        (log_dir / "test.jsonl").write_text(json.dumps(log_entry) + "\n")

        analyzer = PerformanceAnalyzer(log_dir=log_dir)
        result = analyzer.analyze_plugin("test-plugin", days=365000)

        assert len(result["recent_failures"]) == 1
        assert result["recent_failures"][0]["skill"] == "test-plugin:my-skill"
        assert result["recent_failures"][0]["failures"] == 1

    def test_analyze_skill_performance_detects_low_success_rate(self, tmp_path):
        """Phase 2 flags skills with success rate below 80%."""
        from update_plugins_modules.performance_analysis import PerformanceAnalyzer

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # 2 successes, 8 failures = 20% success rate
        lines = []
        for i in range(2):
            lines.append(
                json.dumps(
                    {
                        "skill": "test-plugin:flaky",
                        "outcome": "success",
                        "timestamp": "2099-01-01T00:00:00",
                    }
                )
            )
        for i in range(8):
            lines.append(
                json.dumps(
                    {
                        "skill": "test-plugin:flaky",
                        "outcome": "failure",
                        "timestamp": "2099-01-01T00:00:00",
                    }
                )
            )
        (log_dir / "test.jsonl").write_text("\n".join(lines) + "\n")

        analyzer = PerformanceAnalyzer(log_dir=log_dir)
        result = analyzer.analyze_plugin("test-plugin", days=365000)

        assert len(result["low_success_rate"]) == 1
        assert result["low_success_rate"][0]["success_rate"] == 0.2

    def test_analyze_skill_performance_detects_unstable_skills(self, tmp_path):
        """Phase 2 flags skills with stability_gap > 0.3."""
        from update_plugins_modules.performance_analysis import PerformanceAnalyzer

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        entry = {
            "skill": "test-plugin:wobbly",
            "outcome": "success",
            "timestamp": "2099-01-01T00:00:00",
            "metrics": {"stability_gap": 0.6},
        }
        (log_dir / "test.jsonl").write_text(json.dumps(entry) + "\n")

        analyzer = PerformanceAnalyzer(log_dir=log_dir)
        result = analyzer.analyze_plugin("test-plugin", days=365000)

        assert len(result["unstable_skills"]) == 1
        assert result["unstable_skills"][0]["stability_gap"] == 0.6


class TestPhase3MetaEvaluation:
    """Verify Phase 3 meta-evaluation executes and returns results."""

    def test_check_meta_evaluation_returns_dict(self, tmp_path):
        """Phase 3 meta-evaluation returns a dict."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin"}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert isinstance(result, dict)

    def test_check_meta_evaluation_has_expected_keys(self, tmp_path):
        """Phase 3 result contains all required check categories."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin"}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert "missing_toc" in result
        assert "missing_verification" in result
        assert "missing_tests" in result

    def test_meta_evaluation_with_evaluation_skills(self, tmp_path):
        """Phase 3 handles plugins that have evaluation-related skills."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        eval_skill = skills_dir / "skills-eval"
        eval_skill.mkdir()
        (eval_skill / "SKILL.md").write_text(
            "---\nname: skills-eval\n---\n# Skills Eval\nEvaluate skills.\n"
        )
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps(
                {"name": "test-plugin", "skills": ["./skills/skills-eval"]}, indent=2
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert isinstance(result, dict)

    def test_meta_evaluation_skips_non_eval_skills(self, tmp_path):
        """Phase 3 ignores skills that are not evaluation-related."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        # "deploy" does not match any EVAL_KEYWORDS
        non_eval_skill = skills_dir / "deploy"
        non_eval_skill.mkdir()
        (non_eval_skill / "SKILL.md").write_text(
            "---\nname: deploy\n---\n# Deploy\nDeploy things.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        # Non-eval skills should produce no issues
        assert result["missing_toc"] == []
        assert result["missing_verification"] == []
        assert result["missing_tests"] == []

    def test_meta_evaluation_flags_missing_verification(self, tmp_path):
        """Phase 3 flags eval skills without verification steps."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        # "code-review" matches EVAL_KEYWORDS ("review")
        review_skill = skills_dir / "code-review"
        review_skill.mkdir()
        # Content has no verification/validate/check/test keywords
        skill_content = (
            "---\nname: code-review\n---\n"
            "# Code Review\nLook at code and provide feedback.\n"
        )
        (review_skill / "SKILL.md").write_text(skill_content)

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert "code-review" in result["missing_verification"]
        assert "code-review" in result["missing_tests"]

    def test_meta_evaluation_flags_missing_toc_for_long_skills(self, tmp_path):
        """Phase 3 flags long eval skills missing a Table of Contents."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        audit_skill = skills_dir / "audit-tool"
        audit_skill.mkdir()
        # Create content >2000 chars with no TOC, but with verification/test keywords
        long_content = (
            "---\nname: audit-tool\n---\n# Audit Tool\n"
            + "This tool performs verification and test checks.\n"
            + ("Additional content paragraph.\n" * 200)
        )
        assert len(long_content) > 2000
        (audit_skill / "SKILL.md").write_text(long_content)

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert "audit-tool" in result["missing_toc"]

    def test_meta_evaluation_passes_clean_eval_skill(self, tmp_path):
        """Phase 3 produces no issues for well-structured eval skills."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        check_skill = skills_dir / "lint-check"
        check_skill.mkdir()
        # Short content (<2000 chars), has verification + test keywords
        (check_skill / "SKILL.md").write_text(
            "---\nname: lint-check\n---\n# Lint Check\n"
            "Run verification steps and test correctness.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert "lint-check" not in result["missing_toc"]
        assert "lint-check" not in result["missing_verification"]
        assert "lint-check" not in result["missing_tests"]


class TestEndToEndWorkflow:
    """Integration test: full audit + analysis pipeline."""

    def test_full_audit_then_analysis_pipeline(self, tmp_path):
        """Run complete pipeline: audit -> phase 2 -> phase 3."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        commands_dir = plugin_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "test-cmd.md").write_text("# Test Command")
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()
        skill = skills_dir / "test-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("---\nname: test-skill\n---\n# Test")

        (config_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "commands": ["./commands/test-cmd.md"],
                    "skills": ["./skills/test-skill"],
                    "agents": [],
                },
                indent=2,
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)

        # Phase 1: Audit (returns bool)
        audit_result = auditor.audit_plugin("test-plugin")
        assert isinstance(audit_result, bool)

        # Phase 2: Performance analysis
        perf_result = auditor.analyze_skill_performance("test-plugin")
        assert isinstance(perf_result, dict)
        assert "unstable_skills" in perf_result
        assert "recent_failures" in perf_result
        assert "low_success_rate" in perf_result

        # Phase 3: Meta evaluation
        meta_result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert isinstance(meta_result, dict)
        assert "missing_toc" in meta_result
        assert "missing_verification" in meta_result
        assert "missing_tests" in meta_result

    def test_pipeline_with_eval_skills(self, tmp_path):
        """Full pipeline on a plugin with eval skills triggers meta-eval checks."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir()

        # Create an eval skill with no verification
        review_skill = skills_dir / "code-review"
        review_skill.mkdir()
        (review_skill / "SKILL.md").write_text(
            "---\nname: code-review\n---\n# Code Review\nLook at code.\n"
        )

        (config_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "skills": ["./skills/code-review"],
                },
                indent=2,
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)

        # Phase 1
        auditor.audit_plugin("test-plugin")

        # Phase 2
        perf_result = auditor.analyze_skill_performance("test-plugin")
        assert isinstance(perf_result, dict)

        # Phase 3 should find issues with the eval skill
        meta_result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert "code-review" in meta_result["missing_verification"]

    def test_pipeline_phases_are_independent(self, tmp_path):
        """Each phase can run independently without prior phases."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        (config_dir / "plugin.json").write_text(
            json.dumps({"name": "test-plugin", "skills": []}, indent=2)
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)

        # Phase 2 without Phase 1
        perf_result = auditor.analyze_skill_performance("test-plugin")
        assert isinstance(perf_result, dict)

        # Phase 3 without Phase 1 or 2
        meta_result = auditor.check_meta_evaluation("test-plugin", plugin_dir)
        assert isinstance(meta_result, dict)
