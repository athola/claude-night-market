#!/usr/bin/env python3
"""Shared utilities for skill evaluation and analysis tools.

This module now imports from the centralized abstract.utils package.
All functionality has been moved to src/abstract/utils.py for consistency.
"""

import sys
from pathlib import Path

# Score thresholds for categorization
EXCELLENT_THRESHOLD = 90
GOOD_THRESHOLD = 75
NEEDS_IMPROVEMENT_THRESHOLD = 60

# Import from centralized abstract package
try:
    from abstract.utils import (
        estimate_tokens,
        extract_frontmatter,
        find_skill_files,
        format_score,
        get_skill_name,
        load_skill_file,
    )
    from abstract.utils import (
        parse_yaml_frontmatter as parse_frontmatter,
    )
except ImportError as err:
    # Fallback: add project src to path
    project_root = Path(__file__).parent.parent.parent.parent
    src_path = project_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        from abstract.utils import (
            estimate_tokens,
            extract_frontmatter,
            find_skill_files,
            format_score,
            get_skill_name,
            load_skill_file,
        )
        from abstract.utils import (
            parse_yaml_frontmatter as parse_frontmatter,
        )
    else:
        msg = (
            "Cannot import abstract package. Run: uv pip install -e . from project root"
        )
        raise ImportError(
            msg,
        ) from err

# Re-export for backwards compatibility
__all__ = [
    "estimate_tokens",
    "extract_frontmatter",
    "find_skill_files",
    "format_score",
    "get_skill_name",
    "load_skill_file",
    "parse_frontmatter",
]


# Additional skill-eval specific utilities
def get_efficiency_grade(value: int, thresholds: dict) -> str:
    """Get efficiency grade based on value and thresholds.

    Args:
        value: The value to grade.
        thresholds: Dictionary mapping grades to threshold values.

    Returns:
        Grade string (A, B, C, D).

    """
    if value <= thresholds.get("excellent", 1500):
        return "A"
    if value <= thresholds.get("good", 2000):
        return "B"
    if value <= thresholds.get("acceptable", 2500):
        return "C"
    return "D"


def get_optimization_level(score: float) -> str:
    """Get optimization level description from score.

    Args:
        score: Score value (0-100).

    Returns:
        Description string.

    """
    if score >= EXCELLENT_THRESHOLD:
        return "excellent"
    if score >= GOOD_THRESHOLD:
        return "good"
    if score >= NEEDS_IMPROVEMENT_THRESHOLD:
        return "needs improvement"
    return "poor"
