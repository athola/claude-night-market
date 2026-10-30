"""Write scopes go to the job that writes, not to the whole workflow.

``cross-framework-publish.yml`` granted ``contents: write`` at the top, so
two jobs that only read an artifact and write a step summary could push
to the repository. Only ``build-and-release`` creates a release.
"""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "cross-framework-publish.yml"
)


def test_the_workflow_default_is_read_only() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    assert workflow["permissions"] == {"contents": "read"}


def test_only_the_release_job_can_write_contents() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    writers = sorted(
        name
        for name, job in jobs.items()
        if (job.get("permissions") or {}).get("contents") == "write"
    )
    assert writers == ["build-and-release"]
