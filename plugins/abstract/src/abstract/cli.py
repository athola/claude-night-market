#!/usr/bin/env python3
"""Unified CLI for Abstract skills evaluation tools.

Provides subcommands for compliance checking, auditing, improvement suggestions,
and token usage tracking through a single entry point.
"""

import argparse
import sys
from pathlib import Path

from .cli_framework import AbstractCLI, CLIResult
from .skills_eval import (
    ComplianceChecker,
    ImprovementSuggester,
    SkillsAuditor,
    TokenUsageTracker,
)


class ComplianceCLI(AbstractCLI):
    """CLI for compliance checking."""

    def __init__(self) -> None:
        """Initialize the compliance CLI."""
        super().__init__(
            name="abstract compliance",
            description="Check skills compliance against standards",
            version="1.0.0",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add compliance-specific arguments."""
        parser.add_argument(
            "directory",
            type=Path,
            help="Directory containing skills to check",
        )
        parser.add_argument(
            "--rules-file",
            type=Path,
            help="Custom rules file (JSON)",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output file path",
        )

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute compliance check."""
        checker = ComplianceChecker(args.directory, args.rules_file)
        try:
            results = checker.check_compliance()
            return CLIResult(success=True, data=results)
        except Exception as e:
            return CLIResult(success=False, error=str(e))

    def format_text(self, data: dict) -> str:
        """Format compliance results as text."""
        lines = ["Compliance Report", "=" * 50]

        if data.get("compliant"):
            lines.append("Status: COMPLIANT")
        else:
            lines.append("Status: NON-COMPLIANT")

        if data.get("issues"):
            lines.append(f"\nIssues ({len(data['issues'])}):")
            for issue in data["issues"]:
                lines.append(f"  - {issue}")

        if data.get("warnings"):
            lines.append(f"\nWarnings ({len(data['warnings'])}):")
            for warning in data["warnings"]:
                lines.append(f"  - {warning}")

        lines.append(f"\nTotal skills checked: {data.get('total_skills', 0)}")

        return "\n".join(lines)


class AuditCLI(AbstractCLI):
    """CLI for skills auditing."""

    def __init__(self) -> None:
        """Initialize the audit CLI."""
        super().__init__(
            name="abstract audit",
            description="Audit skills for quality and best practices",
            version="1.0.0",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add audit-specific arguments."""
        parser.add_argument(
            "directory",
            type=Path,
            help="Directory containing skills to audit",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output file path",
        )
        parser.add_argument(
            "--min-score",
            type=float,
            default=0.0,
            help="Minimum score threshold (0-100)",
        )

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute skills audit."""
        auditor = SkillsAuditor(args.directory)
        try:
            results = auditor.audit_skills()
            return CLIResult(success=True, data=results)
        except Exception as e:
            return CLIResult(success=False, error=str(e))

    def format_text(self, data: dict) -> str:
        """Format audit results as text."""
        lines = ["Skills Audit Report", "=" * 50]

        if "skills" in data:
            for skill in data["skills"]:
                lines.append(f"\n{skill.get('name', 'Unknown')}:")
                lines.append(f"  Score: {skill.get('score', 0):.1f}")
                if skill.get("issues"):
                    lines.append("  Issues:")
                    for issue in skill["issues"]:
                        lines.append(f"    - {issue}")

        lines.append(f"\nTotal skills: {data.get('total_skills', 0)}")
        lines.append(f"Average score: {data.get('average_score', 0):.1f}")

        return "\n".join(lines)


class SuggestCLI(AbstractCLI):
    """CLI for improvement suggestions."""

    def __init__(self) -> None:
        """Initialize the suggest CLI."""
        super().__init__(
            name="abstract suggest",
            description="Generate improvement suggestions for skills",
            version="1.0.0",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add suggest-specific arguments."""
        parser.add_argument(
            "skill_path",
            type=Path,
            help="Path to skill file or directory",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output file path",
        )
        parser.add_argument(
            "--priority",
            choices=["critical", "high", "medium", "low"],
            help="Filter by minimum priority",
        )

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute improvement suggestion."""
        skill_path = args.skill_path
        try:
            if skill_path.is_dir():
                # If directory, analyze all skills in it
                suggester = ImprovementSuggester(skill_path)
                suggestions = suggester.analyze_all_skills()
            else:
                # If file, find parent skills dir and analyze that skill
                skills_dir = skill_path.parent.parent
                skill_name = skill_path.parent.name
                suggester = ImprovementSuggester(skills_dir)
                result = suggester.analyze_skill(skill_name)
                suggestions = [result] if result else []
            return CLIResult(success=True, data=suggestions)
        except Exception as e:
            return CLIResult(success=False, error=str(e))

    def format_text(self, data: list) -> str:
        """Format suggestions as text."""
        lines = ["Improvement Suggestions", "=" * 50]

        if not data:
            lines.append("\nNo suggestions - skill looks good!")
            return "\n".join(lines)

        for idx, suggestion in enumerate(data, 1):
            lines.append(
                f"\n{idx}. [{suggestion.get('category', 'medium').upper()}] "
                f"{suggestion.get('description', 'No description')}",
            )
            if suggestion.get("specific_action"):
                lines.append(f"   Action: {suggestion['specific_action']}")

        return "\n".join(lines)


class TokenCLI(AbstractCLI):
    """CLI for token usage tracking."""

    def __init__(self) -> None:
        """Initialize the token CLI."""
        super().__init__(
            name="abstract tokens",
            description="Track and analyze token usage in skills",
            version="1.0.0",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add token-specific arguments."""
        parser.add_argument(
            "path",
            type=Path,
            help="Path to skill file or directory",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output file path",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=4000,
            help="Token count threshold for warnings",
        )

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute token usage tracking."""
        tracker = TokenUsageTracker(args.path)
        try:
            results = tracker.analyze_all_skills()
            return CLIResult(success=True, data=results)
        except Exception as e:
            return CLIResult(success=False, error=str(e))

    def format_text(self, data: dict) -> str:
        """Format token analysis as text."""
        lines = ["Token Usage Analysis", "=" * 50]

        if "files" in data:
            for file_info in data["files"]:
                status = "OK" if file_info.get("under_threshold") else "OVER"
                lines.append(f"\n{file_info.get('path', 'Unknown')}:")
                lines.append(f"  Tokens: {file_info.get('token_count', 0)} [{status}]")

        lines.append(f"\nTotal tokens: {data.get('total_tokens', 0)}")
        lines.append(f"Files analyzed: {data.get('file_count', 0)}")

        return "\n".join(lines)


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main CLI parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="abstract-skills",
        description="Abstract skills evaluation toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  check     Check skills compliance against standards
  audit     Audit skills for quality and best practices
  suggest   Generate improvement suggestions
  tokens    Analyze token usage

Examples:
  abstract-skills check ./skills/
  abstract-skills audit ./skills/ --format json
  abstract-skills suggest ./skills/my-skill/SKILL.md
  abstract-skills tokens ./skills/ --threshold 3000
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="abstract-skills 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add subcommands
    _add_check_subparser(subparsers)
    _add_audit_subparser(subparsers)
    _add_suggest_subparser(subparsers)
    _add_tokens_subparser(subparsers)

    return parser


def _add_check_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add compliance check subparser."""
    check = subparsers.add_parser("check", help="Check skills compliance")
    check.add_argument("directory", type=Path, help="Directory to check")
    check.add_argument("--rules-file", type=Path, help="Custom rules file")
    check.add_argument("--output", "-o", type=Path, help="Output file")
    check.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def _add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add audit subparser."""
    audit = subparsers.add_parser("audit", help="Audit skills")
    audit.add_argument("directory", type=Path, help="Directory to audit")
    audit.add_argument("--output", "-o", type=Path, help="Output file")
    audit.add_argument("--min-score", type=float, default=0.0, help="Minimum score")
    audit.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def _add_suggest_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add suggest subparser."""
    suggest = subparsers.add_parser("suggest", help="Generate improvement suggestions")
    suggest.add_argument("skill_path", type=Path, help="Path to skill")
    suggest.add_argument("--output", "-o", type=Path, help="Output file")
    suggest.add_argument(
        "--priority",
        choices=["critical", "high", "medium", "low"],
        help="Filter by priority",
    )
    suggest.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def _add_tokens_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add tokens subparser."""
    tokens = subparsers.add_parser("tokens", help="Analyze token usage")
    tokens.add_argument("path", type=Path, help="Path to analyze")
    tokens.add_argument("--output", "-o", type=Path, help="Output file")
    tokens.add_argument("--threshold", type=int, default=4000, help="Token threshold")
    tokens.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def main(argv: list[str] | None = None) -> int:
    """Run the unified abstract CLI."""
    parser = create_main_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to appropriate CLI
    cli_map: dict[str, type[ComplianceCLI | AuditCLI | SuggestCLI | TokenCLI]] = {
        "check": ComplianceCLI,
        "audit": AuditCLI,
        "suggest": SuggestCLI,
        "tokens": TokenCLI,
    }

    cli_class = cli_map.get(args.command)
    if cli_class is None:
        return 1

    # Re-run with the subcommand-specific CLI
    cli = cli_class()
    # Remove the command from argv for the subcommand parser
    sub_argv = sys.argv[2:] if argv is None else argv[1:]
    return cli.run(sub_argv)


if __name__ == "__main__":
    sys.exit(main())
