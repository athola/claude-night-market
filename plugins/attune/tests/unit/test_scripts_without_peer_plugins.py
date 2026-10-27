"""In-process runs of the wrapper scripts, with and without their peer plugins.

The subprocess tests in ``test_deferred_capture.py`` check the same
contract end to end, but coverage cannot see a child interpreter. These run
the script files in this process, and block the peer import where the
missing-plugin branch is under test.
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import json
import runpy
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


class _BlockPackage(importlib.abc.MetaPathFinder):
    def __init__(self, package: str) -> None:
        self.package = package

    def find_spec(
        self,
        name: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> None:
        if name.split(".", maxsplit=1)[0] == self.package:
            raise ModuleNotFoundError(f"No module named {name!r}")


@pytest.fixture
def block() -> Iterator[object]:
    """Hide a top-level package, including any copy already imported."""
    blockers: list[_BlockPackage] = []
    saved: dict[str, ModuleType] = {}

    def _block(package: str) -> None:
        for name in [n for n in sys.modules if n.split(".")[0] == package]:
            saved[name] = sys.modules.pop(name)
        blocker = _BlockPackage(package)
        sys.meta_path.insert(0, blocker)
        blockers.append(blocker)

    yield _block
    for blocker in blockers:
        sys.meta_path.remove(blocker)
    sys.modules.update(saved)


def _load(script: str, as_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(as_name, SCRIPTS / script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_deferred_capture_dry_run_enriches_war_room_context(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A war-room capture carries the Strategeion session dir in its body."""
    # conftest puts plugins/ on sys.path, so an earlier ``import leyline``
    # in the suite can leave the plugins/leyline namespace package bound,
    # which has no deferred_capture. Start from an unimported leyline.
    for name in [n for n in sys.modules if n.split(".")[0] == "leyline"]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setenv("STRATEGEION_SESSION_DIR", "/tmp/session-7")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "deferred_capture.py",
            "--title",
            "T",
            "--source",
            "war-room",
            "--context",
            "Base",
            "--dry-run",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(SCRIPTS / "deferred_capture.py"), run_name="__main__")

    assert exc.value.code == 0
    body = json.loads(capsys.readouterr().out)["body"]
    assert "Base" in body
    assert "Strategeion session: /tmp/session-7" in body


@pytest.mark.unit
def test_deferred_capture_without_leyline_exits_one_naming_it(
    block, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing leyline is a clear error and exit 1, not an ImportError trace."""
    block("leyline")

    with pytest.raises(SystemExit) as exc:
        _load("deferred_capture.py", "attune_deferred_capture_no_leyline")

    assert exc.value.code == 1
    assert "leyline plugin not found" in capsys.readouterr().err


@pytest.mark.unit
def test_tasks_manager_without_abstract_refuses_to_construct(
    block, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without abstract the module imports, warns, and reports tasks unavailable."""
    block("abstract")

    module = _load("tasks_manager.py", "attune_tasks_manager_no_abstract")

    assert "abstract plugin not found" in capsys.readouterr().err
    assert module.is_tasks_available() is False
    assert module.get_claude_code_version() == "unknown"
    assert module.detect_ambiguity("refactor all") is None
    with pytest.raises(RuntimeError, match="requires the abstract plugin"):
        module.TasksManager(config=module.ATTUNE_CONFIG)
