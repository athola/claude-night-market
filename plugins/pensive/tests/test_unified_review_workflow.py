"""The shipped unified-review workflow must stay loadable and referenced.

A workflow script is discovered by convention from `workflows/` at the
plugin root. Nothing at runtime reports a malformed one back to this
repository, so the contract is checked here.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "unified-review.js"
SKILL = PLUGIN_ROOT / "skills" / "unified-review" / "SKILL.md"


def test_workflow_ships_at_the_discovered_location() -> None:
    """GIVEN the plugin as installed.

    WHEN the harness looks for workflows
    THEN it finds one at workflows/ in the plugin root
    """
    assert WORKFLOW.is_file()


def test_meta_declares_name_and_description_before_any_statement() -> None:
    """GIVEN the shipped script.

    WHEN the runtime reads its meta block
    THEN meta is the first statement and carries name and description

    Only comments may precede it. This mirrors the check in
    abstract's validate_plugin.py, so a break shows up in this
    plugin's own suite rather than only in a cross-plugin gate.
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


def test_the_script_states_that_it_is_not_an_evidence_gate() -> None:
    """GIVEN a workflow that cannot run a command.

    WHEN it returns findings
    THEN the return says they are claims, not proof-of-work evidence
    """
    content = WORKFLOW.read_text()
    assert "proof-of-work evidence" in content
    assert "Reproduce before acting" in content


def test_the_skill_offers_the_workflow_as_a_second_path() -> None:
    """GIVEN the skill that owns this review.

    WHEN a reader reaches the isolation rule
    THEN both paths are named, and the workflow is not the default
    """
    skill = SKILL.read_text()
    assert "workflows/unified-review.js" in skill
    assert "a workflow never starts unasked" in skill


NODE = shutil.which("node")


