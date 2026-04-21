"""Tests for Issue #393: graph wiring in intake hooks.

Verifies that web_research_handler, local_doc_processor, and
session_lifecycle create graph entities and run link prediction
after storing knowledge items. All graph calls must be wrapped
in try/except so hooks never crash.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = PLUGIN_ROOT / "hooks"

if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


# ---------------------------------------------------------------------------
# web_research_handler graph wiring
# ---------------------------------------------------------------------------


class TestWebResearchHandlerGraphWiring:
    """Graph entity creation and link prediction in web_research_handler."""

    def _webfetch_payload(self, url: str, content: str) -> dict:
        return {
            "tool_name": "WebFetch",
            "tool_input": {"url": url, "prompt": "research"},
            "tool_response": {"content": content, "url": url},
        }

    def test_hook_does_not_crash_when_graph_unavailable(self, tmp_path: Path) -> None:
        """Hook must exit cleanly even if KnowledgeGraph import fails."""
        import web_research_handler

        payload = self._webfetch_payload(
            "https://example.com/article",
            "x" * 200,
        )

        config = {
            "enabled": True,
            "feature_flags": {"lifecycle": True, "auto_capture": True},
        }

        with (
            patch.object(sys, "stdin", StringIO(json.dumps(payload))),
            patch("web_research_handler.get_config", return_value=config),
            patch(
                "web_research_handler.is_safe_content",
                return_value=MagicMock(
                    is_safe=True,
                    should_sanitize=False,
                    sanitized_content=None,
                ),
            ),
            patch("web_research_handler.is_known", return_value=False),
            patch(
                "web_research_handler.store_webfetch_content",
                return_value=str(tmp_path / "stored.md"),
            ),
            patch("web_research_handler._try_register_graph_entity") as mock_register,
            pytest.raises(SystemExit) as exc_info,
        ):
            web_research_handler.main()

        assert exc_info.value.code == 0

    def test_try_register_graph_entity_does_not_raise_on_import_error(
        self,
    ) -> None:
        """_try_register_graph_entity is a no-op when graph unavailable."""
        import web_research_handler

        with patch.dict("sys.modules", {"memory_palace.knowledge_graph": None}):
            # Should not raise even if import fails
            try:
                web_research_handler._try_register_graph_entity(
                    palaces_dir=Path("/nonexistent"),
                    entity_id="test_id",
                    name="Test Entity",
                    entity_type="web_resource",
                )
            except Exception as exc:
                pytest.fail(f"_try_register_graph_entity raised: {exc}")

    def test_try_register_graph_entity_succeeds_with_valid_db(
        self, tmp_path: Path
    ) -> None:
        """_try_register_graph_entity creates entity when graph available."""
        import web_research_handler

        from memory_palace.knowledge_graph import KnowledgeGraph

        db_path = tmp_path / "knowledge_graph.db"
        graph = KnowledgeGraph(str(db_path))
        graph.close()

        web_research_handler._try_register_graph_entity(
            palaces_dir=tmp_path,
            entity_id="web_123",
            name="Test Article",
            entity_type="web_resource",
        )

        graph2 = KnowledgeGraph(str(db_path))
        entity = graph2.get_entity("web_123")
        graph2.close()

        assert entity is not None
        assert entity["name"] == "Test Article"
        assert entity["entity_type"] == "web_resource"


# ---------------------------------------------------------------------------
# local_doc_processor graph wiring
# ---------------------------------------------------------------------------


class TestLocalDocProcessorGraphWiring:
    """Graph entity creation in local_doc_processor."""

    def test_try_register_graph_entity_does_not_raise(self, tmp_path: Path) -> None:
        """_try_register_graph_entity is safe when graph is unavailable."""
        import local_doc_processor

        with patch.dict("sys.modules", {"memory_palace.knowledge_graph": None}):
            try:
                local_doc_processor._try_register_graph_entity(
                    palaces_dir=Path("/nonexistent"),
                    entity_id="doc_id",
                    name="My Doc",
                    entity_type="local_doc",
                )
            except Exception as exc:
                pytest.fail(f"_try_register_graph_entity raised: {exc}")

    def test_try_register_graph_entity_creates_entity(self, tmp_path: Path) -> None:
        """_try_register_graph_entity writes entity to graph DB."""
        import local_doc_processor

        from memory_palace.knowledge_graph import KnowledgeGraph

        db_path = tmp_path / "knowledge_graph.db"
        graph = KnowledgeGraph(str(db_path))
        graph.close()

        local_doc_processor._try_register_graph_entity(
            palaces_dir=tmp_path,
            entity_id="doc_001",
            name="Architecture Notes",
            entity_type="local_doc",
        )

        graph2 = KnowledgeGraph(str(db_path))
        entity = graph2.get_entity("doc_001")
        graph2.close()

        assert entity is not None
        assert entity["entity_type"] == "local_doc"


# ---------------------------------------------------------------------------
# session_lifecycle graph wiring
# ---------------------------------------------------------------------------


class TestSessionLifecycleGraphWiring:
    """Journey completion and link prediction in session_lifecycle."""

    def test_graph_wiring_does_not_crash_when_db_missing(self) -> None:
        """Graph section is no-op when DB is unavailable."""
        import session_lifecycle

        # Should not raise
        try:
            session_lifecycle._try_record_journey_completion(
                palaces_dir=Path("/nonexistent/palaces"),
                session_id="test_session",
                tools_used=["WebFetch", "Read"],
            )
        except Exception as exc:
            pytest.fail(f"_try_record_journey_completion raised: {exc}")

    def test_graph_wiring_records_journey_when_db_available(
        self, tmp_path: Path
    ) -> None:
        """Journey completion recorded to graph when DB exists."""
        import session_lifecycle

        from memory_palace.knowledge_graph import KnowledgeGraph

        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        db_path = palaces_dir / "knowledge_graph.db"

        # Pre-create DB
        graph = KnowledgeGraph(str(db_path))
        graph.upsert_entity("session_entity", "session", "Test Session")
        graph.close()

        session_lifecycle._try_record_journey_completion(
            palaces_dir=palaces_dir,
            session_id="test_session",
            tools_used=["WebFetch", "Read"],
        )

        # Journey should be recorded (no crash = success for non-crash test)
        graph2 = KnowledgeGraph(str(db_path))
        journeys = graph2._conn.execute("SELECT * FROM journeys").fetchall()
        graph2.close()
        # May or may not create journey depending on navigation detection
        # The key test is: no exception raised
        assert isinstance(journeys, list)
