"""FR-9 (C6): before trusting the suite to see a change, make it see
two changes we know are damaging. Selection must be deterministic, and
the floors (12 target, 7 minimum) follow from the Holm arithmetic.
"""

from __future__ import annotations

import json
import os
import shutil

import pytest
from scripts.activation.inventory import build_inventory
from scripts.activation.mutate import (
    apply_descriptions,
    run_self_check,
    select_blank,
    select_swap,
    self_check_passed,
    set_description,
)
from scripts.activation.mutate import (
    main as mutate_main,
)

from .conftest import _fake_eval


def _clean(per_item):
    """per_item: {item: activated_case_count}; adds one inactive case each."""
    cases, meta = {}, {}
    for item, count in per_item.items():
        for n in range(count + 1):
            cid = f"{item.replace(':', '.')}.p{n}"
            cases[cid] = {"v": 3, "errored": 0, "hit": 3 if n < count else 0, "fa": 0}
            meta[cid] = {"type": "positive", "target": item, "cluster": item}
    return {"cases": cases, "case_meta": meta}


def test_blank_takes_items_by_activated_count_until_twelve():
    clean = _clean({"p:a": 5, "p:b": 5, "p:c": 4, "p:d": 1})
    sel = select_blank(clean, anchor=set(clean["cases"]))
    assert sel["items"] == ["p:a", "p:b", "p:c"]
    assert sel["covered"] == 14
    assert sel["status"] == "ok"
    assert select_blank(clean, anchor=set(clean["cases"])) == sel


def test_blank_below_seven_is_infeasible():
    clean = _clean({"p:a": 3, "p:b": 3})
    assert select_blank(clean, anchor=set(clean["cases"]))["status"] == "infeasible"


def test_blank_between_seven_and_eleven_uses_everything():
    clean = _clean({"p:a": 5, "p:b": 4})
    sel = select_blank(clean, anchor=set(clean["cases"]))
    assert sel["status"] == "below_target"
    assert sel["covered"] == 9


def test_blank_ignores_cases_outside_the_anchor():
    clean = _clean({"p:a": 12})
    anchor = {cid for cid in clean["cases"] if cid.endswith(("p0", "p1", "p2"))}
    assert select_blank(clean, anchor=anchor)["covered"] == 3


def test_swap_walks_collision_pairs_by_frequency():
    clean = _clean({"p:a": 4, "p:b": 3, "p:c": 3, "p:d": 3, "p:e": 9})
    collisions = {"p:a -> p:b": 5, "p:c -> p:d": 3, "p:a -> p:e": 9, "p:x -> p:a": 1}
    sel = select_swap(clean, anchor=set(clean["cases"]), collisions=collisions)
    assert sel["pairs"] == [["p:a", "p:e"]]
    assert sel["covered"] == 13
    assert sel["status"] == "ok"


def test_swap_skips_items_already_used():
    clean = _clean({"p:a": 4, "p:b": 3, "p:c": 3, "p:d": 3})
    collisions = {"p:a -> p:b": 5, "p:b -> p:c": 4, "p:c -> p:d": 3}
    sel = select_swap(clean, anchor=set(clean["cases"]), collisions=collisions)
    assert sel["pairs"] == [["p:a", "p:b"], ["p:c", "p:d"]]
    assert sel["covered"] == 13


def test_apply_descriptions_rewrites_every_kind_without_touching_the_source(
    plugin_tree, tmp_path
):
    host = tmp_path / "hostcopy"
    shutil.copytree(plugin_tree, host, copy_function=os.link)
    items = build_inventory(host)
    apply_descriptions(host, items, {i.id: "." for i in items})
    assert {i.description for i in build_inventory(host)} == {"."}
    assert {i.description for i in build_inventory(plugin_tree)} != {"."}
    body = (host / "plugins/alpha/skills/shell-check/SKILL.md").read_text()
    assert "Long body text." in body


@pytest.mark.parametrize(
    ("verdict", "passed"),
    [("regressed", True), ("not significant", False), ("underpowered", False)],
)
def test_self_check_passes_only_on_regressed_sensitivity(verdict, passed):
    out = {"rates": {"sensitivity": {"verdict": verdict}}}
    assert self_check_passed(out) is passed


def test_self_check_end_to_end_with_a_description_sensitive_fake(suite):
    anchor = [
        f"{i.replace(':', '.')}.p{n}"
        for i in ("alpha:shell-check", "alpha:ship", "beta:sweep")
        for n in range(3)
    ]
    (suite / "evals/activation/anchor.txt").write_text("\n".join(anchor) + "\n")

    def fires_unless_blank(host, name):
        cases = {c["id"]: c for c in json.loads((host / "cases.json").read_text())}
        target = cases[name]["target"]
        described = {i.id: i.description for i in build_inventory(host)}
        return [target] if described[target] != "." else []

    summary = run_self_check(suite, "default", runner=_fake_eval(fires_unless_blank))
    blank = summary["mutants"][0]
    assert blank["status"] == "below_target" and blank["covered"] == 9
    assert blank["sensitivity"]["verdict"] == "regressed"
    assert blank["passed"] is True
    report = (
        suite / f"evals/activation/reports/self-check-default-{summary['date']}.md"
    ).read_text()
    assert "| blank | 3 | 9 | below_target | regressed |" in report
    repo_skill = (suite / "plugins/alpha/skills/shell-check/SKILL.md").read_text()
    assert "Audit shell scripts" in repo_skill


def test_dry_run_prices_three_anchor_runs_and_spends_nothing(suite, capsys):
    assert mutate_main(["--root", str(suite), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "3 anchor runs, 18 case-runs, estimate $3.60, ceiling $225" in out
    assert not (suite / "evals/activation/.runs").exists()


def test_workflow_description_edit_stays_inside_the_meta_block(tmp_path):
    path = tmp_path / "wf.js"
    path.write_text(
        "const decoy = { description: 'not routed' }\n"
        "export const meta = {\n  description: 'routed text',\n  whenToUse: 'x',\n}\n"
    )
    set_description(path, "workflow", "new")
    text = path.read_text()
    assert "description: 'not routed'" in text
    assert "description: 'new'" in text
