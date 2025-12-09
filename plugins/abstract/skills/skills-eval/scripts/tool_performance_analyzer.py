#!/usr/bin/env python3
"""CLI wrapper for tool-performance-analyzer script.

Uses core functionality from src/abstract/skills_eval.
"""

import os
import subprocess  # nosec: B404
import sys
import time
from pathlib import Path

# Add src to path to import core functionality
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class ToolPerformanceAnalyzer:
    """CLI wrapper for tool performance analysis functionality."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    def analyze_tools(self) -> dict:
        """Analyze performance of all tools in skills directory."""
        tools = {}
        for file_path in self.skills_dir.rglob("*"):
            if (
                file_path.is_file()
                and os.access(file_path, os.X_OK)
                and not file_path.name.startswith(".")
                and "test" not in file_path.name.lower()
            ):
                tools[file_path.name] = file_path

        results = {"total_tools": len(tools), "tools": {}}

        for tool_name, tool_path in tools.items():
            try:
                start_time = time.time()
                result = subprocess.run(  # nosec: B603
                    [str(tool_path), "--help"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                execution_time = time.time() - start_time

                results["tools"][tool_name] = {
                    "execution_time": execution_time,
                    "exit_code": result.returncode,
                    "output_length": len(result.stdout) + len(result.stderr),
                    "success": result.returncode == 0,
                }
            except subprocess.TimeoutExpired:
                results["tools"][tool_name] = {
                    "execution_time": 5.0,
                    "exit_code": -1,
                    "output_length": 0,
                    "success": False,
                    "timeout": True,
                }
            except Exception:
                results["tools"][tool_name] = {
                    "execution_time": 0.0,
                    "exit_code": -1,
                    "output_length": 0,
                    "success": False,
                    "error": True,
                }

        return results

    def get_performance_report(self) -> str:
        """Generate formatted performance report."""
        results = self.analyze_tools()

        lines = [
            "# Tool Performance Report",
            f"**Skills Directory:** {self.skills_dir}",
            "",
            "## Summary",
            f"- **Total Tools:** {results['total_tools']}",
            "",
        ]

        if results["tools"]:
            lines.extend(
                [
                    "## Detailed Results",
                    "",
                    "| Tool | Execution Time | Success | Output Length |",
                    "|------|----------------|---------|---------------|",
                ]
            )

            for tool_name, perf in results["tools"].items():
                status = "✅" if perf["success"] else "❌"
                " (timeout)" if perf.get("timeout") else ""
                " (error)" if perf.get("error") else ""

                lines.append(
                    f"| {status} {tool_name} | {perf['execution_time']:.3f}s | "
                    f"{perf['success']} | {perf['output_length']} |"
                )

        return "\n".join(lines)


# For direct execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze performance of tools")

    parser.add_argument(
        "skills_dir", type=Path, help="Directory containing skills/tools to analyze"
    )
    parser.add_argument("--output", type=Path, help="Output file path")

    args = parser.parse_args()

    analyzer = ToolPerformanceAnalyzer(args.skills_dir)
    output = analyzer.get_performance_report()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Performance analysis saved to {args.output}")
    else:
        print(output)
