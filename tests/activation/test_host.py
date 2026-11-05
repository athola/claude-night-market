"""FR-4 and FR-5: the generated eval suite and the host it runs in.

`claude plugin eval` loads plugins only from under its target
directory (probe L5), so every run gets a host holding hard-linked
plugin copies and one case.yaml per labeled case.
"""

from __future__ import annotations

import json
import re
import time

import yaml
from scripts.activation.generate import case_yaml
from scripts.activation.host import build_host
from scripts.activation.inventory import build_inventory
from scripts.activation.labels import Case

from .conftest import REPO_ROOT, write

POS = Case(
    id="alpha.ship.p1",
    type="positive",
    prompt="Push it.",
    target="alpha:ship",
    cluster="alpha:ship",
)
NEG = Case(
    id="neg.p1", type="negative", prompt="Rename x.", target=None, cluster="chores"
)
ALLOWED_TOP = {
    "schema_version",
    "name",
    "description",
    "tags",
    "plugins",
    "runs",
    "expected_outcome",
    "graders",
    "execution",
    "context",
}
ALLOWED_EXEC = {
    "model",
    "max_turns",
    "timeout_seconds",
    "allowed_tools",
    "append_system_prompt",
    "env",
    "prompt",
}


def test_positive_case_targets_its_item_with_an_escaped_pattern():
    doc = case_yaml(
        Case(
            id="x.p1", type="positive", prompt="p", target="a.b:c+d", cluster="a.b:c+d"
        ),
        plugins=["a.b"],
        runs=3,
    )
    grader = doc["graders"][0]
    assert (
        grader["type"] == "tool_used"
        and grader["tool"] == "Skill"
        and grader["arm"] == "both"
    )
    assert re.search(grader["input_match"], '{"skill": "a.b:c+d"}')
    assert not re.search(grader["input_match"], '{"skill": "aXb:cccd"}')


def test_negative_case_forbids_every_loaded_plugin():
    doc = case_yaml(NEG, plugins=["alpha", "beta"], runs=3)
    grader = doc["graders"][0]
    assert (grader["min"], grader["max"]) == (0, 0)
    assert re.search(grader["input_match"], '{"skill": "beta:sweep"}')
    assert not re.search(grader["input_match"], '{"skill": "deep-research"}')


def test_case_uses_only_documented_fields_and_relative_plugin_paths():
    doc = case_yaml(POS, plugins=["alpha", "beta"], runs=3)
    assert set(doc) <= ALLOWED_TOP
    assert set(doc["execution"]) <= ALLOWED_EXEC
    assert doc["schema_version"] == "1.1"
    assert doc["plugins"] == ["../../plugins/alpha", "../../plugins/beta"]
    assert all(g.get("name") for g in doc["graders"])


def test_host_holds_plugins_cases_and_metadata(plugin_tree):
    write(plugin_tree / "plugins/alpha/tests/test_x.py", "x = 1\n")
    write(plugin_tree / "plugins/alpha/uv.lock", "lock\n")
    items = build_inventory(plugin_tree)
    host = build_host(
        plugin_tree,
        [POS, NEG],
        items,
        {"run_id": "r1", "tier": "change", "runs": 3},
    )
    assert not (host / "plugins/alpha/tests").exists()
    assert not (host / "plugins/alpha/uv.lock").exists()
    case_dir = host / "evals" / POS.id
    doc = yaml.safe_load((case_dir / "case.yaml").read_text())
    for rel in doc["plugins"]:
        assert (case_dir / rel / "commands").exists() or (
            case_dir / rel / "workflows"
        ).exists()
    run = json.loads((host / "run.json").read_text())
    assert run["run_id"] == "r1" and run["case_set_hash"]
    assert len(json.loads((host / "cases.json").read_text())) == 2
    assert json.loads((host / "inventory.json").read_text())["library_hash"]


def test_host_files_are_copies_because_the_eval_refuses_hard_links(plugin_tree):
    # claude plugin eval 2.1.317 errors on "a file in the plugin has more
    # than one name (a hard link)" (smoke run 2026-11-03).
    write(plugin_tree / "plugins/alpha/.uv-cache/blob", "x" * 10)
    write(plugin_tree / "plugins/alpha/.claude-plugin/plugin.json", "{}")
    host = build_host(
        plugin_tree, [POS], build_inventory(plugin_tree), {"run_id": "r1", "runs": 3}
    )
    copied = host / "plugins/alpha/commands/ship.md"
    original = plugin_tree / "plugins/alpha/commands/ship.md"
    assert copied.stat().st_ino != original.stat().st_ino
    assert copied.stat().st_nlink == 1
    assert not (host / "plugins/alpha/.uv-cache").exists()
    assert (host / "plugins/alpha/.claude-plugin/plugin.json").exists()


def test_full_repo_host_builds_fast_and_cheap(tmp_path):
    items = build_inventory(REPO_ROOT)
    case = Case(
        id="speed.p1",
        type="positive",
        prompt="p",
        target=items[0].id,
        cluster=items[0].id,
    )
    start = time.monotonic()
    host = build_host(
        REPO_ROOT, [case], items, {"run_id": "speed", "runs": 3}, runs_dir=tmp_path
    )
    assert time.monotonic() - start < 10
    assert json.loads((host / "run.json").read_text())["copied_bytes"] < 50_000_000
