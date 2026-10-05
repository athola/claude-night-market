"""`python -m tome.channels.triz analyze` runs the TRIZ workflow in one call.

The triz skill and the triz-analyst agent told the model to call
`near_resolutions`, `physical_contradiction`, `separation_strategies` and
`reformulation_probes`, but named no command, and the agent had no shell.
No code called the three ADR-0026 functions outside tests, so the record
fields the ADR promises were never computed in a real run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"


def _analyze(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "tome.channels.triz", "analyze", *args],
        env={"PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_each_candidate_carries_the_adr_0026_fields() -> None:
    report = _analyze("--topic", "faster cache with less memory", "--domain", "systems")
    assert report["candidates"]
    for candidate in report["candidates"]:
        assert {"contradiction", "ideality", "physical", "probes"} <= candidate.keys()
        assert len(candidate["probes"]) == 5


def test_a_fallback_candidate_lists_near_resolutions() -> None:
    report = _analyze("--topic", "zzqx wobble frobnication", "--domain", "general")
    fallback = [
        c for c in report["candidates"] if c["contradiction"]["matched"] == "fallback"
    ]
    assert fallback
    assert "near_resolutions" in fallback[0]


def test_a_physical_contradiction_gets_separation_axes() -> None:
    report = _analyze("--topic", "faster cache with less memory", "--domain", "systems")
    for candidate in report["candidates"]:
        if candidate["physical"]:
            assert len(candidate["separation"]) == 4
        else:
            assert "separation" not in candidate


def test_usage_error_exits_nonzero() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "tome.channels.triz"],
        env={"PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2


PLUGIN = SRC.parent


def test_skill_and_agent_name_the_command_not_bare_functions() -> None:
    """The workflow steps are reachable only through the command."""
    skill = (PLUGIN / "skills" / "triz" / "SKILL.md").read_text()
    agent = (PLUGIN / "agents" / "triz-analyst.md").read_text()
    assert 'PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src"' in skill
    assert "tome.channels.triz analyze" in skill
    assert "tome.channels.triz analyze" in agent
    for text in (skill, agent):
        assert "near_resolutions(topic)" not in text
        assert "reformulation_probes(contradiction)" not in text


def test_research_passes_the_analysis_to_the_triz_channel_only() -> None:
    """The workflow script has no shell, so the skill runs the command and
    hands its JSON in as `trizAnalysis`; only the triz agent receives it.
    """
    script = (PLUGIN / "workflows" / "research.js").read_text()
    assert "input.trizAnalysis" in script
    assert "c.key === 'triz'" in script
    research = (PLUGIN / "skills" / "research" / "SKILL.md").read_text()
    assert "tome.channels.triz analyze" in research
    assert "trizAnalysis" in research
