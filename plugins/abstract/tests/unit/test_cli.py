"""Tests for the unified abstract CLI entry point.

Covers create_main_parser(), main(), and subcommand dispatch routing.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from abstract.cli import (
    AuditCLI,
    ComplianceCLI,
    SuggestCLI,
    TokenCLI,
    create_main_parser,
    main,
)
from abstract.cli_framework import CLIResult

# ---------------------------------------------------------------------------
# create_main_parser
# ---------------------------------------------------------------------------


class TestCreateMainParser:
    """create_main_parser builds a parser with all four subcommands."""

    @pytest.mark.unit
    def test_returns_argument_parser(self):
        """Given create_main_parser(), returns an ArgumentParser."""
        parser = create_main_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @pytest.mark.unit
    def test_prog_name(self):
        """Given create_main_parser(), prog is 'abstract-skills'."""
        parser = create_main_parser()
        assert parser.prog == "abstract-skills"

    @pytest.mark.unit
    def test_check_subcommand_registered(self):
        """Given parser, 'check' subcommand is registered."""
        parser = create_main_parser()
        args = parser.parse_args(["check", "/tmp/skills"])
        assert args.command == "check"

    @pytest.mark.unit
    def test_audit_subcommand_registered(self):
        """Given parser, 'audit' subcommand is registered."""
        parser = create_main_parser()
        args = parser.parse_args(["audit", "/tmp/skills"])
        assert args.command == "audit"

    @pytest.mark.unit
    def test_suggest_subcommand_registered(self):
        """Given parser, 'suggest' subcommand is registered."""
        parser = create_main_parser()
        args = parser.parse_args(["suggest", "/tmp/skill"])
        assert args.command == "suggest"

    @pytest.mark.unit
    def test_tokens_subcommand_registered(self):
        """Given parser, 'tokens' subcommand is registered."""
        parser = create_main_parser()
        args = parser.parse_args(["tokens", "/tmp/skills"])
        assert args.command == "tokens"

    @pytest.mark.unit
    def test_check_subcommand_accepts_format(self):
        """Given 'check' subcommand, --format is accepted."""
        parser = create_main_parser()
        args = parser.parse_args(["check", "/tmp/skills", "--format", "json"])
        assert args.format == "json"

    @pytest.mark.unit
    def test_audit_subcommand_accepts_min_score(self):
        """Given 'audit' subcommand, --min-score is accepted."""
        parser = create_main_parser()
        args = parser.parse_args(["audit", "/tmp/skills", "--min-score", "75.5"])
        assert args.min_score == 75.5

    @pytest.mark.unit
    def test_suggest_subcommand_accepts_priority(self):
        """Given 'suggest' subcommand, --priority is accepted."""
        parser = create_main_parser()
        args = parser.parse_args(["suggest", "/tmp/skill", "--priority", "high"])
        assert args.priority == "high"

    @pytest.mark.unit
    def test_tokens_subcommand_accepts_threshold(self):
        """Given 'tokens' subcommand, --threshold is accepted."""
        parser = create_main_parser()
        args = parser.parse_args(["tokens", "/tmp/skills", "--threshold", "2000"])
        assert args.threshold == 2000

    @pytest.mark.unit
    def test_check_directory_parsed_as_path(self):
        """Given 'check' with a directory, it is stored as a Path."""
        parser = create_main_parser()
        args = parser.parse_args(["check", "/tmp/skills"])
        assert isinstance(args.directory, Path)

    @pytest.mark.unit
    def test_audit_directory_parsed_as_path(self):
        """Given 'audit' with a directory, it is stored as a Path."""
        parser = create_main_parser()
        args = parser.parse_args(["audit", "/tmp/skills"])
        assert isinstance(args.directory, Path)

    @pytest.mark.unit
    def test_tokens_threshold_default(self):
        """Given 'tokens' without --threshold, default is 4000."""
        parser = create_main_parser()
        args = parser.parse_args(["tokens", "/tmp/skills"])
        assert args.threshold == 4000

    @pytest.mark.unit
    def test_audit_min_score_default(self):
        """Given 'audit' without --min-score, default is 0.0."""
        parser = create_main_parser()
        args = parser.parse_args(["audit", "/tmp/skills"])
        assert args.min_score == 0.0

    @pytest.mark.unit
    def test_no_subcommand_command_is_none(self):
        """Given no subcommand, args.command is None."""
        parser = create_main_parser()
        args = parser.parse_args([])
        assert args.command is None

    @pytest.mark.unit
    def test_check_rules_file_optional(self):
        """Given 'check' without --rules-file, rules_file is None."""
        parser = create_main_parser()
        args = parser.parse_args(["check", "/tmp/skills"])
        assert args.rules_file is None


# ---------------------------------------------------------------------------
# main() - no-subcommand path
# ---------------------------------------------------------------------------


class TestMainNoSubcommand:
    """main() with no subcommand prints help and returns 0."""

    @pytest.mark.unit
    def test_no_subcommand_returns_zero(self, capsys):
        """Given no subcommand, main returns 0 and prints help."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "abstract-skills" in captured.out or len(captured.out) > 0


