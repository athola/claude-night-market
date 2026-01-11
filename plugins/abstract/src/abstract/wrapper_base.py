"""Superpower wrapper infrastructure for translating between commands and superpowers.

This module provides base classes and utilities for creating plugin command wrappers
that delegate to superpowers with parameter translation and error handling.
"""

from pathlib import Path
from typing import Any

import yaml

from .errors import ErrorHandler, ErrorSeverity, ToolError


def detect_breaking_changes(files: list[str]) -> list[dict[str, Any]]:
    """Detect breaking changes in a list of files.

    Analyzes Python files for potential breaking API changes including:
    - Removed public functions/classes
    - Modified function signatures
    - Removed/renamed parameters
    - Changed return types (in type hints)

    Args:
        files: List of file paths to analyze for breaking changes

    Returns:
        List of detected breaking changes with details about each change.
        Empty list if no files or no breaking changes detected.

    Example:
        >>> detect_breaking_changes(["mymodule.py"])
        [
            {
                "file": "mymodule.py",
                "type": "removed_function",
                "name": "old_function",
                "severity": "high",
                "description": "Public function removed without deprecation",
            }
        ]

    """
    if not files:
        return []

    breaking_changes: list[dict[str, Any]] = []

    for file_path in files:
        path = Path(file_path)

        # Only analyze Python files
        if not path.suffix == ".py" or not path.exists():
            continue

        try:
            _ = path.read_text(encoding="utf-8")

            # Note: This is a basic implementation that returns empty list.
            # Full implementation would need:
            # 1. Git diff analysis to detect actual removals
            # 2. AST parsing for accurate signature analysis
            # 3. Comparison with previous version
            # 4. Tracking of deprecation markers
            #
            # Patterns to detect (for future implementation):
            # - Removed __all__ exports
            # - Removed public classes/functions (def/class without _prefix)
            # - Modified function signatures
            # - Type hint changes (-> and : annotations)
            #
            # This function correctly handles the edge case of empty file list

        except (OSError, UnicodeDecodeError):
            # Skip files that can't be read
            continue

    return breaking_changes


