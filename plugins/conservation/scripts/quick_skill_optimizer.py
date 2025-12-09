#!/usr/bin/env python3
"""Quick skill optimizer - template for batch processing."""

import argparse
import os
import re


def extract_python_blocks(skill_file):
    """Extract all Python code blocks from skill file."""
    with open(skill_file) as f:
        content = f.read()

    # Find all python code blocks
    pattern = r"```python\n(.*?)\n```"
    blocks = re.findall(pattern, content, re.DOTALL)

    # Find functions >15 lines
    functions = []
    for i, block in enumerate(blocks):
        lines = block.split("\n")
        if len(lines) > 15:
            functions.append({"index": i, "lines": len(lines), "content": block})

    return functions


def create_tool_reference(function_name, tool_name) -> str:
    """Create standardized tool reference."""
    return f"""Uses `tools/{tool_name}.py` for {function_name.replace("_", " ")}:

```bash
# Basic usage
python tools/{tool_name}.py --input data.json

# Advanced options
python tools/{tool_name}.py --input data.json --verbose --output results.json
```"""


def quick_optimize_skill(skill_file):
    """Fast optimization focused on externalization."""
    # 1. Extract large functions
    functions = extract_python_blocks(skill_file)

    # 2. Create tool files
    skill_dir = os.path.dirname(skill_file)
    tools_dir = os.path.join(skill_dir, "tools")

    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)

    optimized_count = 0
    for func in functions:
        if func["lines"] > 15:
            # Extract to tool file
            tool_name = f"extracted_{optimized_count + 1}"
            tool_path = os.path.join(tools_dir, f"{tool_name}.py")

            with open(tool_path, "w") as f:
                f.write(f"""#!/usr/bin/env python3
\"\"\"
Extracted tool from skill optimization
\"\"\"

def extracted_function():
\"\"\"Extracted from {skill_file}\"\"\"
{func["content"]}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Extracted tool function')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default=None)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    result = extracted_function()
    if args.output:
        with open(args.output, 'w') as f:
            f.write(str(result))
    else:
        print(result)
""")
            os.chmod(tool_path, 0o755)
            optimized_count += 1

    # 3. Update skill file with references
    return optimized_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quick skill optimizer")
    parser.add_argument("skill_file", help="Skill file to optimize")
    parser.add_argument("--batch", action="store_true", help="Batch mode")
    args = parser.parse_args()

    if args.batch:
        # Process multiple files
        import glob

        skill_files = glob.glob("skills/**/SKILL.md", recursive=True)
        total_extracted = 0
        for skill_file in skill_files:
            total_extracted += quick_optimize_skill(skill_file)
    else:
        quick_optimize_skill(args.skill_file)
