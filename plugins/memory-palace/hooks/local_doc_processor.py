#!/usr/bin/env python3
"""Local document processor hook for PostToolUse (Read).

Monitors reads from configured knowledge paths and signals
knowledge-intake for new/updated local documentation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def main() -> None:
    """Main hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get('tool_name', '')

    # Fast path: not a Read tool
    if tool_name != 'Read':
        sys.exit(0)

    tool_input = payload.get('tool_input', {})
    file_path = tool_input.get('file_path', '')

    # Fast path: no file path
    if not file_path:
        sys.exit(0)

    # Fast path: not a documentation file type
    path_lower = file_path.lower()
    doc_extensions = ('.md', '.rst', '.txt', '.adoc')
    if not any(path_lower.endswith(ext) for ext in doc_extensions):
        sys.exit(0)

    # Lazy imports for slow path
    from shared.config import get_config, should_process_path
    from shared.deduplication import get_content_hash, is_known, needs_update
    from shared.safety_checks import is_safe_content

    config = get_config()
    if not config.get('enabled', True):
        sys.exit(0)

    # Check if path should be processed
    if not should_process_path(file_path):
        sys.exit(0)

    tool_response = payload.get('tool_response', {})

    # Extract content from Read response
    content = ""
    if isinstance(tool_response, str):
        content = tool_response
    elif isinstance(tool_response, dict):
        content = tool_response.get('content', '')
        # Sometimes response has different structure
        if not content and 'output' in tool_response:
            content = tool_response['output']

    if not content or len(content) < 50:
        sys.exit(0)  # Too short to be valuable

    # Safety check
    safety_result = is_safe_content(content, config)
    if not safety_result.is_safe:
        # Don't message about safety issues on local docs - just skip
        sys.exit(0)

    # Use sanitized content if needed
    if safety_result.should_sanitize and safety_result.sanitized_content:
        content = safety_result.sanitized_content

    content_hash = get_content_hash(content)
    context_parts = []

    # Get relative path for cleaner messaging
    try:
        rel_path = Path(file_path).relative_to(Path.cwd())
    except ValueError:
        rel_path = Path(file_path)

    if is_known(path=file_path):
        if needs_update(content_hash, path=file_path):
            context_parts.append(
                f"Memory Palace: Local doc '{rel_path}' has changed since last indexing. "
                "Consider updating the stored knowledge entry."
            )
        # else: unchanged, no message
    else:
        context_parts.append(
            f"Memory Palace: Reading local knowledge doc '{rel_path}'. "
            "This path is configured for knowledge tracking. "
            "Consider running knowledge-intake if this contains valuable reference material."
        )

    # Output response
    if context_parts:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "\n".join(context_parts)
            }
        }
        print(json.dumps(response))

    sys.exit(0)


if __name__ == '__main__':
    main()
