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
        r"(?i)<system[^>]*>",
        r"(?i)<assistant[^>]*>",
        r"(?i)<human[^>]*>",
        r"(?i)<IMPORTANT[^>]*>",
        r"(?i)system-reminder",
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

# --- Invisible text injection patterns (high severity) ---

_INVISIBLE_TEXT = [
    re.compile(p)
    for p in [
        r'style\s*=\s*["\'][^"\']*display:\s*none',
        r'style\s*=\s*["\'][^"\']*visibility:\s*hidden',
        r'style\s*=\s*["\'][^"\']*color:\s*(?:white|#fff(?:fff)?)\b',
        r'style\s*=\s*["\'][^"\']*color:\s*rgb\(\s*255',
        r'style\s*=\s*["\'][^"\']*font-size:\s*0\b',
        r'style\s*=\s*["\'][^"\']*opacity:\s*0\b',
        r'style\s*=\s*["\'][^"\']*height:\s*0[^0-9].*overflow:\s*hidden',
    ]
]

_INSTRUCTION_COMMENT = re.compile(
    r"<!--[^>]*(?:ignore|override|forget|you are)[^>]*-->",
    re.IGNORECASE,
)

_ZERO_WIDTH_CHARS = re.compile("[\u200b\u200c\u200d\ufeff]")

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
            "<important",
            "!!python",
            "__import__",
            "__globals__",
            "__builtins__",
            "system-reminder",
            "you are now",
            "ignore previous",
            "ignore all previous",
            "disregard",
            "override",
            "new instructions",
            "eval(",
            "exec(",
            'style="display:none',
            "style='display:none",
            'style="display: none',
            "style='display: none",
            'style="visibility:hidden',
            "style='visibility:hidden",
            'style="visibility: hidden',
            "style='visibility: hidden",
            'style="opacity:0',
            "style='opacity:0",
            'style="opacity: 0',
            "style='opacity: 0",
            'style="font-size:0',
            "style='font-size:0",
            'style="font-size: 0',
            "style='font-size: 0",
        ]
        # Scan in chunks with overlap to cover entire content
        chunk_size = _MAX_SCAN_SIZE  # 100KB
        overlap = 1024  # 1KB overlap to catch patterns at boundaries
        pos = 0
        while pos < len(content):
            end = min(pos + chunk_size, len(content))
            chunk = content[pos:end].lower()
            for check in fast_checks:
                if check in chunk:
                    return (
                        "[CONTENT BLOCKED: injection pattern detected in large output]"
                    )
            pos += chunk_size - overlap
        return content

    # High severity: strip (fail-closed)
    for pattern in _HIGH_SEVERITY:
        if pattern.search(modified):
            modified = pattern.sub("[BLOCKED]", modified)

    # Invisible text patterns: strip (fail-closed)
    for pattern in _INVISIBLE_TEXT:
        if pattern.search(modified):
            modified = pattern.sub("[BLOCKED]", modified)

    # Instruction-bearing HTML comments: strip entirely
    if _INSTRUCTION_COMMENT.search(modified):
        modified = _INSTRUCTION_COMMENT.sub("[BLOCKED]", modified)

    # Zero-width characters: strip silently
    modified = _ZERO_WIDTH_CHARS.sub("", modified)

    # Medium severity: escape with backticks (all occurrences)
    for pattern in _MEDIUM_SEVERITY:
        if pattern.search(modified):
            modified = pattern.sub(lambda m: f"`{m.group(0)}`", modified)

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
        return {}

    tool_output = payload.get("tool_output", "")
    if not tool_output:
        return {}

    sanitized = sanitize_output(tool_output)

    if sanitized != tool_output:
        sys.stderr.write(f"[sanitize] Modified output from {tool_name}\n")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "--- SANITIZED EXTERNAL CONTENT "
                    f"[source: {tool_name}] ---\n"
                    f"{sanitized}\n"
                    "--- END SANITIZED CONTENT ---"
                ),
            },
        }

    return {}


def main() -> None:
    """Hook entry point. On errors, allows content with a safety warning."""
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError) as e:
        # Parse errors: allow content through (can't process)
        sys.stderr.write(f"[sanitize] Input parse error: {e}\n")
        print(json.dumps({}))
        return

    try:
        result = process_hook(payload)
        print(json.dumps(result))
    except Exception as e:
        # Processing errors: allow with caution warning
        sys.stderr.write(f"[sanitize] Processing error: {e}\n")
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "[SANITIZE HOOK ERROR] Content could not be "
                            "verified as safe. Treat with caution."
                        ),
                    },
                }
            )
        )


if __name__ == "__main__":
    main()
