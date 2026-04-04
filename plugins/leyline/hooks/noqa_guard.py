#!/usr/bin/env python3
"""PreToolUse hook: block inline lint suppression directives.

Scans Edit and Write tool inputs for inline lint suppression
comments across multiple languages:

- Python: ``# noqa``, ``# type: ignore``, ``# pylint: disable``
- Rust: ``#[allow(...)]``
- JavaScript/TypeScript: ``eslint-disable``, ``@ts-ignore``,
  ``@ts-expect-error``
- Go: ``//nolint``

Policy: inline suppressions hide issues from reviewers. Use
project-level config files instead (pyproject.toml per-file-ignores,
.eslintrc, Cargo.toml, etc.).
"""

from __future__ import annotations

import json
import os
import re
import sys

# Each tuple: (compiled pattern, label for the message)
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Python
    (re.compile(r"#\s*noqa\b"), "# noqa"),
    (re.compile(r"#\s*type:\s*ignore"), "# type: ignore"),
    (re.compile(r"#\s*pylint:\s*disable"), "# pylint: disable"),
    # Rust
    (re.compile(r"#\[allow\("), "#[allow(...)]"),
    # JavaScript / TypeScript
    (re.compile(r"//\s*eslint-disable"), "eslint-disable"),
    (re.compile(r"//\s*@ts-ignore"), "@ts-ignore"),
    (re.compile(r"//\s*@ts-expect-error"), "@ts-expect-error"),
    # Go
    (re.compile(r"//\s*nolint"), "//nolint"),
]


def check_for_suppressions(text: str) -> list[str]:
    """Return descriptions of lines containing lint suppressions."""
    hits: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        for pattern, label in _PATTERNS:
            if pattern.search(line):
                stripped = line.strip()
                hits.append(f"  line {i} ({label}): {stripped[:80]}")
                break  # one hit per line is enough
    return hits


def main() -> None:
    """Check tool input for lint suppression directives.

    Reads CLAUDE_TOOL_NAME and CLAUDE_TOOL_INPUT from environment
    variables (not stdin) because PreToolUse hooks receive tool
    metadata via env vars set by Claude Code, while stdin carries
    the hook event JSON payload which does not include tool input.
    """
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    if tool_name not in ("Edit", "Write"):
        print(json.dumps({}))
        return

    raw_input = os.environ.get("CLAUDE_TOOL_INPUT", "")
    if not raw_input:
        print(json.dumps({}))
        return

    try:
        tool_input = json.loads(raw_input)
    except (json.JSONDecodeError, TypeError):
        print(json.dumps({}))
        return

    text_to_check = ""
    if tool_name == "Write":
        text_to_check = tool_input.get("content", "")
    elif tool_name == "Edit":
        text_to_check = tool_input.get("new_string", "")

    if not text_to_check:
        print(json.dumps({}))
        return

    hits = check_for_suppressions(text_to_check)
    if not hits:
        print(json.dumps({}))
        return

    msg = (
        "BLOCKED: inline lint suppression comments are not allowed.\n"
        "Fix the issue directly, or add the rule to the project\n"
        "config file (pyproject.toml per-file-ignores, .eslintrc,\n"
        "Cargo.toml, etc.).\n\n"
        "Detected suppressions:\n" + "\n".join(hits)
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "block",
                    "permissionDecisionReason": msg,
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Crash-proof: never block on hook errors, but log for debugging
        print(f"noqa_guard: hook error: {exc}", file=sys.stderr)
        print(json.dumps({}))
        sys.exit(0)
