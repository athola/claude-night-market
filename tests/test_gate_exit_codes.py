"""Guard that no quality gate reports success while its checker failed.

``plugins/abstract/config/make/python.mk`` wraps its own checkers so a
failure propagates::

    @$(MYPY) $(MYPY_TARGETS) || { echo "[WARN] Type checking failed"; exit 1; }

It then runs each plugin's injected hook bare::

    ifneq ($(strip $(TYPECHECK_EXTRA)),)
        @$(TYPECHECK_EXTRA)
    endif

(Recipe lines are tabs in the real file; spaces are used here so this
docstring keeps a single indent style.)

The extension point is unguarded, and conjure filled it with ``ty check
scripts/ || true``. ``ty`` found 17 diagnostics on every run and printed
them, the recipe exited 0 anyway, and the orchestrator reported
``* Type checking passed``. A gate that prints errors and then calls
itself green is worse than no gate: it converts a real finding into
evidence that the code is clean.

conserve had the same shape twice over, in a target named ``validate-all``
that could not fail because both of its checks ended in ``|| true``.

There is no way to make this unrepresentable. The value of a Make variable
is arbitrary shell, so any wrapper the framework adds runs *after* the
suppression has already happened. A guard is the available tool.

Cleanup recipes are excluded. ``rm -rf .mypy_cache || true`` is correct:
removing a path that may not exist is not a check, and the checker name
appears there only as a cache directory.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

# Checkers whose exit code is the entire point of running them. Matched
# either as a literal command or through the Make variable the shared
# includes invoke them by.
CHECKER_PATTERNS = (
    r"\bty\s+check\b",
    r"\bmypy\b",
    r"\bruff\s+check\b",
    r"\bbandit\b",
    r"\bpytest\b",
    r"\bpip\s+check\b",
    r"\bpre-commit\s+run\b",
    r"\bsafety\s+check\b",
    r"\bsemgrep\b",
    r"\$\((?:PYTEST|MYPY|RUFF|BANDIT|TY|SAFETY|SEMGREP)\)",
    # Structure validators and the audit one-liners are gates too. The root
    # ``validate-all`` loop ran validate_plugin.py over every plugin and
    # echoed "(validation failed)" in place of failing, and five abstract
    # audit targets ended in ``|| echo "... completed"``.
    r"validate_plugin\.py",
    r"\$\(UV_RUN_PYTHON\) -c",
    r"slop_score\.py",
    # Root ``plugin-check`` delegates to each plugin and swallowed the result.
    r"\$\(MAKE\) -C \S+ (?:plugin-check|test|lint|check)\b",
)
CHECKER_RE = re.compile("|".join(CHECKER_PATTERNS))

# Trailing ``|| true`` is the suppression this guard was written for. Anchored
# to end-of-line so a mid-pipeline ``|| true`` feeding a later real check is not
# swept up.
#
# ``|| echo "..."`` and ``|| :`` belong here too, and matching only ``|| true``
# left the door open. Thirteen sites used the echo form, including
# ``SECURITY_EXTRA = $(UV_RUN) safety check || echo "[WARNING] Safety check
# unavailable"`` in pensive and parseltongue: a security scanner wired into
# ``make security`` that could not fail, in pensive's case because ``safety``
# was never a declared dependency and the command had never once run. The echo
# form is the worse of the two, because it replaces the checker's verdict with a
# sentence that sounds like a status report. parseltongue's ``$(RUFF) check
# --statistics 2>/dev/null || echo "Linting clean or ruff not configured"``
# printed "Linting clean" on precisely the path where ruff had found problems.
#
# Detecting an optional tool is still legitimate; it just has to be a real
# detection. ``@if $(UV_RUN) python -c "import pytest_benchmark"; then ...`` is
# excluded below because an ``if`` consumes the exit code rather than dropping
# it, and the message it prints is then true.
SUPPRESSION_RE = re.compile(r"\|\|\s*(?:true|:|echo\b.*)\s*;?\s*$")

# ``@if command -v mutmut ...; then`` consumes the verdict instead of discarding
# it, so the checker inside the branch is still able to fail the build.
CONDITION_RE = re.compile(r"^\s*[-@]*\s*(?:if|elif)\b")

# ``rm -rf .mypy_cache 2>/dev/null || true`` and friends.
CLEANUP_RE = re.compile(r"^\s*[-@]*\s*rm\b")

# A coverage run whose failure triggers a second, coverage-free pytest run
# reports the second run's verdict. ``--cov-fail-under`` could never fail
# ``test-coverage`` in python.mk: the tests passed again without the
# threshold and the target exited 0.
FALLBACK_RERUN_RE = re.compile(r"\|\|\s*\{[^}]*\$\(PYTEST\)")

# Targets in python.mk whose recipe runs pytest. A plugin ``test`` target
# that names one of these, or runs ``$(PYTEST)`` itself, runs its tests.
PYTEST_TARGETS = frozenset({"test-unit", "unit-tests", "test-coverage", "test-quick"})


def _makefiles() -> list[Path]:
    """Every plugin Makefile, the shared includes, and the root Makefile."""
    found = sorted(PLUGINS_DIR.glob("*/Makefile"))
    found += sorted((PLUGINS_DIR / "abstract" / "config" / "make").glob("*.mk"))
    found.append(REPO_ROOT / "Makefile")
    return found


def _targets(makefile: Path) -> dict[str, tuple[list[str], list[str]]]:
    """Map each target to (prerequisites, recipe lines)."""
    targets: dict[str, tuple[list[str], list[str]]] = {}
    current: str | None = None
    for raw in makefile.read_text().splitlines():
        if raw.startswith("\t"):
            if current is not None:
                targets[current][1].append(raw.strip())
            continue
        current = None
        head = raw.split("#", 1)[0]
        if (
            ":" not in head
            or head.startswith((" ", "."))
            or "=" in head.split(":", 1)[0]
        ):
            continue
        names, _, prereqs = head.partition(":")
        if prereqs.startswith(":"):
            prereqs = prereqs[1:]
        for name in names.split():
            targets[name] = (prereqs.split(), [])
            current = name
    return targets


def _test_target_runs_pytest(makefile: Path) -> bool:
    """Whether ``make test`` in this plugin reaches a pytest invocation."""
    targets = _targets(makefile)
    if "test" not in targets:
        return True
    prereqs, recipe = targets["test"]
    if any("$(PYTEST)" in line or "pytest" in line for line in recipe):
        return True
    for name in prereqs:
        if name in PYTEST_TARGETS:
            return True
        _, sub_recipe = targets.get(name, ([], []))
        if any("$(PYTEST)" in line or "pytest" in line for line in sub_recipe):
            return True
    return False


def _suppressed_checks(makefile: Path) -> list[tuple[int, str]]:
    """Lines that run a checker and then discard its exit code."""
    offenders = []
    for number, raw in enumerate(makefile.read_text().splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line or CLEANUP_RE.match(line) or CONDITION_RE.match(line):
            continue
        if CHECKER_RE.search(line) and SUPPRESSION_RE.search(line):
            offenders.append((number, line.strip()))
        elif FALLBACK_RERUN_RE.search(line):
            offenders.append((number, line.strip()))
    return offenders


def test_discovery_finds_makefiles() -> None:
    """An empty parametrize list would make the gate below vacuously green."""
    assert len(_makefiles()) > 1


@pytest.mark.parametrize("makefile", _makefiles(), ids=lambda p: p.parent.name)
def test_checker_exit_codes_are_not_suppressed(makefile: Path) -> None:
    """A recipe that runs a checker must let that checker fail the build."""
    offenders = _suppressed_checks(makefile)
    rendered = "\n".join(f"  {makefile.name}:{n}: {text}" for n, text in offenders)
    assert not offenders, (
        f"{makefile.parent.name} runs a quality checker and then discards its "
        f"exit code with '|| true':\n{rendered}\n"
        f"The checker's findings still print, so the recipe looks like it ran, "
        f"but the target exits 0 and the plugin is reported as passing. Either "
        f"let the checker fail the build, or stop running it."
    )


def _python_plugin_makefiles() -> list[Path]:
    """Plugin Makefiles that pull in python.mk, so they own a test suite."""
    return [m for m in PLUGINS_DIR.glob("*/Makefile") if "python.mk" in m.read_text()]


@pytest.mark.parametrize(
    "makefile", _python_plugin_makefiles(), ids=lambda p: p.parent.name
)
def test_plugin_test_target_runs_its_tests(makefile: Path) -> None:
    """``make test`` must reach pytest, not only lint and typecheck.

    conserve's ``test: check lint type-check security`` ran no pytest, so
    38 test files were skipped by root ``make test``, ``make conserve-test``,
    the pre-commit test hook and the trust attestation, and the plugin
    printed "All checks passed!" on every run.
    """
    assert _test_target_runs_pytest(makefile), (
        f"{makefile.parent.name}/Makefile: the `test` target neither runs "
        f"$(PYTEST) nor names a prerequisite that does ({sorted(PYTEST_TARGETS)}), "
        f"so the plugin's tests never run under `make test`."
    )


# ---------------------------------------------------------------------------
# Script-level gates
#
# Stripping '|| true' from a recipe accomplishes nothing when the command it
# guarded cannot fail in the first place. conjure's ``_verify_service`` computed
# ``is_available``, printed "FAILED", and returned None; the process still
# exited 0. That is the same defect as '|| true', moved one layer down and made
# harder to see, because now nothing in the output contradicts the green check.
#
# Scoped to scripts that advertise themselves as validators or verifiers. A
# script that only reports (``--status``, ``--report``) is not covered: exiting
# nonzero because a report contained bad news would be its own bug.
# ---------------------------------------------------------------------------

VENDORED_PARTS = {".uv-cache", ".venv", "__pycache__", "node_modules", "tests"}

# argparse flags whose presence marks a script as making a pass/fail judgment.
GATE_FLAGS = ('"--validate"', "'--validate'", '"--verify"', "'--verify'")
GATE_FILENAMES = ("_validator.py", "_verifier.py")


def _is_gate_script(path: Path, source: str) -> bool:
    """True if the script claims to render a verdict, not merely a report."""
    if path.name.endswith(GATE_FILENAMES):
        return True
    return any(flag in source for flag in GATE_FLAGS)


def _terminates_nonzero(tree: ast.Module) -> bool:
    """True if any path can end the process with a nonzero status.

    Unknown exit codes (a variable, or ``sys.exit(main())``) count as capable:
    the guard exists to catch scripts with *no* failure path at all, not to
    prove any particular path is reachable.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = (
                fn.attr
                if isinstance(fn, ast.Attribute)
                else fn.id
                if isinstance(fn, ast.Name)
                else ""
            )
            if name in {"exit", "_exit"} and node.args:
                arg = node.args[0]
                # Only a literal 0/None is provably a success-only exit.
                if isinstance(arg, ast.Constant) and arg.value in (0, None):
                    continue
                return True
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            target = exc.func if isinstance(exc, ast.Call) else exc
            if isinstance(target, ast.Name) and target.id == "SystemExit":
                return True
    return False


def _gate_scripts() -> list[Path]:
    """First-party CLI scripts that advertise a validate or verify mode."""
    found = []
    for path in sorted(PLUGINS_DIR.glob("*/**/*.py")):
        if VENDORED_PARTS.intersection(path.parts):
            continue
        try:
            source = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "__main__" not in source:
            continue
        if _is_gate_script(path, source):
            found.append(path)
    return found


def test_gate_script_discovery_is_not_empty() -> None:
    """An empty parametrize list would make the gate below vacuously green."""
    assert len(_gate_scripts()) > 1


@pytest.mark.parametrize(
    "script",
    _gate_scripts(),
    ids=lambda p: f"{p.parent.parent.name}-{p.stem}",
)
def test_validators_can_actually_fail(script: Path) -> None:
    """A script offering --validate/--verify must be able to exit nonzero."""
    tree = ast.parse(script.read_text())
    relative = script.relative_to(REPO_ROOT)
    assert _terminates_nonzero(tree), (
        f"{relative} exposes a validate/verify mode but has no path that exits "
        f"nonzero, so it reports every run as a success. Callers that check its "
        f"exit code are reading a constant. Either exit nonzero when the "
        f"verdict is negative, or stop presenting it as a check."
    )
