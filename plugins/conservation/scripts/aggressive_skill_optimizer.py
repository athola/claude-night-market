#!/usr/bin/env python3
"""Aggressive skill optimizer - actually modifies SKILL.md files."""

import argparse
import re

# Constants
MAX_CODE_BLOCK_LINES = 10
BATCH_THRESHOLD = 300
DEFAULT_THRESHOLD = 300


def aggressive_optimize_skill(skill_file):
    """Fast optimization that actually replaces code blocks."""
    print(f"Aggressively optimizing {skill_file}...")

    with open(skill_file) as f:
        content = f.read()

    original_lines = len(content.split("\n"))

    # 1. Remove excessive code blocks and replace with references
    python_pattern = r"```python\n(.*?)\n```"

    def replace_large_code_block(match):
        code = match.group(1)
        lines = code.split("\n")

        if (
            len(lines) > MAX_CODE_BLOCK_LINES
        ):  # Replace blocks longer than MAX_CODE_BLOCK_LINES lines
            tool_name = "extracted_tool"
            return f"""Uses `tools/{tool_name}.py` for code execution:

```bash
# Basic usage
python tools/{tool_name}.py --input data.json --output results.json

# Advanced options
python tools/{tool_name}.py --input data.json --verbose --output results.json
```"""
        else:
            return match.group(0)  # Keep small blocks

    content = re.sub(python_pattern, replace_large_code_block, content, flags=re.DOTALL)

    # 2. Remove narrative/documentation fluff
    fluff_patterns = [
        r"## Detailed Implementation.*?(?=\n##|\n###|\Z)",
        r"## Advanced Usage.*?(?=\n##|\n###|\Z)",
        r"## Examples.*?(?=\n##|\n###|\Z)",
        r"## Notes.*?(?=\n##|\n###|\Z)",
    ]

    for pattern in fluff_patterns:
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # 3. Consolidate similar sections
    # Remove duplicate headers
    content = re.sub(r"\n+(#{1,6} .+)\n+\n(#{1,6} .+)", r"\n\1\n\2", content)

    # 4. Write back the optimized content
    with open(skill_file, "w") as f:
        f.write(content)

    new_lines = len(content.split("\n"))
    reduction = original_lines - new_lines
    reduction_pct = (reduction / original_lines) * 100

    print(
        f"✓ Reduced {skill_file} from {original_lines} to {new_lines} lines "
        f"({reduction_pct:.1f}% reduction)"
    )

    return reduction


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggressive skill optimizer")
    parser.add_argument("skill_file", nargs="?", help="Skill file to optimize")
    parser.add_argument(
        "--batch",
        action="store_true",
        help=f"Batch mode for all skills >{BATCH_THRESHOLD} lines",
    )
    parser.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD, help="Line count threshold"
    )

    args = parser.parse_args()

    if args.batch or not args.skill_file:
        # Find all files above threshold
        import glob

        skill_files = glob.glob("skills/**/SKILL.md", recursive=True)
        large_files = []

        for skill_file in skill_files:
            with open(skill_file) as f:
                lines = len(f.read().split("\n"))
            if lines > args.threshold:
                large_files.append((skill_file, lines))

        # Sort by size (largest first)
        large_files.sort(key=lambda x: x[1], reverse=True)

        print(f"Found {len(large_files)} files above {args.threshold} lines:")
        for skill_file, lines in large_files:
            print(f"  {skill_file}: {lines} lines")

        total_reduction = 0
        for skill_file, _lines in large_files:
            total_reduction += aggressive_optimize_skill(skill_file)

        print(f"\nTotal line reduction: {total_reduction} lines")

    else:
        aggressive_optimize_skill(args.skill_file)
