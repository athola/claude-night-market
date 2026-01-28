#!/usr/bin/env python3
"""Tool: Content Loader.

Description: On-demand content loading tool for progressive skill content
disclosure. Implements conditional loading based on user context and
requirements.

Usage: scripts/content_loader.py [--skill-path PATH] [--context CONTEXT]
[--format FORMAT].
"""

import argparse
import re
import sys
from pathlib import Path


class ContentLoader:
    """Handles progressive loading of skill content based on context and triggers."""

    def __init__(self, skill_path: str) -> None:
        """Initialize content loader with skill path.

        Args:
            skill_path: Path to the skill file to load.

        """
        self.skill_path = Path(skill_path)
        self.skill_content = self._load_skill_content()
        self.loading_markers = self._find_loading_markers()

    def _load_skill_content(self) -> list[str]:
        """Load skill content as lines."""
        try:
            with open(self.skill_path, encoding="utf-8") as f:
                return f.readlines()
        except FileNotFoundError as err:
            msg = f"Skill file not found: {self.skill_path}"
            raise FileNotFoundError(msg) from err

    def _find_loading_markers(self) -> dict[str, tuple[int, str]]:
        """Find all loading markers and their positions."""
        markers = {}
        marker_patterns = [
            r"<!--\s*(.*?)\s*-->",  # HTML-style comments
            r"<!--\s*MORE_CONTENT\s*-->",
            r"<!--\s*DETAILED_GUIDE\s*-->",
            r"<!--\s*ADVANCED_CONTENT\s*-->",
            r"<!--\s*NEED_EXAMPLES\?\s*-->",
            r"<!--\s*FULL_DESIGN_GUIDE_AVAILABLE\s*-->",
            r"<!--\s*FULL_EVALUATION_FRAMEWORK_AVAILABLE\s*-->",
            r"<!--\s*NEED_ADVANCED_METRICS\?\s*-->",
        ]

        for i, line in enumerate(self.skill_content):
            for pattern in marker_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    marker_type = match.group(1) if match.groups() else "MORE_CONTENT"
                    markers[marker_type] = (i, line.strip())
                    break

        return markers

    def load_quick_start(self) -> str:
        """Load only the essential quick-start content."""
        if self.skill_path.name == "QUICK_START.md":
            return "".join(self.skill_content)

        # Look for first loading marker or stop at reasonable length
        cutoff_line = len(self.skill_content)

        for line_num, _ in self.loading_markers.values():
            cutoff_line = min(cutoff_line, line_num)

        # Also limit by reasonable token count (roughly 50-60 lines)
        cutoff_line = min(cutoff_line, 60)

        return "".join(self.skill_content[:cutoff_line])

    def load_with_examples(self) -> str:
        """Load content including examples section."""
        content_lines = []

        # Load quick start content
        quick_content = self.load_quick_start()
        content_lines.extend(quick_content.split("\n"))

        # Add examples if marker exists
        example_markers = [
            k
            for k in self.loading_markers
            if "EXAMPLE" in k.upper() or "DETAILED" in k.upper()
        ]

        if example_markers:
            for marker in example_markers:
                marker_line = self.loading_markers[marker][0]
                # Load content after this marker until next marker or end
                remaining_content = self._load_section_after_marker(marker_line)
                content_lines.extend(remaining_content)
                break

        return "\n".join(content_lines)

    def load_advanced_content(self) -> str:
        """Load full content including advanced sections."""
        return "".join(self.skill_content)

    def _load_section_after_marker(self, marker_line: int) -> list[str]:
        """Load content section after a specific marker."""
        remaining_lines = self.skill_content[marker_line + 1 :]

        # Stop at next marker or reasonable boundary
        for i, line in enumerate(remaining_lines):
            if re.search(r"<!--\s*.*?\s*-->", line):
                return remaining_lines[:i]

        # Limit section size
        return remaining_lines[:80]

    def analyze_token_usage(self) -> dict[str, int | float]:
        """Analyze token usage for different loading levels."""
        quick_tokens = self._estimate_tokens(self.load_quick_start())
        examples_tokens = self._estimate_tokens(self.load_with_examples())
        full_tokens = self._estimate_tokens(self.load_advanced_content())

        return {
            "quick_start": quick_tokens,
            "with_examples": examples_tokens,
            "full_content": full_tokens,
            "savings_quick_vs_full": full_tokens - quick_tokens,
            "savings_percentage": round((1 - quick_tokens / full_tokens) * 100, 1),
        }

    def _estimate_tokens(self, content: str) -> int:
        """Rough token estimation (approximately 4 chars per token)."""
        return len(content) // 4

    def get_optimal_loading_level(self, user_context: dict[str, str]) -> str:
        """Determine optimal loading level based on user context."""
        # Check for explicit requests
        content = " ".join(user_context.get("query", "").lower().split())

        if any(
            keyword in content
            for keyword in ["advanced", "detailed", "detailed", "full"]
        ):
            return "full_content"
        if any(
            keyword in content
            for keyword in ["example", "how to", "implement", "step by step"]
        ):
            return "with_examples"
        return "quick_start"

    def load_optimal_content(self, user_context: dict[str, str] | None = None) -> str:
        """Load optimal content based on context."""
        if user_context is None:
            user_context = {}

        loading_level = self.get_optimal_loading_level(user_context)

        if loading_level == "full_content":
            return self.load_advanced_content()
        if loading_level == "with_examples":
            return self.load_with_examples()
        return self.load_quick_start()


def main() -> None:
    """Run the content loader CLI."""
    parser = argparse.ArgumentParser(
        description="Progressive content loader for skills",
    )
    parser.add_argument("skill_path", help="Path to skill file")
    parser.add_argument(
        "--mode",
        choices=["quick", "examples", "full", "optimal"],
        default="quick",
        help="Loading mode",
    )
    parser.add_argument("--query", help="User query for optimal loading")
    parser.add_argument("--analyze", action="store_true", help="Analyze token usage")
    parser.add_argument("--output", help="Output file for loaded content")

    args = parser.parse_args()

    try:
        loader = ContentLoader(args.skill_path)

        if args.analyze:
            loader.analyze_token_usage()
            return

        # Determine loading mode
        user_context = {"query": args.query} if args.query else {}

        if args.mode == "quick":
            content = loader.load_quick_start()
        elif args.mode == "examples":
            content = loader.load_with_examples()
        elif args.mode == "full":
            content = loader.load_advanced_content()
        elif args.mode == "optimal":
            content = loader.load_optimal_content(user_context)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            pass

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
