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
