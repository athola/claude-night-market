"""Tests for the check_upstream_drift gate.

Feature: Detect drift between recorded upstream state and current reality

As a maintainer
I want a deterministic report of what changed since our last model or
harness update
So that a sweep touches only what actually moved, and so that a clean
check is distinguishable from a check that never ran

The ledger at ``.claude/upstream-baseline.json`` is the watermark. This
script compares it against the installed harness, the vocabularies our
gates freeze, and the model references scattered through the tree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_upstream_drift as cud

# --------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------


@pytest.fixture
def ledger() -> dict:
    """A well-formed ledger recording the current upstream state."""
    return {
        "schema_version": 1,
        "harness": {
            "product": "claude-code",
            "version": "2.1.220",
            "recorded_at": "2026-08-02",
        },
        "models": {
            "tiers": ["haiku", "sonnet", "opus", "fable"],
            "ids": {
                "fable": "claude-fable-5",
                "opus": "claude-opus-5",
                "sonnet": "claude-sonnet-5",
                "haiku": "claude-haiku-4-5-20251001",
            },
            "recorded_at": "2026-08-02",
        },
        "vocabularies": {
            "effort_levels": ["low", "medium", "high", "xhigh", "max"],
        },
        "last_migration": {
            "id": "2026-08-02-initial",
            "trigger": "bootstrap",
            "from": {"harness": None, "model_tiers": []},
            "to": {"harness": "2.1.220", "model_tiers": ["haiku"]},
            "assets_changed": 0,
            "report": "docs/migrations/init.md",
        },
        "history": [],
    }


# --------------------------------------------------------------------
# Ledger read, write, validate
# --------------------------------------------------------------------


def test_ledger_round_trips(tmp_path: Path, ledger: dict) -> None:
    """A written ledger loads back identical."""
    path = tmp_path / "upstream-baseline.json"
    cud.write_ledger(path, ledger)
    assert cud.load_ledger(path) == ledger


def test_written_ledger_is_human_diffable(tmp_path: Path, ledger: dict) -> None:
    """The ledger is committed, so it must diff cleanly."""
    path = tmp_path / "upstream-baseline.json"
    cud.write_ledger(path, ledger)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n"), "must end with a newline"
    assert "\n  " in text, "must be indented, not a single line"


def test_validate_accepts_well_formed_ledger(ledger: dict) -> None:
    assert cud.validate_ledger(ledger) == []


@pytest.mark.parametrize(
    "missing",
    ["schema_version", "harness", "models", "vocabularies"],
)
def test_validate_rejects_missing_top_level_key(ledger: dict, missing: str) -> None:
    del ledger[missing]
    errors = cud.validate_ledger(ledger)
    assert errors, f"deleting {missing} must produce an error"
    assert any(missing in e for e in errors)


def test_validate_rejects_unknown_schema_version(ledger: dict) -> None:
    ledger["schema_version"] = 99
    assert cud.validate_ledger(ledger)


def test_validate_rejects_tier_without_an_id(ledger: dict) -> None:
    """Every recorded tier needs a concrete model ID behind it."""
    ledger["models"]["tiers"].append("phantom")
    errors = cud.validate_ledger(ledger)
    assert any("phantom" in e for e in errors)


def test_load_missing_ledger_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        cud.load_ledger(tmp_path / "absent.json")


# --------------------------------------------------------------------
# Drift class: harness
# --------------------------------------------------------------------


def test_harness_drift_when_version_differs(ledger: dict) -> None:
    drifts = cud.detect_harness_drift(ledger, "2.2.0")
    assert len(drifts) == 1
    assert drifts[0].kind == "harness"
    assert "2.1.220" in drifts[0].detail
    assert "2.2.0" in drifts[0].detail


def test_no_harness_drift_when_version_matches(ledger: dict) -> None:
    assert cud.detect_harness_drift(ledger, "2.1.220") == []


def test_harness_drift_tolerates_undetectable_version(ledger: dict) -> None:
    """A missing binary is reported, never silently treated as a match."""
    drifts = cud.detect_harness_drift(ledger, None)
    assert len(drifts) == 1
    assert "could not" in drifts[0].detail.lower()


# --------------------------------------------------------------------
# Drift class: vocabulary
# --------------------------------------------------------------------


GATE_SOURCE_STALE = """
VALID_MODELS = frozenset({"haiku", "sonnet", "opus"})
VALID_EFFORTS = frozenset({"low", "medium", "high"})
"""

GATE_SOURCE_CURRENT = """
VALID_MODELS = frozenset({"haiku", "sonnet", "opus", "fable"})
VALID_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
"""


def test_extract_frozenset_reads_a_literal() -> None:
    assert cud.extract_frozenset(GATE_SOURCE_STALE, "VALID_MODELS") == {
        "haiku",
        "sonnet",
        "opus",
    }


def test_extract_frozenset_returns_none_when_absent() -> None:
    assert cud.extract_frozenset(GATE_SOURCE_STALE, "NOT_THERE") is None


def test_vocabulary_drift_catches_missing_model_tier(ledger: dict) -> None:
    """The Fable case: a shipped tier the gate cannot express."""
    drifts = cud.detect_vocabulary_drift(ledger, GATE_SOURCE_STALE)
    kinds = {d.kind for d in drifts}
    assert kinds == {"vocabulary"}
    assert any("fable" in d.detail for d in drifts)


def test_vocabulary_drift_catches_missing_effort_levels(ledger: dict) -> None:
    drifts = cud.detect_vocabulary_drift(ledger, GATE_SOURCE_STALE)
    detail = " ".join(d.detail for d in drifts)
    assert "xhigh" in detail
    assert "max" in detail


def test_no_vocabulary_drift_when_gate_is_current(ledger: dict) -> None:
    assert cud.detect_vocabulary_drift(ledger, GATE_SOURCE_CURRENT) == []


def test_vocabulary_drift_ignores_gate_extras(ledger: dict) -> None:
    """A gate accepting more than the ledger records is not drift.

    The ledger is a floor, not a ceiling. Only values the ledger knows
    about and the gate rejects count as drift.
    """
    source = (
        'VALID_MODELS = frozenset({"haiku", "sonnet", "opus", "fable", "extra"})\n'
        'VALID_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})\n'
    )
    assert cud.detect_vocabulary_drift(ledger, source) == []


# --------------------------------------------------------------------
# Drift class: dated_ids
# --------------------------------------------------------------------


def test_dated_id_outside_gated_surface_is_drift(tmp_path: Path) -> None:
    target = tmp_path / "commands" / "thing.md"
    target.parent.mkdir(parents=True)
    target.write_text("Use claude-opus-4-6 for this.\n", encoding="utf-8")
    drifts = cud.detect_dated_ids([tmp_path])
    assert len(drifts) == 1
    assert drifts[0].kind == "dated_ids"
    assert "claude-opus-4-6" in drifts[0].detail


def test_dated_id_inside_gated_surface_is_skipped(tmp_path: Path) -> None:
    """Agent frontmatter and SKILL.md are already gated elsewhere.

    Reporting them here would double-count a violation that
    check_agent_model_matrix.py already fails on.
    """
    agent = tmp_path / "agents" / "a.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("model: claude-opus-4-6\n", encoding="utf-8")
    skill = tmp_path / "skills" / "s" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("claude-sonnet-4-6\n", encoding="utf-8")
    assert cud.detect_dated_ids([tmp_path]) == []


def test_current_model_ids_are_not_dated_drift(tmp_path: Path, ledger: dict) -> None:
    """IDs the ledger records as current must never be flagged."""
    target = tmp_path / "notes.md"
    target.write_text("claude-haiku-4-5-20251001 is current\n", encoding="utf-8")
    known = set(ledger["models"]["ids"].values())
    assert cud.detect_dated_ids([tmp_path], known_ids=known) == []


# --------------------------------------------------------------------
# Drift class: unknown_tier
# --------------------------------------------------------------------


def test_unknown_tier_is_drift(tmp_path: Path, ledger: dict) -> None:
    target = tmp_path / "agents" / "x.md"
    target.parent.mkdir(parents=True)
    target.write_text("---\nmodel: gemini\n---\n", encoding="utf-8")
    drifts = cud.detect_unknown_tiers(ledger, [tmp_path])
    assert len(drifts) == 1
    assert drifts[0].kind == "unknown_tier"
    assert "gemini" in drifts[0].detail


def test_recorded_tier_is_not_drift(tmp_path: Path, ledger: dict) -> None:
    target = tmp_path / "agents" / "x.md"
    target.parent.mkdir(parents=True)
    target.write_text("---\nmodel: fable\n---\n", encoding="utf-8")
    assert cud.detect_unknown_tiers(ledger, [tmp_path]) == []


def test_unknown_tier_ignores_python_type_annotations(
    tmp_path: Path, ledger: dict
) -> None:
    """``model: str`` in a dataclass is a type hint, not a tier pin.

    Found by running the gate against the real tree, where
    ``war_room/models.py`` produced three false positives.
    """
    source = tmp_path / "models.py"
    source.write_text(
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\nclass Config:\n    model: str\n    effort: str\n",
        encoding="utf-8",
    )
    assert cud.detect_unknown_tiers(ledger, [tmp_path]) == []


def test_unknown_tier_only_reads_frontmatter(tmp_path: Path, ledger: dict) -> None:
    """A ``model:`` line in prose is documentation, not a pin."""
    doc = tmp_path / "guide.md"
    doc.write_text(
        "---\nname: guide\n---\n\nSet the field like this:\n\n    model: default\n",
        encoding="utf-8",
    )
    assert cud.detect_unknown_tiers(ledger, [doc]) == []


def test_unknown_tier_still_reads_real_frontmatter(
    tmp_path: Path, ledger: dict
) -> None:
    """Narrowing to frontmatter must not blind the check entirely."""
    doc = tmp_path / "agent.md"
    doc.write_text("---\nname: a\nmodel: gemini\n---\n\nbody\n", encoding="utf-8")
    drifts = cud.detect_unknown_tiers(ledger, [doc])
    assert len(drifts) == 1
    assert "gemini" in drifts[0].detail


# --------------------------------------------------------------------
# Scan exclusions
# --------------------------------------------------------------------


def test_migration_reports_are_not_scanned(tmp_path: Path) -> None:
    """A migration report naming a retired model is a historical record.

    Reports document what shipped and what was retired, so they name
    dated IDs by necessity. Counting them makes the ratchet climb once
    per run forever, and the thing driving the climb is this workflow's
    own output. The repo already exempts historical changelog entries
    from prose rewriting for the same reason.
    """
    report = tmp_path / "migrations" / "2026-08-02-thing.md"
    report.parent.mkdir(parents=True)
    report.write_text(
        "Opus 4.1 (`claude-opus-4-1-20250805`) retires 2026-08-05.\n",
        encoding="utf-8",
    )
    assert cud.detect_dated_ids([tmp_path]) == []


def test_non_migration_docs_are_still_scanned(tmp_path: Path) -> None:
    """The exemption must not leak to ordinary docs."""
    doc = tmp_path / "docs" / "guide.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("Pin `claude-opus-4-6` here.\n", encoding="utf-8")
    assert len(cud.detect_dated_ids([tmp_path])) == 1


@pytest.mark.parametrize(
    "cache_dir",
    [".mypy_cache", ".pytest_cache", ".ruff_cache", "site-packages", "htmlcov"],
)
def test_generated_caches_are_not_scanned(tmp_path: Path, cache_dir: str) -> None:
    """Tool caches are build output, not authored pins.

    Found on the first harness run: 80 of 124 counted dated IDs were
    ``.mypy_cache`` entries for the vendored ``anthropic`` SDK's model
    type stubs. A ratchet measuring build artifacts moves when someone
    reruns mypy, which tells you nothing about the repo.
    """
    target = tmp_path / cache_dir / "nested" / "model.data.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"id": "claude-opus-4-6"}\n', encoding="utf-8")
    assert cud.detect_dated_ids([tmp_path]) == []


@pytest.mark.parametrize("excluded", ["worktrees", "staging", "context-archive"])
def test_scan_skips_derived_and_captured_trees(tmp_path: Path, excluded: str) -> None:
    """Worktrees duplicate the repo; staging holds external web captures.

    Scanning either double-counts findings or reports pins we never
    authored.
    """
    target = tmp_path / excluded / "thing.md"
    target.parent.mkdir(parents=True)
    target.write_text("claude-opus-4-6\n", encoding="utf-8")
    assert cud.detect_dated_ids([tmp_path]) == []


# --------------------------------------------------------------------
# Ratchet on the dated-ID backlog
# --------------------------------------------------------------------


def test_dated_ids_within_backlog_is_not_drift() -> None:
    """An existing backlog must not hold the gate permanently red."""
    found = [cud.Drift("dated_ids", "d", "f") for _ in range(5)]
    assert cud.apply_dated_id_ratchet(found, backlog=5) == []


def test_dated_ids_above_backlog_is_drift() -> None:
    found = [cud.Drift("dated_ids", "d", "f") for _ in range(7)]
    drifts = cud.apply_dated_id_ratchet(found, backlog=5)
    assert len(drifts) == 1
    assert drifts[0].kind == "dated_ids"
    assert "7" in drifts[0].detail
    assert "5" in drifts[0].detail


def test_ratchet_reports_when_backlog_can_tighten() -> None:
    """Dropping below the backlog is progress worth recording."""
    found = [cud.Drift("dated_ids", "d", "f") for _ in range(2)]
    assert cud.ratchet_slack(found, backlog=5) == 3


def test_validate_accepts_optional_ratchets_key(ledger: dict) -> None:
    ledger["ratchets"] = {"dated_ids_backlog": 247}
    assert cud.validate_ledger(ledger) == []


def test_validate_rejects_negative_backlog(ledger: dict) -> None:
    ledger["ratchets"] = {"dated_ids_backlog": -1}
    assert cud.validate_ledger(ledger)


# --------------------------------------------------------------------
# Migration recording
# --------------------------------------------------------------------


def _migration(**overrides) -> dict:
    base = {
        "id": "m",
        "trigger": "harness-update",
        "assets_changed": 1,
        "report": "r.md",
    }
    base.update(overrides)
    return base


def test_snapshot_state_captures_harness_and_tiers(ledger: dict) -> None:
    assert cud.snapshot_state(ledger) == {
        "harness": "2.1.220",
        "model_tiers": ["haiku", "sonnet", "opus", "fable"],
    }


def test_snapshot_state_is_not_a_live_view(ledger: dict) -> None:
    """The snapshot must survive later mutation of the ledger."""
    before = cud.snapshot_state(ledger)
    ledger["models"]["tiers"].append("mythos")
    ledger["harness"]["version"] = "9.9.9"
    assert before["harness"] == "2.1.220"
    assert "mythos" not in before["model_tiers"]


def test_record_migration_appends_previous_to_history(ledger: dict) -> None:
    previous = ledger["last_migration"]
    updated = cud.record_migration(
        ledger,
        _migration(
            id="2026-09-01-opus-6",
            trigger="model-release",
            assets_changed=7,
            report="docs/migrations/2026-09-01-opus-6.md",
        ),
    )
    assert updated["history"][-1] == previous
    assert updated["last_migration"]["id"] == "2026-09-01-opus-6"
    assert updated["last_migration"]["assets_changed"] == 7


def test_record_migration_never_rewrites_history(ledger: dict) -> None:
    ledger["history"] = [{"id": "old"}]
    updated = cud.record_migration(ledger, _migration(id="new"))
    assert updated["history"][0] == {"id": "old"}
    assert len(updated["history"]) == 2


def test_record_migration_records_the_real_from_state(ledger: dict) -> None:
    """The delta must be what this run actually covered.

    Found on the first non-bootstrap run. The ledger said 2.1.80, the
    installed harness was 2.1.220, and the recorded migration claimed
    2.1.220 to 2.1.220 because ``from`` was derived off the previous
    migration's ``to`` rather than the ledger's own state. A watermark
    that records a no-op for a 140-version gap is worse than none.
    """
    ledger["harness"]["version"] = "2.1.80"
    before = cud.snapshot_state(ledger)

    ledger["harness"]["version"] = "2.1.220"
    updated = cud.record_migration(ledger, _migration(), from_state=before)

    assert updated["last_migration"]["from"]["harness"] == "2.1.80"
    assert updated["last_migration"]["to"]["harness"] == "2.1.220"


def test_record_migration_defaults_from_state_to_current_ledger(
    ledger: dict,
) -> None:
    """Omitting from_state records a no-op delta, which must be explicit.

    A caller that has already mutated the ledger and omits from_state
    gets from == to. That is correct behavior for a scheduled check
    that changed nothing, and it is why the parameter exists for every
    other case.
    """
    updated = cud.record_migration(ledger, _migration())
    last = updated["last_migration"]
    assert last["from"] == last["to"]


def test_record_migration_captures_tier_growth(ledger: dict) -> None:
    before = cud.snapshot_state(ledger)
    ledger["models"]["tiers"].append("mythos")
    ledger["models"]["ids"]["mythos"] = "claude-mythos-5"
    updated = cud.record_migration(ledger, _migration(), from_state=before)
    assert "mythos" not in updated["last_migration"]["from"]["model_tiers"]
    assert "mythos" in updated["last_migration"]["to"]["model_tiers"]


# --------------------------------------------------------------------
# Exit codes
# --------------------------------------------------------------------


def _clean_args(tmp_path: Path, ledger: dict, gate_source: str) -> list[str]:
    path = tmp_path / "baseline.json"
    cud.write_ledger(path, ledger)
    gate = tmp_path / "gate.py"
    gate.write_text(gate_source, encoding="utf-8")
    scan = tmp_path / "tree"
    scan.mkdir(exist_ok=True)
    return [
        "--ledger",
        str(path),
        "--gate",
        str(gate),
        "--scan",
        str(scan),
        "--harness-version",
        "2.1.220",
    ]


def test_main_exits_zero_when_ledger_clean(tmp_path: Path, ledger: dict) -> None:
    assert cud.main(_clean_args(tmp_path, ledger, GATE_SOURCE_CURRENT)) == 0


def test_main_exits_one_when_drift_found(tmp_path: Path, ledger: dict) -> None:
    assert cud.main(_clean_args(tmp_path, ledger, GATE_SOURCE_STALE)) == 1


def test_main_exits_two_on_bad_ledger(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text("{not json", encoding="utf-8")
    assert cud.main(["--ledger", str(path)]) == 2


def test_main_json_output_is_machine_readable(
    tmp_path: Path, ledger: dict, capsys: pytest.CaptureFixture
) -> None:
    """The research step consumes this, so it must parse."""
    args = _clean_args(tmp_path, ledger, GATE_SOURCE_STALE)
    cud.main([*args, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["drift_count"] > 0
    assert {d["kind"] for d in payload["drifts"]} == {"vocabulary"}
