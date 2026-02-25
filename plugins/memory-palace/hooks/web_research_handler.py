#!/usr/bin/env python3
"""Unified web research handler hook for PostToolUse (WebFetch/WebSearch).

Combines web content processing, auto-capture to knowledge corpus queue,
and research storage prompting into a single PostToolUse hook.

Merges functionality from:
- web_content_processor.py: Safety checks, dedup, auto-capture storage
- research_storage_prompt.py: Lightweight storage reminder prompts

This hook captures research results when auto_capture is enabled (default: true).
When auto-capture is disabled or fails, it prompts the user to store findings.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from shared.config import get_config
from shared.deduplication import (
    get_content_hash,
    is_known,
    needs_update,
    update_index,
)
from shared.safety_checks import is_safe_content

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = PLUGIN_ROOT / "docs" / "knowledge-corpus" / "queue"
STAGING_DIR = PLUGIN_ROOT / "data" / "staging"


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug."""
    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Truncate
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug or "untitled"


def extract_title_from_content(content: str, url: str) -> str:
    """Extract a reasonable title from content or URL."""
    # Try to find a title-like line at the start
    lines = content.strip().split("\n")[:10]
    for line in lines:
        line = line.strip()
        # Skip empty lines and common prefixes
        if not line or line.startswith("#") and len(line) < 5:
            continue
        # Found a title-like line
        if line.startswith("#"):
            return line.lstrip("#").strip()[:100]
        if len(line) > 10 and len(line) < 150:
            return line[:100]

    # Fall back to URL-based title
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        return path_parts[-1].replace("-", " ").replace("_", " ").title()[:100]
    return parsed.netloc


def extract_content_from_webfetch(
    tool_response: dict[str, Any],
) -> tuple[str, str | None]:
    """Extract content and URL from WebFetch response."""
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


def extract_results_from_websearch(
    tool_response: dict[str, Any],
) -> list[dict[str, str]]:
    """Extract search results from WebSearch response."""
    results = []

    if isinstance(tool_response, dict):
        search_results = tool_response.get("results", [])
        if isinstance(search_results, list):
            for result in search_results[:10]:
                if isinstance(result, dict):
                    results.append(
                        {
                            "url": result.get("url", ""),
                            "title": result.get("title", ""),
                            "snippet": result.get(
                                "snippet", result.get("description", "")
                            ),
                        },
                    )

    return results


def store_webfetch_content(
    content: str,
    url: str,
    prompt: str,
) -> str | None:
    """Store WebFetch content to queue and return the stored path.

    Returns the path where content was stored, or None if storage failed.
    """
    try:
        # Generate entry metadata
        now = datetime.now(timezone.utc)
        entry_id = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:8]}"
        title = extract_title_from_content(content, url)
        slug = slugify(title)
        filename = f"webfetch-{slug}-{entry_id[:19]}.md"

        # Create queue entry content
        content_hash = get_content_hash(content)
        content_preview = content[:500] + "..." if len(content) > 500 else content

        queue_entry = f"""---
queue_entry_id: {entry_id}
created_at: {now.isoformat()}
session_type: auto_capture
source_type: webfetch
topic: "{title}"
status: pending_review
priority: medium
url: "{url}"
content_hash: "{content_hash}"
content_length: {len(content)}
auto_generated: true
---

# {title}

## Source

- **URL**: {url}
- **Fetched**: {now.strftime("%Y-%m-%d %H:%M:%S timezone.utc")}
- **Content Length**: {len(content):,} characters

## Fetch Context

**Prompt used**: {prompt or "Not specified"}

## Content Preview

```
{content_preview}
```

## Full Content

<details>
<summary>Click to expand full content ({len(content):,} chars)</summary>

{content}

</details>

## Evaluation Scores (Auto-Generated)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Novelty | TBD | Review needed |
| Applicability | TBD | Review needed |
| Durability | TBD | Review needed |
| Connectivity | TBD | Review needed |
| Authority | TBD | Review needed |

## Next Actions

- [ ] Review content for accuracy and relevance
- [ ] Score using knowledge-intake rubric
- [ ] Decide on permanent storage location
- [ ] Extract reusable patterns if applicable
- [ ] Archive or delete if not valuable
"""

        # Ensure queue directory exists
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)

        # Write queue entry
        queue_path = QUEUE_DIR / filename
        queue_path.write_text(queue_entry, encoding="utf-8")

        # Update index separately -- if this fails, clean up the orphaned file
        try:
            update_index(
                content_hash=content_hash,
                stored_at=str(queue_path.relative_to(PLUGIN_ROOT)),
                importance_score=50,  # Default pending evaluation
                url=url,
                title=title,
                maturity="seedling",
                routing_type="pending",
            )
        except Exception as idx_err:
            logger.error(
                "web_research_handler: Index update failed, removing orphan: %s",
                idx_err,
            )
            queue_path.unlink(missing_ok=True)
            return None

        return str(queue_path)

    except (PermissionError, OSError) as e:
        logger.error("web_research_handler: Failed to store content (I/O): %s", e)
        return None
    except Exception as e:
        logger.error("web_research_handler: Failed to store content: %s", e)
        return None


