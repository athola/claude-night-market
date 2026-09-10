"""A gate that cannot read its own inputs must not report success.

``test_gate_exit_codes.py`` guards the shape of a gate: that a validator
has *some* path to a nonzero exit. This file guards the behavior, which
is a different question. Every script below already had such a path, and
every one of them still returned 0 when the thing it exists to check was
unreadable, absent, or unparseable.

The five cases, each reproduced before this file was written:

``check_per_file_ignores.py``
    ``tomllib`` is 3.11+. The ``except ImportError`` bound it to ``None``,
    and ``except Exception`` then swallowed the ``AttributeError`` from
    ``None.loads`` into "no ignores found". ``.pre-commit-config.yaml``
    invokes it as ``python3``, which is 3.9.6 here, so the gate had never
    blocked anything on the interpreter its own hook uses.

``supply_chain_scan.py``
    A missing blocklist printed "Blocklist not found, skipping" and
    returned ``{}``; ``main`` then returned 0. The blocklist is the gate's
    only content, so the gate passed precisely when it had nothing to
    check with.

``check_upstream_drift.py``
    ``_read`` swallowed ``OSError`` into ``""``, ``extract_frozenset``
    returned ``None`` on empty source, and the vocabulary loop
    ``continue``d past it. This is the gate whose docstring exists so that
    the guard against model rot cannot itself rot.

``check_skill_graph_drift.py``
    Caught analyzer failure and returned 0 by design. A crashed analyzer
    and a clean ratchet produced the same exit code, and pre-commit shows
    hook output only on failure, so the skip line was never seen.

``clawhub_export.py``
    Printed an error count and exited 0, while
    ``cross-framework-publish.yml`` reads only ``total_exported``. A
    partial export shipped into a tagged release.

Fail-closed is the requirement, not fail-loud. A gate may still decline
to run, but it has to say so through its exit code.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str) -> ModuleType:
    """Import a root script by path, the way the other root tests do.

    The module is registered in ``sys.modules`` before execution because
    ``@dataclass`` resolves ``cls.__module__`` through it; without that,
    ``check_upstream_drift`` raises ``AttributeError`` at import.
    """
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def test_every_guarded_gate_script_exists() -> None:
    """A renamed script would make every test below vacuously green."""
    for name in (
        "check_per_file_ignores",
        "supply_chain_scan",
        "check_upstream_drift",
        "check_skill_graph_drift",
        "clawhub_export",
    ):
        assert (SCRIPTS / f"{name}.py").is_file(), f"{name}.py is missing"


# ---------------------------------------------------------------------------
# check_per_file_ignores.py
# ---------------------------------------------------------------------------


def test_per_file_ignores_gate_finds_a_toml_parser_on_this_interpreter() -> None:
    """The gate must parse TOML under the interpreter pre-commit gives it.

    ``.pre-commit-config.yaml`` runs this hook as bare ``python3``. On the
    repo's declared 3.9.6 that has no ``tomllib``, so the module has to
    reach ``tomli`` rather than binding the name to ``None``.
    """
    module = _load("check_per_file_ignores")
    assert module.TOML_PARSER is not None, (
        "check_per_file_ignores found no TOML parser, so every call to "
        "_get_per_file_ignores returns {} and the gate passes unconditionally. "
        "tomllib is 3.11+; tomli is the 3.9 fallback."
    )


def test_per_file_ignores_gate_blocks_when_no_toml_parser_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No parser means no verdict, which must not be spelled "no ignores"."""
    module = _load("check_per_file_ignores")
    monkeypatch.setattr(module, "TOML_PARSER", None)
    with pytest.raises(module.TomlUnavailableError):
        module._get_per_file_ignores(
            '[tool.ruff.lint.per-file-ignores]\n"a.py" = ["E"]'
        )


