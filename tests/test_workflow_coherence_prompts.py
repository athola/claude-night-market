"""Workflow prompts ask for a second model of a concern.

Four workflows review code, docs and skills through skills that carry the
one-model-per-concern rule (docs/knowledge-corpus/decoherence.md). A
workflow agent receives its prompt string, not the skill text, so each
lens that would see a second model has to ask for it. Each assertion
anchors on the clause added for that purpose. Removing the clause turns
its test red.
"""

from __future__ import annotations

from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[1] / "plugins"


def _script(plugin: str, name: str) -> str:
    return " ".join((PLUGINS / plugin / "workflows" / name).read_text().split())


def test_unified_review_architecture_lens_reports_a_second_model() -> None:
    """The architecture dimension names the existing model it duplicates."""
    script = _script("pensive", "unified-review.js")
    assert "second model of a concern the codebase already models" in script
    assert "Name the existing model and its file" in script


def test_bloat_sweep_consolidation_matches_names_across_areas() -> None:
    """A name with different bodies in two areas is one concern twice."""
    script = _script("conserve", "bloat-sweep.js")
    assert "different bodies in two areas is one concern modeled twice" in script


def test_doc_sweep_economy_layer_reports_a_restated_fact() -> None:
    """A fact another file already states belongs behind a link."""
    script = _script("scribe", "doc-sweep.js")
    assert "that another file already states" in script


def test_skill_library_economy_lens_reports_a_restated_fact() -> None:
    """An authored skill links a fact another file states, as doc-sweep asks."""
    script = _script("attune", "skill-library.js")
    assert "that another skill or file already states" in script
