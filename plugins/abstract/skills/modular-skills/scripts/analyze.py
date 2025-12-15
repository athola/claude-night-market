#!/usr/bin/env python3
"""Skill analyzer wrapper for modular-skills.

This script provides a convenient way to analyze skills from within
the modular-skills directory, using the shared tooling.

Usage:
    python scripts/analyze.py                    # Analyze current skill
    python scripts/analyze.py --threshold 100   # Custom threshold
    python scripts/analyze.py --path ../other-skill  # Analyze different skill
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from abstract.skill_tools import analyze_skill  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze skill complexity and token usage",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to analyze (default: current directory)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=150,
        help="Line count threshold for complexity warnings (default: 150)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        result = analyze_skill(args.path, args.threshold, args.verbose)

        if result["results"]:
            for r in result["results"]:
                if "error" in r:
                    pass
                else:
                    status = "⚠️" if r["above_threshold"] else "✅"

        # Summary
        above_threshold = sum(
            1 for r in result["results"] if r.get("above_threshold", False)
        )
        total_tokens = sum(r.get("tokens", 0) for r in result["results"])

        if above_threshold > 0:
            pass

    except Exception:
        sys.exit(1)
