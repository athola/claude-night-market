"""The Security Scan can fail on a high-severity finding, and its comment posts.

Every scanner step carried ``continue-on-error: true``, so no finding
failed the job. The PR comment had no ``pull-requests: write``, and its
``createComment`` was not awaited, so the 403 became an unhandled
rejection the ``catch`` never saw. ``osv-report.json`` was uploaded but
nothing wrote it.
"""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "security.yml"
)


def _job() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]["security-scan"]


def _step(name: str) -> dict:
    return next(s for s in _job()["steps"] if s.get("name") == name)


def test_a_high_severity_bandit_finding_fails_the_job() -> None:
    gate = _step("Gate on high-severity Bandit findings")
    assert "-lll" in gate["run"]
    assert "|| true" not in gate["run"]
    assert not gate.get("continue-on-error")


def test_the_pr_comment_has_permission_to_post() -> None:
    assert _job()["permissions"].get("pull-requests") == "write"


def test_the_pr_comment_awaits_the_api_call() -> None:
    script = _step("Comment PR with security results")["with"]["script"]
    assert "await github.rest.issues.createComment" in script


def test_only_reports_a_step_writes_are_uploaded() -> None:
    paths = _step("Upload security scan artifacts")["with"]["path"]
    assert "osv-report.json" not in paths
