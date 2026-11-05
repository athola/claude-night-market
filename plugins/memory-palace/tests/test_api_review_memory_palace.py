"""Regression tests for the memory-palace src API review."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import memory_palace.project_palace as package
from memory_palace import corpus
from memory_palace.cli import main
from memory_palace.corpus.cache_lookup import CacheLookup
from memory_palace.corpus.counter_reinforcement import (
    CounterReinforcementTracker,
    FeedbackType,
)
from memory_palace.corpus.decay_model import DecayModel
from memory_palace.garden_metrics import (
    compute_garden_metrics,
    summarize_tending_queue,
)
from memory_palace.knowledge_graph import KnowledgeGraph
from memory_palace.lifecycle.autonomy_state import AutonomyStateStore
from memory_palace.palace_repository import PalaceRepository
from memory_palace.palace_search import PalaceSearchEngine
from memory_palace.project_palace import ProjectPalaceManager
from memory_palace.project_palace import capture as project_capture
from memory_palace.session_history import (
    SessionHistoryManager,
    SessionQuery,
    SessionRecord,
)


def _session(session_id: str, started_at: str = "2026-01-01T10:00:00+00:00"):
    return SessionRecord(session_id=session_id, started_at=started_at)


def test_private_classify_finding_is_not_exported_by_project_palace() -> None:
    assert "_classify_finding" not in package.__all__
    assert "_classify_finding" not in project_capture.__all__
    assert callable(project_capture._classify_finding)


def test_default_threshold_fallback_matches_real_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = importlib.import_module("memory_palace.corpus.semantic_deduplicator")
    monkeypatch.setitem(sys.modules, "memory_palace.corpus.semantic_deduplicator", None)
    assert corpus.DEFAULT_THRESHOLD == real.DEFAULT_THRESHOLD


def test_semantic_deduplicator_raises_import_error_naming_dependency_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "memory_palace.corpus.semantic_deduplicator", None)
    with pytest.raises(ImportError, match="faiss"):
        corpus.SemanticDeduplicator  # noqa: B018 - attribute access is the call


def test_get_session_returns_none_for_an_unknown_valid_id(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    mgr.record_session(_session("known"))
    assert mgr.get_session("unknown") is None
    assert mgr.get_session("known") is not None


def test_get_session_raises_value_error_when_id_invalid(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    with pytest.raises(ValueError, match="session_id"):
        mgr.get_session("../x")


def test_delete_session_raises_value_error_when_id_invalid(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    with pytest.raises(ValueError, match="session_id"):
        mgr.delete_session("../x")


def test_query_sessions_skips_index_entry_with_invalid_id(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    mgr.record_session(_session("good"))
    index = json.loads(mgr.index_path.read_text())
    index["sessions"].append({"session_id": "../bad", "started_at": "2026-02-01"})
    mgr.index_path.write_text(json.dumps(index))
    assert [r.session_id for r in mgr.query_sessions(SessionQuery())] == ["good"]


def test_corrupt_index_is_rebuilt_from_session_files(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    mgr.record_session(_session("a", "2026-01-01T10:00:00+00:00"))
    mgr.record_session(_session("b", "2026-01-02T10:00:00+00:00"))
    mgr.index_path.write_text("{corrupt")
    mgr.record_session(_session("c", "2026-01-03T10:00:00+00:00"))
    ids = [r.session_id for r in mgr.query_sessions(SessionQuery())]
    assert ids == ["c", "b", "a"]


def test_save_index_leaves_no_temp_file(tmp_path: Path) -> None:
    mgr = SessionHistoryManager(data_dir=tmp_path)
    mgr.record_session(_session("a"))
    assert sorted(p.name for p in mgr.sessions_dir.glob("*.tmp")) == []


def test_search_palaces_raises_value_error_when_search_type_unknown() -> None:
    engine = PalaceSearchEngine(MagicMock())
    with pytest.raises(ValueError, match="smantic"):
        engine.search_palaces("hello", "smantic")


def test_compute_garden_metrics_reads_naive_now_as_utc(tmp_path: Path) -> None:
    garden = tmp_path / "garden.json"
    garden.write_text(
        json.dumps(
            {"garden": {"plots": [{"name": "p", "last_tended": "2026-01-01T00:00:00"}]}}
        )
    )
    metrics = compute_garden_metrics(garden, now=datetime(2026, 1, 3))
    assert metrics["avg_days_since_tend"] == 2.0


def test_summarize_tending_queue_reports_error_when_queue_is_corrupt(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.json"
    queue.write_text("{bad")
    summary = summarize_tending_queue(queue)
    assert "error" in summary


def test_summarize_tending_queue_has_no_error_when_queue_is_healthy(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.json"
    queue.write_text(json.dumps({"stale": ["a"], "probation_overdue": []}))
    assert summarize_tending_queue(queue) == {"stale": 1, "probation_overdue": 0}


def test_reinforce_rejects_unknown_feedback_before_mutating_counter() -> None:
    tracker = CounterReinforcementTracker()
    with pytest.raises(ValueError):
        tracker.reinforce("e", "bogus")  # type: ignore[arg-type]  # an invalid str is the input under test
    assert tracker.get_counter("e") is None


def test_reinforce_accepts_feedback_value_string_as_that_feedback() -> None:
    tracker = CounterReinforcementTracker()
    counter = tracker.reinforce("e", "helpful")  # type: ignore[arg-type]  # the raw str value is the input under test
    assert (counter.helpful, counter.neutral) == (1, 0)
    assert FeedbackType.HELPFUL.value == "helpful"


def test_never_validated_entry_decays_from_its_created_at() -> None:
    created = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    stale = DecayModel().get_stale_entries(
        [
            {
                "id": "x",
                "maturity": "seedling",
                "importance_score": 10,
                "created_at": created,
            }
        ],
        threshold=0.5,
    )
    assert [s.entry_id for s in stale] == ["x"]


def test_never_validated_entry_without_created_at_is_not_stale() -> None:
    stale = DecayModel().get_stale_entries(
        [{"id": "x", "maturity": "seedling", "importance_score": 10}]
    )
    assert stale == []


def test_set_level_raises_value_error_when_lock_given_without_domain(
    tmp_path: Path,
) -> None:
    store = AutonomyStateStore(state_path=tmp_path / "state.yaml")
    with pytest.raises(ValueError, match="domain"):
        store.set_level(1, lock=True)


def test_autonomy_set_cli_exits_when_lock_given_without_domain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MEMORY_PALACE_AUTONOMY_STATE", str(tmp_path / "s.yaml"))
    with pytest.raises(SystemExit, match="domain"):
        main(["autonomy", "set", "--level", "1", "--lock"])


def test_save_palace_refreshes_last_modified_on_the_callers_dict(
    tmp_path: Path,
) -> None:
    repo = PalaceRepository(str(tmp_path))
    palace = {"id": "p1", "name": "P", "last_modified": "2000-01-01T00:00:00+00:00"}

    repo.save_palace(palace)

    assert palace["last_modified"] != "2000-01-01T00:00:00+00:00"
    on_disk = json.loads((tmp_path / "p1.json").read_text(encoding="utf-8"))
    assert on_disk["last_modified"] == palace["last_modified"]


@pytest.fixture
def project_manager(tmp_path: Path) -> ProjectPalaceManager:
    config = tmp_path / "settings.json"
    config.write_text(json.dumps({"storage": {"palace_directory": str(tmp_path)}}))
    return ProjectPalaceManager(str(config), str(tmp_path / "palaces"))


def test_load_project_palace_returns_none_when_file_is_corrupt(
    project_manager: ProjectPalaceManager, capsys: pytest.CaptureFixture[str]
) -> None:
    palace = project_manager.create_project_palace("repo")
    (Path(project_manager.project_palaces_dir) / f"{palace['id']}.json").write_text(
        "{corrupt"
    )
    assert project_manager.load_project_palace(palace["id"]) is None
    assert "corrupt" in capsys.readouterr().err


def test_save_project_palace_keeps_old_file_when_write_fails(
    project_manager: ProjectPalaceManager,
) -> None:
    palace = project_manager.create_project_palace("repo")
    palace_file = Path(project_manager.project_palaces_dir) / f"{palace['id']}.json"
    palace["unserializable"] = {1, 2}
    with pytest.raises(TypeError):
        project_manager.save_project_palace(palace)
    assert json.loads(palace_file.read_text())["id"] == palace["id"]


def test_fallback_search_rows_carry_rank_like_fts_rows() -> None:
    with KnowledgeGraph(":memory:") as graph:
        graph.upsert_entity("e1", "concept", "alpha beta")
        rows = graph._fallback_search("alpha", 10)
    assert [row["entity_id"] for row in rows] == ["e1"]
    assert "rank" in rows[0]


def test_fallback_search_treats_like_wildcards_as_literals() -> None:
    with KnowledgeGraph(":memory:") as graph:
        graph.upsert_entity("e1", "concept", "alpha")
        graph.upsert_entity("e2", "concept", "100% sure")
        assert graph._fallback_search("%", 10)[0]["entity_id"] == "e2"
        assert len(graph._fallback_search("%", 10)) == 1
        assert graph._fallback_search("a_pha", 10) == []


def test_cache_lookup_search_raises_value_error_when_mode_unknown(
    tmp_path: Path,
) -> None:
    lookup = CacheLookup(str(tmp_path / "c"), str(tmp_path / "i"))
    with pytest.raises(ValueError, match="keyword"):
        lookup.search("anything", mode="keyword")


def test_cache_lookup_search_accepts_embeddings_mode(tmp_path: Path) -> None:
    lookup = CacheLookup(str(tmp_path / "c"), str(tmp_path / "i"))
    assert lookup.search("anything", mode="embeddings") == []
