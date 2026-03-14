"""Skill coordinator for pensive workflows.

This module previously contained a SkillCoordinator class.
Use CodeReviewWorkflow from pensive.workflows.code_review instead.
"""

from __future__ import annotations

from typing import Any


def dispatch_agent(skill_name: str, _context: Any) -> str:
    return f"{skill_name} execution result"
