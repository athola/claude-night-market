"""The judge panel must count the judges it dispatched, not the survivors.

Feature: A dropped judge cannot change the verdict silently.

As the operator reading a panel verdict
I want the majority computed over the three lenses dispatched
So that one judge returning nothing leaves a visible hole rather than a
two-judge panel that reads as unanimous

Found in the 2026-09 workflow audit (ADR-0025): ``judged.filter(Boolean)``
set the denominator after dropping nulls, so two missing judges let a
single survivor return ``complete`` and the return value carried no sign
of it. Every other workflow under-reported on a dropped agent; this one
moved the verdict.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "workflows" / "judge-panel.js"
NODE = shutil.which("node")


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


class TestTheDenominatorIsTheRoster:
    """Scenario: the majority is computed over the lenses dispatched."""

    @pytest.mark.unit
    def test_majority_is_over_lenses_dispatched(self, script: str) -> None:
        """
        Given three lenses are dispatched
        Then the majority test divides by LENSES.length, not by the survivors
        """
        assert re.search(r"satisfied\.length\s*>\s*LENSES\.length\s*/\s*2", script)
        assert "verdicts.length / 2" not in script

    @pytest.mark.unit
    def test_missing_judges_are_returned_by_lens(self, script: str) -> None:
        """
        Given a judge returned nothing
        Then the return names its lens under ``missing``
        """
        assert re.search(
            r"const missing = LENSES\.filter\(\(lens, index\) => !judged\[index\]\)",
            script,
        )
        assert re.search(r"return \{[^}]*missing", script, re.S)

    @pytest.mark.unit
    def test_a_panel_with_a_missing_judge_cannot_be_complete(self, script: str) -> None:
        """
        Given a lens has no verdict
        Then the verdict is ``inconclusive`` rather than ``complete``

            A lens nobody judged is not a lens that passed.
        """
        assert "'inconclusive'" in script
        assert re.search(r"missing\.length\s*\?\s*'inconclusive'", script)


def _run_panel(
    script_path: Path,
    judged: list[dict | None],
    *,
    claim: str = "the migration is done",
    evidence: str = "pytest: 41 passed",
    tmp_path: Path,
) -> dict:
    """Execute the workflow body under node with stubbed agent and parallel.

    The runtime hands the script `args`, `log`, `agent` and `parallel` as
    free variables and wraps the body in an async function, which is why
    the body carries a top-level `return`. The harness reproduces that
    shape: `export const meta` becomes a plain declaration, the body goes
    inside `async function run()`, and the stubs hand back `judged` in
    dispatch order.
    """
    body = script_path.read_text(encoding="utf-8").replace(
        "export const meta", "const meta", 1
    )
    harness = tmp_path / "harness.mjs"
    harness.write_text(
        "const RESULTS = "
        + json.dumps(judged)
        + ";\nlet cursor = 0;\nconst logs = [];\n"
        "function log(message) { logs.push(String(message)); }\n"
        "async function agent(prompt, options) { return RESULTS[cursor++]; }\n"
        "async function parallel(thunks) "
        "{ return Promise.all(thunks.map((thunk) => thunk())); }\n"
        "const args = " + json.dumps({"claim": claim, "evidence": evidence}) + ";\n"
        "async function run() {\n" + body + "\n}\n"
        "run().then((result) => "
        "console.log(JSON.stringify({ result, logs, dispatched: cursor })));\n",
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


def _verdict(lens: str, complete: bool) -> dict:
    return {"lens": lens, "complete": complete, "reason": f"{lens} reason"}


@pytest.mark.skipif(NODE is None, reason="node is not installed")
class TestTheVerdictIsComputed:
    """Scenario outline: the verdict over a table of judge results.

    The three regex tests above pin the wiring. These run it. A mutation
    that inverts `satisfied` or reorders the verdict precedence leaves
    every regex intact and fails here.
    """

    @pytest.mark.unit
    def test_three_complete_judges_return_complete(self, tmp_path: Path) -> None:
        """
        Given every lens is satisfied
        Then the verdict is complete with no dissent and nothing missing
        """
        out = _run_panel(
            SCRIPT,
            [_verdict(name, True) for name in ("execution", "scope", "regression")],
            tmp_path=tmp_path,
        )

        assert out["result"]["verdict"] == "complete"
        assert out["result"]["dissent"] == []
        assert out["result"]["missing"] == []

    @pytest.mark.unit
    def test_a_missing_judge_makes_the_panel_inconclusive(self, tmp_path: Path) -> None:
        """
        Given two lenses pass and the third judge returns nothing
        Then the verdict is inconclusive and the silent lens is named
        """
        out = _run_panel(
            SCRIPT,
            [_verdict("execution", True), _verdict("scope", True), None],
            tmp_path=tmp_path,
        )

        assert out["result"]["verdict"] == "inconclusive"
        assert out["result"]["missing"] == ["regression"]

    @pytest.mark.unit
    def test_two_of_three_satisfied_is_complete_with_dissent(
        self, tmp_path: Path
    ) -> None:
        """
        Given a two-to-one split with every judge heard from
        Then the verdict is complete and the dissent is carried
        """
        out = _run_panel(
            SCRIPT,
            [
                _verdict("execution", True),
                _verdict("scope", True),
                _verdict("regression", False),
            ],
            tmp_path=tmp_path,
        )

        assert out["result"]["verdict"] == "complete"
        assert [entry["lens"] for entry in out["result"]["dissent"]] == ["regression"]

    @pytest.mark.unit
    def test_one_of_three_satisfied_is_incomplete(self, tmp_path: Path) -> None:
        """
        Given a one-to-two split
        Then the majority fails and the verdict is incomplete
        """
        out = _run_panel(
            SCRIPT,
            [
                _verdict("execution", True),
                _verdict("scope", False),
                _verdict("regression", False),
            ],
            tmp_path=tmp_path,
        )

        assert out["result"]["verdict"] == "incomplete"

    @pytest.mark.unit
    def test_a_lone_survivor_cannot_declare_the_claim_complete(
        self, tmp_path: Path
    ) -> None:
        """
        Given two judges return nothing and the third says complete
        Then the denominator is still the roster, so the panel is
        inconclusive rather than unanimous
        """
        out = _run_panel(
            SCRIPT,
            [_verdict("execution", True), None, None],
            tmp_path=tmp_path,
        )

        assert out["result"]["verdict"] == "inconclusive"
        assert out["result"]["missing"] == ["scope", "regression"]

    @pytest.mark.unit
    def test_no_verdict_at_all_is_unknown(self, tmp_path: Path) -> None:
        """
        Given every judge returns nothing
        Then the verdict is unknown and all three lenses are missing
        """
        out = _run_panel(SCRIPT, [None, None, None], tmp_path=tmp_path)

        assert out["result"]["verdict"] == "unknown"
        assert out["result"]["missing"] == ["execution", "scope", "regression"]

    @pytest.mark.unit
    def test_all_three_lenses_are_dispatched(self, tmp_path: Path) -> None:
        """
        Given a panel run
        Then three judges were asked, which is what the denominator counts
        """
        out = _run_panel(
            SCRIPT,
            [_verdict(name, True) for name in ("execution", "scope", "regression")],
            tmp_path=tmp_path,
        )

        assert out["dispatched"] == 3

    @pytest.mark.unit
    def test_a_panel_with_no_claim_does_not_start(self, tmp_path: Path) -> None:
        """
        Given args carries no claim
        Then the workflow returns started=false and dispatches no judge
        """
        out = _run_panel(SCRIPT, [], claim="", tmp_path=tmp_path)

        assert out["result"]["started"] is False
        assert out["result"]["reason"] == "no-claim"
        assert out["dispatched"] == 0
