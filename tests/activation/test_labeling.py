"""FR-2 creation: the measured models never write or label their own
answer key, and a labeling session cannot overspend by more than one
call. A fake model stands in for `claude -p`.
"""

from __future__ import annotations

import json
import re

import pytest
import yaml
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
    if prompt.startswith("A developer typed"):
        target = re.search(r"PROMPT: work on (\S+)", prompt)
        pick = target.group(1) if target else "none"
        out = [{"pick": pick, "runner_up": "none"}]
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
