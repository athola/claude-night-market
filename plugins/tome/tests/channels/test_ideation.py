"""Tests for the ideation methods catalogue, selector, and scoring.

The ideation channel adds methods beyond TRIZ. The design finding (see
the tome:ideate skill Sources) is that the prize is the meta-pattern,
not the method bundle:

- select methods from DIFFERENT categories (diversity by construction),
- rotate methods across passes so none repeats until the catalogue is
  exhausted (the code-backed gap no prior art fills), and
- score with anti-inflation: a "novel" claim without evidence is capped.

These tests pin that behavior.
"""

from __future__ import annotations

import pytest as _pytest
from tome.channels import ideation
from tome.channels.ideation import (
    IDEATION_CRITERIA,
    get_method,
    list_categories,
    load_methods,
    rotation_plan,
    score_idea,
    select_methods,
)

_EVIDENCE_LEVELS = {"strong", "mixed", "weak", "anecdotal"}


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def test_catalogue_loads_with_required_fields() -> None:
    methods = load_methods()
    assert len(methods) >= 5
    for m in methods:
        for key in ("id", "name", "category", "evidence", "ports", "prompt"):
            assert key in m, f"{m.get('id')} missing {key}"
        assert m["evidence"] in _EVIDENCE_LEVELS


def test_method_ids_are_unique() -> None:
    ids = [m["id"] for m in load_methods()]
    assert len(ids) == len(set(ids))


def test_get_method_known_and_unknown() -> None:
    scamper = get_method("scamper")
    assert scamper is not None
    assert scamper["category"] == "transformation"
    assert get_method("does-not-exist") is None


def test_at_least_four_categories() -> None:
    assert len(list_categories()) >= 4


# ---------------------------------------------------------------------------
# select_methods: category-diverse + rotation/exclusion
# ---------------------------------------------------------------------------


def test_select_picks_distinct_categories() -> None:
    chosen = select_methods(3)
    cats = [m["category"] for m in chosen]
    assert len(chosen) == 3
    assert len(set(cats)) == 3, "first picks must span distinct categories"


def test_select_is_deterministic() -> None:
    assert [m["id"] for m in select_methods(3)] == [m["id"] for m in select_methods(3)]


def test_select_respects_exclude_for_rotation() -> None:
    first = select_methods(2)
    used = [m["id"] for m in first]
    nxt = select_methods(2, exclude=used)
    assert not ({m["id"] for m in nxt} & set(used))


def test_select_more_than_catalogue_returns_all_without_dupes() -> None:
    everything = select_methods(999)
    ids = [m["id"] for m in everything]
    assert len(ids) == len(load_methods())
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# rotation_plan
# ---------------------------------------------------------------------------


def test_rotation_plan_no_repeat_until_exhausted() -> None:
    plan = rotation_plan(passes=2, n_per_pass=3)
    assert len(plan) == 2
    assert all(len(p) == 3 for p in plan)
    flat = [mid for p in plan for mid in p]
    # 2*3 = 6 <= catalogue size, so every id is unique across passes
    assert len(flat) == len(set(flat))


def test_rotation_plan_wraps_after_exhaustion() -> None:
    size = len(load_methods())
    plan = rotation_plan(passes=size + 2, n_per_pass=1)
    flat = [mid for p in plan for mid in p]
    # First `size` picks cover the whole catalogue exactly once.
    assert set(flat[:size]) == {m["id"] for m in load_methods()}


def test_rotation_plan_empty_catalogue_degrades_to_empty_passes(monkeypatch) -> None:
    # An empty catalogue must not raise: the cursor math indexes
    # ``order[cursor % len(order)]`` and would ZeroDivisionError without the
    # guard. Graceful degradation returns one empty pass per requested pass.
    monkeypatch.setattr("tome.channels.ideation.load_methods", lambda: [])
    assert rotation_plan(passes=3, n_per_pass=2) == [[], [], []]


# ---------------------------------------------------------------------------
# load_methods: validate-on-load (issue #569)
# ---------------------------------------------------------------------------


def test_load_methods_raises_on_empty_catalogue(monkeypatch) -> None:
    """An empty or typo'd bundled methods file must fail loudly.

    Treating empty bundled data as a valid empty catalogue silently
    disables the whole channel; a missing/empty data file is a packaging
    bug, not a legitimate state.
    """
    monkeypatch.setattr(ideation, "_METHODS_CACHE", None)
    monkeypatch.setattr(ideation.yaml, "safe_load", lambda *_a, **_k: None)
    with _pytest.raises(ValueError, match="empty|missing"):
        ideation.load_methods()


def test_load_methods_raises_when_method_missing_id(monkeypatch) -> None:
    """A method lacking an 'id' is rejected at load, so downstream
    ``m["id"]`` access (rotation_plan) and ``m.get("id")`` (select_methods)
    are consistently safe."""
    bad = {"methods": [{"name": "x", "category": "c", "evidence": "weak"}]}
    monkeypatch.setattr(ideation, "_METHODS_CACHE", None)
    monkeypatch.setattr(ideation.yaml, "safe_load", lambda *_a, **_k: bad)
    with _pytest.raises(ValueError, match="id"):
        ideation.load_methods()


# ---------------------------------------------------------------------------
# score_idea: weighted total + anti-inflation
# ---------------------------------------------------------------------------


def test_criteria_weights_sum_to_one() -> None:
    assert round(sum(IDEATION_CRITERIA.values()), 6) == 1.0


def test_score_is_weighted_total() -> None:
    # Uniform scores must yield that score as the weighted total, since
    # the weights sum to 1.0. Pass novelty_evidence so the anti-inflation
    # cap does not fire and we test the weighting math in isolation.
    scores = dict.fromkeys(IDEATION_CRITERIA, 8.0)
    result = score_idea(scores, novelty_evidence=True)
    assert round(result["weighted_total"], 4) == 8.0


def test_novelty_capped_without_evidence() -> None:
    scores = dict.fromkeys(IDEATION_CRITERIA, 5.0)
    scores["novelty"] = 9.0
    capped = score_idea(scores, novelty_evidence=False)
    assert capped["adjusted_scores"]["novelty"] == 7.0
    assert capped["capped"] is True


def test_cap_lowers_the_weighted_total() -> None:
    """The cap must actually reduce the score, not just the adjusted dict.

    Guards the anti-inflation rule's whole point: a mutation computing
    weighted_total from the raw (uncapped) scores would still pass the
    adjusted_scores/capped assertions above, so pin the total directly.
    """
    scores = dict.fromkeys(IDEATION_CRITERIA, 5.0)
    scores["novelty"] = 9.0
    capped = score_idea(scores, novelty_evidence=False)
    uncapped = score_idea(scores, novelty_evidence=True)
    assert capped["weighted_total"] < uncapped["weighted_total"]
    # The gap is exactly the novelty weight times the points clipped (9 -> 7).
    assert round(uncapped["weighted_total"] - capped["weighted_total"], 4) == round(
        IDEATION_CRITERIA["novelty"] * 2.0, 4
    )


def test_novelty_not_capped_with_evidence() -> None:
    scores = dict.fromkeys(IDEATION_CRITERIA, 5.0)
    scores["novelty"] = 9.0
    uncapped = score_idea(scores, novelty_evidence=True)
    assert uncapped["adjusted_scores"]["novelty"] == 9.0
    assert uncapped["capped"] is False
