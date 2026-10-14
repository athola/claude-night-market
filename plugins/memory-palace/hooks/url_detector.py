#!/usr/bin/env python3
"""URL detector hook for UserPromptSubmit.

Detects URLs in user prompts and signals knowledge-intake processing.
Optimized for speed - most prompts have no URLs.
"""

from __future__ import annotations

import json
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Simple URL pattern for fast detection (full validation happens later)
_URL_QUICK_PATTERN = re.compile(r'https?://[^\s<>"\')\]]+', re.IGNORECASE)

# Sentence punctuation that follows a pasted URL without belonging to it.
_TRAILING_PUNCTUATION = ".,;:!?"

# Domains to skip (not knowledge sources)
_SKIP_DOMAINS = frozenset(
    [
        "localhost",
        "127.0.0.1",
        "github.com/anthropics/claude-code",  # Claude Code repo (we have local docs)
    ],
)

# File extensions that aren't articles/knowledge
_SKIP_EXTENSIONS = frozenset(
    [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".mp4",
        ".mp3",
        ".wav",
        ".webm",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".exe",
        ".dmg",
        ".pkg",
        ".pdf",  # Could be knowledge but needs special handling
    ],
)


def _is_skipped_domain(url_lower: str) -> bool:
    """Return True when the URL's host (or host/path prefix) is a skip entry."""
    rest = url_lower.split("://", 1)[-1]
    authority, _, path = rest.partition("/")
    host = authority.rsplit("@", 1)[-1].split(":", 1)[0]
    if host.startswith("www."):
        host = host[len("www.") :]
    path = re.split(r"[?#]", path, maxsplit=1)[0]
    if path.endswith(".git"):
        path = path[: -len(".git")]
    for domain in _SKIP_DOMAINS:
        if "/" in domain:
            skip_host, _, skip_path = domain.partition("/")
            # Match whole path segments, so claude-code-action is not claude-code.
            if host == skip_host and (
                path == skip_path or path.startswith(skip_path + "/")
            ):
                return True
        elif host == domain:
            return True
    return False


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text quickly."""
    # Fast path: no URL indicators
    if "://" not in text:
        return []

    urls = [
        url.rstrip(_TRAILING_PUNCTUATION) for url in _URL_QUICK_PATTERN.findall(text)
    ]

    # Filter out non-knowledge URLs
    filtered = []
    for url in urls:
        url_lower = url.lower()

        # Skip certain domains. Matched against the host, so a path
        # segment that merely mentions one does not hide an article.
        if _is_skipped_domain(url_lower):
            continue

        # Skip media/binary files
        if any(url_lower.endswith(ext) for ext in _SKIP_EXTENSIONS):
            continue

        filtered.append(url)

    return filtered


def main() -> None:
    """Run the URL detector hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, exit silently

    prompt = payload.get("prompt", "")

    # Fast path: no URL indicators
    if "://" not in prompt and "www." not in prompt:
        sys.exit(0)

    urls = extract_urls(prompt)

    if not urls:
        sys.exit(0)

    # Imported here, not at module scope: this hook runs on every
    # prompt and `shared` pulls in memory_palace.paths and xxhash,
    # about 100ms that a prompt with no URL has no use for.
    from shared.config import get_config
    from shared.deduplication import is_known

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    # Check which URLs are new
    new_urls = []
    known_urls = []

    for url in urls:
        if is_known(url=url):
            known_urls.append(url)
        else:
            new_urls.append(url)

    # Build response
    response: dict[str, Any] | None = None
    if new_urls or known_urls:
        context_parts = []

        if new_urls:
            context_parts.append(
                f"Memory Palace: Detected {len(new_urls)} new URL(s) for knowledge intake:\n"
                + "\n".join(f"  - {url}" for url in new_urls[:5]),
            )
            if len(new_urls) > 5:
                context_parts.append(f"  ... and {len(new_urls) - 5} more")
            context_parts.append(
                "\nAfter processing the user's request, consider running the knowledge-intake "
                "workflow to store valuable content from these URLs.",
            )

        if known_urls:
            context_parts.append(
                f"\nMemory Palace: {len(known_urls)} URL(s) already indexed. "
                "Check memory-palace for existing knowledge before re-fetching.",
            )

        response = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(context_parts),
            },
        }

    if response:
        print(json.dumps(response))

    sys.exit(0)


if __name__ == "__main__":
    main()
