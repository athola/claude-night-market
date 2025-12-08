#!/usr/bin/env python3
"""Setup script for Skills Evaluation Framework.

Ensures all tools are executable and dependencies are available.
"""

import stat
import subprocess  # nosec: B404
import sys
from pathlib import Path


def setup_skills_eval():
    """Set up the skills-eval framework."""
    print("Setting up Skills Evaluation Framework...")

    # Get script directory
    script_dir = Path(__file__).parent
    skills_eval_dir = script_dir.parent.parent
    modular_skills_dir = skills_eval_dir.parent / "modular-skills"

    # Check required directories exist
    required_dirs = [skills_eval_dir, modular_skills_dir]
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"Error: Required directory {dir_path} not found")
            return False

    # Make tools executable
    tools = [
        skills_eval_dir / "tools" / "skills-auditor",
        skills_eval_dir / "tools" / "improvement-suggester",
        skills_eval_dir / "tools" / "compliance-checker",
        modular_skills_dir / "tools" / "skill-analyzer",
        modular_skills_dir / "tools" / "token-estimator",
        modular_skills_dir / "tools" / "module-validator",
    ]

    for tool in tools:
        if tool.exists():
            current_mode = tool.stat().st_mode
            tool.chmod(current_mode | stat.S_IEXEC)
            print(f"Made {tool.name} executable")
        else:
            print(f"Warning: Tool {tool} not found")

    # Test basic functionality
    print("\nTesting tools...")

    # Test skills-auditor
    auditor = skills_eval_dir / "tools" / "skills-auditor"
    if auditor.exists():
        try:
            result = subprocess.run(  # noqa: S603  # nosec: B603
                [str(auditor), "--help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print("✓ skills-auditor working")
            else:
                print(f"⚠ skills-auditor may have issues: {result.stderr[:100]}")
        except Exception as e:
            print(f"⚠ skills-auditor test failed: {e}")

    print("\nSetup complete!")
    return True


def main():
    """Run the setup process."""
    if setup_skills_eval():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
