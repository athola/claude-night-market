#!/usr/bin/env python3
"""CLI wrapper for skills-auditor script.

Uses core functionality from src/abstract/skills_eval.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path to import core functionality
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


from abstract.skills_eval import SkillsAuditor as CoreSkillsAuditor


class SkillsAuditor(CoreSkillsAuditor):
    """CLI wrapper for core skills auditing functionality."""


# For direct execution
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Audit skills and generate comprehensive reports",
    )

    parser.add_argument(
        "skills_dir",
        type=Path,
        help="Directory containing skills to audit",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--output", type=Path, help="Output file path")

    args = parser.parse_args()

    auditor = SkillsAuditor(args.skills_dir)

    if args.format == "json":
        results = auditor.audit_skills()
        output = json.dumps(results, indent=2, default=str)
    else:
        results = auditor.audit_skills()
        lines = [
            "# Skills Audit Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Skills Directory:** {args.skills_dir}",
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

        output = "\n".join(lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        pass
