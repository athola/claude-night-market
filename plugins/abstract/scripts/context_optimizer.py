#!/usr/bin/env python3
"""Context window optimization for abstract skills.

Uses centralized utilities from abstract.base and abstract.utils.
"""

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

# Set up imports before using abstract package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.cli_framework import AbstractCLI, CLIResult, cli_main
from abstract.config import AbstractConfig
from abstract.tokens import estimate_tokens
from abstract.utils import (
    extract_frontmatter,
    find_project_root,
    find_skill_files,
    load_config_with_fallback,
)


class ContextOptimizer:
    """Optimizes skill content loading for better context window management."""

    def __init__(self, config: AbstractConfig):
        """Initialize context optimizer with configuration."""
        self.config = config
        self.optimizer_config = config.context_optimizer

    def analyze_skill_size(self, skill_path: Path) -> dict[str, Any]:
        """Analyze skill file size and categorize for context optimization."""
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        size = skill_path.stat().st_size

        # Determine size category
        if size <= self.optimizer_config.SMALL_SIZE_LIMIT:
            category = "small"
        elif size <= self.optimizer_config.MEDIUM_SIZE_LIMIT:
            category = "medium"
        elif size <= self.optimizer_config.LARGE_SIZE_LIMIT:
            category = "large"
        else:
            category = "xlarge"

        return {
            "bytes": size,
            "category": category,
            "estimated_tokens": estimate_tokens(skill_path.read_text()),
        }

    def extract_content_summary(self, content: str, max_section_lines: int) -> str:
        """Extract a summary of content based on sections."""
        frontmatter, body = extract_frontmatter(content)

        # Extract main sections (headers)
        lines = body.split("\n")
        summary_lines = [frontmatter] if frontmatter else []
        current_section: list[str] = []

        for line in lines:
            if line.startswith("#"):  # Section header
                if current_section:
                    # Add first few lines of previous section
                    summary_lines.extend(current_section[:max_section_lines])
                    current_section = []
                summary_lines.append(line)
            else:
                current_section.append(line)

        # Add last section
        if current_section:
            summary_lines.extend(current_section[:max_section_lines])

        return "\n".join(summary_lines)

    def analyze_directory(self, directory: Path) -> list[dict[str, Any]]:
        """Analyze all skill files in a directory."""
        results = []

        for skill_file in find_skill_files(directory):
            try:
                size_info = self.analyze_skill_size(skill_file)
                results.append(
                    {
                        "path": str(skill_file.relative_to(directory)),
                        "absolute_path": str(skill_file),
                        **size_info,
                    }
                )
            except Exception as e:
                print(f"WARNING: Failed to analyze {skill_file}: {e}", file=sys.stderr)

        return sorted(results, key=lambda x: x["bytes"], reverse=True)

    def report_statistics(self, results: list[dict[str, Any]]) -> None:
        """Print statistics about skill files."""
        if not results:
            print("No skill files found.")
            return

        total_files = len(results)
        total_size = sum(r["bytes"] for r in results)
        total_tokens = sum(r["estimated_tokens"] for r in results)

        categories = {"small": 0, "medium": 0, "large": 0, "xlarge": 0}
        for r in results:
            categories[r["category"]] += 1

        print("\nContext Optimization Analysis")
        print(f"{'=' * 50}")
        print(f"Total Skills: {total_files}")
        print(f"Total Size: {total_size:,} bytes")
        print(f"Estimated Tokens: {total_tokens:,}")
        print("\nSize Distribution:")
        print(f"  Small (<2KB):   {categories['small']:3d} files")
        print(f"  Medium (2-5KB): {categories['medium']:3d} files")
        print(f"  Large (5-15KB): {categories['large']:3d} files")
        print(f"  XLarge (>15KB): {categories['xlarge']:3d} files")

        if categories["xlarge"] > 0:
            print(f"\nRecommendation: {categories['xlarge']} file(s) exceed 15KB")
            print("Consider using progressive disclosure or modularization")


class ContextOptimizerCLI(AbstractCLI):
    """CLI for context optimization."""

    def __init__(self) -> None:
        """Initialize the context optimizer CLI."""
        super().__init__(
            name="context-optimizer",
            description="Analyze and optimize skill files for context window usage",
            version="1.0.0",
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add tool-specific arguments."""
        parser.add_argument(
            "command",
            choices=["analyze", "report", "stats"],
            help="Command to run",
        )
        parser.add_argument("path", type=Path, help="Path to skill file or directory")

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute the CLI command."""
        # Load configuration
        if args.config:
            config = AbstractConfig.from_yaml(args.config)
        else:
            project_root = find_project_root(args.path)
            config = load_config_with_fallback(project_root)

        optimizer = ContextOptimizer(config)

        try:
            if args.command == "analyze":
                size_info = optimizer.analyze_skill_size(args.path)
                return CLIResult(
                    success=True,
                    data={"command": "analyze", "path": str(args.path), **size_info},
                )

            elif args.command in ("report", "stats"):
                results = optimizer.analyze_directory(args.path)
                return CLIResult(
                    success=True,
                    data={
                        "command": args.command,
                        "results": results,
                        "optimizer": optimizer,
                    },
                )
        except Exception as e:
            return CLIResult(success=False, error=str(e))

        # Handle unknown commands
        return CLIResult(success=False, error=f"Unknown command: {args.command}")

    def format_text(self, data: Any) -> str:
        """Format context optimization results as text."""
        if data["command"] == "analyze":
            lines = [
                f"\nSkill File: {data['path']}",
                f"Size: {data['bytes']:,} bytes",
                f"Category: {data['category']}",
                f"Estimated Tokens: {data['estimated_tokens']:,}",
            ]
            return "\n".join(lines)

        else:  # report or stats
            optimizer = data["optimizer"]
            results = data["results"]

            # Get statistics output
            f = io.StringIO()
            with redirect_stdout(f):
                optimizer.report_statistics(results)

            output = f.getvalue()

            if data["command"] == "report":
                output += "\n\nDetailed Results:\n"
                output += f"{'Path':<50} {'Size':>10} {'Category':>10} {'Tokens':>10}\n"
                output += f"{'-' * 82}\n"
                for r in results:
                    output += (
                        f"{r['path']:<50} {r['bytes']:>10,} "
                        f"{r['category']:>10} {r['estimated_tokens']:>10,}\n"
                    )

            return output


def main() -> None:
    """Entry point for the CLI."""
    cli_main(ContextOptimizerCLI)


if __name__ == "__main__":
    main()
