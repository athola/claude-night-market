#!/usr/bin/env python3
"""Research interceptor hook for PreToolUse (WebSearch/WebFetch).

Intercepts research queries to check local knowledge cache before hitting the web.
Implements cache-first behavior with user-controlled modes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


# Freshness indicators - if present, likely needs web
_FRESHNESS_PATTERNS = re.compile(
    r'\b(latest|recent|new|current|2025|2024|today|now|update)\b',
    re.IGNORECASE
)

# Evergreen indicators - timeless concepts that cache well
_EVERGREEN_PATTERNS = re.compile(
    r'\b(patterns?|principles?|concept|theory|fundamental|basic|how to|guide|tutorial)\b',
    re.IGNORECASE
)


def extract_query_intent(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Extract the query intent from tool parameters.

    Args:
        tool_name: Name of the tool being called
        tool_input: Tool input parameters

    Returns:
        Query string representing user intent
    """
    if tool_name == 'WebSearch':
        return tool_input.get('query', '')
    elif tool_name == 'WebFetch':
        # For WebFetch, use the prompt or URL
        prompt = tool_input.get('prompt', '')
        url = tool_input.get('url', '')
        return prompt or url

    return ''


def needs_freshness(query: str) -> bool:
    """Check if query likely needs fresh data from web.

    Args:
        query: Query string

    Returns:
        True if query contains freshness indicators
    """
    return bool(_FRESHNESS_PATTERNS.search(query))


def is_evergreen(query: str) -> bool:
    """Check if query is about timeless concepts.

    Args:
        query: Query string

    Returns:
        True if query appears to be about evergreen topics
    """
    return bool(_EVERGREEN_PATTERNS.search(query))


def search_local_knowledge(query: str) -> list[dict[str, Any]]:
    """Search local knowledge corpus for matches.

    Args:
        query: Query string

    Returns:
        List of matching entries with match scores
    """
    try:
        # Import here to avoid import overhead if not needed
        # Add the src directory to path
        plugin_root = Path(__file__).parent.parent
        src_path = plugin_root / "src"

        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from memory_palace.corpus.cache_lookup import CacheLookup

        # Get corpus and index directories from config
        corpus_dir = str(plugin_root / "docs" / "knowledge-corpus")
        index_dir = str(plugin_root / "hooks")

        # Create lookup instance
        lookup = CacheLookup(corpus_dir, index_dir)

        # Search with minimum score of 0 to get all results
        results = lookup.search(query, mode="unified", min_score=0.0)

        return results

    except Exception as e:
        # If search fails, return empty results
        # Don't block the request
        return []


