"""Expose Pensive code review skills.

Attributes resolve lazily (PEP 562). ``pensive.workflows`` pulls in
psutil, and a caller that wants only ``pensive.skills.tiered_audit``,
such as ``scripts/tiered_audit.py`` running under the system Python,
must not pay for it or fail on it. Loading that file by path instead
gave the same dataclass two module identities.
"""

from __future__ import annotations

import importlib
from typing import Any

_EXPORTS: dict[str, str] = {
    "AnalysisError": "pensive.exceptions",
    "ConfigurationError": "pensive.exceptions",
    "PensiveError": "pensive.exceptions",
    "PluginError": "pensive.exceptions",
    "ApiReviewSkill": "pensive.skills",
    "ArchitectureReviewSkill": "pensive.skills",
    "BugReviewSkill": "pensive.skills",
    "EscalationFlag": "pensive.skills",
    "MakefileReviewSkill": "pensive.skills",
    "MathReviewSkill": "pensive.skills",
    "RustReviewSkill": "pensive.skills",
    "TestReviewSkill": "pensive.skills",
    "Tier1Results": "pensive.skills",
    "UnifiedReviewSkill": "pensive.skills",
    "should_escalate_to_tier2": "pensive.skills",
    "CodeReviewWorkflow": "pensive.workflows",
}

__all__ = [
    "AnalysisError",
    "ApiReviewSkill",
    "ArchitectureReviewSkill",
    "BugReviewSkill",
    "CodeReviewWorkflow",
    "ConfigurationError",
    "EscalationFlag",
    "MakefileReviewSkill",
    "MathReviewSkill",
    "PensiveError",
    "PluginError",
    "RustReviewSkill",
    "TestReviewSkill",
    "Tier1Results",
    "UnifiedReviewSkill",
    "should_escalate_to_tier2",
]

__version__ = "1.9.21"


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_name), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))
