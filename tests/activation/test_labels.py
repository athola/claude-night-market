"""FR-2: the labeled set is the answer key, so a malformed label must
fail loudly instead of quietly shifting a rate.
"""

from __future__ import annotations

import hashlib
import json

import pytest
from scripts.activation.inventory import build_inventory
from scripts.activation.labels import (
    Case,
    LabelError,
    case_set_hash,
    coverage_gaps,
    load_cases,
    validate,
)

from .conftest import write


def _case(**overrides) -> dict:
    base = {
        "id": "alpha.ship.p1",
        "type": "positive",
        "prompt": "Push my branch.",
        "target": "alpha:ship",
        "competitor": None,
        "cluster": "alpha:ship",
        "proposers": ["router"],
        "adjudicated": False,
        "notes": "",
    }
    base.update(overrides)
    return base


def _check(plugin_tree, *rows):
    cases = [Case.from_dict(r) for r in rows]
    validate(cases, build_inventory(plugin_tree), plugin_tree)


def test_valid_positive_passes(plugin_tree):
    _check(plugin_tree, _case())


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([_case(), _case()], "duplicate id"),
        ([_case(target="alpha:nope", cluster="alpha:nope")], "unknown target"),
        ([_case(type="near_miss")], "competitor"),
        ([_case(type="negative", cluster="chores")], "negative with a target"),
        (
            [_case(target="alpha:hidden", cluster="alpha:hidden")],
            "disable-model-invocation",
        ),
        ([_case(id="Bad ID")], "id"),
        ([_case(type="near_miss", competitor="alpha:ship")], "competitor"),
    ],
)
def test_validate_rejects(plugin_tree, rows, message):
    with pytest.raises(LabelError, match=message):
        _check(plugin_tree, *rows)


def test_load_reads_every_label_file(tmp_path):
    write(
        tmp_path / "a.yaml",
        "schema_version: 1\ncases:\n  - id: x.p1\n    type: negative\n"
        "    prompt: Rename a variable.\n    target: null\n    cluster: chores\n",
    )
    cases = load_cases(tmp_path)
    assert [c.id for c in cases] == ["x.p1"]
    assert cases[0].target is None


def test_coverage_reports_items_short_of_three_positives(plugin_tree):
    items = build_inventory(plugin_tree)
    cases = [Case.from_dict(_case(id=f"alpha.ship.p{n}")) for n in range(3)]
    gaps = coverage_gaps(cases, items, min_positives=3, min_negatives=1, min_sources=1)
    assert gaps["items"] == {"alpha:shell-check": 0, "beta:sweep": 0}
    assert gaps["negatives"] == (0, 1)
    assert not gaps["ok"]


def test_coverage_ok_when_every_minimum_met(plugin_tree):
    items = build_inventory(plugin_tree)
    rows = [
        _case(id=f"{i.id.replace(':', '.')}.p{n}", target=i.id, cluster=i.id)
        for i in items
        for n in range(3)
    ]
    rows.append(_case(id="neg.p1", type="negative", target=None, cluster="chores"))
    gaps = coverage_gaps(
        [Case.from_dict(r) for r in rows],
        items,
        min_positives=3,
        min_negatives=1,
        min_sources=1,
    )
    assert gaps["ok"]


def test_case_set_hash_ignores_order_and_metadata():
    one = Case.from_dict(_case())
    two = Case.from_dict(_case(id="alpha.ship.p2", notes="x"))
    two_reworded = Case.from_dict(
        _case(id="alpha.ship.p2", notes="y", adjudicated=True)
    )
    assert case_set_hash([one, two]) == case_set_hash([two_reworded, one])


def test_case_set_hash_is_byte_stable():
    neg = Case.from_dict(
        _case(id="n.p1", type="negative", target=None, prompt="Ünïcode")
    )
    expected = hashlib.sha256(
        json.dumps(
            [["n.p1", "negative", "Ünïcode", None]],
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    assert case_set_hash([neg]) == expected
