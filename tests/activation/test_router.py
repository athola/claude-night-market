"""FR-3: the free per-commit proxy. It cannot say whether the model
activates a skill, only whether a description edit made two items
harder to tell apart for a lexical ranker.
"""

from __future__ import annotations

import json

from scripts.activation.inventory import Item
from scripts.activation.labels import Case
from scripts.activation.router import Router, check, evaluate, main, snapshot


def _item(name: str, description: str) -> Item:
    return Item(
        f"p:{name}",
        "skill",
        "p",
        name,
        description,
        f"plugins/p/skills/{name}/SKILL.md",
    )


def _pos(cid: str, prompt: str, target: str) -> Case:
    return Case(id=cid, type="positive", prompt=prompt, target=target, cluster=target)


ITEMS = [
    _item("shell-check", "Audit shell scripts for quoting bugs."),
    _item("commit-push", "Commit staged changes and push the branch."),
]
CASES = [
    _pos("a.p1", "check my shell scripts for quoting bugs", "p:shell-check"),
    _pos("b.p1", "commit and push my branch", "p:commit-push"),
]


def test_rank_puts_lexical_match_first_and_breaks_ties_by_id():
    router = Router(ITEMS)
    assert router.rank("quoting bugs")[0][0] == "p:shell-check"
    assert [i for i, _ in router.rank("nothing matches")] == [
        "p:commit-push",
        "p:shell-check",
    ]


def test_snapshot_is_byte_identical_across_runs():
    one = json.dumps(snapshot(ITEMS, CASES), sort_keys=True)
    two = json.dumps(snapshot(ITEMS, CASES), sort_keys=True)
    assert one == two


def test_metrics_on_a_clean_library():
    metrics = evaluate(Router(ITEMS), CASES)
    assert metrics["mrr"] == 1.0
    assert metrics["top1"] == 1.0
    assert metrics["collisions"] == {}


def test_absorbed_terms_create_a_new_collision_and_baseline_clears_it():
    base = snapshot(ITEMS, CASES)
    greedy = [
        ITEMS[0],
        _item(
            "commit-push",
            "Commit and push, or check my shell scripts for quoting bugs.",
        ),
    ]
    ok, messages = check(base, snapshot(greedy, CASES))
    assert not ok
    assert any("new collision a.p1" in m and "p:commit-push" in m for m in messages)
    ok_after, _ = check(snapshot(greedy, CASES), snapshot(greedy, CASES))
    assert ok_after


def test_mrr_drop_past_tolerance_fails_even_without_new_collision():
    base = snapshot(ITEMS, CASES)
    current = dict(base, mrr=base["mrr"] - 0.02)
    ok, messages = check(base, current)
    assert not ok
    assert any("MRR" in m for m in messages)


def test_collision_from_unchanged_descriptions_is_not_blamed_on_the_edit():
    base = snapshot(ITEMS, CASES)
    current = json.loads(json.dumps(base))
    current["cases"]["a.p1"]["top1"] = "p:commit-push"
    ok, messages = check(base, current)
    assert ok
    assert not any("new collision" in m for m in messages)


def test_neighbors_count_items_ranked_above_target():
    items = ITEMS + [_item("lint", "Lint shell scripts.")]
    cases = [_pos("a.p1", "lint shell scripts", "p:shell-check")]
    metrics = evaluate(Router(items), cases)
    assert metrics["neighbors"]["p:shell-check"][0] == "p:lint"
    assert len(metrics["neighbors"]["p:shell-check"]) == 2


def test_cli_check_refuses_without_a_baseline(suite, capsys):
    assert main(["check", "--root", str(suite)]) == 1
    assert "no baseline" in capsys.readouterr().err


def test_cli_baseline_then_check_passes_on_an_unchanged_tree(suite, capsys):
    assert main(["baseline", "--root", str(suite)]) == 0
    assert (suite / "evals/activation/router-baseline.json").exists()
    assert main(["check", "--root", str(suite)]) == 0
    assert "If the change is intended" not in capsys.readouterr().out


def test_cli_check_fails_and_says_how_to_accept_a_new_collision(suite, capsys):
    main(["baseline", "--root", str(suite)])
    # shell-check absorbs every term the alpha:ship prompts use.
    (suite / "plugins/alpha/skills/shell-check/SKILL.md").write_text(
        "---\nname: shell-check\ndescription: alpha ship task alpha ship task\n---\n"
    )
    capsys.readouterr()
    assert main(["check", "--root", str(suite)]) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "router baseline" in out


def test_cli_report_prints_rates_then_collision_pairs(suite, capsys):
    assert main(["report", "--root", str(suite)]) == 0
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith("positives ") and " MRR " in first


def test_a_case_added_after_the_baseline_is_not_judged_against_it():
    items = [_item("a", "alpha words"), _item("b", "beta words")]
    old = [Case("c1", "positive", "alpha words", "p:a", None, "p:a")]
    base = snapshot(items, old)
    new = old + [Case("c2", "positive", "beta words", "p:b", None, "p:b")]
    ok, messages = check(base, snapshot(items, new))
    assert ok, messages
    assert not any("c2" in m for m in messages)
