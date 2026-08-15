"""The test session must not shadow leyline with a namespace package.

`plugins/leyline/` has no `__init__.py`, and leyline is an editable
install whose finder sits behind PathFinder on `sys.meta_path`. Put
`plugins/` on `sys.path` -- the obvious way to reach
`plugins/conftest_shared.py` -- and `import leyline` binds to the bare
directory as a namespace package. `sys.modules` caches that binding, so
every later `leyline.cli_envelope` import fails even though
`scripts/quality_checker.py` adds `leyline/src` to the path itself.

The failure mode is nasty because it is order-dependent: all 87 affected
tests pass when their file is run alone and fail in a full-suite run,
which reads as flakiness rather than as a path bug.

These tests pin the invariant rather than the workaround, so any future
conftest that reintroduces the shadowing turns them red.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

PLUGINS_ROOT = Path(__file__).resolve().parents[2]


def _import_after_path_setup(name: str) -> ModuleType:
    """Import ``name`` the way sanctum's scripts do.

    `scripts/quality_checker.py` prepends `plugins/leyline/src` and then
    imports. Reproducing that here rather than importing at module scope
    keeps the test honest about the sequence that actually broke.
    """
    leyline_src = str(PLUGINS_ROOT / "leyline" / "src")
    if leyline_src not in sys.path:
        sys.path.insert(0, leyline_src)
    return importlib.import_module(name)


def test_plugins_root_is_not_on_sys_path() -> None:
    """The plugins/ directory must stay off sys.path during tests."""
    entries = {Path(p).resolve() for p in sys.path if p}
    assert PLUGINS_ROOT not in entries, (
        f"{PLUGINS_ROOT} is on sys.path, which shadows every plugin package "
        "that lacks an __init__.py. Load plugins/conftest_shared.py with "
        "importlib.util.spec_from_file_location instead."
    )


def test_leyline_src_import_still_works() -> None:
    """Reproduce what sanctum's scripts do, and require it to succeed.

    `scripts/quality_checker.py` prepends `plugins/leyline/src` and then
    imports `leyline.cli_envelope`. That is the exact sequence the
    namespace shadowing defeated: if `leyline` is already bound in
    `sys.modules` to the bare `plugins/leyline/` directory, adding the
    real source root afterwards changes nothing.
    """
    envelope = _import_after_path_setup("leyline.cli_envelope")

    assert callable(envelope.error_envelope)
    assert callable(envelope.success_envelope)


def test_leyline_resolves_to_a_real_package() -> None:
    """Once imported, leyline must be a regular package."""
    leyline = _import_after_path_setup("leyline")

    assert leyline.__file__ is not None, (
        "leyline resolved to a namespace package "
        f"({getattr(leyline, '__path__', None)}), not the real source tree"
    )


def test_shared_fixtures_are_loaded_without_path_pollution() -> None:
    """conftest_shared must still be reachable despite the constraint."""
    assert "conftest_shared" in sys.modules, (
        "conftest_shared was never loaded, so the CLAUDE_HOME isolation "
        "fixture is not active"
    )
    assert hasattr(sys.modules["conftest_shared"], "isolate_claude_home")
