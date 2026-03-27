"""Shared data models for the marginal value subsystem.

Kept in a separate module to break the circular import between
``marginal_value`` and ``integration_policy``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

OVERLAP_STRONG = 0.8
OVERLAP_PARTIAL = 0.4
VALUE_NOVEL = 0.8
VALUE_CONTRADICTION = 0.7
VALUE_MORE_EXAMPLES = 0.4
VALUE_LOW = 0.3
VALUE_NONE = 0.1
MIN_NOVEL_HEADINGS = 2
MIN_NOVEL_KEYWORD_RATIO = 0.5


class RedundancyLevel(Enum):
    """Classification of content redundancy."""

    EXACT_MATCH = "exact_match"
    HIGHLY_REDUNDANT = "redundant"
    PARTIAL_OVERLAP = "partial"
    NOVEL = "novel"


class DeltaType(Enum):
    """Type of new information in partially overlapping content."""

    NOVEL_INSIGHT = "novel_insight"
    DIFFERENT_FRAMING = "different_framing"
    MORE_EXAMPLES = "more_examples"
    CONTRADICTS = "contradicts"
    NONE = "none"


class IntegrationDecision(Enum):
    """How to handle new knowledge."""

    STANDALONE = "standalone"
    MERGE = "merge"
    REPLACE = "replace"
    SKIP = "skip"


@dataclass
class RedundancyCheck:
    """Result of redundancy analysis."""

    level: RedundancyLevel
    overlap_score: float
    matching_entries: list[str]
    reasons: list[str]


@dataclass
class DeltaAnalysis:
    """Analysis of what's new in partially overlapping content."""

    delta_type: DeltaType
    value_score: float
    novel_aspects: list[str]
    redundant_aspects: list[str]
    teaching_delta: str


@dataclass
class IntegrationPlan:
    """Decision on how to integrate new knowledge."""

    decision: IntegrationDecision
    target_entries: list[str]
    rationale: str
    confidence: float
