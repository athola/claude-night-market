"""Skills evaluation package for the abstract plugin.

This package provides modular functionality for skills compliance checking,
improvement suggestions, auditing, token tracking, and performance analysis.
"""

# Re-export constants from auditor for backwards compatibility
from .auditor import (
    DESCRIPTION_TRIGGER,
    EXIT_CRITERIA_HEADING,
    MAX_BODY_LINES,
    MAX_DESCRIPTION_CHARS,
    MIN_EXIT_CRITERIA_ITEMS,
    MIN_NUMBERED_LISTS,
    MIN_SECTION_COUNT,
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_GOOD,
    SCORE_WELL_STRUCTURED,
    SkillMetrics,
    SkillsAuditor,
)
from .compliance import ComplianceChecker, ComplianceIssue, ComplianceReport
from .improvements import (
    CODE_BLOCKS_MODULARIZE,
    MIN_CODE_BLOCKS,
    MIN_SECTIONS,
    SUGGESTIONS_LOW,
    SUGGESTIONS_MEDIUM,
    TOKEN_LARGE_SKILL,
    TOKEN_MAX_EFFICIENT,
    Improvement,
    ImprovementSuggester,
)
from .performance import ToolPerformanceAnalyzer
from .token_tracker import TokenUsageTracker

__all__ = [
    # Rubric constants
    "DESCRIPTION_TRIGGER",
    "EXIT_CRITERIA_HEADING",
    "MAX_BODY_LINES",
    "MAX_DESCRIPTION_CHARS",
    "MIN_EXIT_CRITERIA_ITEMS",
    # Modularization constants
    "CODE_BLOCKS_MODULARIZE",
    # Code block constants
    "MIN_CODE_BLOCKS",
    # Structure constants
    "MIN_NUMBERED_LISTS",
    "MIN_SECTIONS",
    "MIN_SECTION_COUNT",
    "SCORE_ACCEPTABLE",
    # Score constants
    "SCORE_EXCELLENT",
    "SCORE_GOOD",
    "SCORE_WELL_STRUCTURED",
    "SUGGESTIONS_LOW",
    "SUGGESTIONS_MEDIUM",
    "TOKEN_LARGE_SKILL",
    # Token constants
    "TOKEN_MAX_EFFICIENT",
    # Classes
    "ComplianceChecker",
    "ComplianceIssue",
    "ComplianceReport",
    "Improvement",
    "ImprovementSuggester",
    "SkillMetrics",
    "SkillsAuditor",
    "TokenUsageTracker",
    "ToolPerformanceAnalyzer",
]
