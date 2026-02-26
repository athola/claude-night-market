#!/usr/bin/env python3
"""Skill Complexity Analyzer.

Analyze skill files and suggest modularization strategies.
Use centralized utilities from abstract.base and abstract.utils.
"""

from __future__ import annotations

import argparse
import logging
import re
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
from abstract.tokens import TokenAnalyzer, extract_code_blocks  # noqa: E402
from abstract.utils import count_sections, find_skill_files  # noqa: E402

# Constants for analysis thresholds
MAX_THEMES = 3
MAX_SECTIONS = 2
HIGH_TOKEN_LIMIT = 2048
MODERATE_TOKEN_LIMIT = 1500


class SkillAnalyzer:
    """Analyze skill files for complexity and modularization opportunities."""

    def __init__(self, threshold: int = 150) -> None:
        """Initialize the analyzer.

        Args:
            threshold: Line count threshold for modularization recommendation.

        """
        self.threshold = threshold

    def analyze_file(self, file_path: Path, verbose: bool = False) -> dict:
        """Analyze a single skill file for complexity.

        Args:
            file_path: Path to the skill file.
            verbose: Enable detailed output.

        Returns:
            Dictionary containing analysis results.

        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Basic metrics
        line_count = len(lines)
        word_count = len(content.split())
        char_count = len(content)

        # Extract themes/sections using shared utilities
        themes = count_sections(content, level=1)
        subsections = count_sections(content, level=2)
        code_blocks = len(extract_code_blocks(content))
        multiple_sections = themes

        # Token estimation using TokenAnalyzer
        estimated_tokens = TokenAnalyzer.analyze_content(content)["total_tokens"]

        # Build analysis result
        result = {
            "file": str(file_path),
            "line_count": line_count,
            "word_count": word_count,
            "char_count": char_count,
            "themes": themes,
            "subsections": subsections,
            "code_blocks": code_blocks,
            "estimated_tokens": estimated_tokens,
            "recommendations": self._generate_recommendations(
                line_count,
                themes,
                multiple_sections,
                estimated_tokens,
            ),
        }

        if verbose:
            result["main_sections"] = [
                line.strip() for line in lines if re.match(r"^#\s+", line)
            ][:10]
            result["sub_sections"] = [
                line.strip() for line in lines if re.match(r"^##\s+", line)
            ][:10]

        return result

    def _generate_recommendations(
        self,
        line_count: int,
        themes: int,
        sections: int,
        tokens: int,
    ) -> list[str]:
        """Generate modularization recommendations.

        Args:
            line_count: Number of lines in the file.
            themes: Number of main themes/sections.
            sections: Number of major sections.
            tokens: Estimated token count.

        Returns:
            List of recommendation strings.

        """
        recommendations = []

        if line_count > self.threshold:
            recommendations.append(
                f"MODULARIZE: File exceeds threshold ({line_count} > {self.threshold})",
            )
        else:
            recommendations.append(
                f"OK: File within threshold ({line_count} <= {self.threshold})",
            )

        if themes > MAX_THEMES:
            recommendations.append(
                f"MODULARIZE: Multiple themes detected ({themes} themes)",
            )

        if sections > MAX_SECTIONS:
            recommendations.append(
                "CONSIDER: Multiple main sections - possible candidate "
                "for modularization",
            )

        if tokens > HIGH_TOKEN_LIMIT:
            recommendations.append(
                f"MODULARIZE: High token usage ({tokens} tokens >2KB)",
            )
        elif tokens > MODERATE_TOKEN_LIMIT:
            recommendations.append(
                f"CONSIDER: Moderate token usage ({tokens} tokens, "
                "approaching 2KB limit)",
            )

        return recommendations

    def format_analysis(self, analysis: dict, verbose: bool = False) -> str:
        """Format analysis results for display.

        Args:
            analysis: Analysis results dictionary.
            verbose: Enable detailed output.

        Returns:
            Formatted string output.

        """
        lines = [
            f"=== Analysis for: {analysis['file']} ===",
            f"Line count: {analysis['line_count']} (threshold: {self.threshold})",
            f"Word count: {analysis['word_count']:,}",
            f"Character count: {analysis['char_count']:,}",
            f"Theme sections: {analysis['themes']}",
            f"Sub-sections: {analysis['subsections']}",
            f"Code blocks: {analysis['code_blocks']}",
            f"Estimated tokens: {analysis['estimated_tokens']:,}",
            "",
            "=== Recommendations ===",
        ]

        lines.extend(analysis["recommendations"])

        if verbose and "main_sections" in analysis:
            lines.extend(
                [
                    "",
                    "=== Detailed Analysis ===",
                    "Main sections:",
                    *analysis["main_sections"],
                    "",
                    "Sub-sections:",
                    *analysis["sub_sections"],
                ],
            )

        lines.append("")
        return "\n".join(lines)

    def analyze_directory(self, dir_path: Path, verbose: bool = False) -> list[dict]:
        """Analyze all skill files in a directory.

        Args:
            dir_path: Path to directory containing skill files.
            verbose: Enable detailed output.

        Returns:
            List of analysis results for each file.

        """
        skill_files = find_skill_files(dir_path)

        if not skill_files:
            return []

        results = []
        for skill_file in skill_files:
            try:
                result = self.analyze_file(skill_file, verbose)
                results.append(result)
            except Exception as e:
                logger.debug(f"Failed to analyze {skill_file}: {e}")

        return results


class SkillAnalyzerCLI(AbstractCLI, PathArgumentMixin):
    """CLI for skill analysis."""

    def __init__(self) -> None:
        """Initialize the skill analyzer CLI."""
        super().__init__(
            name="skill-analyzer",
            description="Analyze skill files for complexity and suggest modularization",
            version="1.0.0",
        )
        self._analyzer: SkillAnalyzer | None = None
        self._verbose: bool = False

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add tool-specific arguments."""
        self.add_path_arguments(
            parser,
            file_help="Path to skill file to analyze",
            dir_help="Path to directory containing skill files",
            require_one=True,
        )
        parser.add_argument(
            "-t",
            "--threshold",
            type=int,
            default=150,
            help="Line count threshold (default: 150)",
        )
        # Verbose already handled by AbstractCLI

    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute the CLI command."""
        path = args.file or args.directory

        if not path.exists():
            return CLIResult(success=False, error=f"'{path}' does not exist")

        self._analyzer = SkillAnalyzer(threshold=args.threshold)
        self._verbose = args.verbose > 0

        try:
            if path.is_file():
                result = self._analyzer.analyze_file(path, self._verbose)
                return CLIResult(success=True, data=[result])
            # directory
            results = self._analyzer.analyze_directory(path, self._verbose)
            return CLIResult(success=True, data=results)
        except Exception as e:
            return CLIResult(success=False, error=str(e))

    def format_text(self, data: Any) -> str:
        """Format skill analysis results as text."""
        if not data:
            return "No results to display"

        # Store verbose flag for formatting
        # This is a bit of a hack since we don't have args in format_text
        # We could also override run() to store args if needed

        lines = []
        if self._analyzer is None:
            # Fallback formatting if analyzer not initialized
            for result in data:
                lines.append(f"Analysis: {result}")
        else:
            for i, result in enumerate(data):
                analysis = self._analyzer.format_analysis(
                    result,
                    getattr(self, "_verbose", False),
                )
                lines.append(analysis)
                if i < len(data) - 1:
                    lines.append("\n" + "-" * 50 + "\n")
        return "\n".join(lines)


def main() -> None:
    """Entry point for the CLI."""
    cli_main(SkillAnalyzerCLI)


if __name__ == "__main__":
    main()
