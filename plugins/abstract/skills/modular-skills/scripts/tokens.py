#!/usr/bin/env python3
"""Token estimator wrapper for modular-skills.

This script provides a convenient way to estimate token usage from within
the modular-skills directory, using the shared tooling.

Usage:
    python scripts/tokens.py                    # Analyze current skill's SKILL.md
    python scripts/tokens.py --file module.md   # Analyze specific file
    python scripts/tokens.py --directory modules/  # Analyze directory
"""

import sys
from pathlib import Path

# Constants for magic numbers
LARGE_SKILL_THRESHOLD = 4000
LARGE_FRONTMATTER_THRESHOLD = 500

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from abstract.skill_tools import estimate_tokens

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Estimate token usage for skills")
    parser.add_argument(
        "--file",
        default="SKILL.md",
        help="File to analyze (default: SKILL.md)",
    )

    args = parser.parse_args()

    try:
        result = estimate_tokens(args.file)

        # Visual breakdown
        total = result["total_tokens"]
        if total > 0:
            frontmatter_pct = (result["frontmatter_tokens"] / total) * 100
            body_pct = (result["body_tokens"] / total) * 100
            code_pct = (result["code_tokens"] / total) * 100

        # Context window analysis
        context_4k = 4096
        context_8k = 8192
        context_32k = 32768

        # Recommendations
        if total > LARGE_SKILL_THRESHOLD:
            pass
        if result["code_tokens"] > total * 0.3:
            pass
        if result["frontmatter_tokens"] > LARGE_FRONTMATTER_THRESHOLD:
            pass

    except Exception:
        sys.exit(1)
