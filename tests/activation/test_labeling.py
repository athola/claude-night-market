"""FR-2 creation: the measured models never write or label their own
answer key, and a labeling session cannot overspend by more than one
call. A fake model stands in for `claude -p`.
"""

from __future__ import annotations

import json
import re
import subprocess

import pytest
import yaml
from scripts.activation import labeling
from scripts.activation.inventory import build_inventory
from scripts.activation.labeling import (
    Budget,
    BudgetExceeded,
    LabelingRefused,
    draft,
    item_body,
    pending,
    pick_roles,
    resolve,
    resolved_model,
    write_resolved,
)
from scripts.activation.labels import load_cases, validate

CONFIG = {
    "writer_models": ["sonnet", "opus"],
    "judge_models": ["sonnet", "opus"],
    "arms": {"default": None, "haiku": "haiku"},
    "label_max_cost_usd": 30,
}
IDS = {
    None: "claude-sonnet-5-5",
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
}


def _probe(model, _prompt):
    return {
        "modelUsage": {IDS[model]: {"outputTokens": 3}},
        "total_cost_usd": 0.01,
    }, 0.01


def test_resolve_records_every_arm_and_candidate():
    resolved = resolve(CONFIG, call=_probe)
    assert resolved["arm:default"] == "claude-sonnet-5-5"
    assert resolved["opus"] == "claude-opus-5-5"


def test_roles_skip_candidates_that_resolve_to_a_measured_arm():
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}
    assert pick_roles(config) == {"writer": "opus", "judge": "opus"}


def test_labeling_fails_closed_when_unresolved():
    with pytest.raises(LabelingRefused, match="unresolved"):
        pick_roles({**CONFIG, "resolved": {}})


def test_labeling_refuses_when_every_candidate_is_an_arm():
    config = {
        **CONFIG,
        "writer_models": ["sonnet"],
        "resolved": resolve(CONFIG, call=_probe),
    }
    with pytest.raises(LabelingRefused, match="writer"):
        pick_roles(config)


def test_resolved_model_reads_model_usage():
    assert (
        resolved_model(
            {"modelUsage": {"a": {"outputTokens": 1}, "b": {"outputTokens": 9}}}
        )
        == "b"
    )
    with pytest.raises(LabelingRefused):
        resolved_model({})


def test_budget_stops_before_the_call_after_the_ceiling():
    calls = []

    def costly(model, prompt):
        calls.append(prompt)
        return {"result": "[]"}, 0.6

    budget = Budget(costly, ceiling=1.0)
    budget("m", "a")
    budget("m", "b")
    with pytest.raises(BudgetExceeded):
        budget("m", "c")
    assert calls == ["a", "b"]


def test_item_body_never_includes_the_routed_description(plugin_tree):
    for item in build_inventory(plugin_tree):
        assert item.description.split(" - ")[0] not in item_body(plugin_tree, item)


def _fake_model(model, prompt):
    """Writes two prompts per ITEM, one near-miss, sources, and judges by echo."""
    items = re.findall(r"### ITEM (\S+)", prompt)
    if prompt.startswith("Each PROMPT below"):
        out = []
        for n, text in re.findall(r"PROMPT (\d+): (.*)", prompt):
            target = re.match(r"work on (\S+)", text)
            out.append(
                {
                    "n": int(n),
                    "pick": target.group(1) if target else "none",
                    "runner_up": "none",
                }
            )
    elif "hasty reader" in prompt:
        out = [{"item": i, "prompt": f"work on {i} carefully"} for i in items]
    elif "everyday coding requests" in prompt:
        out = [
            {"source": s, "prompt": f"help with {s} #{n}"}
            for s in re.search(r"plugin: (.*)\. Objects", prompt).group(1).split("; ")
            for n in range(5)
        ]
    else:
        out = [
            {"item": i, "prompt": f"work on {i} task {n}"}
            for i in items
            for n in range(2)
        ]
    return {"result": json.dumps(out)}, 0.01


def test_draft_writes_valid_labels_and_an_adjudication_queue(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}
    queue = draft(plugin_tree, config, call=_fake_model)
    cases = load_cases(plugin_tree / "evals/activation/labels")
    validate(cases, build_inventory(plugin_tree), plugin_tree)
    kinds = {c.type for c in cases}
    assert kinds == {"positive", "near_miss", "negative"}
    assert sum(c.type == "negative" for c in cases) == 60
    assert len({c.cluster for c in cases if c.type == "negative"}) == 12
    assert queue["writer"] == "opus" and queue["spent_usd"] > 0
    assert queue == yaml.safe_load(
        (plugin_tree / "evals/activation/adjudicate.yaml").read_text()
    )
    assert set(pending(plugin_tree)) == set(queue["disagreements"]) | set(
        queue["audit_sample"]
    )
    again = draft(plugin_tree, config, call=_fake_model)
    assert again["audit_sample"] == queue["audit_sample"]


