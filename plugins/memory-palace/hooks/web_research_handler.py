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
    _load_index,
    get_content_hash,
    get_stored_at,
    is_known,
    needs_update,
    update_index,
)
from shared.safety_checks import is_safe_content
from shared.text_utils import slugify

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = PLUGIN_ROOT / "data" / "staging"
QUEUE_DIR = STAGING_DIR  # was docs/knowledge-corpus/queue before 1.5.0

# ---------------------------------------------------------------------------
# src/ on sys.path so memory_palace.* imports work in hook context
# ---------------------------------------------------------------------------
_SRC_DIR = str(PLUGIN_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Unguarded, unlike the analytics import below: the title rules are core
# to what this hook stores, and the promoter shares them so a repaired
# title matches what capture would produce today (#624).
from memory_palace.corpus.titles import looks_like_title, title_from_url

try:
    from memory_palace.corpus.index_analytics import (
        _domain,
        _domain_authority,
        cluster_by_domain,
    )

    _ANALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover - src/ is not importable in every hook context
    _ANALYTICS_AVAILABLE = False


def _current_index() -> dict[str, Any]:
    """Return the live capture index for connectivity scoring.

    ``_load_index`` yields the empty sentinel on any read failure, so no
    guard is needed here: a missing index scores connectivity 0 rather
    than failing the capture.
    """
    return _load_index()


def _first_result_url(results: list[dict[str, str]]) -> str:
    """Best available URL for a search capture: the top hit's."""
    return results[0].get("url", "") if results else ""


def build_eval_table(url: str, index: dict[str, Any] | None) -> str:
    """Render the evaluation table from signals the index actually has.

    Emits only criteria that vary per capture and are derivable at fetch
    time: Authority from domain rank, Connectivity from topic-cluster
    size. Both reuse the helpers the promotion ranker scores on, so the
    table and the promote decision cannot drift apart.

    Novelty, Applicability, and Durability are deliberately omitted.
    None is computable here: the first two need a judgment about content,
    and durability is keyed on maturity tier, which is ``seedling`` for
    every capture, so it would print an identical number on every file.
    Previously all five read ``TBD`` on all 554 entries, implying a
    review that never ran (issue #649). A constant dressed as a
    measurement would be that same mistake in a new costume.
    """
    if not _ANALYTICS_AVAILABLE:
        return ""

    domain = _domain(url)
    authority = _domain_authority(domain)

    connectivity = 0.0
    detail = "no sibling captures yet"
    if index:
        sizes = {d: len(keys) for d, keys in cluster_by_domain(index).items()}
        if sizes:
            largest = max(sizes.values())
            mine = sizes.get(domain, 0)
            connectivity = mine / largest if largest else 0.0
            detail = f"{mine} of {largest} in largest cluster"

    return f"""## Evaluation Scores (Auto-Generated)

| Criterion | Score | Source |
|-----------|-------|--------|
| Authority | {authority:.2f} | domain rank ({domain}) |
| Connectivity | {connectivity:.2f} | {detail} |

Scored on structural signals only. Novelty and applicability need a
judgment call this hook cannot make; run knowledge-intake for those."""


def _try_register_graph_entity(
    palaces_dir: Path,
    entity_id: str,
    name: str,
    entity_type: str,
) -> None:
    """Create a graph entity and run link prediction. Never raises.

    Runs silently if the graph DB or package is unavailable.
    """
    try:
        from memory_palace.knowledge_graph import (
            KnowledgeGraph,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
        )

        db_path = palaces_dir / "knowledge_graph.db"
        graph = KnowledgeGraph(str(db_path))
        try:
            graph.upsert_entity(
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
            )
            try:
                from memory_palace.graph_analyzer import (
                    PalaceGraphAnalyzer,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
                )

                analyzer = PalaceGraphAnalyzer(graph)
                suggestions = analyzer.predict_links(top_n=5)
                if suggestions:
                    sys.stderr.write(
                        f"web_research_handler: link predictions: {suggestions[:3]}\n"
                    )
            except Exception:  # noqa: BLE001 - link prediction is optional; entity write already succeeded
                pass
        finally:
            graph.close()
    except Exception as exc:  # noqa: BLE001 - hooks must never crash; log and continue
        sys.stderr.write(f"web_research_handler: graph wiring skipped: {exc}\n")


# The title shape rules live in the corpus package because the index
# promoter needs the same ruling to repair titles this hook stored
# before the rules were right (#624).
_looks_like_title = looks_like_title


def extract_title_from_content(content: str, url: str) -> str:
    """Extract a reasonable title from content or URL.

    Lines that read as model preamble rather than a page title are
    skipped, so a later real heading can still win. When no line
    qualifies, fall back to the URL slug (#621).
    """
    # Try to find a title-like line at the start
    lines = content.strip().split("\n")[:10]
    for raw_line in lines:
        line = raw_line.strip()
        # Skip empty lines and common prefixes
        if not line or (line.startswith("#") and len(line) < 5):
            continue
        # A heading is explicit markup, so it needs no length floor; a
        # plain line does, to avoid promoting stray one-word fragments.
        if line.startswith("#"):
            candidate = line.lstrip("#").strip()
        elif len(line) > 10:
            candidate = line
        else:
            continue
        if _looks_like_title(candidate):
            return candidate

    # Fall back to URL-based title
    return title_from_url(url)


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


# WebFetch reports transport failures as content text, e.g.
# "The server returned HTTP 429 Too Many Requests." Anchoring on this
# exact phrase keeps the detector precise: an article that merely
# mentions "404" or "HTTP 500" in prose is not a failed fetch.
_FETCH_STATUS_RE = re.compile(r"server returned HTTP\s+(\d{3})")


def detect_failed_fetch_status(
    tool_response: dict[str, Any] | str,
    content: str,
) -> int | None:
    """Return the HTTP status of a non-2xx fetch, or None if it looks OK.

    Storing an error body (HTTP 404/429/5xx page) as a seedling knowledge
    note pollutes the index (issue #547). The caller drops any response we
    can positively identify as non-2xx. A return of None means "no failure
    detected", not "verified 2xx": a present body without the failure
    signature is treated as a successful fetch, matching prior behavior.
    """
    if isinstance(tool_response, dict):
        for key in ("status_code", "status", "http_status"):
            val = tool_response.get(key)
            if isinstance(val, bool):
                continue
            if isinstance(val, int) and not 200 <= val < 300:
                return val
    match = _FETCH_STATUS_RE.search(content or "")
    if match:
        code = int(match.group(1))
        if 100 <= code < 600 and not 200 <= code < 300:
            return code
    return None


# WebFetch emits this exact notice when a URL bounces to a different
# host: what follows is the notice itself, not the page. Anchoring on
# the literal marker keeps this as precise as _FETCH_STATUS_RE.
_REDIRECT_NOTICE = "REDIRECT DETECTED"


def detect_null_capture(
    tool_response: dict[str, Any] | str,
    content: str,
) -> str | None:
    """Return why a 2xx response carried no content, or None if it did.

    Sibling of :func:`detect_failed_fetch_status`, which covers non-2xx
    responses. This covers fetches that succeeded but returned nothing
    usable: a redirect notice, or a structured result set with zero
    entries. Such captures were promoted on domain and cluster signals
    alone, scoring above much of the real corpus (issue #649).

    Only structural signals are used. The prose body is written by the
    model summarizing the page, so phrases like "no stories found" are
    not reliable: a capture can carry a full result table and still note
    that one subset is absent. Two heuristics built on that prose were
    tried against the live corpus and both deleted real research, which
    is why nothing here reads the summary text.
    """
    if _REDIRECT_NOTICE in (content or ""):
        return "redirect-notice"

    if isinstance(tool_response, dict):
        for key in ("results", "hits"):
            val = tool_response.get(key)
            if isinstance(val, list) and not val:
                return "empty-results"
        total = tool_response.get("nbHits")
        if isinstance(total, int) and not isinstance(total, bool) and total == 0:
            return "empty-results"

    return None


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


def _store_to_queue(  # noqa: PLR0913 - one queue entry carries this many fields
    filename: str,
    content: str,
    content_hash: str,
    source_ref: str,
    title: str,
    null_capture: str | None = None,
) -> str | None:
    """Write a queue entry file and update the dedup index.

    Returns the stored path on success, or None on failure.
    """
    try:
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        queue_path = QUEUE_DIR / filename
        queue_path.write_text(content, encoding="utf-8")

        try:
            update_index(
                content_hash=content_hash,
                stored_at=str(queue_path.relative_to(PLUGIN_ROOT)),
                importance_score=50,
                url=source_ref,
                title=title,
                maturity="seedling",
                routing_type="pending",
                null_capture=null_capture,
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


def _register_duplicate_url(
    content_hash: str,
    canonical: str,
    url: str,
    content: str,
) -> None:
    """Index a URL against a capture already stored under another URL.

    Writes no file: ``canonical`` already holds these bytes. The entry
    records where the content lives so retrieval and dedup agree.
    """
    try:
        update_index(
            content_hash=content_hash,
            stored_at=canonical,
            importance_score=50,
            url=url,
            title=extract_title_from_content(content, url),
            maturity="seedling",
            routing_type="pending",
        )
    except Exception as idx_err:
        logger.error(
            "web_research_handler: Duplicate-URL index update failed: %s",
            idx_err,
        )


def store_webfetch_content(
    content: str,
    url: str,
    prompt: str,
    null_capture: str | None = None,
) -> str | None:
    """Store WebFetch content to queue and return the stored path.

    Returns the path where content was stored, or None if storage failed.
    """
    now = datetime.now(timezone.utc)
    entry_id = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:8]}"
    title = extract_title_from_content(content, url)
    slug = slugify(title)
    filename = f"webfetch-{slug}-{entry_id[:19]}.md"

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
- **Fetched**: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
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

