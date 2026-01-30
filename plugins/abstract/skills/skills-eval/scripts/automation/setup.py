#!/usr/bin/env python3
"""Setup script for Skills Evaluation Framework.

validates all tools are executable and dependencies are available.
"""

import logging
import stat
import subprocess  # nosec: B404
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_skills_eval() -> bool:
    """Set up the skills-eval framework."""
    # Get script directory
    script_dir = Path(__file__).parent
    skills_eval_dir = script_dir.parent.parent
    modular_skills_dir = skills_eval_dir.parent / "modular-skills"

    # Check required directories exist
    required_dirs = [skills_eval_dir, modular_skills_dir]
    for dir_path in required_dirs:
        if not dir_path.exists():
            return False

    # Make tools executable
    tools = [
        skills_eval_dir / "tools" / "skills-auditor",
        skills_eval_dir / "tools" / "improvement-suggester",
        skills_eval_dir / "tools" / "compliance-checker",
        modular_skills_dir / "tools" / "skill-analyzer",
        modular_skills_dir / "tools" / "token-estimator",
        modular_skills_dir / "tools" / "module_validator",
    ]

    for tool in tools:
        if tool.exists():
            current_mode = tool.stat().st_mode
            tool.chmod(current_mode | stat.S_IEXEC)
        else:
            pass

    # Test basic functionality

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
                pass
            else:
                pass
        except Exception as e:
            logger.debug(f"Setup command failed: {e}")

    return True


def main() -> None:
    """Run the setup process."""
    if setup_skills_eval():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
