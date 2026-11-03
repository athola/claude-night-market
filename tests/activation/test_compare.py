"""FR-8: a delta is claimed only under C1 (paired, fingerprinted), C3
(exact McNemar with Holm) and C7 (declared before the run). Each
refusal below is a way a past comparison could have fooled us.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess

import pytest
import yaml
from scripts.activation.compare import (
    RATES,
    CompareRefused,
    compare,
    git_is_ancestor,
    holm,
    main,
    mcnemar_p,
)

ALPHA = 0.05


def _metrics(sens_hits, fa_neg_hits=(), fa_pos_hits=None, *, runs=3, **fp):
    """Build metrics: one positive case per entry of sens_hits (hit count
    out of ``runs``) and one negative per entry of fa_neg_hits.
    """
    cases, meta = {}, {}
    fa_pos_hits = fa_pos_hits or [0] * len(sens_hits)
    for n, (hit, fa) in enumerate(zip(sens_hits, fa_pos_hits)):
        cid = f"pos.p{n}"
        cases[cid] = {"v": runs, "errored": 0, "hit": hit, "fa": fa}
        meta[cid] = {
            "type": "positive",
            "cluster": f"p:item{n % 4}",
            "target": f"p:item{n % 4}",
        }
    for n, fa in enumerate(fa_neg_hits):
        cid = f"neg.p{n}"
        cases[cid] = {"v": runs, "errored": 0, "hit": 0, "fa": fa}
        meta[cid] = {"type": "negative", "cluster": f"src{n % 3}", "target": None}
    fingerprint = {
        "arm": "default",
        "model": "m",
        "claude_code_version": "1",
        "plugins": ["p"],
        "case_set_hash": "h",
        "runs": runs,
        "tier": "change",
        "commit": "c1",
        "dirty": False,
        "item_hashes": {"p:item0": "a", "p:item1": "b"},
    }
    fingerprint.update(fp)
    return {
        "cases": cases,
        "case_meta": meta,
        "fingerprint": fingerprint,
        "fingerprint_valid": True,
        "partial": False,
    }


def _change(cases):
    return {
        "id": "x",
        "declared_at": "c0",
        "items": ["p:item0"],
        "cases": sorted(cases),
    }


def _always_ancestor(_older, _newer):
    return True


def _run(base, new, change=None, **kw):
    change = change or _change(base["cases"])
    return compare(
        base, new, change, is_ancestor=kw.pop("is_ancestor", _always_ancestor), **kw
    )


def test_mcnemar_exact_values():
    assert mcnemar_p(0, 0) == 1.0
    assert mcnemar_p(7, 0) == pytest.approx(0.015625)
    assert mcnemar_p(6, 0) == pytest.approx(0.03125)
    assert mcnemar_p(3, 3) == 1.0


def test_holm_orders_three_p_values():
    assert holm({"a": 0.01, "b": 0.04, "c": 0.02}, ALPHA) == {
        "a": True,
        "b": True,
        "c": True,
    }
    assert holm({"a": 0.01, "b": 0.04, "c": 0.026}, ALPHA) == {
        "a": True,
        "b": False,
        "c": False,
    }
    assert holm({"a": 0.02, "b": 0.001, "c": 0.5}, ALPHA) == {
        "a": True,
        "b": True,
        "c": False,
    }


def test_seven_one_way_cases_alone_are_significant():
    base = _metrics([3] * 7 + [0] * 3)
    new = _metrics([0] * 7 + [0] * 3)
    out = _run(base, new)
    assert out["rates"]["sensitivity"]["b"] == 7
    assert out["rates"]["sensitivity"]["verdict"] == "regressed"


def test_six_one_way_cases_alone_are_not_significant():
    base = _metrics([3] * 6)
    new = _metrics([0] * 6)
    assert _run(base, new)["rates"]["sensitivity"]["verdict"] == "not significant"


def test_six_one_way_cases_are_significant_after_the_other_two_reject():
    base = _metrics([3] * 6 + [0] * 7, fa_neg_hits=[0] * 7, fa_pos_hits=[0] * 13)
    new = _metrics(
        [0] * 6 + [0] * 7, fa_neg_hits=[3] * 7, fa_pos_hits=[0] * 6 + [3] * 7
    )
    rates = _run(base, new)["rates"]
    assert rates["fa_negative"]["verdict"] == "regressed"
    assert rates["fa_positive"]["verdict"] == "regressed"
    assert rates["sensitivity"]["verdict"] == "regressed"


def test_direction_and_quiet_verdicts():
    base = _metrics([0] * 7 + [3, 3], fa_neg_hits=[3, 0])
    new = _metrics([3] * 7 + [3, 3], fa_neg_hits=[0, 0])
    rates = _run(base, new)["rates"]
    assert rates["sensitivity"]["verdict"] == "improved"
    assert rates["fa_negative"]["verdict"] == "underpowered"
    assert rates["fa_positive"]["verdict"] == "no evidence of change"
    lo, hi = rates["sensitivity"]["delta_ci"]
    assert lo <= rates["sensitivity"]["delta"] <= hi


def test_tied_cases_are_dropped_and_counted():
    base = _metrics([1, 2], runs=2)
    new = _metrics([0, 0], runs=2)
    rates = _run(base, new)["rates"]
    assert rates["sensitivity"]["dropped"] == 1
    assert rates["sensitivity"]["b"] == 1


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda b, n: n["fingerprint"].update(model="other"), "model"),
        (
            lambda b, n: n["fingerprint"].update(claude_code_version="2"),
            "claude_code_version",
        ),
        (lambda b, n: n["fingerprint"].update(plugins=["q"]), "plugins"),
        (lambda b, n: n["fingerprint"].update(case_set_hash="z"), "case_set_hash"),
        (lambda b, n: n["fingerprint"].update(arm="haiku"), "arm"),
        (lambda b, n: n["fingerprint"].update(tier="anchor"), "tier"),
        (lambda b, n: n.update(partial=True), "partial"),
        (lambda b, n: b.update(fingerprint_valid=False), "fingerprint"),
        (lambda b, n: n["fingerprint"].update(dirty=True), "dirty"),
        (
            lambda b, n: n["fingerprint"]["item_hashes"].update({"p:item1": "changed"}),
            "p:item1",
        ),
        (lambda b, n: n["cases"].pop("pos.p0"), "cases"),
    ],
)
def test_refusals(mutate, message):
    base = _metrics([3, 0])
    new = copy.deepcopy(base)
    change = _change(base["cases"])
    mutate(base, new)
    with pytest.raises(CompareRefused, match=message):
        _run(base, new, change)


def test_runs_count_mismatch_is_refused():
    with pytest.raises(CompareRefused, match="runs"):
        _run(_metrics([3, 0]), _metrics([3, 0], runs=5))


def test_change_file_declared_after_a_run_is_refused():
    base = _metrics([3, 0])
    with pytest.raises(CompareRefused, match="declared"):
        _run(base, copy.deepcopy(base), is_ancestor=lambda older, newer: False)


def test_listed_item_may_change_hash():
    base = _metrics([3, 0])
    new = copy.deepcopy(base)
    new["fingerprint"]["item_hashes"]["p:item0"] = "edited"
    assert _run(base, new)["rates"]["sensitivity"]["verdict"] == "no evidence of change"


def test_self_check_mode_waives_the_declaration_order():
    base = _metrics([3, 0])
    out = _run(
        base, copy.deepcopy(base), is_ancestor=lambda o, n: False, self_check=True
    )
    assert out["self_check"] is True


def _cli_files(tmp_path, base, new):
    paths = []
    for name, metrics in (("base.json", base), ("new.json", new)):
        path = tmp_path / name
        path.write_text(json.dumps(metrics))
        paths.append(str(path))
    change = tmp_path / "change.yaml"
    change.write_text(yaml.safe_dump(_change(base["cases"])))
    return [*paths, "--change", str(change)]


def test_cli_prints_one_table_row_per_rate(tmp_path, capsys):
    base = _metrics([3, 0])
    argv = _cli_files(tmp_path, base, copy.deepcopy(base))
    assert main([*argv, "--self-check"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Comparison: x\n")
    for rate in RATES:
        assert f"| {rate} |" in out


def test_cli_exits_two_and_states_the_refusal(tmp_path, capsys):
    argv = _cli_files(tmp_path, _metrics([3, 0]), _metrics([3, 0], runs=5))
    assert main(argv) == 2
    assert capsys.readouterr().err.startswith("compare refused:")


def test_git_is_ancestor_follows_commit_order(tmp_path, monkeypatch):
    # A hook's GIT_DIR would point these commands at the real repository.
    for name in [k for k in os.environ if k.startswith("GIT_")]:
        monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q"], check=True)
    shas = []
    for n in range(2):
        subprocess.run(
            [*git, "commit", "-q", "--allow-empty", "-m", str(n)], check=True
        )
        shas.append(
            subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()
        )
    assert git_is_ancestor(shas[0], shas[1])
    assert not git_is_ancestor(shas[1], shas[0])
