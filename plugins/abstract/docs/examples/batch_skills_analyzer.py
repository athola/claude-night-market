#!/usr/bin/env python3
"""Example script for batch analyzing skills.

This script demonstrates how to use the Abstract framework for batch processing
of multiple skills, generating comprehensive reports.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.skills_eval import ComplianceChecker, SkillsAuditor, TokenUsageTracker

# Constants
MAX_ISSUES_DISPLAY = 10


def generate_batch_report(skills_dir: Path, output_dir: Path) -> None:
    """Generate a comprehensive batch analysis report.

    Args:
        skills_dir: Directory containing skills to analyze
        output_dir: Directory to save reports

    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize analyzers
    auditor = SkillsAuditor(skills_dir)
    token_tracker = TokenUsageTracker(skills_dir)
    compliance_checker = ComplianceChecker(skills_dir)

    # Run all analyses
    audit_results = auditor.audit_skills()

    token_stats = token_tracker.get_usage_statistics()

    compliance_results = compliance_checker.check_compliance()

    # Prepare summary
    summary = {
        "analysis_date": str(Path.cwd()),
        "total_skills": audit_results.get("total_skills", 0),
        "average_score": audit_results.get("average_score", 0),
        "total_tokens": token_stats.get("total_tokens", 0),
        "well_structured_skills": audit_results.get("well_structured", 0),
        "skills_needing_improvement": audit_results.get("needs_improvement", 0),
        "compliant_skills": compliance_results.get("compliant_count", 0),
        "compliance_issues": len(compliance_results.get("issues", [])),
        "token_efficiency": {
            "optimal_usage": token_stats.get("optimal_usage_count", 0),
            "over_limit": token_stats.get("skills_over_limit", 0),
            "average_tokens": token_stats.get("average_tokens", 0),
        },
    }

    # Save detailed reports
    reports = {
        "summary": summary,
        "audit": audit_results,
        "token_usage": token_stats,
        "compliance": compliance_results,
        "recommendations": audit_results.get("recommendations", []),
    }

    # Write JSON report
    report_file = output_dir / "skills_analysis_report.json"
    with open(report_file, "w") as f:
        json.dump(reports, f, indent=2, default=str)

    # Generate markdown summary
    md_content = generate_markdown_summary(
        summary,
        compliance_results.get("issues", []),
    )
    summary_file = output_dir / "README.md"
    with open(summary_file, "w") as f:
        f.write(md_content)

    # Print results

    if summary["compliance_issues"] > 0:
        pass


def generate_markdown_summary(summary: dict[str, Any], issues: list[str]) -> str:
    """Generate a markdown summary of the analysis.

    Args:
        summary: Summary statistics
        issues: List of compliance issues

    Returns:
        Markdown formatted summary

    """
    lines = [
        "# Skills Analysis Report",
        "",
        f"**Analysis Date:** {summary['analysis_date']}",
        "",
        "## Summary",
        "",
        f"- **Total Skills:** {summary['total_skills']}",
        f"- **Average Score:** {summary['average_score']:.1f}/100",
        f"- **Total Tokens:** {summary['total_tokens']:,}",
        f"- **Well-Structured:** {summary['well_structured_skills']}",
        f"- **Need Improvement:** {summary['skills_needing_improvement']}",
        "",
        "## Token Efficiency",
        "",
        f"- **Optimal Usage:** {summary['token_efficiency']['optimal_usage']} skills",
        f"- **Over Token Limit:** {summary['token_efficiency']['over_limit']} skills",
        (
            f"- **Average Tokens per Skill:** "
            f"{summary['token_efficiency']['average_tokens']:,}"
        ),
        "",
        "## Compliance",
        "",
        f"- **Compliant Skills:** {summary['compliant_skills']}",
        f"- **Compliance Issues:** {summary['compliance_issues']}",
        "",
    ]

    if issues:
        lines.extend(["### Issues Found", ""])
        for issue in issues[
            :MAX_ISSUES_DISPLAY
        ]:  # Limit to first MAX_ISSUES_DISPLAY issues
            lines.append(f"- {issue}")

        if len(issues) > MAX_ISSUES_DISPLAY:
            lines.append(f"- ... and {len(issues) - MAX_ISSUES_DISPLAY} more issues")

    lines.extend(
        [
            "",
            "## Detailed Reports",
            "",
            "- `skills_analysis_report.json` - Complete analysis data",
            "- Individual skill details available in the JSON report",
            "",
        ],
    )

    return "\n".join(lines)


def main() -> None:
    """Run the batch skills analyzer."""
    parser = argparse.ArgumentParser(
        description="Batch analyze skills and generate comprehensive reports",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default="skills",
        help="Directory containing skills (default: skills)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="reports",
        help="Output directory for reports (default: reports)",
    )

    args = parser.parse_args()

    if not Path(args.skills_dir).exists():
        sys.exit(1)

    try:
        generate_batch_report(args.skills_dir, args.output_dir)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
