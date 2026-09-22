"""Memory Palace plugin for Claude Code.

Provides spatial knowledge organization using memory palace techniques.

Nothing here is imported eagerly. The managers pull in PyYAML, networkx
and numpy between them, while the hooks that run at session start need
only ``memory_palace.paths`` and execute under whatever ``python3`` the
operator's PATH resolves: a system or Homebrew interpreter with none of
those installed. Importing any submodule runs this file first, so a
single eager re-export here turns every session start into a traceback.
Resolving each export on first attribute access keeps the package root
free, and ``from memory_palace import MemoryPalaceManager`` still works
wherever the dependency is present.

``tests/hooks/test_hook_imports_without_yaml.py`` holds the invariant.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .corpus.embedding_index import EmbeddingIndex
    from .garden_metrics import compute_garden_metrics
    from .graph_analyzer import PalaceGraphAnalyzer
    from .knowledge_graph import KnowledgeGraph
    from .palace_manager import MemoryPalaceManager
    from .project_palace import (
        ProjectPalaceManager,
        ReviewEntry,
        ReviewSubroom,
        RoomType,
        SortBy,
        capture_pr_review_knowledge,
    )
    from .session_history import SessionHistoryManager, SessionQuery, SessionRecord

__all__ = [
    "EmbeddingIndex",
    "KnowledgeGraph",
    "MemoryPalaceManager",
    "PalaceGraphAnalyzer",
    "ProjectPalaceManager",
    "ReviewEntry",
    "ReviewSubroom",
    "RoomType",
    "SessionHistoryManager",
    "SessionQuery",
    "SessionRecord",
    "SortBy",
    "capture_pr_review_knowledge",
    "compute_garden_metrics",
]

#: The module each exported name is resolved from on first access.
_EXPORT_SOURCES = {
    "EmbeddingIndex": "memory_palace.corpus.embedding_index",
    "KnowledgeGraph": "memory_palace.knowledge_graph",
    "MemoryPalaceManager": "memory_palace.palace_manager",
    "PalaceGraphAnalyzer": "memory_palace.graph_analyzer",
    "ProjectPalaceManager": "memory_palace.project_palace",
    "ReviewEntry": "memory_palace.project_palace",
    "ReviewSubroom": "memory_palace.project_palace",
    "RoomType": "memory_palace.project_palace",
    "SessionHistoryManager": "memory_palace.session_history",
    "SessionQuery": "memory_palace.session_history",
    "SessionRecord": "memory_palace.session_history",
    "SortBy": "memory_palace.project_palace",
    "capture_pr_review_knowledge": "memory_palace.project_palace",
    "compute_garden_metrics": "memory_palace.garden_metrics",
}


def __getattr__(name: str) -> Any:
    """Resolve an export from the module that defines it."""
    source = _EXPORT_SOURCES.get(name)
    if source is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(source), name)


def __dir__() -> list[str]:
    """List the exports alongside this module's own globals.

    ``__getattr__`` is invisible to ``dir()``, which would otherwise
    report a package root that looks empty.
    """
    return sorted({*globals(), *__all__})


__version__ = "1.9.21"
