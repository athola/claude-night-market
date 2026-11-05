"""Guard that the Python 3.9 syntax gate can fail.

``python39-compat.yml`` runs one ruff rule over every hooks directory to
catch ``X | Y`` annotations that raise ``TypeError`` at import time on
system Python 3.9. It selected UP007, which never fires on that input:
UP007 rewrites ``Optional[X]`` into ``X | Y``, the opposite direction, so
``def f(x: int | None)`` exited 0 and the gate reported green on exactly
the code it was written to stop. FA102 is the rule that flags a PEP 604
union in a module targeting py39 without ``from __future__ import
annotations``.

The probe test runs ruff on a file carrying the defect, so a rule swap
that reintroduces a gate unable to fail turns this red.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import tomllib
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "python39-compat.yml"

UNGUARDED_UNION = "def f(x: int | None) -> int | None:\n    return x\n"


def _syntax_step_command() -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["syntax-check"]["steps"]
    commands = [str(step.get("run", "")) for step in steps]
    ruff_commands = [c for c in commands if "ruff check" in c]
    assert ruff_commands, "python39-compat.yml has no ruff check step"
    return ruff_commands[0]


def _run_ruff(select: str, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--select",
            select,
            "--target-version",
            "py39",
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_python39_gate_selects_fa102() -> None:
    """The workflow must select the rule that flags unguarded unions."""
    command = _syntax_step_command()
    assert "--select FA102" in command, (
        f"the py39 syntax step does not select FA102:\n{command}"
    )
    assert "UP007" not in command, (
        "UP007 exits 0 on `int | None` at py39; selecting it alone makes "
        "the gate unable to fail"
    )


def test_python39_gate_targets_py39() -> None:
    assert "--target-version py39" in _syntax_step_command()


@pytest.mark.skipif(
    importlib.util.find_spec("ruff") is None, reason="ruff is not installed"
)
def test_fa102_fails_on_an_unguarded_union(tmp_path: Path) -> None:
    """GIVEN a module with a PEP 604 union and no future import
    WHEN ruff checks it with FA102 at py39
    THEN it exits nonzero, which is what lets the gate fail.
    """
    probe = tmp_path / "probe.py"
    probe.write_text(UNGUARDED_UNION, encoding="utf-8")

    outcome = _run_ruff("FA102", probe)

    assert outcome.returncode == 1, outcome.stdout + outcome.stderr
    assert "FA102" in outcome.stdout


@pytest.mark.skipif(
    importlib.util.find_spec("ruff") is None, reason="ruff is not installed"
)
def test_fa102_passes_once_the_future_import_is_present(tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(
        "from __future__ import annotations\n\n" + UNGUARDED_UNION, encoding="utf-8"
    )

    assert _run_ruff("FA102", probe).returncode == 0


def test_root_ruff_config_selects_fa102() -> None:
    """Catch the defect at edit time, before the workflow runs.

    The root config targets py39 and every plugin config extends it or,
    like cartograph, has no ``[tool.ruff]`` table and falls through to it.
    """
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lint = config["tool"]["ruff"]["lint"]
    assert "FA102" in lint["select"]


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_python39_gate_runs_when_a_hook_import_chain_changes(event: str) -> None:
    """Hooks import plugin `src/` packages, so a `src/` change can break 3.9."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads the bare key `on` as the boolean True.
    assert "plugins/*/src/**" in workflow[True][event]["paths"]


def test_python39_gate_imports_every_registered_hook_under_3_9() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["hook-imports"]
    text = " ".join(
        str(step.get("run", "")) + str(step.get("with", "")) for step in job["steps"]
    )
    assert "tests/test_hooks_import_without_project_deps.py" in text
    assert "3.9" in text