# ---------------------------------------------------------------------------
# main() - subcommand dispatch
# ---------------------------------------------------------------------------


class TestMainSubcommandDispatch:
    """main() routes subcommands to the correct CLI class."""

    @pytest.mark.unit
    def test_check_dispatches_to_compliance_cli(self, tmp_path, capsys):
        """Given 'check' subcommand, ComplianceCLI.execute() is called."""
        mock_result = CLIResult(
            success=True,
            data={"compliant": True, "issues": [], "warnings": [], "total_skills": 0},
        )
        with patch.object(
            ComplianceCLI, "execute", return_value=mock_result
        ) as mock_exec:
            exit_code = main(["check", str(tmp_path)])
        mock_exec.assert_called_once()
        assert exit_code == 0

    @pytest.mark.unit
    def test_audit_dispatches_to_audit_cli(self, tmp_path, capsys):
        """Given 'audit' subcommand, AuditCLI.execute() is called."""
        mock_result = CLIResult(
            success=True, data={"skills": [], "total_skills": 0, "average_score": 0}
        )
        with patch.object(AuditCLI, "execute", return_value=mock_result) as mock_exec:
            exit_code = main(["audit", str(tmp_path)])
        mock_exec.assert_called_once()
        assert exit_code == 0

    @pytest.mark.unit
    def test_suggest_dispatches_to_suggest_cli(self, tmp_path, capsys):
        """Given 'suggest' subcommand, SuggestCLI.execute() is called."""
        mock_result = CLIResult(success=True, data=[])
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: test\n---\n\n# Test\n")
        with patch.object(SuggestCLI, "execute", return_value=mock_result) as mock_exec:
            exit_code = main(["suggest", str(skill_file)])
        mock_exec.assert_called_once()
        assert exit_code == 0

    @pytest.mark.unit
    def test_tokens_dispatches_to_token_cli(self, tmp_path, capsys):
        """Given 'tokens' subcommand, TokenCLI.execute() is called."""
        mock_result = CLIResult(
            success=True, data={"files": [], "total_tokens": 0, "file_count": 0}
        )
        with patch.object(TokenCLI, "execute", return_value=mock_result) as mock_exec:
            exit_code = main(["tokens", str(tmp_path)])
        mock_exec.assert_called_once()
        assert exit_code == 0

    @pytest.mark.unit
    def test_failed_execute_returns_one(self, tmp_path, capsys):
        """Given execute returns failure, main propagates exit code 1."""
        mock_result = CLIResult(success=False, error="audit failed")
        with patch.object(AuditCLI, "execute", return_value=mock_result):
            exit_code = main(["audit", str(tmp_path)])
        assert exit_code == 1


# ---------------------------------------------------------------------------
# ComplianceCLI
# ---------------------------------------------------------------------------


class TestComplianceCLI:
    """ComplianceCLI initialises and produces formatted output."""

    @pytest.mark.unit
    def test_init_sets_name(self):
        """Given ComplianceCLI(), name is set correctly."""
        cli = ComplianceCLI()
        assert "compliance" in cli.name

    @pytest.mark.unit
    def test_format_text_compliant(self):
        """Given compliant=True data, format_text reports COMPLIANT."""
        cli = ComplianceCLI()
        output = cli.format_text(
            {"compliant": True, "issues": [], "warnings": [], "total_skills": 3}
        )
        assert "COMPLIANT" in output
        assert "3" in output

    @pytest.mark.unit
    def test_format_text_non_compliant_with_issues(self):
        """Given compliant=False, format_text lists issues."""
        cli = ComplianceCLI()
        output = cli.format_text(
            {
                "compliant": False,
                "issues": ["missing field", "bad format"],
                "warnings": [],
                "total_skills": 1,
            }
        )
        assert "NON-COMPLIANT" in output
        assert "missing field" in output
        assert "bad format" in output

    @pytest.mark.unit
    def test_format_text_includes_warnings(self):
        """Given warnings in data, format_text includes them."""
        cli = ComplianceCLI()
        output = cli.format_text(
            {
                "compliant": True,
                "issues": [],
                "warnings": ["deprecated field used"],
                "total_skills": 1,
            }
        )
        assert "deprecated field used" in output

    @pytest.mark.unit
    def test_execute_returns_cli_result(self, tmp_path):
        """Given a valid directory, execute returns CLIResult."""
        cli = ComplianceCLI()
        mock_checker = MagicMock()
        mock_checker.check_compliance.return_value = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "total_skills": 0,
        }
        with patch("abstract.cli.ComplianceChecker", return_value=mock_checker):
            args = argparse.Namespace(directory=tmp_path, rules_file=None, output=None)
            result = cli.execute(args)
        assert isinstance(result, CLIResult)
        assert result.success is True

    @pytest.mark.unit
    def test_execute_returns_failure_on_expected_exception(self, tmp_path):
        """Given checker raises OSError, execute returns failure CLIResult."""
        cli = ComplianceCLI()
        mock_checker = MagicMock()
        mock_checker.check_compliance.side_effect = OSError("boom")
        with patch("abstract.cli.ComplianceChecker", return_value=mock_checker):
            args = argparse.Namespace(directory=tmp_path, rules_file=None, output=None)
            result = cli.execute(args)
        assert result.success is False
        assert "boom" in result.error

    @pytest.mark.unit
    def test_execute_propagates_unexpected_exception(self, tmp_path):
        """Given checker raises RuntimeError, execute re-raises."""
        cli = ComplianceCLI()
        mock_checker = MagicMock()
        mock_checker.check_compliance.side_effect = RuntimeError("boom")
        with patch("abstract.cli.ComplianceChecker", return_value=mock_checker):
            args = argparse.Namespace(directory=tmp_path, rules_file=None, output=None)
            with pytest.raises(RuntimeError, match="boom"):
                cli.execute(args)


