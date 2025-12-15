#!/usr/bin/env python3
"""CLI wrapper for compliance-checker script.

Uses core functionality from src/abstract/skills_eval.
"""

import sys
from pathlib import Path

# Add src to path to import core functionality
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from abstract.skills_eval import (  # noqa: E402
    ComplianceChecker as CoreComplianceChecker,
)


class ComplianceChecker(CoreComplianceChecker):
    """CLI wrapper for core compliance checking functionality."""


# For direct execution
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Check compliance of skills in directory",
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing skills to check",
    )
    parser.add_argument("--rules-file", type=Path, help="Custom rules file")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    checker = ComplianceChecker(args.directory, args.rules_file)

    if args.format == "json":
        results = checker.check_compliance()
        output = json.dumps(results, indent=2)
    else:
        output = checker.generate_report()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        pass
