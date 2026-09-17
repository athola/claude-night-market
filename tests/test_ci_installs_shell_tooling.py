"""Guard that any workflow running the full sweep installs shell tooling.

`make test` runs every plugin suite, and pensive's shell-review suite is
the one that shells out to external binaries: five pattern-detection
tests invoke `rg`, and four more call shellcheck and shfmt.

`plugin-tests.yml` installs all three for its pensive matrix job.
`trust-attestation.yml` did not, so its `make test` failed the whole
sweep on `FileNotFoundError: 'rg'` while the other 22 plugins passed,
and the four shellcheck and shfmt tests skipped without asserting. That
job signs the report it produces, which makes a silent skip worse there
than anywhere else: an attestation naming a test suite as passed is a
claim about tests that ran.

The rule discovered here is per job rather than per workflow, because
the tooling has to be present in the same runner that executes the
sweep.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

# `make test-ecosystem` runs the root suite alone and needs none of this,
# so the target has to end where the word ends.
FULL_SWEEP = re.compile(r"make test(?!\S)")

REQUIRED_TOOLS = ("shellcheck", "shfmt", "ripgrep")


def _jobs_running_the_full_sweep() -> list[tuple[str, str, dict]]:
    """Return (workflow, job name, job) for every full-sweep job."""
    found = []
    for path in sorted(WORKFLOW_DIR.glob("*.y*ml")):
        workflow = yaml.safe_load(path.read_text())
        for name, job in (workflow.get("jobs") or {}).items():
            runs = " ".join(str(step.get("run", "")) for step in job.get("steps", []))
            if FULL_SWEEP.search(runs):
                found.append((path.name, name, job))
    return found


def test_some_job_runs_the_full_sweep() -> None:
    """A rule with nothing to apply to would pass by being vacuous."""
    assert _jobs_running_the_full_sweep(), "no workflow job runs `make test`"


def test_ecosystem_workflow_is_not_treated_as_a_full_sweep() -> None:
    """`make test-ecosystem` must not match: it needs no shell tooling."""
    names = {workflow for workflow, _, _ in _jobs_running_the_full_sweep()}

    assert "ecosystem-tests.yml" not in names


@pytest.mark.parametrize("tool", REQUIRED_TOOLS)
def test_full_sweep_jobs_install_shell_tooling(tool: str) -> None:
    """Every job running the sweep installs what pensive shells out to."""
    for workflow, job_name, job in _jobs_running_the_full_sweep():
        steps = " ".join(str(step.get("run", "")) for step in job.get("steps", []))
        assert tool in steps, (
            f"{workflow} job '{job_name}' runs `make test` without installing "
            f"{tool}; pensive's shell-review suite shells out to it"
        )
