"""In-process runs of conserve scripts that import leyline, with leyline hidden.

ADR-0001: a plugin that misses a peer says so. A direct run exits with a
one-line message, and an importer gets the ImportError to handle itself.
Subprocess runs cannot be seen by coverage, so the peer import is blocked
inside this interpreter instead.
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import runpy
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

LEYLINE_USERS = [
    "safe_replacer.py",
    "coordination_workspace.py",
    "area_agent_registry.py",
]


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
def without_leyline() -> Iterator[None]:
    """Hide leyline, including any copy already imported, for one test."""
    saved = {
        n: sys.modules.pop(n) for n in list(sys.modules) if n.split(".")[0] == "leyline"
    }
    blocker = _BlockPackage("leyline")
    sys.meta_path.insert(0, blocker)
    yield
    sys.meta_path.remove(blocker)
    sys.modules.update(saved)


@pytest.mark.unit
@pytest.mark.parametrize("script", LEYLINE_USERS)
def test_direct_run_without_leyline_exits_naming_the_missing_plugin(
    script: str, without_leyline: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A direct run without leyline exits with a message, not a traceback.

    GIVEN leyline cannot be imported
    WHEN the script runs as __main__
    THEN SystemExit carries a message naming the script and leyline.
    """
    monkeypatch.setattr(sys, "argv", [script])

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(SCRIPTS / script), run_name="__main__")

    assert (
        exc.value.code
        == f"{script}: requires the leyline plugin, which is not installed"
    )


@pytest.mark.unit
@pytest.mark.parametrize("script", LEYLINE_USERS)
def test_import_without_leyline_raises_import_error_for_the_importer(
    script: str, without_leyline: None
) -> None:
    """An importer gets the ImportError instead of a process exit.

    GIVEN leyline cannot be imported
    WHEN the script is imported as a module
    THEN ModuleNotFoundError propagates and SystemExit does not.
    """
    spec = importlib.util.spec_from_file_location(
        f"no_leyline_{script[:-3]}", SCRIPTS / script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    with pytest.raises(ImportError, match="leyline"):
        spec.loader.exec_module(module)
