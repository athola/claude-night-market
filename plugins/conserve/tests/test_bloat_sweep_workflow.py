"""A finding with no line count must not rank as a measured zero.

``lines`` is optional in the scan schema, and scanners leave it out for
``unused-dep`` and ``god-object``. The sort read a missing count as 0,
which put an unmeasured finding below every measured one and reported it
as saving nothing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "workflows" / "bloat-sweep.js"
NODE = shutil.which("node")


def _run_sweep(tmp_path: Path, areas: list[str], results: list[dict | None]) -> dict:
    """Run the workflow body under node with stubbed ``agent`` and ``parallel``.

    The runtime wraps the body in an async function and supplies ``args``,
    ``log``, ``agent`` and ``parallel``. The stub hands back ``results`` in
    dispatch order.
    """
    body = SCRIPT.read_text(encoding="utf-8").replace(
        "export const meta", "const meta", 1
    )
    harness = tmp_path / "harness.mjs"
    harness.write_text(
        "const RESULTS = " + json.dumps(results) + ";\nlet cursor = 0;\n"
        "function log(message) {}\n"
        "async function agent(prompt, options) { return RESULTS[cursor++]; }\n"
        "async function parallel(thunks) "
        "{ return Promise.all(thunks.map((thunk) => thunk())); }\n"
        "const args = " + json.dumps({"areas": areas}) + ";\n"
        "async function run() {\n" + body + "\n}\n"
        "run().then((result) => console.log(JSON.stringify(result)));\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [NODE or "node", str(harness)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _finding(location: str, lines: int | None = None) -> dict:
    finding = {"kind": "dead-code", "location": location, "evidence": "no refs"}
    if lines is not None:
        finding["lines"] = lines
    return finding


@pytest.mark.skipif(NODE is None, reason="node is not installed")
class TestUnmeasuredFindingsAreNotZero:
    """Scenario: one scanner reports a finding without a line count."""

    @pytest.mark.unit
    def test_unmeasured_findings_follow_the_measured_ones_marked_null(
        self, tmp_path: Path
    ) -> None:
        """Measured findings rank by size; unmeasured ones follow as null.

        Given findings of 5 lines, unknown size, and 40 lines
        Then the measured ones rank first by size
        And the unmeasured one follows with ``lines: null``.
        """
        scans = [
            {"area": "a", "findings": [_finding("a.py:1", 5), _finding("a.py:9")]},
            {"area": "b", "findings": [_finding("b.py:3", 40)]},
        ]
        out = _run_sweep(tmp_path, ["a", "b"], [*scans, {"duplications": []}])

        ranked = [(f["location"], f["lines"]) for f in out["findings"]]
        assert ranked == [("b.py:3", 40), ("a.py:1", 5), ("a.py:9", None)]

    @pytest.mark.unit
    def test_a_reported_zero_stays_a_measured_zero(self, tmp_path: Path) -> None:
        """A scanner that reports 0 lines measured it; it ranks as measured."""
        scans = [
            {"area": "a", "findings": [_finding("a.py:9"), _finding("a.py:1", 0)]},
        ]
        out = _run_sweep(tmp_path, ["a"], [*scans, {"duplications": []}])

        ranked = [(f["location"], f["lines"]) for f in out["findings"]]
        assert ranked == [("a.py:1", 0), ("a.py:9", None)]
