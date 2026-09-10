"""Guard that the lint gate reports findings instead of rewriting the tree.

``scripts/run-plugin-lint.sh`` passed ``--fix`` to ruff on both of its
fallback paths, the per-plugin ``uv run ruff`` and the global one. Anyone
who ran it to see what was wrong got a rewritten working tree and an
empty finding list, so the gate's own output could never disagree with
the code it had just edited. ``check-all-quality.sh`` had the mirror
defect: ``--fix`` printed "Running with auto-fix enabled" and then
invoked the lint runner without the flag, so its only caller that wanted
rewriting was the one that did not get it.

``make lint`` does not reach this script; it calls ruff directly from the
root Makefile. ``check-all-quality.sh`` is the script's only caller in
the repo, which is why both are driven here.

The global-ruff branch carried a third shape, and it is the one worth
naming carefully. ``ruff check "$dir" | head -20`` puts the checker in a
pipeline, where the ``if`` reads the last stage's status unless
``pipefail`` is set. It was set, so the branch was correct; the pipe was
load-bearing on a flag two hundred lines away. Dropping the pipe made the
branch independent of it. The guard below fails when both go: it is a
regression test for the pair, not for either alone.

Each test below drives the real script under a fake project root with
recording shims on PATH, so it asserts what the script *invokes*, not
what its source text looks like.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LINT_RUNNER = REPO_ROOT / "scripts" / "run-plugin-lint.sh"
QUALITY_GATE = REPO_ROOT / "scripts" / "check-all-quality.sh"

#: A shim records the argv it was called with, one invocation per line,
#: then exits with the status the test asked for.
SHIM = """#!/bin/sh
printf '%s\\n' "$*" >> "{log}"
exit {status}
"""


def _write_shim(bin_dir: Path, name: str, log: Path, status: int = 0) -> None:
    """Install a recording stand-in for ``name`` in ``bin_dir``."""
    path = bin_dir / name
    path.write_text(SHIM.format(log=log, status=status), encoding="utf-8")
    path.chmod(0o755)


def _fake_root(tmp_path: Path, script: Path) -> tuple[Path, Path, Path]:
    """A project root holding a copy of ``script``, plus its bin and log.

    The scripts derive PROJECT_ROOT from their own location, so copying
    one into ``<tmp>/scripts/`` is what makes ``<tmp>`` the root they
    walk. Returns the root, the PATH directory for shims, and the log
    file the shims append to.
    """
    root = tmp_path / "root"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(script, root / "scripts" / script.name)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    return root, bin_dir, tmp_path / "invocations.log"


def _run(
    root: Path, name: str, bin_dir: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a copied gate script with only ``bin_dir`` ahead on PATH."""
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        [str(root / "scripts" / name), *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _plugin_with_ruff_config(root: Path, name: str) -> Path:
    """A plugin the runner routes down the ``uv run ruff`` branch.

    It needs a ``scripts`` or ``src`` directory to not be skipped, no
    Makefile ``lint:`` target, and the string ``ruff`` in its
    pyproject.
    """
    plugin = root / "plugins" / name
    (plugin / "src").mkdir(parents=True)
    (plugin / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 88\n", encoding="utf-8"
    )
    return plugin


def _lines(log: Path) -> list[str]:
    """Recorded invocations, or an empty list if nothing ran."""
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


def test_default_lint_run_does_not_ask_ruff_to_rewrite_the_tree(tmp_path: Path) -> None:
    """A bare run must invoke ruff without ``--fix``.

    GIVEN a plugin whose pyproject configures ruff
    WHEN run-plugin-lint.sh runs with no flags
    THEN the ruff invocation carries no --fix, so the gate reports the
         findings rather than editing them away
    """
    root, bin_dir, log = _fake_root(tmp_path, LINT_RUNNER)
    _plugin_with_ruff_config(root, "probe")
    _write_shim(bin_dir, "uv", log)

    _run(root, LINT_RUNNER.name, bin_dir, "probe")

    invocations = _lines(log)
    assert invocations, "the runner never reached ruff"
    assert any("ruff check" in line for line in invocations), invocations
    assert not any("--fix" in line for line in invocations), (
        f"the default lint run rewrites the tree: {invocations}"
    )


def test_lint_run_forwards_fix_when_it_is_asked_for(tmp_path: Path) -> None:
    """``--fix`` is opt-in, and opting in must still reach ruff.

    GIVEN the same plugin
    WHEN run-plugin-lint.sh runs with --fix
    THEN ruff is invoked with --fix
    AND --fix is not passed on as a plugin name
    """
    root, bin_dir, log = _fake_root(tmp_path, LINT_RUNNER)
    _plugin_with_ruff_config(root, "probe")
    _write_shim(bin_dir, "uv", log)

    result = _run(root, LINT_RUNNER.name, bin_dir, "--fix", "probe")

    invocations = _lines(log)
    assert any("--fix" in line for line in invocations), invocations
    assert "Plugin not found: --fix" not in result.stdout, result.stdout


def test_lint_runner_fails_when_the_global_ruff_branch_finds_problems(
    tmp_path: Path,
) -> None:
    """A failing ruff must fail the script.

    GIVEN a plugin with no pyproject and no Makefile, so the runner
          falls through to the global ruff on PATH
    WHEN that ruff exits non-zero
    THEN the script exits non-zero and names the plugin as failed

    Three probes, all run: pipe with pipefail is green (master), pipe
    with ``set -eu`` is red -- "All linting checks passed" at exit 0 --
    and no pipe with ``set -eu`` is green. So neither change fails alone
    and the pair does, which is the coupling this test pins.
    """
    root, bin_dir, log = _fake_root(tmp_path, LINT_RUNNER)
    plugin = root / "plugins" / "probe"
    (plugin / "scripts").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    _write_shim(bin_dir, "ruff", log, status=1)

    result = _run(root, LINT_RUNNER.name, bin_dir, "probe")

    assert _lines(log), "the runner never reached ruff"
    assert result.returncode != 0, (
        f"ruff failed and the lint gate still reported success:\n{result.stdout}"
    )
    assert "Failed" in result.stdout, result.stdout


@pytest.mark.parametrize(
    ("flag", "expect_fix"),
    [(None, False), ("--fix", True)],
)
def test_quality_gate_forwards_fix_to_the_lint_runner(
    tmp_path: Path, flag: str | None, expect_fix: bool
) -> None:
    """``check-all-quality.sh --fix`` must reach the lint runner.

    GIVEN stand-ins for the three sub-runners the gate shells out to
    WHEN check-all-quality.sh runs with and without --fix
    THEN the lint runner receives --fix exactly when the gate was asked
         for it, rather than the gate only announcing auto-fix
    """
    root, bin_dir, log = _fake_root(tmp_path, QUALITY_GATE)
    for name in (
        "run-plugin-lint.sh",
        "run-plugin-typecheck.sh",
        "run-plugin-tests.sh",
    ):
        _write_shim(root / "scripts", name, log)

    result = _run(root, QUALITY_GATE.name, bin_dir, *([flag] if flag else []))

    lint_calls = [line for line in _lines(log) if "--all" in line]
    assert lint_calls, f"the gate never invoked the lint runner:\n{result.stdout}"
    assert ("--fix" in lint_calls[0]) is expect_fix, (
        f"lint runner argv was {lint_calls[0]!r} for flag {flag!r}"
    )
