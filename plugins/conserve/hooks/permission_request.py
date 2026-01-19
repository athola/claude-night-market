#!/usr/bin/env python3
"""PermissionRequest hook for workflow automation.

This hook implements permission auto-approval for safe operations
and auto-denial for dangerous patterns.

Claude Code 2.0.54+ supports PermissionRequest hooks that can:
- Auto-approve safe operations (bypasses permission dialog)
- Auto-deny dangerous commands with explanations
- Modify inputs before approval (e.g., adding safety flags)

Security Model:
- Allowlist approach with denylist override
- Dangerous patterns ALWAYS checked first
- Safe patterns use conservative matching
- Unknown commands default to showing dialog

Usage:
    Add to .claude/settings.json:
    {
        "hooks": {
            "PermissionRequest": [{
                "command": "python plugins/conserve/hooks/permission_request.py"
            }]
        }
    }
"""

import json
import logging
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Configure logging for hook diagnostics
logging.basicConfig(level=logging.WARNING, format="%(name)s: %(message)s")
logger = logging.getLogger("permission_request")


class PermissionDecision(Enum):
    """Possible permission decisions."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"  # Show dialog (default)


@dataclass
class Decision:
    """Permission decision with optional message."""

    behavior: PermissionDecision
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to hook output format."""
        result: dict[str, Any] = {"behavior": self.behavior.value}
        if self.message:
            result["message"] = self.message
        return result


# ============================================================================
# Pattern Definitions
# ============================================================================

# DANGEROUS patterns - always deny these
# Order matters: more specific patterns should come first
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    # Destructive file operations
    (r"rm\s+-rf\s+/(?!\S)", "Blocked: recursive delete on root"),
    (r"rm\s+-rf\s+/\*", "Blocked: recursive delete on root"),
    (r"rm\s+-rf\s+~", "Blocked: recursive delete on home"),
    (r"rm\s+-rf\s+\$HOME", "Blocked: recursive delete on home"),
    # Privilege escalation
    (r"^sudo\s+", "Blocked: sudo requires explicit approval"),
    (r"\|\s*sudo\s+", "Blocked: piped sudo is dangerous"),
    # Remote code execution
    (r"curl\s+.*\|\s*(bash|sh|zsh)", "Blocked: pipe-to-shell pattern"),
    (r"wget\s+.*\|\s*(bash|sh|zsh)", "Blocked: pipe-to-shell pattern"),
    (r"curl\s+.*>\s*/", "Blocked: curl to root path"),
    # Fork bombs and resource exhaustion
    (r":\(\)\{.*:\|:.*\}", "Blocked: fork bomb detected"),
    (r"while\s+true\s*;\s*do.*done", "Blocked: infinite loop pattern"),
    # Credential exposure
    (r"cat\s+.*\.env", "Blocked: potential credential exposure"),
    (r"cat\s+.*credentials", "Blocked: potential credential exposure"),
    (r"cat\s+.*/\.ssh/", "Blocked: SSH key exposure"),
    # Git dangerous operations
    (r"git\s+push\s+.*--force\s+origin\s+(main|master)", "Blocked: force push to main"),
    (r"git\s+reset\s+--hard\s+origin/", "Blocked: hard reset from remote"),
]

# SAFE patterns - auto-approve these
# These are read-only or low-risk operations
SAFE_PATTERNS: list[str] = [
    # File system inspection (read-only)
    r"^ls(\s|$)",
    r"^pwd$",
    r"^cat\s+(?!.*\.env|.*credentials|.*\.ssh)",
    r"^head\s+",
    r"^tail\s+",
    r"^wc\s+",
    r"^file\s+",
    r"^stat\s+",
    r"^realpath\s+",
    r"^dirname\s+",
    r"^basename\s+",
    # Search operations (read-only)
    r"^grep\s+",
    r"^rg\s+",
    r"^ag\s+",
    r"^find\s+.*-name\s+",
    r"^find\s+.*-type\s+",
    r"^which\s+",
    r"^whereis\s+",
    r"^type\s+",
    # Git read operations
    r"^git\s+status(\s|$)",
    r"^git\s+log(\s|$)",
    r"^git\s+diff(\s|$)",
    r"^git\s+branch(\s|$)",
    r"^git\s+show(\s|$)",
    r"^git\s+remote\s+-v$",
    r"^git\s+rev-parse(\s|$)",
    r"^git\s+describe(\s|$)",
    # Help commands
    r"^man\s+",
    r".*--help$",
    r".*-h$",
    r"^help\s+",
    # Environment inspection
    r"^env$",
    r"^printenv(\s|$)",
    r"^echo\s+\$",
    # Python/Node read operations
    r"^python\s+--version$",
    r"^python3\s+--version$",
    r"^node\s+--version$",
    r"^npm\s+--version$",
    r"^uv\s+--version$",
    r"^pip\s+--version$",
    # Package info (read-only)
    r"^pip\s+show\s+",
    r"^npm\s+list(\s|$)",
    r"^uv\s+pip\s+list(\s|$)",
]


def check_dangerous(command: str) -> Decision | None:
    """Check if command matches dangerous patterns.

    Args:
        command: The command string to check.

    Returns:
        Decision to deny if dangerous, None otherwise.

    """
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.info("Dangerous pattern matched: %s", pattern)
            return Decision(PermissionDecision.DENY, message)
    return None


def check_safe(command: str) -> Decision | None:
    """Check if command matches safe patterns.

    Args:
        command: The command string to check.

    Returns:
        Decision to allow if safe, None otherwise.

    """
    for pattern in SAFE_PATTERNS:
        if re.match(pattern, command, re.IGNORECASE):
            logger.debug("Safe pattern matched: %s", pattern)
            return Decision(PermissionDecision.ALLOW)
    return None


def evaluate_permission(tool_name: str, tool_input: dict[str, Any]) -> Decision | None:
    """Evaluate permission request and return decision.

    Args:
        tool_name: The Claude Code tool being invoked (e.g., "Bash").
        tool_input: The tool input parameters.

    Returns:
        Decision if determined, None to show dialog.

    """
    # Only process Bash commands for now
    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    if not command:
        return None

    # Dangerous patterns take priority
    dangerous = check_dangerous(command)
    if dangerous:
        return dangerous

    # Then check safe patterns
    safe = check_safe(command)
    if safe:
        return safe

    # Unknown - show dialog
    return None


def format_hook_output(decision: Decision | None) -> dict[str, Any]:
    """Format decision as hook-compatible output.

    Args:
        decision: The permission decision, or None for default behavior.

    Returns:
        Dictionary suitable for hook JSON output.

    """
    output: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
        }
    }

    if decision:
        output["hookSpecificOutput"]["decision"] = decision.to_dict()

    return output


def main() -> int:
    """Execute hook entry point.

    Returns:
        Exit code (0 for success).

    """
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse hook input as JSON: %s", e)
        # Return empty output to show default dialog
        print(json.dumps(format_hook_output(None)))
        return 0

    # Extract tool information
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Evaluate permission
    decision = evaluate_permission(tool_name, tool_input)

    # Output result
    print(json.dumps(format_hook_output(decision)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
