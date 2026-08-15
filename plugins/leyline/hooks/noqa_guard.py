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
from typing import Any

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


def _coerce_tool_input(value: Any) -> dict[str, Any]:
    """Normalize ``tool_input`` to a dict regardless of source.

    Stdin delivers it already parsed; the legacy env var delivers a JSON
    string. A non-object value collapses to an empty dict rather than
    raising, matching the lenient behavior the hooks relied on.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _read_payload() -> dict[str, Any]:
    """Read the PreToolUse payload Claude Code delivers as JSON on stdin.

    Falls back to the legacy ``CLAUDE_TOOL_NAME`` / ``CLAUDE_TOOL_INPUT``
    environment variables when stdin is empty, so the existing test
    harness and any older callers keep working.

    Returns ``tool_name`` as a ``str`` and ``tool_input`` as a ``dict`` on
    every path, including a stdin payload that omits them or sends them as
    null. Callers index both without checking.

    Sync note: this stdin-unless-tty / decode-or-warn / env-fallback shape is
    duplicated by ``sanctum/hooks/deferred_item_watcher.read_payload`` and
    ``abstract/hooks/shared/hook_io.read_hook_payload``. Plugin isolation
    forbids a cross-plugin import, so the three copies must be changed
    together. ``tests/unit/test_hook_payload_readers.py`` at the repo root
    is what makes that requirement fail a run instead of a review.
    """
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except (OSError, ValueError):
        raw = ""

    payload: Any = None
    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            # Fail-open is intentional (crash-proof), but log so a disabled
            # guard is distinguishable from an idle one.
            sys.stderr.write(f"noqa_guard: malformed stdin payload: {exc}\n")
            payload = None

    if not isinstance(payload, dict):
        payload = {
            "tool_name": os.environ.get("CLAUDE_TOOL_NAME", ""),
            "tool_input": os.environ.get("CLAUDE_TOOL_INPUT", ""),
        }

    return {
        **payload,
        "tool_name": payload.get("tool_name") or "",
        "tool_input": _coerce_tool_input(payload.get("tool_input", {})),
    }


def main() -> None:
    """Check tool input for lint suppression directives.

    Reads the PreToolUse payload (``tool_name``, ``tool_input``) from the
    JSON object Claude Code provides on stdin, with a legacy
    ``CLAUDE_TOOL_*`` env-var fallback for the test harness.
    """
    payload = _read_payload()
    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        print(json.dumps({}))
        return

    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
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
                    "permissionDecision": "deny",
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