def test_claude_call_runs_a_lean_isolated_session(monkeypatch):
    seen = {}

    class Done:
        stdout = json.dumps({"result": "ok", "total_cost_usd": 0.02})

    def fake_run(cmd, **kwargs):
        seen["cmd"], seen["cwd"] = cmd, kwargs.get("cwd")
        return Done()

    monkeypatch.setattr(labeling.subprocess, "run", fake_run)
    result, cost = labeling.claude_call("opus", "hello")
    assert cost == 0.02 and result["result"] == "ok"
    cmd = seen["cmd"]
    assert cmd[-1] == "hello"
    for flag in ("--disable-slash-commands", "--no-session-persistence"):
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--model") + 1] == "opus"
    assert seen["cwd"] and "night-market" not in seen["cwd"]


def test_budget_stop_during_judging_keeps_drafts_and_queues_the_rest(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {
        **CONFIG,
        "resolved": resolve(CONFIG, call=_probe),
        "label_max_cost_usd": 0.045,
    }
    queue = draft(plugin_tree, config, call=_fake_model)
    assert queue["stopped"]
    cases = load_cases(plugin_tree / "evals/activation/labels")
    assert cases
    unjudged = [c for c in cases if "judge: unjudged" in c.notes]
    assert unjudged
    assert {c.id for c in unjudged if c.type != "negative"} <= set(
        queue["disagreements"]
    )


def test_judge_batches_ten_prompts_per_call(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    calls = []

    def counting(model, prompt):
        calls.append(prompt)
        return _fake_model(model, prompt)

    draft(
        plugin_tree, {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}, call=counting
    )
    judge_calls = [c for c in calls if c.startswith("Each PROMPT below")]
    prompts = sum(len(re.findall(r"^PROMPT \d+:", c, re.M)) for c in judge_calls)
    assert prompts == 6 + 3 + 60
    assert len(judge_calls) == 7


def test_a_failed_call_is_counted_and_skipped_not_fatal():
    def flaky(model, prompt):
        if prompt == "bad":
            raise subprocess.CalledProcessError(1, ["claude"], stderr="overloaded")
        return {"result": "[1]"}, 0.01

    budget = Budget(flaky, ceiling=1.0)
    assert budget("m", "bad") == ""
    assert budget("m", "good") == "[1]"
    assert budget.failures == ["overloaded"]


def test_write_resolved_keeps_the_config_comments(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("# keep me\nwriter_models: [sonnet]\n# and me\nresolved: {}\n")
    write_resolved(
        path, {"arm:default": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
    )
    text = path.read_text()
    assert "# keep me" in text and "# and me" in text
    assert "writer_models: [sonnet]" in text
    assert yaml.safe_load(text)["resolved"] == {
        "arm:default": "claude-opus-5-5",
        "sonnet": "claude-sonnet-5-5",
    }
    write_resolved(path, {"sonnet": "x"})
    assert yaml.safe_load(path.read_text())["resolved"] == {"sonnet": "x"}


def test_judge_always_sees_the_writer_target(plugin_tree, monkeypatch):
    # The first full draft lost 328 of 628 positive labels because the
    # judge chose only among the router's top 8.
    monkeypatch.setattr(labeling, "SHORTLIST", 1)
    items = build_inventory(plugin_tree)
    router = labeling.Router(items)
    seen = []

    def ask(prompt):
        seen.append(prompt)
        return json.dumps([{"n": 0, "pick": "beta:sweep", "runner_up": "none"}])

    by_id = {i.id: i for i in items}
    out = labeling.judge_batch(
        plugin_tree,
        router,
        by_id,
        ask,
        [("audit shell scripts for quoting bugs", "beta:sweep")],
    )
    candidates = re.search(r"CANDIDATES 0: (.*)", seen[0]).group(1).split(", ")
    assert "beta:sweep" in candidates and "alpha:shell-check" in candidates
    assert out == [("beta:sweep", None)]


def test_repair_fills_short_items_and_rejudges_unseen_targets(plugin_tree, monkeypatch):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}
    draft(plugin_tree, config, call=_fake_model)
    labels = plugin_tree / "evals/activation/labels"
    (labels / "beta.yaml").unlink()
    alpha = yaml.safe_load((labels / "alpha.yaml").read_text())
    alpha["cases"][0]["adjudicated"] = True
    alpha["cases"][0]["notes"] = "checked by hand"
    for row in alpha["cases"][1:]:
        row["proposers"], row["proposals"] = (
            ["writer"],
            {"aimed_at": row.get("competitor")},
        )
    (labels / "alpha.yaml").write_text(yaml.safe_dump(alpha, sort_keys=False))
    monkeypatch.setattr(labeling, "SHORTLIST", 0)

    queue = labeling.repair(plugin_tree, config, call=_fake_model)

    cases = {c.id: c for c in load_cases(labels)}
    validate(list(cases.values()), build_inventory(plugin_tree), plugin_tree)
    assert queue["repaired"]["filled_items"] == ["beta:sweep"]
    assert sum(c.target == "beta:sweep" for c in cases.values()) == 3
    assert queue["repaired"]["rejudged"] == len(alpha["cases"]) - 1
    first = alpha["cases"][0]["id"]
    assert cases[first].notes == "checked by hand"
    rejudged = [
        c
        for c in cases.values()
        if c.target and c.target.startswith("alpha") and c.id != first
    ]
    assert all("judge" in c.proposers for c in rejudged)
    first_spend = yaml.safe_load((labels.parent / "adjudicate.yaml").read_text())[
        "spent_usd"
    ]
    assert first_spend == queue["spent_usd"] > 0


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (
            {"type": "positive", "target": "a:x", "notes": ""},
            {"router": "a:x", "judge": "a:x"},
        ),
        (
            {"type": "positive", "target": "a:x", "notes": "router: a:y; judge: None"},
            {"router": "a:y", "judge": None},
        ),
        (
            {
                "type": "near_miss",
                "target": "a:x",
                "competitor": "a:y",
                "notes": "aimed at a:y; router: a:x; judge: a:x/a:y",
            },
            {
                "aimed_at": "a:y",
                "router": "a:x",
                "judge": "a:x",
                "judge_runner_up": "a:y",
            },
        ),
        (
            {
                "type": "negative",
                "target": None,
                "notes": "router top: a:z (1.50); judge: None",
            },
            {"router": "a:z", "judge": None},
        ),
    ],
)
def test_first_draft_rows_backfill_their_proposals_from_notes(row, expected):
    labeling.backfill_proposals(row)
    assert {k: row["proposals"][k] for k in expected} == expected


@pytest.mark.parametrize(
    ("row", "queued"),
    [
        (
            {
                "type": "positive",
                "target": "a:x",
                "proposals": {"router": "a:y", "judge": "a:x"},
            },
            False,
        ),
        (
            {
                "type": "positive",
                "target": "a:x",
                "proposals": {"router": "a:x", "judge": "a:y"},
            },
            True,
        ),
        (
            {
                "type": "positive",
                "target": "a:x",
                "proposals": {"router": "a:x", "judge": None},
            },
            True,
        ),
        (
            {
                "type": "near_miss",
                "target": "a:x",
                "competitor": "a:z",
                "proposals": {"aimed_at": "a:y", "router": "a:q", "judge": "a:x"},
            },
            False,
        ),
        (
            {
                "type": "negative",
                "target": None,
                "proposals": {"router": "a:z", "judge": None},
            },
            False,
        ),
        (
            {
                "type": "negative",
                "target": None,
                "proposals": {"router": "a:z", "judge": "a:z"},
            },
            True,
        ),
    ],
)
def test_queue_follows_the_judge_not_the_lexical_router(row, queued):
    assert labeling.disagrees(row) is queued


def test_requeue_rebuilds_the_queue_without_spending(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}
    before = draft(plugin_tree, config, call=_fake_model)
    after = labeling.requeue(plugin_tree)
    assert after["spent_usd"] == before["spent_usd"]
    assert after["disagreements"] == before["disagreements"]


def _garbles_first_writer_batch():
    # The first full draft lost 11 items to one writer reply that did not parse.
    state = {"garbled": False}

    def call(model, prompt):
        writer_batch = "### ITEM" in prompt and "hasty reader" not in prompt
        if writer_batch and not state["garbled"]:
            state["garbled"] = True
            return {"result": "Here are the prompts: [{oops"}, 0.01
        return _fake_model(model, prompt)

    return call


def test_draft_redrafts_items_a_garbled_writer_reply_left_short(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}
    queue = draft(plugin_tree, config, call=_garbles_first_writer_batch())
    cases = load_cases(plugin_tree / "evals/activation/labels")
    for item in build_inventory(plugin_tree):
        assert sum(c.is_positive and c.target == item.id for c in cases) == 3
    assert queue["unfilled_items"] == []


def test_draft_records_items_still_short_after_the_retry(plugin_tree):
    (plugin_tree / "evals/activation").mkdir(parents=True)
    config = {**CONFIG, "resolved": resolve(CONFIG, call=_probe)}

    def never_writes_beta(model, prompt):
        if "### ITEM beta:sweep" in prompt and "PROMPT" not in prompt:
            return {"result": "not json"}, 0.01
        return _fake_model(model, prompt)

    queue = draft(plugin_tree, config, call=never_writes_beta)
    assert queue["unfilled_items"] == ["beta:sweep"]
