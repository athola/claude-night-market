"""Base plugin class for pensive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class PensivePlugin:
    """Base class for pensive plugins."""

    name: str = "base"
    version: str = "1.0.0"

    def __init__(self, config: Any = None) -> None:
        """Initialize plugin."""
        self.config = config or {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def analyze(self, _context: Any) -> dict[str, Any]:
        """Run analysis."""
        return {}

    def execute_review(self, repo_path: Path | str) -> dict[str, Any]:
        """Execute a code review on a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Review results dictionary
        """
        from pensive.workflows.code_review import CodeReviewWorkflow

        workflow = CodeReviewWorkflow(config=self.config)
        return workflow.execute_full_review(repo_path)

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
