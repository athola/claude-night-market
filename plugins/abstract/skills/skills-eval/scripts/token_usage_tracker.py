#!/usr/bin/env python3
"""CLI wrapper for token-usage-tracker script.

Uses core functionality from src/abstract/skills_eval.
"""

import sys
from pathlib import Path

# Add src to path to import core functionality
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


import logging  # noqa: E402

logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """CLI wrapper for token usage tracking functionality."""

    def __init__(
        self,
        skills_dir: Path,
        optimal_limit: int = 2000,
        max_limit: int = 4000,
    ) -> None:
        self.skills_dir = skills_dir
        self.optimal_limit = optimal_limit
        self.max_limit = max_limit

    def track_usage(self) -> dict:
        """Track token usage for all skills in directory."""
        skill_files = list(self.skills_dir.rglob("SKILL.md"))

        if not skill_files:
            return {
                "total_skills": 0,
                "total_tokens": 0,
                "average_tokens": 0,
                "skills_over_limit": 0,
                "optimal_usage_count": 0,
            }

        total_tokens = 0
        skills_over_limit = 0
        optimal_usage_count = 0

        for skill_file in skill_files:
            try:
                with open(skill_file, encoding="utf-8") as f:
                    content = f.read()
                tokens = len(content) // 4
                total_tokens += tokens

                if tokens > self.optimal_limit:
                    skills_over_limit += 1
                else:
                    optimal_usage_count += 1

            except (OSError, UnicodeDecodeError) as e:
                # Log the error if needed, but continue processing other files
                logger.debug(f"Skipping file {skill_file}: {e}")
                continue

        return {
            "total_skills": len(skill_files),
            "total_tokens": total_tokens,
            "average_tokens": total_tokens // len(skill_files) if skill_files else 0,
            "skills_over_limit": skills_over_limit,
            "optimal_usage_count": optimal_usage_count,
        }

    def get_usage_report(self) -> str:
        """Generate formatted usage report."""
        results = self.track_usage()

        lines = [
            "# Token Usage Report",
            f"**Skills Directory:** {self.skills_dir}",
            "",
            "## Summary",
            f"- **Total Skills:** {results['total_skills']}",
            f"- **Total Tokens:** {results['total_tokens']:,}",
            f"- **Average Tokens:** {results['average_tokens']:,}",
            f"- **Skills Over Limit ({self.optimal_limit}):** "
            f"{results['skills_over_limit']}",
            f"- **Optimal Usage (≤{self.optimal_limit}):** "
            f"{results['optimal_usage_count']}",
            "",
        ]

        return "\n".join(lines)


# For direct execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Track token usage for skills")

    parser.add_argument(
        "skills_dir",
        type=Path,
        help="Directory containing skills to analyze",
    )
    parser.add_argument(
        "--optimal-limit",
        type=int,
        default=2000,
        help="Optimal token limit per skill",
    )
    parser.add_argument("--output", type=Path, help="Output file path")

    args = parser.parse_args()

    tracker = TokenUsageTracker(args.skills_dir, args.optimal_limit)
    output = tracker.get_usage_report()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        pass