def store_websearch_results(
    query: str,
    results: list[dict[str, str]],
) -> str | None:
    """Store WebSearch results to queue and return the stored path."""
    if not results:
        return None

    try:
        now = datetime.now(timezone.utc)
        entry_id = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:8]}"
        slug = slugify(query)
        filename = f"websearch-{slug}-{entry_id[:19]}.md"

        # Format results
        results_md = []
        for i, r in enumerate(results[:10], 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            results_md.append(f"""### {i}. {title}

- **URL**: {url}
- **Snippet**: {snippet}
""")

        results_content = "\n".join(results_md)
        content_for_hash = f"{query}|{results_content}"
        content_hash = get_content_hash(content_for_hash)

        queue_entry = f"""---
queue_entry_id: {entry_id}
created_at: {now.isoformat()}
session_type: auto_capture
source_type: websearch
topic: "{query}"
status: pending_review
priority: medium
query: "{query}"
result_count: {len(results)}
content_hash: "{content_hash}"
auto_generated: true
---

# WebSearch: {query}

## Search Metadata

- **Query**: {query}
- **Searched**: {now.strftime("%Y-%m-%d %H:%M:%S timezone.utc")}
- **Results**: {len(results)} items captured

## Search Results

{results_content}

## Evaluation Scores (Auto-Generated)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Novelty | TBD | Review needed |
| Applicability | TBD | Review needed |
| Durability | TBD | Review needed |
| Connectivity | TBD | Review needed |
| Authority | TBD | Review needed |

## Next Actions

- [ ] Review search results for relevance
- [ ] Fetch full content from promising URLs
- [ ] Extract key findings and patterns
- [ ] Create knowledge entry if valuable
- [ ] Archive or delete if not useful
"""

        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        queue_path = QUEUE_DIR / filename
        queue_path.write_text(queue_entry, encoding="utf-8")

        return str(queue_path)

    except (PermissionError, OSError) as e:
        logger.error(
            "web_research_handler: Failed to store search results (I/O): %s", e
        )
        return None
    except Exception as e:
        logger.error("web_research_handler: Failed to store search results: %s", e)
        return None


def _recent_intake_pending(query: str) -> bool:
    """Check if research_interceptor already flagged this query for intake.

    Merged from research_storage_prompt.py to avoid redundant prompts.
    """
    queue_path = PLUGIN_ROOT / "data" / "intake_queue.jsonl"
    if not queue_path.exists():
        return False

    try:
        # Read last 20 lines (most recent entries) to avoid scanning huge files
        lines = queue_path.read_text(encoding="utf-8").strip().splitlines()[-20:]
        normalized_query = query.lower().strip()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("query", "").lower().strip() == normalized_query:
                    return True
            except json.JSONDecodeError:
                continue
    except OSError:
        pass

    return False


def _build_storage_reminder(tool_name: str) -> str:
    """Build a storage reminder message for when auto-capture is not active."""
    skill_ref = "/memory-palace:knowledge-intake"
    return (
        f"Research detected via {tool_name}. "
        f"Consider storing valuable findings with {skill_ref}"
    )


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

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    feature_flags = dict(config.get("feature_flags") or {})
    if not feature_flags.get("lifecycle", True):
        sys.exit(0)

    # Auto-capture feature flag (default: True)
    auto_capture = feature_flags.get("auto_capture", True)

    context_parts = []
    response: dict[str, Any] | None = None
    stored_path: str | None = None

    # Check if research_interceptor already flagged this query for intake
    query = tool_input.get("query", "") or tool_input.get("prompt", "")
    intake_already_pending = query and _recent_intake_pending(query)

    if tool_name == "WebFetch":
        content, url = extract_content_from_webfetch(tool_response)
        url = url or tool_input.get("url", "")
        prompt = tool_input.get("prompt", "")

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
            # Auto-capture the content
            elif auto_capture:
                stored_path = store_webfetch_content(content, url, prompt)
                if stored_path:
                    context_parts.append(
                        f"Memory Palace: Auto-captured web content from {url}\n"
                        f"  Stored to: {Path(stored_path).name}\n"
                        f"  Content length: {len(content):,} chars\n"
                        "  Status: pending_review\n"
                        "  IMPORTANT: Do NOT delete without evaluation - run knowledge-intake to review",
                    )
                else:
                    context_parts.append(
                        f"Memory Palace: New web content fetched from {url}. "
                        "Auto-capture failed - consider manual knowledge-intake. "
                        f"Content length: {len(content)} chars.",
                    )
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

            # Auto-capture search results
            if auto_capture and new_urls:
                stored_path = store_websearch_results(query, results)
                if stored_path:
                    context_parts.append(
                        f"Memory Palace: Auto-captured WebSearch results for '{query}'\n"
                        f"  Stored to: {Path(stored_path).name}\n"
                        f"  New sources: {len(new_urls)}, Known: {len(known_urls)}\n"
                        "  Status: pending_review\n"
                        "  IMPORTANT: Do NOT delete without evaluation - run knowledge-intake to review",
                    )
                else:
                    # Fallback to old behavior
                    context_parts.append(
                        f"Memory Palace: WebSearch found {len(new_urls)} new sources "
                        "not in memory palace (auto-capture failed):",
                    )
                    for r in new_urls[:5]:
                        context_parts.append(
                            f"  - {r.get('title', 'Untitled')}: {r.get('url')}"
                        )
            elif new_urls:
                context_parts.append(
                    f"Memory Palace: WebSearch found {len(new_urls)} new sources "
                    "not in memory palace:",
                )
                for r in new_urls[:5]:
                    context_parts.append(
                        f"  - {r.get('title', 'Untitled')}: {r.get('url')}"
                    )

            if known_urls:
                context_parts.append(
                    f"\nMemory Palace: {len(known_urls)} result(s) already stored. "
                    "Check existing knowledge before re-fetching.",
                )

    # Add storage reminder if no auto-capture happened and intake not already pending
    if not stored_path and not intake_already_pending and not context_parts:
        context_parts.append(_build_storage_reminder(tool_name))

    # Output response
    if context_parts:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "\n".join(context_parts),
            },
        }

    if response:
        print(json.dumps(response))

    sys.exit(0)


if __name__ == "__main__":
    main()