def make_decision(
    query: str,
    results: list[dict[str, Any]],
    mode: str
) -> dict[str, Any]:
    """Make decision based on cache results and mode.

    Args:
        query: Original query
        results: Search results from cache
        mode: Research mode (cache_only, cache_first, augment, web_only)

    Returns:
        Decision dict with action, context, and optional modifications
    """
    decision: dict[str, Any] = {
        "action": "proceed",  # proceed, block, augment
        "context": [],
        "should_flag_for_intake": False,
    }

    # web_only: skip cache entirely
    if mode == "web_only":
        return decision

    # Check for matches
    best_match = results[0] if results else None

    if not best_match:
        # No matches found
        if mode == "cache_only":
            decision["action"] = "block"
            decision["context"].append(
                "Memory Palace (cache_only mode): No local knowledge found for this query. "
                "Web search blocked. Consider switching to cache_first mode or adding knowledge manually."
            )
        else:
            # Proceed with web, flag for potential intake
            decision["should_flag_for_intake"] = True
            decision["context"].append(
                "Memory Palace: No cached knowledge found. Proceeding with web search. "
                "Result will be flagged for potential knowledge intake."
            )
        return decision

    # We have matches
    match_score = best_match.get("match_score", 0.0)
    match_strength = best_match.get("match_strength", "weak")

    # Strong match (>80%)
    if match_score > 0.8:
        # Check if evergreen or needs freshness
        is_fresh_needed = needs_freshness(query)
        is_evergreen_topic = is_evergreen(query)

        if is_evergreen_topic or not is_fresh_needed:
            # Strong match on evergreen topic
            if mode == "cache_only":
                decision["action"] = "block"
                decision["context"].append(
                    f"Memory Palace (cache_only): Found strong match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. Web search blocked."
                )
            elif mode == "augment":
                decision["action"] = "augment"
                decision["context"].append(
                    f"Memory Palace: Found strong cached match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. Combining with web search."
                )
                decision["cached_entries"] = results[:3]  # Top 3 results
            else:  # cache_first
                decision["action"] = "augment"
                decision["context"].append(
                    f"Memory Palace: Found strong cached match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. "
                    "This may answer your question. Proceeding with web verification."
                )
                decision["cached_entries"] = results[:1]  # Just the top result
        else:
            # Needs freshness, proceed with web
            decision["action"] = "augment"
            decision["context"].append(
                f"Memory Palace: Found cached match but query needs fresh data. "
                "Combining cache with web search."
            )
            decision["cached_entries"] = results[:2]

    # Partial match (40-80%)
    elif match_score >= 0.4:
        if mode == "cache_only":
            decision["action"] = "block"
            decision["context"].append(
                f"Memory Palace (cache_only): Found partial match ({match_score:.0%}) - "
                f"'{best_match.get('title', 'Untitled')}'. Web search blocked."
            )
        elif mode == "augment":
            decision["action"] = "augment"
            decision["context"].append(
                f"Memory Palace: Found partial match ({match_score:.0%}) - "
                f"'{best_match.get('title', 'Untitled')}'. Augmenting with web search."
            )
            decision["cached_entries"] = results[:3]
        else:  # cache_first
            # Inject context but proceed with targeted web query
            decision["action"] = "augment"
            decision["context"].append(
                f"Memory Palace: Found partial match ({match_score:.0%}). "
                "Injecting cached knowledge and proceeding with web search."
            )
            decision["cached_entries"] = results[:2]
            decision["should_flag_for_intake"] = True

    # Weak match (<40%)
    else:
        if mode == "cache_only":
            decision["action"] = "block"
            decision["context"].append(
                "Memory Palace (cache_only): Only weak matches found. Web search blocked."
            )
        else:
            # Proceed with web search
            decision["should_flag_for_intake"] = True
            decision["context"].append(
                "Memory Palace: Weak cache match. Proceeding with full web search."
            )

    return decision


def format_cached_entry_context(entry: dict[str, Any]) -> str:
    """Format a cached entry for context injection.

    Args:
        entry: Cache entry with metadata

    Returns:
        Formatted string for context
    """
    title = entry.get('title', 'Untitled')
    file_path = entry.get('file', 'unknown')
    match_score = entry.get('match_score', 0.0)

    # Get a brief excerpt if available
    excerpt = ""
    if 'content' in entry:
        content = entry['content']
        # Get first 200 chars
        excerpt = content[:200].strip()
        if len(content) > 200:
            excerpt += "..."

    parts = [
        f"\n--- Cached Knowledge: {title} ({match_score:.0%} match) ---",
        f"Source: {file_path}",
    ]

    if excerpt:
        parts.append(f"Excerpt: {excerpt}")

    parts.append("---")

    return "\n".join(parts)


def main() -> None:
    """Main hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get('tool_name', '')
    tool_input = payload.get('tool_input', {})

    # Fast path: not a web research tool
    if tool_name not in ('WebFetch', 'WebSearch'):
        sys.exit(0)

    # Lazy imports for slow path
    from shared.config import get_config

    config = get_config()
    if not config.get('enabled', True):
        sys.exit(0)

    # Get research mode
    mode = config.get('research_mode', 'cache_first')

    # web_only mode: skip cache entirely
    if mode == 'web_only':
        sys.exit(0)

    # Extract query intent
    query = extract_query_intent(tool_name, tool_input)

    if not query or len(query) < 3:
        sys.exit(0)  # Query too short

    # Search local knowledge
    results = search_local_knowledge(query)

    # Make decision
    decision = make_decision(query, results, mode)

    # Build response based on decision
    response_parts = []

    # Add context messages
    if decision["context"]:
        response_parts.extend(decision["context"])

    # Add cached entry context if augmenting
    if decision.get("cached_entries"):
        response_parts.append("\n--- Relevant Cached Knowledge ---")
        for entry in decision["cached_entries"]:
            response_parts.append(format_cached_entry_context(entry))

    # Build hook response
    if decision["action"] == "block":
        # Block the tool execution
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "cache_only mode: local knowledge available",
                "additionalContext": "\n".join(response_parts)
            }
        }
        print(json.dumps(response))

    elif decision["action"] == "augment" or decision.get("should_flag_for_intake"):
        # Inject context but proceed
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": "\n".join(response_parts)
            }
        }
        print(json.dumps(response))

    # Exit successfully
    sys.exit(0)


if __name__ == '__main__':
    main()
