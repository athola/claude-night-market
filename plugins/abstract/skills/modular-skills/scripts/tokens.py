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
        help="File to analyze (default: SKILL.md)"
    )

    args = parser.parse_args()

    try:
        result = estimate_tokens(args.file)

        print("\n🔤 Token Estimation Results")
        print(f"📁 File: {Path(result['file_path']).name}")
        print("="*50)
        print(f"📊 Total tokens: {result['total_tokens']:,}")
        print(f"📝 Frontmatter: {result['frontmatter_tokens']:,}")
        print(f"📄 Body content: {result['body_tokens']:,}")
        print(f"💻 Code blocks: {result['code_tokens']:,} ({result['code_blocks_count']} blocks)")

        # Visual breakdown
        total = result['total_tokens']
        if total > 0:
            print("\n📈 Token Breakdown:")
            frontmatter_pct = (result['frontmatter_tokens'] / total) * 100
            body_pct = (result['body_tokens'] / total) * 100
            code_pct = (result['code_tokens'] / total) * 100

            print(f"   📝 Frontmatter: {frontmatter_pct:.1f}%")
            print(f"   📄 Body: {body_pct:.1f}%")
            print(f"   💻 Code: {code_pct:.1f}%")

        # Context window analysis
        context_4k = 4096
        context_8k = 8192
        context_32k = 32768

        print("\n🎯 Context Window Analysis:")
        print(f"   4K context: {(total / context_4k) * 100:.1f}% used")
        print(f"   8K context: {(total / context_8k) * 100:.1f}% used")
        print(f"   32K context: {(total / context_32k) * 100:.1f}% used")

        # Recommendations
        print("\n💡 Recommendations:")
        if total > 4000:
            print("   ⚠️  Consider modularizing for smaller context windows")
        if result['code_tokens'] > total * 0.3:
            print("   💡 High code-to-text ratio - consider externalizing code examples")
        if result['frontmatter_tokens'] > 500:
            print("   📝 Large frontmatter - consider moving some content to body")

        print("\n✨ Done!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
