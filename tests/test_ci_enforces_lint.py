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

from pathlib import Path

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
