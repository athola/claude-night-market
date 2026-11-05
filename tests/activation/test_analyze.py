"""FR-7: every library number is computed from kept traces, so these
fixtures pin the arithmetic that turns Skill calls into rates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.activation.analyze import analyze_host, parse_trace, render_report, wilson
from scripts.activation.labels import Case

from .conftest import make_host

FIXTURES = Path(__file__).parent / "fixtures"


def _pos(cid, target, kind="positive", competitor=None):
    return Case(
        id=cid,
        type=kind,
        prompt="p",
        target=target,
        cluster=target,
        competitor=competitor,
    )


def _neg(cid, source):
    return Case(id=cid, type="negative", prompt="n", target=None, cluster=source)


CASES = [
    _pos("ship.p1", "alpha:ship"),
    _pos("shell.p1", "alpha:shell-check"),
    _neg("neg.p1", "chores"),
]


def test_real_trace_yields_the_skill_the_model_called():
    run = parse_trace(FIXTURES / "trace-sanctum-acp.jsonl")
    assert run.skills == ["sanctum:acp"]
    assert run.model == "claude-opus-5-5"
    assert run.version == "2.1.314"


def test_max_turns_result_is_not_an_error(tmp_path):
    run = parse_trace(FIXTURES / "trace-sanctum-acp.jsonl")
    assert run is not None


def test_exact_rates_matrix_and_per_case_counts(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        CASES,
        {
            "ship.p1": [["alpha:ship"], ["alpha:ship"], ["beta:sweep"]],
            "shell.p1": [
                [],
                ["beta:sweep", "alpha:shell-check"],
                ["alpha:shell-check"],
            ],
            "neg.p1": [[], ["alpha:ship"], []],
        },
    )
    m = analyze_host(host)
    assert m["rates"]["sensitivity"]["k"] == 4
    assert m["rates"]["sensitivity"]["n"] == 6
    assert m["rates"]["fa_positive"]["k"] == 2
    assert m["rates"]["fa_negative"]["k"] == 1
    assert m["rates"]["fa_negative"]["n"] == 3
    assert m["cases"]["ship.p1"] == {"v": 3, "errored": 0, "hit": 2, "fa": 1}
    assert m["cases"]["shell.p1"] == {"v": 3, "errored": 0, "hit": 2, "fa": 1}
    assert m["confusion"]["alpha:ship"] == {"alpha:ship": 2, "beta:sweep": 1}
    assert m["confusion"]["alpha:shell-check"] == {
        "none": 1,
        "beta:sweep": 1,
        "alpha:shell-check": 1,
    }
    assert m["items"]["alpha:ship"]["k"] == 2
    assert m["ceiling"] is False
    assert m["fingerprint_valid"] is True
    assert m["partial"] is False


def test_skill_outside_inventory_is_reported_not_counted(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        [_neg("neg.p1", "chores")],
        {"neg.p1": [["deep-research"], [], []]},
    )
    m = analyze_host(host)
    assert m["rates"]["fa_negative"]["k"] == 0
    assert m["outside_inventory"] == {"deep-research": 1}


def test_unnamespaced_call_maps_to_the_unique_item(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        [_pos("ship.p1", "alpha:ship")],
        {"ship.p1": [["ship"], ["/alpha:ship"], ["ship"]]},
    )
    assert analyze_host(host)["rates"]["sensitivity"]["k"] == 3


def test_mixed_models_invalidate_the_fingerprint(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        [_pos("ship.p1", "alpha:ship")],
        {"ship.p1": [["alpha:ship"]] * 3},
        trace_kwargs={("ship.p1", 1): {"model": "claude-other"}},
    )
    m = analyze_host(host)
    assert m["fingerprint_valid"] is False
    assert "model" in m["fingerprint_problems"][0]


def test_item_missing_from_listing_invalidates_the_fingerprint(plugin_tree, tmp_path):
    listed = ("alpha:shell-check", "beta:sweep")
    host = make_host(
        plugin_tree,
        [_pos("ship.p1", "alpha:ship")],
        {"ship.p1": [["alpha:ship"]] * 3},
        trace_kwargs={("ship.p1", n): {"skills": list(listed)} for n in range(3)},
    )
    m = analyze_host(host)
    assert m["fingerprint_valid"] is False
    assert m["missing_from_listing"] == ["alpha:ship"]


def _twenty_runs(errored):
    cases = [_pos(f"c.p{n}", "alpha:ship") for n in range(20)]
    runs = {c.id: [["alpha:ship"]] for c in cases}
    for n in range(errored):
        runs[f"c.p{n}"] = [None]
    return cases, runs


@pytest.mark.parametrize(("errored", "partial"), [(1, False), (2, True)])
def test_errored_runs_leave_denominators_and_set_partial_past_five_percent(
    plugin_tree, tmp_path, errored, partial
):
    cases, runs = _twenty_runs(errored)
    host = make_host(plugin_tree, cases, runs, run_extra={"runs": 1})
    m = analyze_host(host)
    assert m["rates"]["sensitivity"]["n"] == 20 - errored
    assert m["errored"] == errored
    assert m["partial"] is partial


def test_cost_ceiling_exit_marks_partial(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        [_pos("ship.p1", "alpha:ship")],
        {"ship.p1": [["alpha:ship"]] * 3},
        run_extra={"eval_exit": 2},
    )
    assert analyze_host(host)["partial"] is True


def test_ceiling_flags_runs_at_or_above_point_nine_five(plugin_tree, tmp_path):
    host = make_host(
        plugin_tree,
        [_pos("ship.p1", "alpha:ship")],
        {"ship.p1": [["alpha:ship"]] * 3},
    )
    m = analyze_host(host)
    assert m["ceiling"] is True
    assert m["ceiling_cases"] == ["ship.p1"]


def test_bootstrap_interval_is_deterministic_and_brackets_the_rate(
    plugin_tree, tmp_path
):
    host = make_host(
        plugin_tree,
        CASES,
        {
            "ship.p1": [["alpha:ship"], [], ["alpha:ship"]],
            "shell.p1": [["alpha:shell-check"], [], []],
            "neg.p1": [[], [], []],
        },
    )
    one = analyze_host(host)["rates"]["sensitivity"]
    two = analyze_host(host)["rates"]["sensitivity"]
    assert one == two
    assert one["ci"][0] <= one["rate"] <= one["ci"][1]


def test_wilson_matches_known_value():
    low, high = wilson(8, 10)
    assert low == pytest.approx(0.4902, abs=1e-4)
    assert high == pytest.approx(0.9433, abs=1e-4)


def test_report_leads_with_rates_and_carries_echo_risk(plugin_tree, tmp_path):
    cases = [
        Case(
            id="ship.p1",
            type="positive",
            prompt="p",
            target="alpha:ship",
            cluster="alpha:ship",
            proposers=("router",),
        )
    ]
    host = make_host(plugin_tree, cases, {"ship.p1": [["alpha:ship"]] * 3})
    report = render_report(analyze_host(host))
    first = report.split("\n## ")[0]
    assert "Sensitivity" in first and "ceiling" in first.lower()
    assert "Echo risk: 100% of positive cases" in report
    json.loads((host / "metrics.json").read_text()) if (
        host / "metrics.json"
    ).exists() else None
