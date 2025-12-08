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
    print(f"\nValidating skill: {skill_path}")

    if not skill_path.exists():
        print(f"❌ Skill file not found: {skill_path}")
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

            print("Validation output:")
            print(result.stdout)

            if result.stderr:
                print("Validation errors:")
                print(result.stderr)

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    else:
        print("❌ Module validator not found")
        return False


def validate_directory(directory):
    """Validate all skills in directory."""
    print(f"Validating all skills in: {directory}")

    skill_files = list(Path(directory).glob("**/SKILL.md"))

    if not skill_files:
        print("No SKILL.md files found")
        return True

    success_count = 0
    total_count = len(skill_files)

    for skill_file in skill_files:
        if validate_skill(skill_file):
            success_count += 1

    print(f"\nValidation complete: {success_count}/{total_count} skills passed")
    return success_count == total_count


def check_dependencies():
    """Check if required dependencies are available."""
    print("Checking dependencies...")

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
            print(f"✓ {tool.name}")

    if missing_tools:
        print(f"❌ Missing tools: {missing_tools}")
        return False

    return True


def main():
    """Validate skills from command line."""
    parser = argparse.ArgumentParser(description="Validate skills")
    parser.add_argument("path", help="Path to skill file or directory")
    parser.add_argument(
        "--check-deps", action="store_true", help="Check dependencies only"
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
            print(f"❌ Invalid path: {path}")
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
