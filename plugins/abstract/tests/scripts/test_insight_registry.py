"""Tests for InsightRegistry content-hash deduplication."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from insight_registry import InsightRegistry
from insight_types import Finding


def _make_finding(**overrides) -> Finding:
    defaults = {
        "type": "Trend",
        "severity": "medium",
        "skill": "abstract:skill-auditor",
        "summary": "success rate dropped",
        "evidence": "data here",
        "recommendation": "investigate",
        "source": "trend_lens",
    }
    defaults.update(overrides)
    return Finding(**defaults)


@pytest.fixture()
def registry(tmp_path):
    return InsightRegistry(state_path=tmp_path / "insights_posted.json")


def test_new_finding_is_not_duplicate(registry):
    f = _make_finding()
    result = registry.check_local(f)
    assert result == "create"


def test_same_finding_is_duplicate(registry):
    f = _make_finding()
    registry.record_posted(f, "https://example.com/1")
    result = registry.check_local(f)
    assert result == "skip"


def test_different_finding_is_not_duplicate(registry):
    f1 = _make_finding(summary="dropped 92 to 71")
    f2 = _make_finding(summary="dropped 71 to 50")
    registry.record_posted(f1, "https://example.com/1")
    result = registry.check_local(f2)
    assert result == "create"


def test_stale_finding_can_repost(registry):
    f = _make_finding()
    registry.record_posted(f, "https://example.com/1")
    # Manually age the entry to 31 days
    from insight_types import finding_hash

    h = finding_hash(f)
    registry._state["posted_hashes"][h]["posted_at"] = "2026-03-01"
    registry._save()
    result = registry.check_local(f)
    assert result == "create"


def test_state_persists_to_disk(tmp_path):
    path = tmp_path / "insights_posted.json"
    r1 = InsightRegistry(state_path=path)
    f = _make_finding()
    r1.record_posted(f, "https://example.com/1")

    r2 = InsightRegistry(state_path=path)
    assert r2.check_local(f) == "skip"


def test_snapshot_save_and_load(registry):
    snapshot = {"abstract:skill-auditor": {"success_rate": 40.0}}
    registry.save_snapshot(snapshot)
    loaded = registry.load_snapshot()
    assert loaded == snapshot


def test_empty_state_has_empty_snapshot(registry):
    loaded = registry.load_snapshot()
    assert loaded == {}


def test_record_posted_saves_metadata(registry):
    f = _make_finding(summary="test summary")
    registry.record_posted(f, "https://example.com/42")

    from insight_types import finding_hash

    h = finding_hash(f)
    entry = registry._state["posted_hashes"][h]
    assert entry["url"] == "https://example.com/42"
    assert entry["type"] == "Trend"
    assert entry["summary"] == "test summary"
    assert "posted_at" in entry
