#!/usr/bin/env python3
"""CLI wrapper for improvement-suggester script.

Uses core functionality from src/abstract/skills_eval.
"""

import sys
from pathlib import Path

# Add src to path to import core functionality
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


from abstract.skills_eval import (  # noqa: E402
    ImprovementSuggester as CoreImprovementSuggester,
)


class ImprovementSuggester(CoreImprovementSuggester):
    """CLI wrapper for core improvement suggestion functionality."""


# For direct execution
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Generate improvement suggestions for skills",
    )

    parser.add_argument("skill_path", type=Path, help="Path to skill file or directory")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--output", type=Path, help="Output file path")

    args = parser.parse_args()

    # Handle both SKILL.md files and directories
    if args.skill_path.is_dir():
        skill_file = args.skill_path / "SKILL.md"
        if not skill_file.exists():
            sys.exit(1)
        skill_name = args.skill_path.name
    else:
        skill_name = args.skill_path.parent.name

    suggester = ImprovementSuggester(
        args.skill_path.parent if args.skill_path.is_file() else args.skill_path.parent,
    )

    if args.format == "json":
        plan = suggester.generate_improvement_plan(skill_name)
        output = json.dumps(plan, indent=2, default=str)
    else:
        output = suggester.generate_improvement_plan(skill_name)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        pass