# ---------------------------------------------------------------------------
# AuditCLI
# ---------------------------------------------------------------------------


class TestAuditCLI:
    """AuditCLI initialises and produces formatted output."""

    @pytest.mark.unit
    def test_init_sets_name(self):
        """Given AuditCLI(), name is set correctly."""
        cli = AuditCLI()
        assert "audit" in cli.name

    @pytest.mark.unit
    def test_format_text_with_skills(self):
        """Given skills in data, format_text lists them."""
        cli = AuditCLI()
        output = cli.format_text(
            {
                "skills": [{"name": "my-skill", "score": 85.0, "issues": []}],
                "total_skills": 1,
                "average_score": 85.0,
            }
        )
        assert "my-skill" in output
        assert "85.0" in output

    @pytest.mark.unit
    def test_format_text_with_skill_issues(self):
        """Given skill with issues, they appear in format_text output."""
        cli = AuditCLI()
        output = cli.format_text(
            {
                "skills": [
                    {"name": "bad-skill", "score": 40.0, "issues": ["missing overview"]}
                ],
                "total_skills": 1,
                "average_score": 40.0,
            }
        )
        assert "missing overview" in output

    @pytest.mark.unit
    def test_execute_returns_cli_result(self, tmp_path):
        """Given a valid directory, execute returns CLIResult."""
        cli = AuditCLI()
        mock_auditor = MagicMock()
        mock_auditor.audit_skills.return_value = {
            "skills": [],
            "total_skills": 0,
            "average_score": 0.0,
        }
        with patch("abstract.cli.SkillsAuditor", return_value=mock_auditor):
            args = argparse.Namespace(directory=tmp_path, output=None, min_score=0.0)
            result = cli.execute(args)
        assert isinstance(result, CLIResult)
        assert result.success is True

    @pytest.mark.unit
    def test_execute_returns_failure_on_exception(self, tmp_path):
        """Given auditor raises, execute returns failure CLIResult."""
        cli = AuditCLI()
        mock_auditor = MagicMock()
        mock_auditor.audit_skills.side_effect = ValueError("no skills")
        with patch("abstract.cli.SkillsAuditor", return_value=mock_auditor):
            args = argparse.Namespace(directory=tmp_path, output=None, min_score=0.0)
            result = cli.execute(args)
        assert result.success is False
        assert "no skills" in result.error


# ---------------------------------------------------------------------------
# SuggestCLI
# ---------------------------------------------------------------------------


