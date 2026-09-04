"""Memory Palace plugin for Claude Code.

Provides spatial knowledge organization using memory palace techniques.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .corpus.embedding_index import EmbeddingIndex
from .garden_metrics import compute_garden_metrics
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

if TYPE_CHECKING:
    from .graph_analyzer import PalaceGraphAnalyzer

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


def __getattr__(name: str) -> Any:
    """Lazily expose the networkx-backed graph analyzer.

    ``PalaceGraphAnalyzer`` pulls in networkx (and, transitively, numpy).
    Importing it at module load would make ``import memory_palace`` fail
    in the stdlib-only environments that need only the lightweight
    managers, such as the Python 3.9 hook-compatibility CI job. Deferring
    the import keeps the package importable without the heavy optional
    dependency; ``from memory_palace import PalaceGraphAnalyzer`` still
    works wherever networkx is installed.
    """
    if name == "PalaceGraphAnalyzer":
        return import_module("memory_palace.graph_analyzer").PalaceGraphAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__version__ = "1.9.20"
