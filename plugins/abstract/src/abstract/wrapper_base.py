"""Superpower wrapper infrastructure for translating between commands and superpowers.

This module provides base classes and utilities for creating plugin command wrappers
that delegate to superpowers with parameter translation and error handling.
"""

from __future__ import annotations

import ast
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from .errors import ErrorHandler, ErrorSeverity, ToolError


def _detect_breaking_changes(files: list[str]) -> list[dict[str, Any]]:
    """Detect breaking changes in a list of files.

    Compares the working-tree version of each file against the
    git HEAD version and reports:

    - Removed public functions/classes
    - Modified function signatures
    - Removed/renamed parameters
    - Changed return types (in type hints)

    Args:
        files: List of file paths to analyze for breaking changes

    Returns:
        List of detected breaking changes with details about each change.
        Empty list if no files or no breaking changes detected.

    """
    if not files:
        return []

    changes: list[dict[str, Any]] = []

    for file_path in files:
        path = Path(file_path)

        # Skip non-Python files
        if path.suffix != ".py":
            continue

        # Parse the current version
        try:
            current_source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        try:
            current_tree = ast.parse(current_source)
        except SyntaxError:
            continue

        # Get the HEAD version via git
        try:
            cmd = ["git", "show", "HEAD:" + file_path]  # noqa: S607
            result = subprocess.run(  # noqa: S603  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

        if result.returncode != 0:
            # File is new (no git history) -- no breaking changes
            continue

        try:
            old_tree = ast.parse(result.stdout)
        except SyntaxError:
            continue

        old_public = _extract_public_symbols(old_tree)
        new_public = _extract_public_symbols(current_tree)
        _compare_symbols(file_path, old_public, new_public, changes)

    return changes


def _compare_symbols(
    file_path: str,
    old_public: dict[str, dict[str, Any]],
    new_public: dict[str, dict[str, Any]],
    changes: list[dict[str, Any]],
) -> None:
    """Compare old and new public symbols, appending breaking changes."""
    for name in sorted(old_public):
        if name not in new_public:
            kind = old_public[name]["kind"]
            changes.append(
                {
                    "file": file_path,
                    "type": "removed",
                    "name": name,
                    "details": f"public {kind} '{name}' was removed",
                }
            )
            continue

        old_sym = old_public[name]
        new_sym = new_public[name]

        if old_sym["kind"] != "function" or new_sym["kind"] != "function":
            continue

        _compare_function_sigs(file_path, name, old_sym, new_sym, changes)


def _compare_function_sigs(
    file_path: str,
    name: str,
    old_sym: dict[str, Any],
    new_sym: dict[str, Any],
    changes: list[dict[str, Any]],
) -> None:
    """Compare function signatures and record parameter/return type changes."""
    old_params = old_sym["params"]
    new_params = new_sym["params"]

    for p in old_params:
        if p not in new_params:
            changes.append(
                {
                    "file": file_path,
                    "type": "parameter_removed",
                    "name": name,
                    "details": f"parameter '{p}' was removed from '{name}'",
                }
            )

    common = [p for p in old_params if p in new_params]
    new_order = [p for p in new_params if p in old_params]
    if common != new_order:
        changes.append(
            {
                "file": file_path,
                "type": "parameters_reordered",
                "name": name,
                "details": (
                    f"parameters of '{name}' were reordered: {common} -> {new_order}"
                ),
            }
        )

    old_ret = old_sym["return_type"]
    new_ret = new_sym["return_type"]
    if old_ret is not None and old_ret != new_ret:
        changes.append(
            {
                "file": file_path,
                "type": "return_type_changed",
                "name": name,
                "details": (
                    f"return type of '{name}' changed: '{old_ret}' -> '{new_ret}'"
                ),
            }
        )


def _extract_public_symbols(
    tree: ast.Module,
) -> dict[str, dict[str, Any]]:
    """Extract public functions and classes from an AST module.

    Args:
        tree: Parsed AST module

    Returns:
        Dict mapping symbol name to metadata (kind, params,
        return_type).

    """
    symbols: dict[str, dict[str, Any]] = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if name.startswith("_"):
                continue
            params = _extract_param_names(node)
            ret = _unparse_annotation(node.returns)
            symbols[name] = {
                "kind": "function",
                "params": params,
                "return_type": ret,
            }
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if name.startswith("_"):
                continue
            symbols[name] = {
                "kind": "class",
                "params": [],
                "return_type": None,
            }

    return symbols


def _extract_param_names(func_node: ast.FunctionDef) -> list[str]:
    """Return the parameter names of a function (excluding 'self'/'cls').

    Args:
        func_node: An AST FunctionDef node

    Returns:
        Ordered list of parameter names.

    """
    names: list[str] = []
    for arg in func_node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        names.append(arg.arg)
    for arg in func_node.args.kwonlyargs:
        names.append(arg.arg)
    if func_node.args.vararg:
        names.append("*" + func_node.args.vararg.arg)
    if func_node.args.kwarg:
        names.append("**" + func_node.args.kwarg.arg)
    return names


def _unparse_annotation(node: Any) -> str | None:
    """Convert an AST annotation node to a string representation.

    Uses ast.unparse on Python 3.9+.

    Args:
        node: An AST expression node (or None)

    Returns:
        String representation of the annotation, or None.

    """
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


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