{build_eval_table(url, _current_index())}

## Next Actions

- [ ] Review content for accuracy and relevance
- [ ] Score using knowledge-intake rubric
- [ ] Decide on permanent storage location
- [ ] Extract reusable patterns if applicable
- [ ] Archive or delete if not valuable
"""

    return _store_to_queue(
        filename, queue_entry, content_hash, url, title, null_capture
    )


def store_websearch_results(
    query: str,
    results: list[dict[str, str]],
) -> str | None:
    """Store WebSearch results to queue and return the stored path."""
    if not results:
        return None

    now = datetime.now(timezone.utc)
    entry_id = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:8]}"
    slug = slugify(query)
    filename = f"websearch-{slug}-{entry_id[:19]}.md"

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
- **Searched**: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Results**: {len(results)} items captured

## Search Results

{results_content}

{build_eval_table(_first_result_url(results), _current_index())}

## Next Actions

- [ ] Review search results for relevance
- [ ] Fetch full content from promising URLs
- [ ] Extract key findings and patterns
- [ ] Create knowledge entry if valuable
- [ ] Archive or delete if not useful
"""

    return _store_to_queue(
        filename, queue_entry, content_hash, query, f"WebSearch: {query}"
    )


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
    return f"Research detected via {tool_name}. Consider storing valuable findings with {skill_ref}"