class TestSuggestCLI:
    """SuggestCLI initialises and produces formatted output."""

    @pytest.mark.unit
    def test_init_sets_name(self):
        """Given SuggestCLI(), name is set correctly."""
        cli = SuggestCLI()
        assert "suggest" in cli.name

    @pytest.mark.unit
    def test_format_text_no_suggestions(self):
        """Given empty suggestions list, format_text reports no suggestions."""
        cli = SuggestCLI()
        output = cli.format_text([])
        assert "No suggestions" in output

    @pytest.mark.unit
    def test_format_text_with_suggestions(self):
        """Given suggestions, format_text lists them with categories."""
        cli = SuggestCLI()
        output = cli.format_text(
            [
                {
                    "category": "high",
                    "description": "Add more examples",
                    "specific_action": "Create examples/ directory",
                }
            ]
        )
        assert "Add more examples" in output
        assert "Create examples/ directory" in output
        assert "HIGH" in output

    @pytest.mark.unit
    def test_execute_directory_path(self, tmp_path):
        """Given a directory path, execute calls analyze_all_skills."""
        cli = SuggestCLI()
        mock_suggester = MagicMock()
        mock_suggester.analyze_all_skills.return_value = []
        with patch("abstract.cli.ImprovementSuggester", return_value=mock_suggester):
            args = argparse.Namespace(skill_path=tmp_path, output=None, priority=None)
            result = cli.execute(args)
        assert result.success is True
        mock_suggester.analyze_all_skills.assert_called_once()

    @pytest.mark.unit
    def test_execute_file_path(self, tmp_path):
        """Given a file path, execute calls analyze_skill for that skill."""
        cli = SuggestCLI()
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: test\n---\n")

        mock_suggester = MagicMock()
        mock_suggester.analyze_skill.return_value = {
            "category": "low",
            "description": "looks good",
        }
        with patch("abstract.cli.ImprovementSuggester", return_value=mock_suggester):
            args = argparse.Namespace(skill_path=skill_file, output=None, priority=None)
            result = cli.execute(args)
        assert result.success is True
        mock_suggester.analyze_skill.assert_called_once()

    @pytest.mark.unit
    def test_execute_returns_failure_on_exception(self, tmp_path):
        """Given suggester raises, execute returns failure CLIResult."""
        cli = SuggestCLI()
        mock_suggester = MagicMock()
        mock_suggester.analyze_all_skills.side_effect = OSError("disk error")
        with patch("abstract.cli.ImprovementSuggester", return_value=mock_suggester):
            args = argparse.Namespace(skill_path=tmp_path, output=None, priority=None)
            result = cli.execute(args)
        assert result.success is False
        assert "disk error" in result.error


# ---------------------------------------------------------------------------
# TokenCLI
# ---------------------------------------------------------------------------


class TestTokenCLI:
    """TokenCLI initialises and produces formatted output."""

    @pytest.mark.unit
    def test_init_sets_name(self):
        """Given TokenCLI(), name is set correctly."""
        cli = TokenCLI()
        assert "token" in cli.name.lower()

    @pytest.mark.unit
    def test_format_text_with_files(self):
        """Given files in data, format_text lists token counts."""
        cli = TokenCLI()
        output = cli.format_text(
            {
                "files": [
                    {
                        "path": "/tmp/SKILL.md",
                        "token_count": 500,
                        "under_threshold": True,
                    }
                ],
                "total_tokens": 500,
                "file_count": 1,
            }
        )
        assert "/tmp/SKILL.md" in output
        assert "500" in output
        assert "OK" in output

    @pytest.mark.unit
    def test_format_text_over_threshold(self):
        """Given file over threshold, format_text shows OVER status."""
        cli = TokenCLI()
        output = cli.format_text(
            {
                "files": [
                    {
                        "path": "/tmp/BIG.md",
                        "token_count": 9000,
                        "under_threshold": False,
                    }
                ],
                "total_tokens": 9000,
                "file_count": 1,
            }
        )
        assert "OVER" in output

    @pytest.mark.unit
    def test_execute_returns_cli_result(self, tmp_path):
        """Given a valid path, execute returns CLIResult."""
        cli = TokenCLI()
        mock_tracker = MagicMock()
        mock_tracker.analyze_all_skills.return_value = {
            "files": [],
            "total_tokens": 0,
            "file_count": 0,
        }
        with patch("abstract.cli.TokenUsageTracker", return_value=mock_tracker):
            args = argparse.Namespace(path=tmp_path, output=None, threshold=4000)
            result = cli.execute(args)
        assert isinstance(result, CLIResult)
        assert result.success is True

    @pytest.mark.unit
    def test_execute_returns_failure_on_expected_exception(self, tmp_path):
        """Given tracker raises ValueError, execute returns failure CLIResult."""
        cli = TokenCLI()
        mock_tracker = MagicMock()
        mock_tracker.analyze_all_skills.side_effect = ValueError("tracker error")
        with patch("abstract.cli.TokenUsageTracker", return_value=mock_tracker):
            args = argparse.Namespace(path=tmp_path, output=None, threshold=4000)
            result = cli.execute(args)
        assert result.success is False
        assert "tracker error" in result.error

    @pytest.mark.unit
    def test_execute_propagates_unexpected_exception(self, tmp_path):
        """Given tracker raises RuntimeError, execute re-raises."""
        cli = TokenCLI()
        mock_tracker = MagicMock()
        mock_tracker.analyze_all_skills.side_effect = RuntimeError("tracker error")
        with patch("abstract.cli.TokenUsageTracker", return_value=mock_tracker):
            args = argparse.Namespace(path=tmp_path, output=None, threshold=4000)
            with pytest.raises(RuntimeError, match="tracker error"):
                cli.execute(args)
