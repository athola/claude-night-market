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
)
CHECKER_RE = re.compile("|".join(CHECKER_PATTERNS))

# Trailing ``|| true`` is the suppression this guard exists for. Anchored to
# end-of-line so a mid-pipeline ``|| true`` feeding a later real check is not
# swept up.
SUPPRESSION_RE = re.compile(r"\|\|\s*true\s*;?\s*$")

# ``rm -rf .mypy_cache 2>/dev/null || true`` and friends.
CLEANUP_RE = re.compile(r"^\s*[-@]*\s*rm\b")


def _makefiles() -> list[Path]:
    """Every plugin Makefile plus the shared includes they pull in."""
    found = sorted(PLUGINS_DIR.glob("*/Makefile"))
    found += sorted((PLUGINS_DIR / "abstract" / "config" / "make").glob("*.mk"))
    return found


def _suppressed_checks(makefile: Path) -> list[tuple[int, str]]:
    """Lines that run a checker and then discard its exit code."""
    offenders = []
    for number, raw in enumerate(makefile.read_text().splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line or CLEANUP_RE.match(line):
            continue
        if CHECKER_RE.search(line) and SUPPRESSION_RE.search(line):
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
