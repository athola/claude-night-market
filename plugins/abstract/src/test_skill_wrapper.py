"""Test skill wrapper implementation.

This module provides a test implementation of the skill wrapper
for testing and demonstration purposes.
"""

from typing import Any

from .wrapper_base import SuperpowerWrapper


class TestSkillWrapper(SuperpowerWrapper):
    """Wrapper for test-skill that delegates to test-driven-development superpower.

    This wrapper translates plugin-specific parameters to superpower parameters
    and adds skill-specific validation and extensions for TDD-based skill testing.
    """

    def __init__(self) -> None:
        """Initialize the test-skill wrapper."""
        super().__init__(
            source_plugin="abstract",
            source_command="test-skill",
            target_superpower="test-driven-development",
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the wrapped test-skill command.

        Args:
            params: Dictionary containing required parameters:
                - skill-path: Path to the skill to test
                - phase: TDD phase to execute (red/green/refactor)

        Returns:
            Dictionary containing execution results

        Raises:
            ValueError: If required parameters are missing
            TypeError: If parameters have invalid types

        """
        # Validate required parameters
        if not params:
            msg = "Parameters dictionary cannot be empty"
            raise ValueError(msg)

        if "skill-path" not in params:
            msg = "Missing required parameter: skill-path"
            raise ValueError(msg)

        if "phase" not in params:
            msg = "Missing required parameter: phase"
            raise ValueError(msg)

        # Validate parameter types
        if not isinstance(params["skill-path"], str):
            msg = "skill-path must be a string"
            raise TypeError(msg)

        if not isinstance(params["phase"], str):
            msg = "phase must be a string"
            raise TypeError(msg)

        # Validate phase values
        valid_phases = ["red", "green", "refactor"]
        if params["phase"] not in valid_phases:
            msg = f"phase must be one of: {', '.join(valid_phases)}"
            raise ValueError(msg)

        # Translate parameters
        superpower_params = self.translate_parameters(params)

        # Call superpower with skill-specific extensions
        return {
            "superpower_called": self.target_superpower,
            "phase_executed": superpower_params.get("tdd_phase"),
            "target": superpower_params.get("target_under_test"),
            "extensions": self._apply_skill_extensions(superpower_params),
        }

    def _apply_skill_extensions(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply skill-specific extensions to superpower call.

        Args:
            params: Translated parameters for the superpower

        Returns:
            Dictionary of skill-specific extensions

        """
        extensions = {
            "skill_validation": True,
            "rationalization_detection": True,
            "skill_specific_reporting": True,
        }

        # Add skill path to extensions for validation
        if "target_under_test" in params:
            extensions["skill_path"] = params["target_under_test"]

        return extensions
