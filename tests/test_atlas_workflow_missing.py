"""The atlas workflow names a lens that drew nothing by its key.

``missing`` held the lens objects themselves, so the log line read
``no diagram from [object Object]`` and the returned list carried whole
roster entries where every sibling workflow returns keys.
"""

from __future__ import annotations

from tests.test_shipped_workflows import PLUGINS, _run_workflow

ATLAS = PLUGINS / "cartograph" / "workflows" / "atlas.js"


def test_a_lens_that_drew_nothing_is_reported_by_its_key() -> None:
    out = _run_workflow(
        ATLAS,
        "if (opts.label === 'map:architecture') return null;"
        "if (opts.label === 'reconcile') return { disagreements: [] };"
        "const lens = opts.label.slice('map:'.length);"
        "return { lens, mermaid: 'graph TD', nodes: ['a'] };",
        {"root": "."},
    )
    assert out["result"]["missing"] == ["architecture"]
    assert not any("[object Object]" in line for line in out["log"]), out["log"]
