"""FR-6: the runner is where money is spent, so every refusal and the
dry run are tested with a fake eval process instead of `claude`.
"""

from __future__ import annotations

import json

import yaml
from scripts.activation import run as run_mod
from scripts.activation.inventory import build_inventory
from scripts.activation.labels import Case

from .conftest import _fake_eval, _labels, write


def _main(root, *argv, runner=None, monkeypatch=None):
    monkeypatch.chdir(root)
    return run_mod.main(["--root", str(root), *argv], runner=runner or _fake_eval({}))


def test_even_runs_are_refused(suite, monkeypatch, capsys):
    assert (
        _main(
            suite,
            "--tier",
            "anchor",
            "--runs",
            "4",
            "--dry-run",
            monkeypatch=monkeypatch,
        )
        == 2
    )
    assert "odd" in capsys.readouterr().err


def test_anchor_and_full_refused_while_coverage_fails(suite, monkeypatch, capsys):
    write(
        suite / "evals/activation/labels/all.yaml", yaml.safe_dump(_labels(full=False))
    )
    for tier in ("anchor", "full"):
        assert _main(suite, "--tier", tier, "--dry-run", monkeypatch=monkeypatch) == 2
        assert "coverage" in capsys.readouterr().err


def test_dry_run_prints_counts_and_command_and_spends_nothing(
    suite, monkeypatch, capsys
):
    runner = _fake_eval({})
    assert (
        _main(
            suite,
            "--tier",
            "anchor",
            "--dry-run",
            runner=runner,
            monkeypatch=monkeypatch,
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "2 cases x R=3 = 6 case-runs, estimate $1.20, ceiling $75" in out
    assert "claude plugin eval" in out and "--max-cost-usd 75" in out
    assert runner.calls == []


def test_haiku_dry_run_reports_unmeasured_cost_and_model(suite, monkeypatch, capsys):
    _main(
        suite, "--tier", "full", "--arm", "haiku", "--dry-run", monkeypatch=monkeypatch
    )
    out = capsys.readouterr().out
    assert "59 cases x R=3 = 177 case-runs, estimate unmeasured" in out
    assert "--model haiku" in out


def test_live_anchor_run_at_ceiling_exits_three(suite, monkeypatch):
    runner = _fake_eval({"alpha.ship.p0": ["alpha:ship"]})
    assert _main(suite, "--tier", "anchor", runner=runner, monkeypatch=monkeypatch) == 3
    host = next((suite / "evals/activation/.runs").iterdir())
    metrics = json.loads((host / "metrics.json").read_text())
    assert metrics["rates"]["sensitivity"]["k"] == 3
    assert metrics["fingerprint"]["dirty"] is False
    assert "--threshold" in runner.calls[0]


def test_cost_ceiling_exit_two_marks_the_run_partial(suite, monkeypatch):
    runner = _fake_eval({}, code=2)
    _main(suite, "--tier", "anchor", runner=runner, monkeypatch=monkeypatch)
    host = next((suite / "evals/activation/.runs").iterdir())
    assert json.loads((host / "metrics.json").read_text())["partial"] is True


def test_dirty_tree_is_recorded(suite, monkeypatch):
    write(suite / "plugins/alpha/commands/ship.md", "---\ndescription: Edited.\n---\n")
    _main(suite, "--tier", "anchor", runner=_fake_eval({}), monkeypatch=monkeypatch)
    host = next((suite / "evals/activation/.runs").iterdir())
    run = json.loads((host / "run.json").read_text())
    assert run["dirty"] is True and run["diff_sha256"]


def test_missing_trace_is_marked_errored(tmp_path):
    host = tmp_path / "h"
    host.mkdir()
    (host / "result.json").write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "name": "c.p1",
                        "arms": {
                            "with": [
                                {"tracePath": str(tmp_path / "gone.jsonl")},
                                {"error": "timeout"},
                            ]
                        },
                    }
                ]
            }
        )
    )
    assert run_mod.collect_traces(host) == 0
    assert (host / "traces/c.p1/0.error").read_text() == "no trace"
    assert (host / "traces/c.p1/1.error").read_text() == "timeout"


def test_declare_freezes_targets_competitors_neighbors_and_anchor_negatives(
    suite, monkeypatch
):
    change = write(
        suite / "evals/activation/changes/x.yaml",
        yaml.safe_dump({"schema_version": 1, "id": "x", "items": ["alpha:ship"]}),
    )
    monkeypatch.chdir(suite)
    assert run_mod.main(["declare", str(change)]) == 0
    declared = yaml.safe_load(change.read_text())
    assert "alpha.ship.p0" in declared["cases"]
    assert "beta.sweep.p2" in declared["cases"]  # its competitor is alpha:ship
    assert "neg.p0" in declared["cases"]
    assert declared["cases"] == sorted(declared["cases"])
    assert len(declared["declared_at"]) == 40


def test_change_tier_refuses_an_uncommitted_change_file(suite, monkeypatch, capsys):
    change = write(
        suite / "evals/activation/changes/x.yaml",
        yaml.safe_dump(
            {
                "schema_version": 1,
                "id": "x",
                "items": ["alpha:ship"],
                "cases": ["alpha.ship.p0"],
                "declared_at": "abc",
            }
        ),
    )
    code = _main(
        suite, "--tier", "change", "--change", str(change), monkeypatch=monkeypatch
    )
    assert code == 2
    assert "committed" in capsys.readouterr().err


def test_anchor_selection_starts_with_confusable_near_misses(suite):
    items = build_inventory(suite)
    cases = [Case.from_dict(r) for r in _labels(full=True)["cases"]]
    metrics = {"collisions": {"alpha:ship -> beta:sweep": 5}}
    chosen = run_mod.select_anchor(cases, items, metrics)
    assert chosen[0] == "alpha.ship.p2"
    assert len([c for c in chosen if c.startswith("neg.")]) == 10
    assert len(chosen) == len(set(chosen))
    assert chosen == run_mod.select_anchor(cases, items, metrics)


def test_declare_refuses_without_an_anchor_file(suite, monkeypatch, capsys):
    (suite / "evals/activation/anchor.txt").unlink()
    change = write(
        suite / "evals/activation/changes/x.yaml",
        yaml.safe_dump({"schema_version": 1, "id": "x", "items": ["alpha:ship"]}),
    )
    monkeypatch.chdir(suite)
    assert run_mod.main(["declare", str(change)]) == 2
    assert "anchor-select" in capsys.readouterr().err