def _handle_webfetch(
    tool_input: dict[str, Any],
    tool_response: dict[str, Any],
    config: dict[str, Any],
    auto_capture: bool,
) -> tuple[list[str], str | None, dict[str, str] | None]:
    """Process a WebFetch tool result.

    Returns ``(context_parts, stored_path, graph_register_kwargs)``.
    ``graph_register_kwargs`` is ``None`` when nothing was stored.
    Exits with code 0 if the fetched content is too short to be valuable.
    """
    context_parts: list[str] = []
    stored_path: str | None = None

    content, url = extract_content_from_webfetch(tool_response)
    url = url or tool_input.get("url", "")
    prompt = tool_input.get("prompt", "")

    failed_status = detect_failed_fetch_status(tool_response, content)
    if failed_status is not None:
        logger.info("Skipping non-2xx fetch (HTTP %s) from %s", failed_status, url)
        context_parts.append(
            f"Memory Palace: Fetch from {url} returned HTTP {failed_status}; not captured.",
        )
        return context_parts, None, None

    if not content or len(content) < 100:
        sys.exit(0)  # Too short to be valuable

    safety_result = is_safe_content(content, config)
    if not safety_result.is_safe:
        context_parts.append(
            f"Memory Palace: Content from {url} skipped - {safety_result.reason}",
        )
        return context_parts, None, None

    if safety_result.should_sanitize and safety_result.sanitized_content:
        content = safety_result.sanitized_content

    content_hash = get_content_hash(content)

    if is_known(url=url):
        if needs_update(content_hash, url=url):
            context_parts.append(
                f"Memory Palace: Content at {url} has changed. "
                "Consider updating the stored knowledge entry.",
            )
        return context_parts, None, None

    canonical = get_stored_at(content_hash)
    if canonical is not None:
        # These exact bytes are already on disk under a different URL
        # (an empty API result, a mirror, a redirect target). Record the
        # new URL against the existing capture instead of writing a
        # second copy of content we already have.
        _register_duplicate_url(content_hash, canonical, url, content)
        context_parts.append(
            f"Memory Palace: Content from {url} is byte-identical to an "
            f"existing capture. Indexed against {Path(canonical).name} "
            "instead of storing a duplicate.",
        )
        return context_parts, None, None

    # Computed here, where tool_response is still structured. Downstream
    # only sees the model's prose summary, which cannot be read reliably
    # for emptiness (issue #649).
    null_capture = detect_null_capture(tool_response, content)

    if auto_capture:
        stored_path = store_webfetch_content(
            content, url, prompt, null_capture=null_capture
        )
        if stored_path:
            context_parts.append(
                f"Memory Palace: Auto-captured web content from {url}\n"
                f"  Stored to: {Path(stored_path).name}\n"
                f"  Content length: {len(content):,} chars\n"
                "  Status: pending_review\n"
                "  IMPORTANT: Do NOT delete without evaluation"
                " - run knowledge-intake to review",
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

    register_kwargs: dict[str, str] | None = None
    if stored_path:
        register_kwargs = {
            "entity_id": "web_"
            + (url or "unknown").replace("://", "_").replace("/", "_")[:40],
            "name": extract_title_from_content(content, url or ""),
        }
    return context_parts, stored_path, register_kwargs


def _partition_by_known(
    results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split WebSearch results into (new, known) by URL, dropping empty URLs."""
    new_urls: list[dict[str, Any]] = []
    known_urls: list[dict[str, Any]] = []
    for result in results:
        url = result.get("url")
        if not url:
            continue
        target = known_urls if is_known(url=url) else new_urls
        target.append(result)
    return new_urls, known_urls


def _format_new_url_lines(new_urls: list[dict[str, Any]]) -> list[str]:
    """Format up to five new-source result rows for the context output."""
    return [f"  - {r.get('title', 'Untitled')}: {r.get('url')}" for r in new_urls[:5]]


def _handle_websearch(
    query: str,
    tool_response: dict[str, Any],
    auto_capture: bool,
) -> tuple[list[str], str | None, dict[str, str] | None]:
    """Process a WebSearch tool result.

    Returns ``(context_parts, stored_path, graph_register_kwargs)``.
    ``graph_register_kwargs`` is ``None`` when nothing was stored.
    """
    context_parts: list[str] = []
    stored_path: str | None = None

    results = extract_results_from_websearch(tool_response)
    if not results:
        return context_parts, None, None

    new_urls, known_urls = _partition_by_known(results)

    if auto_capture and new_urls:
        stored_path = store_websearch_results(query, results)
        if stored_path:
            context_parts.append(
                f"Memory Palace: Auto-captured WebSearch results for '{query}'\n"
                f"  Stored to: {Path(stored_path).name}\n"
                f"  New sources: {len(new_urls)}, Known: {len(known_urls)}\n"
                "  Status: pending_review\n"
                "  IMPORTANT: Do NOT delete without evaluation"
                " - run knowledge-intake to review",
            )
        else:
            context_parts.append(
                f"Memory Palace: WebSearch found {len(new_urls)} new sources "
                "not in memory palace (auto-capture failed):",
            )
            context_parts.extend(_format_new_url_lines(new_urls))
    elif new_urls:
        context_parts.append(
            f"Memory Palace: WebSearch found {len(new_urls)} new sources not in memory palace:",
        )
        context_parts.extend(_format_new_url_lines(new_urls))

    if known_urls:
        context_parts.append(
            f"\nMemory Palace: {len(known_urls)} result(s) already stored. "
            "Check existing knowledge before re-fetching.",
        )

    register_kwargs: dict[str, str] | None = None
    if stored_path:
        register_kwargs = {
            "entity_id": "websearch_" + slugify(query or "")[:40],
            "name": f"WebSearch: {query}",
        }
    return context_parts, stored_path, register_kwargs


def main() -> None:
    """Run the web research handler hook entry point.

    Routes WebFetch / WebSearch postToolUse payloads to dimension-specific
    handlers, then handles graph registration, storage reminders, and
    response shaping.
    """
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.warning("web_research_handler: Failed to parse payload: %s", e)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = payload.get("tool_response", {})

    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    feature_flags = dict(config.get("feature_flags") or {})
    if not feature_flags.get("lifecycle", True):
        sys.exit(0)

    auto_capture = feature_flags.get("auto_capture", True)
    query = tool_input.get("query", "") or tool_input.get("prompt", "")
    intake_already_pending = query and _recent_intake_pending(query)

    if tool_name == "WebFetch":
        context_parts, stored_path, register_kwargs = _handle_webfetch(
            tool_input, tool_response, config, auto_capture
        )
    else:  # WebSearch
        context_parts, stored_path, register_kwargs = _handle_websearch(
            query, tool_response, auto_capture
        )

    if stored_path and register_kwargs:
        palaces_dir = PLUGIN_ROOT / "data" / "palaces"
        _try_register_graph_entity(
            palaces_dir=palaces_dir,
            entity_id=register_kwargs["entity_id"],
            name=register_kwargs["name"],
            entity_type="web_resource",
        )

    if not stored_path and not intake_already_pending and not context_parts:
        context_parts.append(_build_storage_reminder(tool_name))

    if context_parts:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "\n".join(context_parts),
            },
        }
        print(json.dumps(response))

    sys.exit(0)


if __name__ == "__main__":
    main()
