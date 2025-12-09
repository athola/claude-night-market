#!/usr/bin/env python3
"""Hook Validator - Validate Claude Code hooks (JSON) and SDK hooks (Python).

This script validates:
1. JSON hooks: Syntax, required fields, known event types
2. Python hooks: AgentHooks inheritance, callback signatures, async definitions

Exit codes:
  0 - Success, no issues
  1 - Warnings found
  2 - Errors found
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import TypedDict


class ValidationResult(TypedDict):
    """Result of hook validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    info: list[str]


# Known hook event types
KNOWN_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "PreCompact",
}

# Required fields for JSON hooks
REQUIRED_JSON_FIELDS = {"hooks"}

# AgentHooks callback signatures
EXPECTED_CALLBACKS = {
    "on_pre_tool_use": {
        "args": ["self", "tool_name", "tool_input"],
        "return_annotation": "dict | None",
    },
    "on_post_tool_use": {
        "args": ["self", "tool_name", "tool_input", "tool_output"],
        "return_annotation": "str | None",
    },
    "on_user_prompt_submit": {
        "args": ["self", "message"],
        "return_annotation": "str | None",
    },
    "on_stop": {
        "args": ["self", "reason", "result"],
        "return_annotation": "None",
    },
    "on_subagent_stop": {
        "args": ["self", "subagent_id", "result"],
        "return_annotation": "None",
    },
    "on_pre_compact": {
        "args": ["self", "context_size"],
        "return_annotation": "dict | None",
    },
}


def validate_json_hook(hook_file: Path) -> ValidationResult:
    """Validate a JSON hook file.

    Args:
        hook_file: Path to hooks.json file

    Returns:
        ValidationResult with errors, warnings, and info

    """
    result: ValidationResult = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": [],
    }

    # Check file exists
    if not hook_file.exists():
        result["errors"].append(f"Hook file not found: {hook_file}")
        result["valid"] = False
        return result

    # Load JSON
    try:
        with open(hook_file) as f:
            hooks_data = json.load(f)
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON syntax: {e}")
        result["valid"] = False
        return result

    result["info"].append(f"Loaded JSON from {hook_file}")

    # Validate structure
    if not isinstance(hooks_data, dict):
        result["errors"].append("Root element must be a JSON object")
        result["valid"] = False
        return result

    # Check for known event types
    for event_type in hooks_data.keys():
        if event_type not in KNOWN_EVENTS:
            result["warnings"].append(f"Unknown event type: {event_type}")

    # Validate each event type
    for event_type, event_hooks in hooks_data.items():
        if not isinstance(event_hooks, list):
            result["errors"].append(f"{event_type}: must be a list")
            result["valid"] = False
            continue

        # Validate each hook entry
        for idx, hook_entry in enumerate(event_hooks):
            if not isinstance(hook_entry, dict):
                result["errors"].append(
                    f"{event_type}[{idx}]: hook entry must be an object"
                )
                result["valid"] = False
                continue

            # Check for 'hooks' field
            if "hooks" not in hook_entry:
                result["errors"].append(
                    f"{event_type}[{idx}]: missing required 'hooks' field"
                )
                result["valid"] = False
                continue

            # Validate hooks array
            hooks_array = hook_entry["hooks"]
            if not isinstance(hooks_array, list):
                result["errors"].append(f"{event_type}[{idx}]: 'hooks' must be a list")
                result["valid"] = False
                continue

            # Validate each hook action
            for hook_idx, hook_action in enumerate(hooks_array):
                if not isinstance(hook_action, dict):
                    result["errors"].append(
                        f"{event_type}[{idx}].hooks[{hook_idx}]: must be an object"
                    )
                    result["valid"] = False
                    continue

                # Check for 'type' field
                if "type" not in hook_action:
                    result["warnings"].append(
                        f"{event_type}[{idx}].hooks[{hook_idx}]: missing 'type' field"
                    )

                # Check for 'command' field if type is 'command'
                if (
                    hook_action.get("type") == "command"
                    and "command" not in hook_action
                ):
                    result["errors"].append(
                        f"{event_type}[{idx}].hooks[{hook_idx}]: "
                        "missing 'command' field"
                    )
                    result["valid"] = False

            # Validate matcher if present
            if "matcher" in hook_entry:
                matcher = hook_entry["matcher"]
                if not isinstance(matcher, dict):
                    result["warnings"].append(
                        f"{event_type}[{idx}]: 'matcher' should be an object"
                    )

                # Check for known matcher fields
                known_matcher_fields = {"toolName", "inputPattern"}
                for field in matcher.keys():
                    if field not in known_matcher_fields:
                        result["warnings"].append(
                            f"{event_type}[{idx}]: unknown matcher field '{field}'"
                        )

    # Summary
    result["info"].append(f"Validated {len(hooks_data)} event type(s)")

    return result


