"""The shipped research workflow must stay loadable, honest, and bounded."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "research.js"
README = PLUGIN_ROOT / "README.md"


def test_workflow_ships_at_the_discovered_location() -> None:
    """GIVEN the plugin as installed.

    WHEN the harness looks for workflows
    THEN it finds one at workflows/ in the plugin root
    """
    assert WORKFLOW.is_file()


def test_meta_is_the_first_statement_and_is_complete() -> None:
    """GIVEN the shipped script.

    WHEN the runtime reads meta
    THEN only comments precede it and it carries name and description
    """
    content = WORKFLOW.read_text()
    match = re.search(r"^export\s+const\s+meta\s*=", content, re.MULTILINE)
    assert match is not None
    for line in content[: match.start()].splitlines():
        stripped = line.strip()
        assert not stripped or stripped.startswith(("//", "/*", "*", "*/"))
    meta = content[match.end() : content.index("\n}\n", match.end())]
    assert "name:" in meta
    assert "description:" in meta


def test_every_channel_routes_to_a_tome_agent_that_exists() -> None:
    """GIVEN a script that names agent types.

    WHEN it dispatches a channel
    THEN the agent it names is one this plugin actually ships
    """
    content = WORKFLOW.read_text()
    named = set(re.findall(r"agentType: 'tome:([a-z-]+)'", content))
    assert named
    shipped = {p.stem for p in (PLUGIN_ROOT / "agents").glob("*.md")}
    assert named <= shipped, f"missing agents: {named - shipped}"


def test_an_empty_channel_is_distinguishable_from_a_broken_one() -> None:
    """GIVEN a channel that returns nothing.

    WHEN the workflow reports coverage
    THEN empty, failed and skipped are separate, with what was searched

    A thin topic and an error must not look alike; that distinction is
    the reason the skill records what each channel searched for.
    """
    content = WORKFLOW.read_text()
    for key in ("empty", "failed", "skipped", "searched"):
        assert f"{key}," in content or f"{key}:" in content


def test_the_readme_states_the_bundled_overlap() -> None:
    """GIVEN a harness that now bundles /deep-research.

    WHEN a reader opens the channel list
    THEN the overlap is stated rather than left to be discovered
    """
    readme = README.read_text()
    assert "/deep-research" in readme
    assert "workflows/research.js" in readme


# --- Named-entity gap fill (coverage gap, 2026-10-05) ----------------------
#
# A run comparing radios ruled Beartooth out without anyone searching for it:
# no channel happened to cover it, and nothing noticed. Entities the skill
# names must each be searched, and any still uncovered must be reported.

_HARNESS = r"""
const fs = require('fs')
const src = fs.readFileSync(process.argv[2], 'utf8').replace('export const meta', 'const meta')
const input = JSON.parse(process.argv[3])
const calls = []
const agent = async (prompt, opts) => {
  calls.push({ label: opts.label, prompt })
  if (opts.label === 'gap-fill') {
    if (process.argv[4] === 'gap-null') return null
    return { searched: 'gap fill', findings: [{ title: 'Beartooth MK2 specs', url: 'https://beartooth.example/mk2', why: 'vendor page' }] }
  }
  return { searched: 'meshtastic reticulum', findings: [{ title: 'Meshtastic range test', url: 'https://x/m', why: 'measured' }] }
}
const parallel = async (fns) => Promise.all(fns.map((f) => f()))
const run = new Function('args', 'agent', 'parallel', 'phase', 'log',
  `return (async () => {${src}})()`)
run(input, agent, parallel, () => {}, () => {}).then((out) => {
  console.log(JSON.stringify({ out, calls }))
})
"""


def _run_workflow(tmp_path: Path, payload: dict, mode: str = "") -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    harness = tmp_path / "harness.cjs"
    harness.write_text(_HARNESS)
    result = subprocess.run(
        [node, str(harness), str(WORKFLOW), json.dumps(payload), mode],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(result.stdout)


def test_an_unsearched_named_entity_gets_a_gap_fill_search(tmp_path: Path) -> None:
    run = _run_workflow(
        tmp_path,
        {
            "topic": "mesh radios",
            "channels": ["discourse"],
            "entities": ["Meshtastic", "Beartooth"],
        },
    )
    gap = [c for c in run["calls"] if c["label"] == "gap-fill"]
    assert len(gap) == 1
    assert "Beartooth" in gap[0]["prompt"]
    assert "Meshtastic" not in gap[0]["prompt"].split("named options:")[-1]
    titles = [f["title"] for f in run["out"]["findings"]]
    assert "Beartooth MK2 specs" in titles
    assert run["out"]["coverage"]["unsearched"] == []


def test_entities_covered_by_the_channels_need_no_gap_fill(tmp_path: Path) -> None:
    run = _run_workflow(
        tmp_path,
        {"topic": "mesh radios", "channels": ["discourse"], "entities": ["Meshtastic"]},
    )
    assert not [c for c in run["calls"] if c["label"] == "gap-fill"]
    assert run["out"]["coverage"]["unsearched"] == []


def test_an_entity_still_uncovered_is_reported(tmp_path: Path) -> None:
    run = _run_workflow(
        tmp_path,
        {
            "topic": "mesh radios",
            "channels": ["discourse"],
            "entities": ["Beartooth", "goTenna"],
        },
    )
    assert run["out"]["coverage"]["unsearched"] == ["goTenna"]


def test_a_gap_fill_that_returns_nothing_is_a_failure(tmp_path: Path) -> None:
    run = _run_workflow(
        tmp_path,
        {"topic": "mesh radios", "channels": ["discourse"], "entities": ["Beartooth"]},
        mode="gap-null",
    )
    assert run["out"]["coverage"]["failed"] == ["gap-fill"]
    assert run["out"]["coverage"]["unsearched"] == ["Beartooth"]
