#!/usr/bin/env python3
"""CLI wrapper for improvement-suggester script.

Uses core functionality from src/abstract/skills_eval.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cli_scaffold import create_parser, format_result, setup_src_path, write_output

setup_src_path()

from abstract.skills_eval import (  # noqa: E402 - import after setup_src_path() call
    ImprovementSuggester,
)

# For direct execution
if __name__ == "__main__":
    parser = create_parser(
        "Generate improvement suggestions for skills",
        add_format=True,
    )
    parser.add_argument("skill_path", type=Path, help="Path to skill file or directory")

    args = parser.parse_args()

    # Accept a skill directory or its SKILL.md. ImprovementSuggester takes
    # the directory that holds skills and looks up <dir>/<name>/SKILL.md.
    skill_dir = args.skill_path if args.skill_path.is_dir() else args.skill_path.parent
    if not (skill_dir / "SKILL.md").exists():
        sys.exit(1)

    suggester = ImprovementSuggester(skill_dir.parent)
    skill_name = skill_dir.name
    output = format_result(
        suggester.generate_improvement_plan(skill_name),
        fmt=args.format,
    )
    if not write_output(output, args.output):
        sys.exit(1)