def test_per_file_ignores_gate_reports_nonzero_when_it_cannot_parse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The unparseable case reaches the exit code, not just the exception."""
    module = _load("check_per_file_ignores")
    monkeypatch.setattr(module, "TOML_PARSER", None)
    staged = tmp_path / "pyproject.toml"
    staged.write_text('[tool.ruff.lint.per-file-ignores]\n"a.py" = ["E501"]\n')
    assert module.main([str(staged)], repo_root=tmp_path) != 0


def test_per_file_ignores_gate_reports_nonzero_on_malformed_toml(
    tmp_path: Path,
) -> None:
    """Unparseable input is "cannot tell", which is not "nothing added"."""
    module = _load("check_per_file_ignores")
    staged = tmp_path / "pyproject.toml"
    staged.write_text("[tool.ruff.lint\nthis is not toml")
    assert module.main([str(staged)], repo_root=tmp_path) != 0


def test_per_file_ignores_gate_still_detects_a_new_ignore() -> None:
    """The fix must not cost the gate its actual job."""
    module = _load("check_per_file_ignores")
    before = module._get_per_file_ignores("")
    after = module._get_per_file_ignores(
        '[tool.ruff.lint.per-file-ignores]\n"a.py" = ["E501"]\n'
    )
    assert before == {}
    assert after == {"a.py": ["E501"]}


# ---------------------------------------------------------------------------
# supply_chain_scan.py
# ---------------------------------------------------------------------------


def test_supply_chain_scan_fails_when_the_blocklist_is_missing(
    tmp_path: Path,
) -> None:
    """The blocklist is the gate's only content; absent means no scan ran."""
    module = _load("supply_chain_scan")
    with pytest.raises(module.BlocklistMissingError):
        module.load_blocklist(tmp_path)


def test_supply_chain_scan_main_exits_nonzero_without_a_blocklist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproduces the finding: renaming the blocklist away exited 0."""
    module = _load("supply_chain_scan")

    def _absent(root: Path) -> dict:
        raise module.BlocklistMissingError(root / "known-bad-versions.json")

    monkeypatch.setattr(module, "load_blocklist", _absent)
    assert module.main() != 0


def test_supply_chain_scan_passes_with_the_real_blocklist() -> None:
    """The repository's own blocklist must still load and scan clean."""
    module = _load("supply_chain_scan")
    blocklist = module.load_blocklist(REPO_ROOT)
    assert blocklist, "the shipped blocklist parsed to nothing"


# ---------------------------------------------------------------------------
# check_upstream_drift.py
# ---------------------------------------------------------------------------


def test_upstream_drift_gate_fails_on_an_unreadable_gate_file(
    tmp_path: Path,
) -> None:
    """``--gate /nonexistent`` reported only harness drift and exited 0."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check_upstream_drift.py"),
            "--gate",
            str(tmp_path / "definitely-not-here.py"),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode != 0, (
        "check_upstream_drift accepted an unreadable gate file and exited 0. "
        "The vocabulary class is then absent from the report entirely, so the "
        "guard against model rot silently checks nothing.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "vocabulary" in (result.stdout + result.stderr).lower()


def test_upstream_drift_read_surfaces_an_unreadable_path(tmp_path: Path) -> None:
    """``_read`` must not turn a missing file into an empty document."""
    module = _load("check_upstream_drift")
    with pytest.raises(OSError):
        module._read(tmp_path / "absent.py")


# ---------------------------------------------------------------------------
# check_skill_graph_drift.py
# ---------------------------------------------------------------------------


def test_skill_graph_drift_fails_when_the_analyzer_crashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A dead analyzer produces no count, so it cannot clear a ratchet."""
    module = _load("check_skill_graph_drift")

    def _boom() -> dict:
        raise subprocess.CalledProcessError(1, ["skill_graph"], stderr="traceback")

    monkeypatch.setattr(module, "_run_skill_graph", _boom)
    monkeypatch.delenv(module.SKIP_ENV_VAR, raising=False)
    assert module.main() != 0


def test_skill_graph_drift_honors_an_explicit_documented_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contributors keep an escape hatch, but must ask for it by name."""
    module = _load("check_skill_graph_drift")

    def _boom() -> dict:
        raise subprocess.CalledProcessError(1, ["skill_graph"], stderr="traceback")

    monkeypatch.setattr(module, "_run_skill_graph", _boom)
    monkeypatch.setenv(module.SKIP_ENV_VAR, "1")
    assert module.main() == 0


# ---------------------------------------------------------------------------
# clawhub_export.py
# ---------------------------------------------------------------------------


def test_clawhub_export_exits_nonzero_when_skills_failed_to_export(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A partial export shipped into a tagged release reporting success."""
    module = _load("clawhub_export")
    monkeypatch.setattr(
        module,
        "export_all",
        lambda output, top, plugins_dir: {"total_exported": 3, "total_errors": 2},
    )
    monkeypatch.setattr(sys, "argv", ["clawhub_export.py", "--output", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        module.main()
    assert raised.value.code != 0


def test_clawhub_export_succeeds_on_a_clean_export(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Zero errors must still be a zero exit."""
    module = _load("clawhub_export")
    monkeypatch.setattr(
        module,
        "export_all",
        lambda output, top, plugins_dir: {"total_exported": 3, "total_errors": 0},
    )
    monkeypatch.setattr(sys, "argv", ["clawhub_export.py", "--output", str(tmp_path)])
    module.main()
