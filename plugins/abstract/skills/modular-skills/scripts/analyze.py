#!/usr/bin/env python3
"""Skill analyzer wrapper for modular-skills.

This script provides a convenient way to analyze skills from within
the modular-skills directory, using the shared tooling.

Usage:
    python scripts/analyze.py                    # Analyze current skill
    python scripts/analyze.py --threshold 100   # Custom threshold
    python scripts/analyze.py --path ../other-skill  # Analyze different skill
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from abstract.skill_tools import analyze_skill  # noqa: E402

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze skill complexity and token usage"
    )
    parser.add_argument(
        "--path", default=".", help="Path to analyze (default: current directory)"
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

        print("\n📊 Skill Analysis Results")
        print(f"📁 Analyzed: {result['path']}")
        print(f"📄 Files found: {result['total_files']}")
        print(f"⚠️  Threshold: {args.threshold} lines")

        if result["results"]:
            print("\n" + "=" * 60)
            for r in result["results"]:
                if "error" in r:
                    print(f"❌ {Path(r['path']).name}: {r['error']}")
                else:
                    status = "⚠️" if r["above_threshold"] else "✅"
                    print(f"{status} {Path(r['path']).name}")
                    print(f"   📏 Lines: {r['lines']:,}")
                    print(f"   🔤 Tokens: {r['tokens']:,}")
                    print(f"   📦 Code blocks: {r['code_blocks']}")
                    print(f"   🏷️  Complexity: {r['complexity']}")
                    print()

        # Summary
        above_threshold = sum(
            1 for r in result["results"] if r.get("above_threshold", False)
        )
        total_tokens = sum(r.get("tokens", 0) for r in result["results"])

        print("=" * 60)
        print("📈 Summary:")
        print(f"   Above threshold: {above_threshold}/{result['total_files']}")
        print(f"   Total tokens: {total_tokens:,}")

        if above_threshold > 0:
            print(f"\n💡 Consider modularizing files above {args.threshold} lines")

        print("\n✨ Done!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
