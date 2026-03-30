#!/usr/bin/env python3
"""CLI wrapper for skills-auditor script.

Uses core functionality from src/abstract/skills_eval.
"""

from datetime import datetime
from pathlib import Path

from cli_scaffold import create_parser, format_result, setup_src_path, write_output

setup_src_path()

from abstract.skills_eval import (  # noqa: E402 - import after setup_src_path() call
    SkillsAuditor as CoreSkillsAuditor,
)


class SkillsAuditor(CoreSkillsAuditor):
    """CLI wrapper for core skills auditing functionality."""


def _format_audit_text(results: dict, skills_dir: Path) -> str:
    """Format audit results as readable text."""
    lines = [
        "# Skills Audit Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Skills Directory:** {skills_dir}",
        "",
        "## Summary",
        f"- **Total Skills:** {results['total_skills']}",
        f"- **Average Score:** {results['average_score']:.1f}/100",
        f"- **Well Structured (>=80):** {results['well_structured']}",
        f"- **Needs Improvement (<70):** {results['needs_improvement']}",
        "",
    ]
    if results["recommendations"]:
        lines.extend(["## Recommendations", ""])
        for rec in results["recommendations"]:
            lines.append(f"- {rec}")
    return "\n".join(lines)


# For direct execution
if __name__ == "__main__":
    parser = create_parser(
        "Audit skills and generate detailed reports",
        add_format=True,
    )
    parser.add_argument(
        "skills_dir",
        type=Path,
        help="Directory containing skills to audit",
    )

    args = parser.parse_args()

    auditor = SkillsAuditor(args.skills_dir)
    results = auditor.audit_skills()
    output = format_result(
        results,
        fmt=args.format,
        text_fn=lambda r: _format_audit_text(r, args.skills_dir),
    )
    write_output(output, args.output)
