"""Code review entry point for pensive."""

from __future__ import annotations

from typing import Any

from pensive.workflows.code_review import CodeReviewWorkflow


def run_code_review(repo_path: str, config: Any = None) -> dict[str, Any]:
    """Execute a code review on a repository."""
    return CodeReviewWorkflow(config=config or {}).execute_full_review(repo_path)
