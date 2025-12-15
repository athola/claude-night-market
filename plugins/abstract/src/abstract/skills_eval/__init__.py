"""Skills evaluation package for the abstract plugin.

This package provides modular functionality for skills compliance checking,
improvement suggestions, auditing, token tracking, and performance analysis.
"""

# Re-export constants from auditor for backwards compatibility
from .auditor import (
    MIN_CODE_BLOCKS_EXCELLENT,
    MIN_HEADINGS,
    MIN_NUMBERED_LISTS,
    MIN_NUMBERED_LISTS_GOOD,
    MIN_NUMBERED_STEPS,
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
    # Modularization constants
    "CODE_BLOCKS_MODULARIZE",
    # Code block constants
    "MIN_CODE_BLOCKS",
    "MIN_CODE_BLOCKS_EXCELLENT",
    # Structure constants
    "MIN_HEADINGS",
    "MIN_NUMBERED_LISTS",
    "MIN_NUMBERED_LISTS_GOOD",
    "MIN_NUMBERED_STEPS",
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
