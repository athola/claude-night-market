#!/usr/bin/env python3
"""Token Usage Estimator for Skills - Estimates token usage for skill files.

Uses centralized utilities from abstract.base and abstract.utils.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Set up imports before using abstract package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.cli_framework import (  # noqa: E402
    AbstractCLI,
    CLIResult,
    PathArgumentMixin,
    cli_main,
)
from abstract.tokens import TokenAnalyzer  # noqa: E402
from abstract.utils import (  # noqa: E402
    extract_dependencies,
    find_dependency_file,
    find_skill_files,
    parse_yaml_frontmatter,
)

# Token usage thresholds
OPTIMAL_MIN = 800
OPTIMAL_MAX = 2000
CONSIDER_MAX = 3000


class TokenEstimator:
    """Estimates token usage for skill files."""

    def analyze_file(self, file_path: Path, include_dependencies: bool = False) -> dict:
        """Analyze a single skill file for token usage.

        Args:
            file_path: Path to the skill file.
            include_dependencies: Whether to include dependency token counts.

        Returns:
            Dictionary containing token analysis.

        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        content = file_path.read_text(encoding="utf-8")

        # Use TokenAnalyzer for token analysis
        analysis = TokenAnalyzer.analyze_content(content)

        # Parse frontmatter for dependencies
        frontmatter_dict = parse_yaml_frontmatter(content)
        dependencies = extract_dependencies(frontmatter_dict)

        result = {
            "file": str(file_path),
            "total_tokens": analysis["total_tokens"],
            "frontmatter_tokens": analysis["frontmatter_tokens"],
            "body_tokens": analysis["body_tokens"],
            "code_tokens": analysis["code_tokens"],
            "dependencies": dependencies,
            "character_count": analysis["char_count"],
            "line_count": len(content.splitlines()),
        }

        # Add dependency analysis if requested
        if include_dependencies and dependencies:
            dependency_tokens = 0
            missing_deps = []

            for dep in dependencies:
                # Use shared utility to find dependency
                dep_file = find_dependency_file(file_path, dep)

                if dep_file:
                    try:
                        dep_analysis = self.analyze_file(
                            dep_file,
                            include_dependencies=False,
                        )
                        dependency_tokens += dep_analysis["total_tokens"]
                    except Exception:
                        missing_deps.append(dep)
                else:
                    missing_deps.append(dep)

            result["dependency_tokens"] = dependency_tokens
            result["missing_dependencies"] = missing_deps
            result["total_with_dependencies"] = (
                result["total_tokens"] + dependency_tokens
            )

        return result

    def format_analysis(
        self,
        analysis: dict,
        include_dependencies: bool = False,
    ) -> str:
        """Format analysis results for display.

        Args:
            analysis: Analysis results dictionary.
            include_dependencies: Whether to include dependency information.

        Returns:
            Formatted string output.

        """
        lines = [
            f"=== {analysis['file']} ===",
            f"Total tokens: {analysis['total_tokens']:,}",
            f"Character count: {analysis['character_count']:,}",
            f"Line count: {analysis['line_count']:,}",
            "",
            "Component breakdown:",
            f"  Frontmatter: {analysis['frontmatter_tokens']:,} tokens",
            f"  Body content: {analysis['body_tokens']:,} tokens",
            f"  Code blocks: {analysis['code_tokens']:,} tokens",
        ]

        if analysis["dependencies"]:
            lines.extend(
                [
                    "",
                    f"Dependencies: {len(analysis['dependencies'])}",
                    f"  {', '.join(analysis['dependencies'])}",
                ],
            )

        if include_dependencies:
            if "dependency_tokens" in analysis:
                lines.extend(
                    [
                        "",
                        f"Dependency tokens: {analysis['dependency_tokens']:,}",
                        (
                            f"Total with dependencies: "
                            f"{analysis['total_with_dependencies']:,}"
                        ),
                    ],
                )

            if analysis.get("missing_dependencies"):
                lines.extend(
                    [
                        "",
                        (
                            f"Missing dependencies: "
                            f"{len(analysis['missing_dependencies'])}"
                        ),
                        (f"  {', '.join(analysis['missing_dependencies'])}"),
                    ],
                )

        # Recommendations
        lines.extend(["", "=== Recommendations ==="])

        total = analysis.get("total_with_dependencies", analysis["total_tokens"])

        if total <= OPTIMAL_MIN:
            lines.append("OPTIMAL: Low token usage, excellent for quick loading")
        elif total <= OPTIMAL_MAX:
            lines.append("GOOD: Optimal token range (800-2000 tokens)")
        elif total <= CONSIDER_MAX:
            lines.append("CONSIDER: Moderate token usage, consider modularization")
        else:
            lines.append("MODULARIZE: High token usage (>3000 tokens)")

        if analysis["code_tokens"] > analysis["body_tokens"]:
            lines.append(
                "CONSIDER: Extract code examples to scripts/ directory "
                "for better efficiency",
            )

        lines.append("")
        return "\n".join(lines)

    def analyze_directory(
        self,
        dir_path: Path,
        include_dependencies: bool = False,
    ) -> list[dict]:
        """Analyze all skill files in a directory.

        Args:
            dir_path: Path to directory containing skill files.
            include_dependencies: Whether to include dependency token counts.

        Returns:
            List of analysis results for each file.

        """
        skill_files = find_skill_files(dir_path)

        if not skill_files:
            return []

        results = []
        for skill_file in skill_files:
            try:
                result = self.analyze_file(skill_file, include_dependencies)
                results.append(result)
            except Exception as e:
                logger.debug(f"Failed to analyze {skill_file}: {e}")

        return results


class TokenEstimatorCLI(AbstractCLI, PathArgumentMixin):
    """CLI for token estimation."""

    def __init__(self) -> None:
        """Initialize the token estimator CLI."""
        super().__init__(
            name="token-estimator",
            description="Estimate token usage for skill files and dependencies.",
            version="1.0.0",
        )
        self.estimator = TokenEstimator()

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add tool-specific arguments."""
        self.add_path_arguments(
            parser,
            file_help="Path to skill file to analyze",
            dir_help="Path to directory containing skill files",
            require_one=True,
        )
        parser.add_argument(
            "--include-dependencies",
            action="store_true",
            help="Include dependency token counts",
        )

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute the CLI command."""
        results = []

        if args.file:
            try:
                result = self.estimator.analyze_file(
                    args.file,
                    args.include_dependencies,
                )
                results = [result]
            except Exception as e:
                return CLIResult(success=False, error=str(e))
        else:  # directory
            all_results = self.estimator.analyze_directory(
                args.directory,
                args.include_dependencies,
            )
            if not all_results:
                return CLIResult(
                    success=True,
                    data=[],
                    warnings=["No skill files found in directory"],
                )
            results = all_results

        return CLIResult(success=True, data=results)

    def format_text(self, data: Any) -> str:
        """Format token analysis results as text."""
        if isinstance(data, list):
            lines = []
            for result in data:
                analysis = self.estimator.format_analysis(
                    result,
                    hasattr(self, "_args") and self._args.include_dependencies,
                )
                lines.append(analysis)
                if len(data) > 1:
                    lines.append("-" * 50)
            return "\n".join(lines)
        return self.estimator.format_analysis(data, False)


def main() -> None:
    """Entry point for the CLI."""
    cli_main(TokenEstimatorCLI)


if __name__ == "__main__":
    main()
