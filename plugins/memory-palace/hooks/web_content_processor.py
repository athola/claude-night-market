#!/usr/bin/env python3
"""Web content processor hook for PostToolUse (WebFetch/WebSearch).

Processes fetched web content through safety checks and signals
knowledge-intake for storage.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def extract_content_from_webfetch(tool_response: dict[str, Any]) -> tuple[str, str | None]:
    """Extract content and URL from WebFetch response."""
    # WebFetch returns content directly or in a structured response
    content = ""
    url = None

    if isinstance(tool_response, str):
        content = tool_response
    elif isinstance(tool_response, dict):
        content = tool_response.get("content", "")
        url = tool_response.get("url")

        # Sometimes content is nested
        if not content and "result" in tool_response:
            result = tool_response["result"]
            if isinstance(result, str):
                content = result
            elif isinstance(result, dict):
                content = result.get("content", "")

    return content, url


def extract_results_from_websearch(tool_response: dict[str, Any]) -> list[dict[str, str]]:
    """Extract search results from WebSearch response."""
    results = []

    if isinstance(tool_response, dict):
        # WebSearch typically returns results array
        search_results = tool_response.get("results", [])
        if isinstance(search_results, list):
            for result in search_results[:10]:  # Limit to top 10
                if isinstance(result, dict):
                    results.append(
                        {
                            "url": result.get("url", ""),
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", result.get("description", "")),
                        },
                    )

    return results


def main() -> None:
    """Main hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = payload.get("tool_response", {})

    # Fast path: not a web tool
    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    # Lazy imports for slow path
    from shared.config import get_config
    from shared.deduplication import get_content_hash, is_known, needs_update
    from shared.safety_checks import is_safe_content

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    context_parts = []

    if tool_name == "WebFetch":
        content, url = extract_content_from_webfetch(tool_response)
        url = url or tool_input.get("url", "")

        if not content or len(content) < 100:
            sys.exit(0)  # Too short to be valuable

        # Safety check
        safety_result = is_safe_content(content, config)
        if not safety_result.is_safe:
            context_parts.append(
                f"Memory Palace: Content from {url} skipped - {safety_result.reason}",
            )
        else:
            # Use sanitized content if available
            if safety_result.should_sanitize and safety_result.sanitized_content:
                content = safety_result.sanitized_content

            content_hash = get_content_hash(content)

            if is_known(url=url):
                if needs_update(content_hash, url=url):
                    context_parts.append(
                        f"Memory Palace: Content at {url} has changed. "
                        "Consider updating the stored knowledge entry.",
                    )
                # else: unchanged, no message needed
            else:
                context_parts.append(
                    f"Memory Palace: New web content fetched from {url}. "
                    "Consider running knowledge-intake to evaluate and store if valuable. "
                    f"Content length: {len(content)} chars.",
                )

    elif tool_name == "WebSearch":
        results = extract_results_from_websearch(tool_response)

        if results:
            new_urls = []
            known_urls = []

            for result in results:
                url = result.get("url")
                if url:
                    if is_known(url=url):
                        known_urls.append(result)
                    else:
                        new_urls.append(result)

            if new_urls:
                context_parts.append(
                    f"Memory Palace: WebSearch found {len(new_urls)} new sources not in memory palace:",
                )
                for r in new_urls[:5]:
                    context_parts.append(f"  - {r.get('title', 'Untitled')}: {r.get('url')}")

            if known_urls:
                context_parts.append(
                    f"\nMemory Palace: {len(known_urls)} result(s) already stored. "
                    "Check existing knowledge before re-fetching.",
                )

    # Output response
    if context_parts:
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "\n".join(context_parts),
            },
        }

    sys.exit(0)


if __name__ == "__main__":
    main()
