#!/usr/bin/env python3
"""Local document processor hook for PostToolUse (Read).

Monitors reads from configured knowledge paths and signals
knowledge-intake for new/updated local documentation.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shared.config import get_config, should_process_path
from shared.deduplication import get_content_hash, is_known, needs_update
from shared.safety_checks import is_safe_content

if TYPE_CHECKING:
    from typing import Any

# ---------------------------------------------------------------------------
# src/ on sys.path so memory_palace.* imports work in hook context
# ---------------------------------------------------------------------------
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = str(_PLUGIN_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


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
                        f"local_doc_processor: link predictions: {suggestions[:3]}\n"
                    )
            except Exception:  # noqa: BLE001 - link prediction is optional; entity write already succeeded
                pass
        finally:
            graph.close()
    except Exception as exc:  # noqa: BLE001 - hooks must never crash; log and continue
        sys.stderr.write(f"local_doc_processor: graph wiring skipped: {exc}\n")


def main() -> None:  # noqa: PLR0912, PLR0915 - hook entry point with many validation branches
    """Process local documents through the hook."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logging.warning("local_doc_processor: Failed to parse payload: %s", e)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")

    # Fast path: not a Read tool
    if tool_name != "Read":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Fast path: no file path
    if not file_path:
        sys.exit(0)

    # Fast path: not a documentation file type
    path_lower = file_path.lower()
    doc_extensions = (".md", ".rst", ".txt", ".adoc")
    if not any(path_lower.endswith(ext) for ext in doc_extensions):
        sys.exit(0)

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    # Check if path should be processed
    if not should_process_path(file_path):
        sys.exit(0)

    tool_response = payload.get("tool_response", {})

    # Extract content from Read response
    content = ""
    if isinstance(tool_response, str):
        content = tool_response
    elif isinstance(tool_response, dict):
        content = tool_response.get("content", "")
        # Sometimes response has different structure
        if not content and "output" in tool_response:
            content = tool_response["output"]

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
            msg = (
                f"Memory Palace: Local doc '{rel_path}' has changed since "
                "last indexing. Consider updating the stored knowledge entry."
            )
            context_parts.append(msg)
        # else: unchanged, no message
    else:
        msg = (
            f"Memory Palace: Reading local knowledge doc '{rel_path}'. "
            "This path is configured for knowledge tracking. "
            "Consider running knowledge-intake if this contains "
            "valuable reference material."
        )
        context_parts.append(msg)

        # Register in knowledge graph (non-blocking)
        palaces_dir = _PLUGIN_ROOT / "data" / "palaces"
        entity_id = "doc_" + content_hash[:16]
        _try_register_graph_entity(
            palaces_dir=palaces_dir,
            entity_id=entity_id,
            name=str(rel_path),
            entity_type="local_doc",
        )

    # Output response
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