def validate_python_hook(hook_file: Path) -> ValidationResult:
    """Validate a Python SDK hook file.

    Args:
        hook_file: Path to Python file containing AgentHooks subclass

    Returns:
        ValidationResult with errors, warnings, and info

    """
    result: ValidationResult = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": [],
    }

    # Check file exists
    if not hook_file.exists():
        result["errors"].append(f"Hook file not found: {hook_file}")
        result["valid"] = False
        return result

    # Read file
    try:
        source = hook_file.read_text()
    except Exception as e:
        result["errors"].append(f"Cannot read file: {e}")
        result["valid"] = False
        return result

    # Parse Python AST
    try:
        tree = ast.parse(source, filename=str(hook_file))
    except SyntaxError as e:
        result["errors"].append(f"Python syntax error: {e}")
        result["valid"] = False
        return result

    result["info"].append(f"Parsed Python from {hook_file}")

    # Find classes
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    if not classes:
        result["warnings"].append("No classes found in file")
        return result

    # Check for AgentHooks inheritance
    agent_hooks_classes = []
    for cls in classes:
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id == "AgentHooks":
                agent_hooks_classes.append(cls)
                break

    if not agent_hooks_classes:
        result["warnings"].append(
            "No classes inherit from AgentHooks (may not be a hook file)"
        )
        return result

    result["info"].append(f"Found {len(agent_hooks_classes)} AgentHooks subclass(es)")

    # Validate each AgentHooks subclass
    for cls in agent_hooks_classes:
        result["info"].append(f"Validating class: {cls.name}")

        # Find callback methods
        methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]

        for method in methods:
            method_name = method.name

            # Check if it's a known callback
            if method_name not in EXPECTED_CALLBACKS:
                continue

            expected = EXPECTED_CALLBACKS[method_name]

            # Check if async
            if not isinstance(method, ast.AsyncFunctionDef):
                result["errors"].append(
                    f"{cls.name}.{method_name}: should be async (async def)"
                )
                result["valid"] = False

            # Check arguments
            actual_args = [arg.arg for arg in method.args.args]
            expected_args = expected["args"]

            if actual_args != expected_args:
                result["errors"].append(
                    f"{cls.name}.{method_name}: incorrect arguments. "
                    f"Expected {expected_args}, got {actual_args}"
                )
                result["valid"] = False

            result["info"].append(f"  ✓ {method_name}: signature correct")

    return result


def validate_hook_file(
    hook_file: Path, file_type: str | None = None
) -> ValidationResult:
    """Validate a hook file (auto-detect type or use specified type).

    Args:
        hook_file: Path to hook file
        file_type: 'json' or 'python', or None to auto-detect

    Returns:
        ValidationResult

    """
    # Auto-detect type
    if file_type is None:
        if hook_file.suffix == ".json":
            file_type = "json"
        elif hook_file.suffix == ".py":
            file_type = "python"
        else:
            return {
                "valid": False,
                "errors": [
                    f"Cannot determine file type from extension: {hook_file.suffix}"
                ],
                "warnings": [],
                "info": [],
            }

    # Validate based on type
    if file_type == "json":
        return validate_json_hook(hook_file)
    elif file_type == "python":
        return validate_python_hook(hook_file)
    else:
        return {
            "valid": False,
            "errors": [f"Unknown file type: {file_type}"],
            "warnings": [],
            "info": [],
        }


def print_result(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation result.

    Args:
        result: ValidationResult to print
        verbose: If True, print info messages

    """
    # Print info (if verbose)
    if verbose and result["info"]:
        print("\nInfo:")
        for msg in result["info"]:
            print(f"  ℹ  {msg}")

    # Print warnings
    if result["warnings"]:
        print("\nWarnings:")
        for msg in result["warnings"]:
            print(f"  ⚠  {msg}")

    # Print errors
    if result["errors"]:
        print("\nErrors:")
        for msg in result["errors"]:
            print(f"  ✗ {msg}")

    # Print summary
    print()
    if result["valid"]:
        if result["warnings"]:
            print("✓ Valid with warnings")
        else:
            print("✓ Valid")
    else:
        print("✗ Invalid")


def main() -> None:
    """Main entry point for hook validator."""
    parser = argparse.ArgumentParser(
        description="Validate Claude Code hooks (JSON) and SDK hooks (Python)"
    )
    parser.add_argument(
        "hook_file",
        type=Path,
        help="Path to hook file (hooks.json or Python file)",
    )
    parser.add_argument(
        "--type",
        choices=["json", "python"],
        help="Hook file type (auto-detected if not specified)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output (show info messages)",
    )

    args = parser.parse_args()

    # Validate
    result = validate_hook_file(args.hook_file, args.type)

    # Print result
    print_result(result, verbose=args.verbose)

    # Exit with appropriate code
    if not result["valid"]:
        sys.exit(2)  # Errors
    elif result["warnings"]:
        sys.exit(1)  # Warnings
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
