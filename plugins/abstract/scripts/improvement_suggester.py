#!/usr/bin/env python3
"""CLI wrapper for improvement-suggester script.

Uses core functionality from src/abstract/skills_eval.
"""

import sys
from pathlib import Path

from cli_scaffold import create_parser, format_result, setup_src_path, write_output

setup_src_path()

from abstract.skills_eval import (
    ImprovementSuggester as CoreImprovementSuggester,
)


class ImprovementSuggester(CoreImprovementSuggester):
    """CLI wrapper for core improvement suggestion functionality."""


# For direct execution
if __name__ == "__main__":
    parser = create_parser(
        "Generate improvement suggestions for skills",
        add_format=True,
    )
    parser.add_argument("skill_path", type=Path, help="Path to skill file or directory")

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
        args.skill_path.parent if args.skill_path.is_file() else args.skill_path,
    )
    output = format_result(
        suggester.generate_improvement_plan(skill_name),
        fmt=args.format,
    )
    write_output(output, args.output)
