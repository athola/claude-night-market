"""capabilities-sync-check.sh is a CI gate; prove it can fail.

The Capabilities Sync workflow runs it on every push. The only test that
touched it ran ``-h``, so its comparison had never been seen to report a
discrepancy.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "capabilities-sync-check.sh"

_REFERENCE = """\
### All Skills (Alphabetical)

| Skill | Plugin | Description |
|-------|--------|-------------|
{skills}

### All Commands (Alphabetical)

| Command | Plugin | Description |
|---------|--------|-------------|
{commands}

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
{agents}
"""


def _write_repo(
    root: Path,
    registered: dict[str, list[str]],
    documented: dict[str, list[str]],
) -> None:
    (root / "scripts").mkdir()
    shutil.copy2(GATE, root / "scripts" / GATE.name)
    shutil.copy2(REPO_ROOT / "scripts" / "logging.sh", root / "scripts")
    manifest = root / "plugins" / "demo" / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "demo", **registered}))
    reference = root / "book" / "src" / "reference" / "capabilities-reference.md"
    reference.parent.mkdir(parents=True)
    rows = {
        kind: "\n".join(f"| `{name}` | demo | d |" for name in documented[kind])
        for kind in ("skills", "commands", "agents")
    }
    reference.write_text(_REFERENCE.format(**rows))


def _gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/capabilities-sync-check.sh"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


REGISTERED = {
    "skills": ["./skills/alpha"],
    "commands": ["./commands/run.md"],
    "agents": ["./agents/helper.md"],
}
DOCUMENTED = {"skills": ["alpha"], "commands": ["/demo:run"], "agents": ["helper"]}


@pytest.mark.skipif(shutil.which("jq") is None, reason="the gate requires jq")
class TestCapabilitiesSyncGate:
    """Feature: the gate fails when registrations and the reference differ."""

    def test_matching_registrations_and_docs_pass(self, tmp_path: Path) -> None:
        """GIVEN one skill, command and agent, each registered and documented
        WHEN the gate runs
        THEN it exits 0
        """
        _write_repo(tmp_path, REGISTERED, DOCUMENTED)
        run = _gate(tmp_path)
        assert run.returncode == 0, run.stdout + run.stderr

    def test_a_registered_skill_missing_from_the_docs_fails(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a skill in plugin.json with no row in the reference
        WHEN the gate runs
        THEN it exits nonzero and names the skill as missing from docs
        """
        registered = {**REGISTERED, "skills": ["./skills/alpha", "./skills/beta"]}
        _write_repo(tmp_path, registered, DOCUMENTED)

        run = _gate(tmp_path)

        assert run.returncode != 0
        assert "beta (demo) - registered but NOT in docs" in run.stdout + run.stderr

    def test_a_documented_agent_nobody_registers_fails(self, tmp_path: Path) -> None:
        """GIVEN a reference row for an agent no plugin.json lists
        WHEN the gate runs
        THEN it exits nonzero and names the agent as extra
        """
        documented = {**DOCUMENTED, "agents": ["helper", "ghost"]}
        _write_repo(tmp_path, REGISTERED, documented)

        run = _gate(tmp_path)

        assert run.returncode != 0
        assert "ghost - in docs but NOT registered" in run.stdout + run.stderr
