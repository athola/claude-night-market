#!/usr/bin/env python3
"""CLI for tool-performance analysis.

Discovery, probing, timeouts and error rows come from
``abstract.skills_eval.performance``. This file keeps only what the CLI
does differently: it probes with ``--help``, keys rows by tool name, and
renders its own table.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from cli_scaffold import create_parser, setup_src_path, write_output

setup_src_path()

from abstract.skills_eval.performance import (  # noqa: E402 - import after setup_src_path() call
    ToolPerformanceAnalyzer as _LibraryAnalyzer,
)


class ToolPerformanceAnalyzer(_LibraryAnalyzer):
    """CLI wrapper for tool performance analysis functionality."""

    PROBE_ARGS = ("--help",)

    def analyze_tools(self) -> dict[str, Any]:
        """Probe every tool, keyed by name as the report expects."""
        tools: dict[str, Any] = {}
        for row in self.benchmark_all_tools()["tools"]:
            perf = {
                "execution_time": row["execution_time"],
                "exit_code": row.get("exit_code", -1),
                "output_length": row.get("output_length", 0),
                "success": row["success"],
            }
            for flag in ("timeout", "error"):
                if row.get(flag):
                    perf[flag] = True
            tools[row["name"]] = perf
        return {"total_tools": len(tools), "tools": tools}

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
                ],
            )

            for tool_name, perf in results["tools"].items():
                status = "OK" if perf["success"] else "FAIL"
                if perf.get("timeout"):
                    status += " (timeout)"
                if perf.get("error"):
                    status += " (error)"

                lines.append(
                    f"| {status} {tool_name} | {perf['execution_time']:.3f}s | "
                    f"{perf['success']} | {perf['output_length']} |",
                )

        return "\n".join(lines)


# For direct execution
if __name__ == "__main__":
    parser = create_parser("Analyze performance of tools")
    parser.add_argument(
        "skills_dir",
        type=Path,
        help="Directory containing skills/tools to analyze",
    )

    args = parser.parse_args()

    analyzer = ToolPerformanceAnalyzer(args.skills_dir)
    if not write_output(analyzer.get_performance_report(), args.output):
        sys.exit(1)
