#!/usr/bin/env python3
"""Validation script for Skills Evaluation Framework.

Validates skill structure and compliance.
"""

import argparse
import subprocess  # nosec: B404
import sys
from pathlib import Path


def validate_skill(skill_path):
    """Validate a single skill."""
    if not skill_path.exists():
        return False

    # Use modular-skills validator
    modular_skills_dir = Path(__file__).parent.parent.parent / "modular-skills"
    validator = modular_skills_dir / "tools" / "module-validator"

    if validator.exists():
        try:
            result = subprocess.run(  # noqa: S603  # nosec: B603
                [str(validator), "-s", str(skill_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stderr:
                pass

            return result.returncode == 0

        except Exception:
            return False
    else:
        return False


def validate_directory(directory):
    """Validate all skills in directory."""
    skill_files = list(Path(directory).glob("**/SKILL.md"))

    if not skill_files:
        return True

    success_count = 0
    total_count = len(skill_files)

    for skill_file in skill_files:
        if validate_skill(skill_file):
            success_count += 1

    return success_count == total_count


def check_dependencies() -> bool:
    """Check if required dependencies are available."""
    script_dir = Path(__file__).parent
    skills_eval_dir = script_dir.parent.parent
    modular_skills_dir = skills_eval_dir.parent / "modular-skills"

    # Check tools exist
    required_tools = [
        skills_eval_dir / "tools" / "compliance-checker",
        modular_skills_dir / "tools" / "skill-analyzer",
        modular_skills_dir / "tools" / "token-estimator",
    ]

    missing_tools = []
    for tool in required_tools:
        if not tool.exists():
            missing_tools.append(tool.name)
        else:
            pass

    return not missing_tools


def main() -> None:
    """Validate skills from command line."""
    parser = argparse.ArgumentParser(description="Validate skills")
    parser.add_argument("path", help="Path to skill file or directory")
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies only",
    )

    args = parser.parse_args()

    if args.check_deps:
        success = check_dependencies()
    else:
        path = Path(args.path)

        if path.is_file():
            success = validate_skill(path)
        elif path.is_dir():
            success = validate_directory(path)
        else:
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