def _run_review(responses: dict, tmp_path: Path) -> dict:
    """Execute the workflow body under node with stubbed runtime globals.

    The runtime wraps the body in an async function and hands it `args`,
    `log`, `phase`, `agent`, `pipeline` and `parallel`. A review agent
    answers from `responses` by dimension key. Every verifier stands
    the finding, so the result shape depends on the reviewers alone.
    """
    body = WORKFLOW.read_text(encoding="utf-8").replace(
        "export const meta", "const meta", 1
    )
    harness = tmp_path / "harness.mjs"
    harness.write_text(
        "const RESPONSES = " + json.dumps(responses) + ";\n"
        "const logs = [];\nconst prompts = {};\n"
        "function log(message) { logs.push(String(message)); }\n"
        "function phase() {}\n"
        "async function agent(prompt, options) {\n"
        "  prompts[options.label] = prompt;\n"
        "  if (options.label.startsWith('review:')) {\n"
        "    const key = options.label.slice('review:'.length);\n"
        "    return key in RESPONSES ? RESPONSES[key] : { findings: [] };\n"
        "  }\n"
        "  return { refuted: false, reason: 'stands' };\n"
        "}\n"
        "async function parallel(thunks) "
        "{ return Promise.all(thunks.map((thunk) => thunk())); }\n"
        "async function pipeline(items, first, second) {\n"
        "  return Promise.all(items.map(async (item) => "
        "second(await first(item), item)));\n"
        "}\n"
        "const args = {};\n"
        "async function run() {\n" + body + "\n}\n"
        "run().then((result) => "
        "console.log(JSON.stringify({ result, logs, prompts })));\n",
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


@pytest.mark.skipif(NODE is None, reason="node is not installed")
class TestAReviewerCanDecline:
    """Scenario: a reviewer that cannot assess says so.

    A referee without the time or expertise should decline rather than
    send a report (Caldara and Fernandez-Villaverde 2026, section 6).
    Before this, the only way out was an empty findings list, which
    the return reports as a reviewed, clean dimension.
    """

    def test_a_declined_dimension_is_unreviewed_and_carries_its_reason(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the security reviewer declines with a reason.

        WHEN the workflow returns
        THEN security is listed under declined with that reason
        AND it is not listed as reviewed
        """
        reason = "the diff touches only generated lockfiles"
        out = _run_review({"security": {"findings": [], "declined": reason}}, tmp_path)
        dims = out["result"]["dimensions"]
        assert dims["declined"] == [{"dimension": "security", "reason": reason}]
        assert "security" not in dims["reviewed"]
        assert any("security" in line and "declined" in line for line in out["logs"])

    def test_an_empty_list_without_a_decline_still_counts_as_reviewed(
        self, tmp_path: Path
    ) -> None:
        """GIVEN every reviewer returns no findings and no decline.

        WHEN the workflow returns
        THEN every dimension is reviewed and none is declined
        """
        out = _run_review({}, tmp_path)
        dims = out["result"]["dimensions"]
        assert dims["declined"] == []
        assert dims["reviewed"] == dims["selected"]

    def test_findings_sent_with_a_decline_are_still_verified(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a reviewer declines part of its dimension and reports a finding.

        WHEN the workflow returns
        THEN the finding is verified and confirmed rather than dropped
        AND the dimension is still listed as declined, not reviewed
        """
        finding = {
            "title": "token compared with ==",
            "file": "auth.py",
            "line": 12,
            "severity": "blocking",
            "why": "timing leak",
        }
        out = _run_review(
            {
                "security": {
                    "findings": [finding],
                    "declined": "no access to the vault code",
                }
            },
            tmp_path,
        )
        result = out["result"]
        assert [f["title"] for f in result["confirmed"]] == ["token compared with =="]
        assert result["dimensions"]["declined"][0]["dimension"] == "security"
        assert "security" not in result["dimensions"]["reviewed"]

    def test_the_decline_prompt_keeps_the_required_findings_list(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the schema requires a findings list.

        WHEN a reviewer is told how to decline
        THEN the prompt asks for an empty list beside the reason
        """
        out = _run_review({}, tmp_path)
        assert "return an empty findings list" in out["prompts"]["review:bugs"]

    def test_the_reviewer_prompt_offers_the_decline(self, tmp_path: Path) -> None:
        """GIVEN any review dimension.

        WHEN its reviewer is prompted
        THEN the prompt names the declined field
        """
        out = _run_review({}, tmp_path)
        assert "declined" in out["prompts"]["review:bugs"]

    def test_a_dead_reviewer_and_a_decline_are_reported_apart(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the bugs reviewer dies and the security reviewer declines.

        WHEN the workflow returns
        THEN bugs is missing, security is declined
        AND neither is listed as reviewed
        """
        out = _run_review(
            {"bugs": None, "security": {"findings": [], "declined": "out of depth"}},
            tmp_path,
        )
        dims = out["result"]["dimensions"]
        assert dims["missing"] == ["bugs"]
        assert [d["dimension"] for d in dims["declined"]] == ["security"]
        assert dims["reviewed"] == ["architecture", "tests"]

    def test_an_empty_decline_reason_is_not_a_decline(self, tmp_path: Path) -> None:
        """GIVEN a reviewer fills the optional declined field with an empty string.

        WHEN the workflow returns
        THEN the dimension counts as reviewed and none is declined

        An empty reason names nothing the operator could act on.
        """
        out = _run_review({"tests": {"findings": [], "declined": ""}}, tmp_path)
        dims = out["result"]["dimensions"]
        assert dims["declined"] == []
        assert "tests" in dims["reviewed"]

    def test_the_skill_says_a_declined_dimension_is_unreviewed(self) -> None:
        """GIVEN the unified-review skill.

        WHEN a reader looks up what a decline means
        THEN the skill names it as unreviewed
        """
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        assert (
            "returns `declined`, and the workflow reports that dimension as unreviewed"
            in text
        )


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_the_architecture_reviewer_must_name_what_a_departure_costs(
    tmp_path: Path,
) -> None:
    """GIVEN the architecture dimension.

    WHEN its reviewer is prompted
    THEN a departure from a standard counts only with its cost named

    Innovative work departs from standards by construction, so a
    reviewer that lists departures is biased against it (Caldara and
    Fernandez-Villaverde 2026, section 4).
    """
    out = _run_review({}, tmp_path)
    prompt = out["prompts"]["review:architecture"]
    assert "A departure is a finding only when you name its cost." in prompt


def test_lens_agreement_is_not_reported_as_independent_confirmation() -> None:
    """GIVEN three verifier lenses that run on one model.

    WHEN the workflow and its skill describe a standing finding
    THEN both say agreement among lenses is not independent evidence

    Ten LLM judges carried about 3.5 judges' worth of independent
    information in arXiv 2609.22512, because their errors correlate.
    """
    clause = "Lens votes share one model and their errors correlate."
    assert clause in WORKFLOW.read_text(encoding="utf-8")
    assert clause in SKILL.read_text(encoding="utf-8")
