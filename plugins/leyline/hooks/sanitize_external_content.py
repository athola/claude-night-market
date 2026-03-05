#!/usr/bin/env python3
"""PostToolUse hook: sanitize external content.

Scans tool outputs from external sources (WebFetch,
WebSearch, gh CLI) for prompt injection and code execution
patterns. High-severity patterns are blocked (fail-closed).
Medium-severity patterns are escaped (fail-open).

Crash-proof: entire hook wrapped in try/except. On any
unhandled error, content passes through unchanged.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

# --- Pattern compilation (module load time) ---

_MAX_SCAN_SIZE = 100 * 1024  # 100KB

_HIGH_SEVERITY = [
    re.compile(p)
    for p in [
        r"<system[^>]*>",
        r"<assistant[^>]*>",
        r"<human[^>]*>",
        r"<IMPORTANT[^>]*>",
        r"system-reminder",
        r"(?i)you\s+are\s+now\b",
        r"(?i)ignore\s+(all\s+)?previous",
        r"(?i)disregard\s+(all\s+)?prior",
        r"(?i)override\s+(your|the)\s+instructions",
        r"(?i)new\s+instructions\s*:",
        r"!!python/",
        r"__import__\s*\(",
        r"(?<![`])eval\s*\(",
        r"(?<![`])exec\s*\(",
        r"__globals__",
        r"__builtins__",
    ]
]

_MEDIUM_SEVERITY = [
    re.compile(p)
    for p in [
        r"(?<![`])IMPORTANT:",
        r"(?<![`])CRITICAL:",
        r"(?i)(?<![`])act\s+as\b",
        r"(?i)(?<![`])pretend\s+you\s+are\b",
    ]
]

_EXTERNAL_BASH_PATTERNS = [
    "gh api",
    "gh issue",
    "gh pr",
    "gh run",
    "gh release",
    "curl ",
    "wget ",
]


def is_external_tool(tool_name: str, tool_input: dict[str, Any]) -> bool:
    """Check if a tool invocation fetches external content."""
    if tool_name in ("WebFetch", "WebSearch"):
        return True
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return any(pat in cmd for pat in _EXTERNAL_BASH_PATTERNS)
    return False


def sanitize_output(content: str | None) -> str:
    """Sanitize external content for injection patterns.

    High-severity patterns are replaced with [BLOCKED].
    Medium-severity patterns are escaped with backticks.
    Returns empty string for None or non-string input.
    For content over _MAX_SCAN_SIZE, uses fast substring
    checks and blocks if any match.
    """
    if not content:
        return ""

    if not isinstance(content, str):
        return ""

    modified = content

    # For very large content, use fast substring checks only
    if len(content) > _MAX_SCAN_SIZE:
        fast_checks = [
            "<system",
            "<assistant",
            "<human",
            "!!python",
            "__import__",
            "ignore previous",
            "Ignore all previous",
        ]
        for check in fast_checks:
            if check in content[:_MAX_SCAN_SIZE]:
                return "[CONTENT BLOCKED: injection pattern detected in large output]"
        return content

    # High severity: strip (fail-closed)
    for pattern in _HIGH_SEVERITY:
        if pattern.search(modified):
            modified = pattern.sub("[BLOCKED]", modified)

    # Medium severity: escape with backticks
    for pattern in _MEDIUM_SEVERITY:
        match = pattern.search(modified)
        if match:
            matched_text = match.group(0)
            modified = modified.replace(matched_text, f"`{matched_text}`")

    return modified


def process_hook(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a PostToolUse hook payload.

    Returns ALLOW for all tools. For external tools with
    detected injection patterns, attaches sanitized content
    as additionalContext.
    """
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if not is_external_tool(tool_name, tool_input):
        return {"decision": "ALLOW"}

    tool_output = payload.get("tool_output", "")
    if not tool_output:
        return {"decision": "ALLOW"}

    sanitized = sanitize_output(tool_output)

    if sanitized != tool_output:
        sys.stderr.write(f"[sanitize] Modified output from {tool_name}\n")
        return {
            "decision": "ALLOW",
            "additionalContext": (
                "--- SANITIZED EXTERNAL CONTENT "
                f"[source: {tool_name}] ---\n"
                f"{sanitized}\n"
                "--- END SANITIZED CONTENT ---"
            ),
        }

    return {"decision": "ALLOW"}


def main() -> None:
    """Hook entry point. Crash-proof wrapper."""
    try:
        payload = json.loads(sys.stdin.read())
        result = process_hook(payload)
        print(json.dumps(result))
    except Exception as e:
        sys.stderr.write(f"[sanitize] Hook error: {e}\n")
        print(json.dumps({"decision": "ALLOW"}))


if __name__ == "__main__":
    main()
