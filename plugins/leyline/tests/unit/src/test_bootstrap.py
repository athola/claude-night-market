"""Tests for leyline.bootstrap (AR-15).

Feature: One canonical helper that adds a sibling plugin's
``src/`` directory to ``sys.path`` so cross-plugin imports
do not need each script to roll its own discovery logic.

As a plugin script that imports from a sibling plugin
I want ``add_plugin_src_to_path("herald")``
So that the 45 hand-rolled ``parents[N] / "<plugin>" / "src"``
shims collapse to one tested helper.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from leyline.bootstrap import add_plugin_src_to_path


class TestAddPluginSrcToPath:
    """Scenarios for add_plugin_src_to_path()."""

    @pytest.mark.unit
    def test_returns_path_when_plugin_exists(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given a plugins/<name>/src directory below the caller,
        When add_plugin_src_to_path(<name>) is called,
        Then the src dir is inserted on sys.path and returned.
        """
        # Build a fake repo: tmp_path/plugins/foo/src
        plugins = tmp_path / "plugins"
        foo_src = plugins / "foo" / "src"
        foo_src.mkdir(parents=True)
        # Caller location is below tmp_path so the walker can find plugins/
        caller = tmp_path / "plugins" / "bar" / "scripts" / "x.py"
        caller.parent.mkdir(parents=True)
        caller.touch()

        # Snapshot sys.path so we can assert and restore
        before = list(sys.path)
        try:
            result = add_plugin_src_to_path("foo", caller=caller)
        finally:
            sys.path[:] = before
        assert result == foo_src

    @pytest.mark.unit
    def test_inserts_dir_on_sys_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given a plugin found by the walker,
        When add_plugin_src_to_path is called,
        Then the dir is at the front of sys.path during the call.
        """
        plugins = tmp_path / "plugins"
        foo_src = plugins / "foo" / "src"
        foo_src.mkdir(parents=True)
        caller = tmp_path / "plugins" / "bar" / "scripts" / "x.py"
        caller.parent.mkdir(parents=True)
        caller.touch()

        # Make sure foo's src isn't already there
        before = [p for p in sys.path if p != str(foo_src)]
        sys.path[:] = before
        try:
            add_plugin_src_to_path("foo", caller=caller)
            assert str(foo_src) in sys.path
        finally:
            sys.path[:] = before

    @pytest.mark.unit
    def test_idempotent(
        self,
        tmp_path: Path,
    ) -> None:
        """Given the dir already on sys.path,
        When add_plugin_src_to_path is called twice,
        Then sys.path contains exactly one entry for it.
        """
        plugins = tmp_path / "plugins"
        foo_src = plugins / "foo" / "src"
        foo_src.mkdir(parents=True)
        caller = tmp_path / "plugins" / "bar" / "scripts" / "x.py"
        caller.parent.mkdir(parents=True)
        caller.touch()

        before = [p for p in sys.path if p != str(foo_src)]
        sys.path[:] = before
        try:
            add_plugin_src_to_path("foo", caller=caller)
            add_plugin_src_to_path("foo", caller=caller)
            assert sys.path.count(str(foo_src)) == 1
        finally:
            sys.path[:] = before

    @pytest.mark.unit
    def test_raises_when_plugin_missing(self, tmp_path: Path) -> None:
        """Given no plugins/<name>/src below the caller,
        When add_plugin_src_to_path is called,
        Then FileNotFoundError is raised.
        """
        caller = tmp_path / "scripts" / "x.py"
        caller.parent.mkdir(parents=True)
        caller.touch()
        with pytest.raises(FileNotFoundError):
            add_plugin_src_to_path("nonexistent", caller=caller)

    @pytest.mark.unit
    def test_caller_introspection_via_sys_getframe(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """NB8 (PR #470 review): when caller is omitted, the helper
        introspects the stack via sys._getframe(1) to locate the
        invoking module's __file__. Exercise that path explicitly.

        Strategy: write a fake caller module under plugins/bar/scripts/
        and import it; from inside the import, call
        add_plugin_src_to_path with no caller argument. The sys._getframe
        path must resolve back to the caller module's file location.
        """
        plugins = tmp_path / "plugins"
        foo_src = plugins / "foo" / "src"
        foo_src.mkdir(parents=True)
        bar_scripts = plugins / "bar" / "scripts"
        bar_scripts.mkdir(parents=True)
        caller_module = bar_scripts / "_bootstrap_no_caller.py"
        caller_module.write_text(
            "from leyline.bootstrap import add_plugin_src_to_path\n"
            "RESULT = add_plugin_src_to_path('foo')\n"
        )

        before = list(sys.path)
        # Make the fake caller importable as a top-level module.
        monkeypatch.syspath_prepend(str(bar_scripts))
        try:
            import importlib

            sys.modules.pop("_bootstrap_no_caller", None)
            mod = importlib.import_module("_bootstrap_no_caller")
            assert mod.RESULT == foo_src
            assert str(foo_src) in sys.path
        finally:
            sys.modules.pop("_bootstrap_no_caller", None)
            sys.path[:] = before