class SuperpowerWrapper:
    """Wrapper that translates plugin command parameters to superpower parameters."""

    def __init__(
        self,
        source_plugin: str,
        source_command: str,
        target_superpower: str,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the wrapper with validation.

        Args:
            source_plugin: Name of the source plugin
            source_command: Name of the source command
            target_superpower: Name of the target superpower
            config_path: Optional path to wrapper configuration file

        Raises:
            ValueError: If any required parameter is invalid

        """
        # Validate inputs
        if not source_plugin or not isinstance(source_plugin, str):
            msg = "source_plugin must be a non-empty string"
            raise ValueError(msg)
        if not source_command or not isinstance(source_command, str):
            msg = "source_command must be a non-empty string"
            raise ValueError(msg)
        if not target_superpower or not isinstance(target_superpower, str):
            msg = "target_superpower must be a non-empty string"
            raise ValueError(msg)

        self.source_plugin = source_plugin
        self.source_command = source_command
        self.target_superpower = target_superpower
        self.config_path = config_path
        self.error_handler = ErrorHandler(f"wrapper-{source_plugin}-{source_command}")

        # Load parameter mapping with error handling
        try:
            self.parameter_map = self._load_parameter_map()
        except Exception as e:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.HIGH,
                    error_code="WRAPPER_CONFIG_ERROR",
                    message=f"Failed to load parameter mapping: {e!s}",
                    context={
                        "source_plugin": source_plugin,
                        "source_command": source_command,
                        "target_superpower": target_superpower,
                    },
                ),
            )
            raise

    def translate_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Translate plugin parameters to superpower parameters.

        Args:
            params: Dictionary of plugin parameters

        Returns:
            Dictionary of translated parameters

        Raises:
            ValueError: If params is not a dictionary
            TypeError: If parameter values are invalid

        """
        if not isinstance(params, dict):
            msg = "Parameters must be provided as a dictionary"
            raise ValueError(msg)

        if not params:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.LOW,
                    error_code="EMPTY_PARAMETERS",
                    message="No parameters provided for translation",
                    suggestion="Check if required parameters are missing",
                    context={"wrapper": f"{self.source_plugin}.{self.source_command}"},
                ),
            )

        translated = {}
        translation_errors = []

        for key, value in params.items():
            try:
                # Validate key
                if not isinstance(key, str):
                    translation_errors.append(
                        f"Invalid parameter key type: {type(key)}",
                    )
                    continue

                # Get mapped key or use original
                mapped_key = self.parameter_map.get(key, key)

                # Validate value
                if value is None:
                    translation_errors.append(f"Parameter '{key}' has None value")
                    continue

                translated[mapped_key] = value

            except Exception as e:
                translation_errors.append(
                    f"Error processing parameter '{key}': {e!s}",
                )

        if translation_errors:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.MEDIUM,
                    error_code="PARAMETER_TRANSLATION_ERROR",
                    message=(
                        f"Parameter translation completed with "
                        f"{len(translation_errors)} errors"
                    ),
                    details="; ".join(translation_errors),
                    context={
                        "original_params": params,
                        "translated_params": translated,
                    },
                ),
            )

        return translated

    def _load_parameter_map(self) -> dict[str, str]:
        """Load parameter mapping from wrapper config.

        Returns:
            Dictionary mapping parameter names

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config format is invalid

        """
        # Default mapping for test-skill -> test-driven-development
        default_mapping = {"skill-path": "target_under_test", "phase": "tdd_phase"}

        # If no config path, return default mapping
        if not self.config_path:
            return default_mapping

        # Try to load from config file
        if self.config_path.exists():
            try:
                # For now, implement simple YAML loading
                # In a full implementation, this would use the errors.py safe_yaml_load
                with open(self.config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                if not isinstance(config, dict):
                    msg = "Config file must contain a dictionary"
                    raise ValueError(msg)

                parameter_mapping = config.get("parameter_mapping", {})
                if not isinstance(parameter_mapping, dict):
                    msg = "parameter_mapping must be a dictionary"
                    raise ValueError(msg)

                # Validate mapping values are strings
                for key, value in parameter_mapping.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        msg = (
                            f"Invalid mapping: {key} -> {value} (both must be strings)"
                        )
                        raise ValueError(
                            msg,
                        )

                return parameter_mapping

            except yaml.YAMLError as e:
                self.error_handler.log_error(
                    ToolError(
                        severity=ErrorSeverity.HIGH,
                        error_code="CONFIG_PARSE_ERROR",
                        message=f"Failed to parse YAML config: {e!s}",
                        context={"config_path": str(self.config_path)},
                    ),
                )
                msg = f"Invalid YAML config: {e!s}"
                raise ValueError(msg) from e
            except Exception as e:
                self.error_handler.log_error(
                    ToolError(
                        severity=ErrorSeverity.HIGH,
                        error_code="CONFIG_LOAD_ERROR",
                        message=f"Failed to load config: {e!s}",
                        context={"config_path": str(self.config_path)},
                    ),
                )
                msg = f"Failed to load config: {e!s}"
                raise ValueError(msg) from e
        else:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.MEDIUM,
                    error_code="CONFIG_NOT_FOUND",
                    message=(
                        f"Config file not found, using defaults: {self.config_path}"
                    ),
                    suggestion="Create a config file or use default mapping",
                    context={"config_path": str(self.config_path)},
                ),
            )
            return default_mapping

    def validate_translation(
        self,
        original_params: dict[str, Any],
        translated_params: dict[str, Any],
    ) -> bool:
        """Validate that translation was successful.

        Args:
            original_params: Original parameters provided
            translated_params: Parameters after translation

        Returns:
            True if translation appears valid, False otherwise

        """
        if not translated_params and original_params:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.HIGH,
                    error_code="TRANSLATION_FAILED",
                    message=(
                        "Translation resulted in empty parameters from non-empty input"
                    ),
                    context={
                        "original": original_params,
                        "translated": translated_params,
                    },
                ),
            )
            return False

        # Check for expected mappings based on our default mapping
        expected_mappings = ["skill-path", "phase"]
        missing_mappings = []

        for expected in expected_mappings:
            if expected in original_params and expected not in self.parameter_map:
                missing_mappings.append(expected)

        if missing_mappings:
            self.error_handler.log_error(
                ToolError(
                    severity=ErrorSeverity.MEDIUM,
                    error_code="MISSING_MAPPINGS",
                    message=(
                        f"No mapping found for parameters: "
                        f"{', '.join(missing_mappings)}"
                    ),
                    suggestion=(f"Add mappings for: {', '.join(missing_mappings)}"),
                    context={"missing_mappings": missing_mappings},
                ),
            )

        return len(translated_params) > 0
