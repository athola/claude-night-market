"""Shared fixtures for the activation-quality tooling tests.

The tooling is the ``scripts.activation`` package, run from the repo
root as ``uv run python -m scripts.activation.<tool>``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from scripts.activation.inventory import (
    build_inventory,
    item_hashes,
    library_hash,
)
from scripts.activation.labels import case_set_hash

LISTED = ("alpha:shell-check", "alpha:ship", "beta:sweep")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def plugin_tree(tmp_path: Path) -> Path:
    """Two plugins: one of each routed kind, plus one disabled command."""
    root = tmp_path / "repo"
    write(
        root / "plugins/alpha/skills/shell-check/SKILL.md",
        "---\nname: shell-check\ndescription: >-\n  Audit shell scripts\n"
        "  for quoting bugs.\n---\n\n# Body\n\nLong body text.\n",
    )
    write(
        root / "plugins/alpha/commands/ship.md",
        "---\ndescription: Commit and push the current branch.\n---\n\n# Ship\n",
    )
    write(
        root / "plugins/alpha/commands/hidden.md",
        "---\ndescription: Hidden.\ndisable-model-invocation: true\n---\n",
    )
    write(
        root / "plugins/beta/workflows/sweep.js",
        "// comment\nexport const meta = {\n  name: 'sweep',\n  description:\n"
        "    'Sweep every area in parallel',\n  whenToUse:\n"
        "    'Run before a release. It\\'s read-only.',\n  phases: [],\n}\n",
    )
    return root


def trace_lines(fired: list[str], **init_overrides) -> str:
    """A minimal stream-json trace in the shape the eval child writes.

    ``init_overrides`` replaces fields of the init event: ``model``,
    ``claude_code_version``, ``plugins`` (names) or ``skills``.
    """
    plugins = init_overrides.pop("plugins", ("alpha", "beta"))
    init = {
        "type": "system",
        "subtype": "init",
        "model": "claude-test-1",
        "claude_code_version": "9.9.9",
        "plugins": [{"name": p, "source": f"{p}@inline"} for p in plugins],
        "skills": list(LISTED),
        "slash_commands": [],
    }
    init.update(init_overrides)
    events = [init]
    for n, skill in enumerate(fired):
        block = {
            "type": "tool_use",
            "id": f"t{n}",
            "name": "Skill",
            "input": {"skill": skill},
        }
        events.append({"type": "assistant", "message": {"content": [block]}})
    events.append(
        {
            "type": "result",
            "subtype": "error_max_turns",
            "is_error": True,
            "num_turns": 2,
            "total_cost_usd": 0.1,
        }
    )
    return "".join(json.dumps(e) + "\n" for e in events)


def make_host(root, cases, runs_by_case, *, trace_kwargs=None, run_extra=None):
    """Build an analyzable run host beside ``root``.

    ``runs_by_case`` maps a case id to one fired-skill list per run, with
    None marking an errored run. ``run_extra`` overrides run.json fields
    (``runs`` defaults to 3).
    """
    items = build_inventory(root)
    host = root.parent / "host"
    host.mkdir(exist_ok=True)
    (host / "cases.json").write_text(json.dumps([c.to_dict() for c in cases]))
    inventory = {
        "items": [i.__dict__ for i in items],
        "library_hash": library_hash(items),
        "item_hashes": item_hashes(items),
    }
    (host / "inventory.json").write_text(json.dumps(inventory))
    run = {
        "run_id": "r1",
        "tier": "anchor",
        "arm": "default",
        "runs": 3,
        "commit": "abc",
        "dirty": False,
        "case_set_hash": case_set_hash(cases),
        "change": None,
        "eval_exit": 0,
    }
    run.update(run_extra or {})
    (host / "run.json").write_text(json.dumps(run))
    for cid, run_list in runs_by_case.items():
        for n, fired in enumerate(run_list):
            path = host / "traces" / cid / f"{n}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            if fired is None:
                path.with_suffix(".error").write_text("timeout")
                continue
            path.write_text(
                trace_lines(fired, **(trace_kwargs or {}).get((cid, n), {}))
            )
    return host


ITEMS = ("alpha:shell-check", "alpha:ship", "beta:sweep")


def _labels(full: bool) -> dict:
    cases = []
    for item in ITEMS:
        slug = item.replace(":", ".")
        for n in range(3 if full else 1):
            kind = "near_miss" if n == 2 else "positive"
            competitor = "beta:sweep" if item != "beta:sweep" else "alpha:ship"
            cases.append(
                {
                    "id": f"{slug}.p{n}",
                    "type": kind,
                    "prompt": f"{item} task {n}",
                    "target": item,
                    "cluster": item,
                    "competitor": competitor if kind == "near_miss" else None,
                }
            )
    for n in range(50 if full else 2):
        cases.append(
            {
                "id": f"neg.p{n}",
                "type": "negative",
                "prompt": f"rename var {n}",
                "target": None,
                "cluster": f"src{n % 10}",
            }
        )
    return {"schema_version": 1, "cases": cases}


@pytest.fixture
def suite(plugin_tree: Path) -> Path:
    root = plugin_tree
    write(
        root / "evals/activation/config.yaml",
        yaml.safe_dump({"runs": 3, "arms": {"default": None, "haiku": "haiku"}}),
    )
    write(root / "evals/activation/labels/all.yaml", yaml.safe_dump(_labels(full=True)))
    write(root / "evals/activation/anchor.txt", "alpha.ship.p0\nneg.p0\n")
    for cmd in (
        ["init", "-q"],
        ["add", "-A"],
        ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
    ):
        subprocess.run(["git", *cmd], cwd=root, check=True)
    return root


def _fake_eval(fired_for, code: int = 0):
    """An eval stand-in: writes a trace per run and the aggregate JSON.

    ``fired_for`` maps a case name to the skills it fires, or is a
    callable ``(host, case_name) -> list`` for host-dependent behavior.
    """
    calls = []

    def runner(cmd: list[str]) -> int:
        calls.append(cmd)
        host = Path(cmd[3])
        runs = int(cmd[cmd.index("--runs") + 1])
        cases = []
        for case_yaml in sorted((host / "evals").glob("*/case.yaml")):
            name = yaml.safe_load(case_yaml.read_text())["name"]
            out = []
            for n in range(runs):
                trace = host / "tmp" / name / f"{n}.jsonl"
                trace.parent.mkdir(parents=True, exist_ok=True)
                fired = (
                    fired_for(host, name)
                    if callable(fired_for)
                    else fired_for.get(name, [])
                )
                trace.write_text(trace_lines(fired))
                out.append({"score": 1, "tracePath": str(trace)})
            cases.append({"name": name, "arms": {"with": out}})
        (host / "result.json").write_text(json.dumps({"cases": cases}))
        return code

    runner.calls = calls
    return runner
