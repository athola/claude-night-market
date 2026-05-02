"""Shared constants for architecture_review mixins (AR-01)."""

from __future__ import annotations

import logging

logger = logging.getLogger("pensive.skills.architecture_review")

# Architecture detection thresholds
MIN_LAYERS_FOR_LAYERED = 3  # Minimum layers to detect layered architecture
MIN_SERVICES_FOR_MICROSERVICES = 2  # Minimum services to detect microservices
MIN_EVENT_COMPONENTS = 3  # Minimum event components for event-driven
MIN_RESPONSIBILITIES_FOR_LOW_COHESION = 3  # Threshold for cohesion calculation
MIN_VIOLATIONS_TO_REPORT = 2  # Minimum violations before flagging
MIN_ADR_SECTIONS = 3  # Minimum ADR sections for completeness

# Coupling score calculation
COUPLING_DEPENDENCY_SCALE = 10.0
COUPLING_VIOLATION_WEIGHT = 0.5

# Cohesion score thresholds
COHESION_SCORE_MEDIUM = 0.7
COHESION_SCORE_HIGH = 0.9
MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION = 2

# A-11: avoid re-allocating a 3-element list literal per match.
_BUILTIN_EXC_NAMES = frozenset({"Exception", "ValueError", "TypeError"})

# SRP keyword detection
_SRP_KEYWORDS = frozenset(
    ["user", "email", "report", "backup", "send", "generate", "create"]
)

__all__ = [
    "COHESION_SCORE_HIGH",
    "COHESION_SCORE_MEDIUM",
    "COUPLING_DEPENDENCY_SCALE",
    "COUPLING_VIOLATION_WEIGHT",
    "MIN_ADR_SECTIONS",
    "MIN_EVENT_COMPONENTS",
    "MIN_LAYERS_FOR_LAYERED",
    "MIN_RESPONSIBILITIES_FOR_LOW_COHESION",
    "MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION",
    "MIN_SERVICES_FOR_MICROSERVICES",
    "MIN_VIOLATIONS_TO_REPORT",
    "_BUILTIN_EXC_NAMES",
    "_SRP_KEYWORDS",
    "logger",
]
