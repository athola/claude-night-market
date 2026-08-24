"""Guard that CI runs the ruff lint gate, not only pre-commit.

``make lint`` and the pre-commit ruff hooks resolve each file against its
own plugin's ``pyproject.toml``, which extends the root floor. That union
is the strongest rule set the repo defines, and it fires only for people
who have pre-commit installed. ``docs/quality-gates.md`` claimed CI ran
``make lint``; it ran ``make typecheck`` and ``make test-ecosystem`` only,
so the lint gate stopped at the contributor's machine.

The failure is silent in the same way the path-filter gap in
``test_ci_covers_ecosystem_gates.py`` is silent: a gate nobody runs does
not fail, it just never reports. This test asserts a workflow actually
invokes the lint gate, so removing that step turns the suite red rather
than quietly narrowing enforcement.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import tomllib
import yaml

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def _run_steps() -> list[str]:
    """Collect every ``run:`` script across all workflow jobs."""
    scripts: list[str] = []
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        try:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    scripts.append(step["run"])
    return scripts


def test_a_workflow_runs_the_lint_gate() -> None:
    """Some workflow invokes make lint or the per-plugin ruff sweep."""
    scripts = _run_steps()

    invokes_lint = [
        s
        for s in scripts
        if "make lint" in s
        or "run-plugin-lint.sh" in s
        or ("ruff check" in s and "--select" not in s)
    ]

    assert invokes_lint, (
        "no workflow runs the lint gate; the union rule set would be "
        "enforced only on machines with pre-commit installed"
    )


def _lint_workflows() -> list[tuple[Path, dict]]:
    """Every workflow document whose steps invoke the lint gate."""
    found: list[tuple[Path, dict]] = []
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        try:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not (isinstance(step, dict) and isinstance(step.get("run"), str)):
                    continue
                script = step["run"]
                if (
                    "make lint" in script
                    or "run-plugin-lint.sh" in script
                    or ("ruff check" in script and "--select" not in script)
                ):
                    found.append((wf, doc))
                    break
            else:
                continue
            break
    return found


def _triggers(doc: dict) -> dict:
    """The workflow's ``on:`` mapping.

    YAML 1.1 reads a bare ``on`` key as the boolean ``True``, so the
    parsed document keys it under ``True`` and not the string. Both are
    checked, because a quoted ``"on":`` is equally valid YAML.
    """
    for key in (True, "on"):
        value = doc.get(key)
        if isinstance(value, dict):
            return value
    return {}


def test_the_lint_gate_runs_on_pull_requests() -> None:
    """The lint workflow must carry a ``pull_request:`` trigger.

    Nothing read the ``on:`` block, so deleting the entire
    ``pull_request:`` trigger left this module green while the gate it
    guards stopped firing before merge. That is the same silent
    narrowing the module docstring describes, one level up: the step is
    present and correct, and no event ever reaches it.
    """
    workflows = _lint_workflows()
    assert workflows, "no workflow invokes the lint gate"

    without = [wf.name for wf, doc in workflows if "pull_request" not in _triggers(doc)]
    assert len(without) < len(workflows), (
        "no workflow that runs the lint gate is triggered by pull_request, "
        f"so the union rule set is never enforced before merge: {without}"
    )


def test_ci_lint_does_not_pin_the_root_config() -> None:
    """The CI lint step must not pass --config, which would collapse the
    per-plugin union back to the root subset it replaced.
    """
    for script in _run_steps():
        if "ruff check" not in script:
            continue
        if "--select" in script:  # a targeted single-rule probe, not the gate
            continue
        assert "--config" not in script, (
            f"CI lint pins a config and loses the per-plugin union:\n{script}"
        )


def _dev_extra_tools() -> set[str]:
    """Console-script names provided only by the ``dev`` optional extra.

    ``uv run`` resolves the default dependency set. Anything declared under
    ``[project.optional-dependencies] dev`` is absent unless the step also
    passes ``--extra dev``, so these are the names that need the flag.
    """
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    doc = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    dev = doc["project"]["optional-dependencies"]["dev"]
    return {re.split(r"[><=!~\[]", spec, maxsplit=1)[0].strip() for spec in dev}


def _uv_run_invocations(script: str) -> list[list[str]]:
    """Split a ``run:`` script into the token lists of its ``uv run`` calls.

    Returns one token list per ``uv run`` invocation, starting at the token
    after ``run``. Lines that shell out to ``make`` are excluded: the
    Makefile prepends ``.uv-tools`` to PATH and carries its own contract.
    """
    calls: list[list[str]] = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "uv run" not in stripped:
            continue
        if re.search(r"\bmake\b", stripped):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            continue
        for i in range(len(tokens) - 1):
            if tokens[i] == "uv" and tokens[i + 1] == "run":
                calls.append(tokens[i + 2 :])
    return calls


def test_ci_installs_the_dev_extra_before_running_its_tools() -> None:
    """A ``uv run`` of a dev-extra tool must also pass ``--extra dev``.

    Without the flag uv builds an environment that lacks the tool and the
    step dies on "Failed to spawn", reporting failure without having
    checked anything. That is the silent-gate failure this module exists
    to prevent, one level down: the step is present but cannot run.
    """
    tools = _dev_extra_tools()
    offenders: list[str] = []

    for script in _run_steps():
        for tokens in _uv_run_invocations(script):
            # Exact token match, never substring: a path like
            # --paths-to-mutate=plugins/black/x names a dev tool without
            # invoking one, and a guard that cries wolf gets deleted.
            reached = sorted({tok for tok in tokens if tok in tools})
            if not reached:
                continue
            flagged = any(
                tokens[i] == "--extra" and tokens[i + 1] == "dev"
                for i in range(len(tokens) - 1)
            ) or any(tok in ("--extra=dev", "--all-extras") for tok in tokens)
            if not flagged:
                offenders.append(
                    f"  uv run {' '.join(tokens)}  (needs: {', '.join(reached)})"
                )

    assert not offenders, (
        "uv run reaches for a dev-extra tool without --extra dev:\n"
        + "\n".join(offenders)
    )


def _piped_run_steps() -> list[tuple[str, str]]:
    """Every ``run:`` script containing a pipeline, with its workflow name."""
    found: list[tuple[str, str]] = []
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        try:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not (isinstance(step, dict) and isinstance(step.get("run"), str)):
                    continue
                if "|" in step["run"]:
                    found.append((wf.name, step["run"]))
    return found


#: Commands whose exit code is the thing the step exists to report. A
#: pipeline that starts with one of these and does not set pipefail
#: reports the last stage's status instead, which is usually `tee`.
_GATE_COMMANDS = ("make test", "make lint", "make typecheck", "pytest", "ruff check")


def test_a_gate_piped_into_another_command_still_reports_its_own_failure() -> None:
    """A gate in a pipeline needs ``set -o pipefail`` to be able to fail.

    GitHub runs `run:` blocks under `bash -e`, which does not include
    `pipefail`. `make test 2>&1 | tee test-output.txt` therefore exits
    with tee's status, always 0, and the trust-attestation workflow
    signed an SLSA attestation over a report built from a red suite.
    """
    offenders: list[str] = []

    for name, script in _piped_run_steps():
        for line in script.splitlines():
            stripped = line.strip()
            if "|" not in stripped or stripped.startswith("#"):
                continue
            head = stripped.split("|", 1)[0]
            if not any(gate in head for gate in _GATE_COMMANDS):
                continue
            if "pipefail" not in script:
                offenders.append(f"  {name}: {stripped}")

    assert not offenders, (
        "a quality gate is piped without `set -o pipefail`, so the step "
        "reports the pipeline's last stage rather than the gate:\n"
        + "\n".join(offenders)
    )
