"""Helper utilities for hookify operations."""

import re
from pathlib import Path


def format_rule_name(name: str) -> str:
    """Format a rule name to kebab-case.

    Args:
        name: Raw rule name

    Returns:
        Formatted kebab-case name

    Examples:
        >>> format_rule_name("Block Dangerous RM")
        'block-dangerous-rm'
        >>> format_rule_name("Warn console.log")
        'warn-console-log'
    """
    # Convert to lowercase
    name = name.lower()

    # Replace non-alphanumeric with hyphens
    name = re.sub(r"[^a-z0-9]+", "-", name)

    # Remove leading/trailing hyphens
    name = name.strip("-")

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    return name


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to project root (directory containing .git or .claude)

    Raises:
        FileNotFoundError: If no project root found
    """
    current = Path.cwd()

    # Walk up directory tree looking for .git or .claude
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / ".claude").exists():
            return parent

    # Default to current directory if no markers found
    return current


def validate_event_type(event: str) -> bool:
    """Validate an event type.

    Args:
        event: Event type to validate

    Returns:
        True if valid event type
    """
    valid_events = {"bash", "file", "stop", "prompt", "all"}
    return event in valid_events


def validate_action_type(action: str) -> bool:
    """Validate an action type.

    Args:
        action: Action type to validate

    Returns:
        True if valid action type
    """
    valid_actions = {"warn", "block"}
    return action in valid_actions


def get_field_for_event(event: str) -> list[str]:
    """Get valid fields for an event type.

    Args:
        event: Event type

    Returns:
        List of valid field names for this event
    """
    field_map = {
        "bash": ["command"],
        "file": ["file_path", "new_text", "old_text", "content"],
        "stop": ["transcript"],
        "prompt": ["user_prompt"],
        "all": ["command", "file_path", "new_text", "user_prompt", "transcript"],
    }
    return field_map.get(event, [])


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
