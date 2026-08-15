"""Initiative tracking must outlive the plugin version that wrote it.

``ProjectTracker`` defaults its store to ``<plugin_root>/data/
project-data.json`` and ``_save_data`` writes there. In an install the
plugin root is ``~/.claude/plugins/cache/<marketplace>/minister/
<version>/``, so every update starts a fresh tree and the initiative
history accumulated under the previous one stops being reachable.

This is the defect issue #661 measured in memory-palace, where 1,470
staged captures were stranded across one update. minister was not in
that issue's list, because the list was assembled by matching the code
shape rather than by asking what writes. Nothing has accumulated here
yet: the shipped ``project-data.json`` is byte-identical across 1.9.17
and 1.9.18 on the machine this was written on, so the fix lands before
the loss rather than after it.

Feature: tracking data resolves to a location an update cannot strand.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from minister.project_tracker import (
    ProjectTracker,
    _default_data_file,
    _leyline_src,
)


@pytest.fixture(autouse=True)
def _no_host_data_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the host variable so derivation is what these tests cover."""
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)


def _install_tree(root: Path, version: str = "1.9.18") -> Path:
    """Build the directory shape a real plugin install has."""
    plugin_root = (
        root / "plugins" / "cache" / "claude-night-market" / "minister" / version
    )
    (plugin_root / "src" / "minister").mkdir(parents=True)
    return plugin_root


class TestDataFileLocation:
    """Where the tracker puts its store when no path is passed."""

    def test_an_explicit_path_is_always_honored(self, tmp_path: Path) -> None:
        """GIVEN a caller passes data_file
        WHEN the tracker is built
        THEN that path is used.

        The CLI passes one, and the resolution change must not disturb
        it; this pins the contract the rest of the suite relies on.
        """
        explicit = tmp_path / "somewhere" / "data.json"

        assert ProjectTracker(data_file=explicit).data_file == explicit

    def test_a_checkout_keeps_its_own_data_file(self) -> None:
        """GIVEN the tracker running from a source checkout
        WHEN it resolves its default
        THEN the path stays inside the checkout's ``data/``.

        The shipped ``project-data.json`` is tracked and read by tests.
        If the default redirected here, a test run would read the
        operator's real tracking data.
        """
        resolved = ProjectTracker().data_file

        assert resolved.name == "project-data.json"
        assert resolved.parent.name == "data"
        assert "cache" not in resolved.parts

    def test_an_install_resolves_outside_the_version_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the module located inside an install tree
        WHEN the default is resolved
        THEN the path is not under the version directory, so an update
        cannot strand what was written there.
        """
        plugin_root = _install_tree(tmp_path)
        module_file = plugin_root / "src" / "minister" / "project_tracker.py"
        monkeypatch.setattr("minister.project_tracker.__file__", str(module_file))

        resolved = ProjectTracker().data_file

        assert "1.9.18" not in resolved.parts
        assert plugin_root not in resolved.parents

    def test_an_install_resolves_to_the_provisioned_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the same install
        WHEN the default is resolved
        THEN it is ``plugins/data/minister-<marketplace>/data/``, the
        location Claude Code provisions, rather than a path of our own.
        """
        plugin_root = _install_tree(tmp_path)
        module_file = plugin_root / "src" / "minister" / "project_tracker.py"
        monkeypatch.setattr("minister.project_tracker.__file__", str(module_file))

        resolved = ProjectTracker().data_file

        expected = (
            tmp_path
            / "plugins"
            / "data"
            / "minister-claude-night-market"
            / "data"
            / "project-data.json"
        )
        assert resolved == expected

    def test_the_host_variable_is_honored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the host sets CLAUDE_PLUGIN_DATA
        WHEN the default is resolved
        THEN the store sits under that directory.

        Claude Code 2.1.78+ names the per-plugin directory it
        provisions, and where it does, its answer is authoritative.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))

        resolved = ProjectTracker().data_file

        assert resolved == tmp_path / "host" / "data" / "project-data.json"


class TestSharedResolution:
    """The rule is leyline's, so minister must not restate it."""

    def test_resolution_agrees_with_the_shared_helper(self, tmp_path: Path) -> None:
        """GIVEN an install tree
        WHEN leyline's helper resolves it
        THEN minister's default sits under that root.

        Two plugins that disagreed about where their data lives would
        reintroduce the bug one plugin at a time.
        """
        leyline_src = Path(__file__).resolve().parents[3] / "leyline" / "src"
        if not leyline_src.is_dir():
            pytest.skip("leyline source not present; nothing to compare against")
        if str(leyline_src) not in sys.path:
            sys.path.insert(0, str(leyline_src))

        # Loaded dynamically: the sys.path entry above is what makes
        # leyline reachable, so a module-scope import would fail.
        plugin_data_dir = importlib.import_module("leyline.plugin_data").plugin_data_dir

        plugin_root = tmp_path / "plugins" / "cache" / "mkt" / "minister" / "9.9.9"
        plugin_root.mkdir(parents=True)

        assert plugin_data_dir(plugin_root) == (
            tmp_path / "plugins" / "data" / "minister-mkt"
        )


class TestLeylineBootstrap:
    """Finding the shared helper is the part that makes the hoist real.

    A guarded import that always lands in the except-branch moves the
    code without moving the behavior. leyline is reachable in a checkout
    as a sibling and in an install as a versioned directory under the
    same marketplace, and both have to work or installs keep the bug.
    """

    def test_the_sibling_layout_is_found(self, tmp_path: Path) -> None:
        """GIVEN a checkout with leyline beside this plugin
        WHEN the source is located
        THEN the sibling path is returned.
        """
        plugins = tmp_path / "plugins"
        (plugins / "leyline" / "src").mkdir(parents=True)
        plugin_root = plugins / "minister"
        plugin_root.mkdir()

        assert _leyline_src(plugin_root) == plugins / "leyline" / "src"

    def test_the_install_layout_is_found(self, tmp_path: Path) -> None:
        """GIVEN an install where leyline sits under its own version
        WHEN the source is located
        THEN that path is returned.

        This is the case ``add_plugin_src_to_path`` misses: it looks for
        ``plugins/<name>/src`` and an install has
        ``plugins/cache/<marketplace>/<name>/<version>/src``.
        """
        marketplace = tmp_path / "plugins" / "cache" / "claude-night-market"
        (marketplace / "leyline" / "1.9.18" / "src").mkdir(parents=True)
        plugin_root = marketplace / "minister" / "1.9.18"
        plugin_root.mkdir(parents=True)

        assert _leyline_src(plugin_root) == (marketplace / "leyline" / "1.9.18" / "src")

    def test_the_newest_installed_leyline_wins(self, tmp_path: Path) -> None:
        """GIVEN two installed leyline versions
        WHEN the source is located
        THEN the highest is chosen, compared numerically so 1.9.9 does
        not outrank 1.9.17.
        """
        marketplace = tmp_path / "plugins" / "cache" / "claude-night-market"
        for version in ("1.9.9", "1.9.17"):
            (marketplace / "leyline" / version / "src").mkdir(parents=True)
        plugin_root = marketplace / "minister" / "1.9.17"
        plugin_root.mkdir(parents=True)

        assert _leyline_src(plugin_root) == (marketplace / "leyline" / "1.9.17" / "src")

    def test_absent_leyline_reports_nothing_rather_than_guessing(
        self, tmp_path: Path
    ) -> None:
        """GIVEN neither layout present
        WHEN the source is located
        THEN None is returned, so the caller takes its documented
        fallback instead of inserting a path that does not exist.
        """
        plugin_root = tmp_path / "plugins" / "minister"
        plugin_root.mkdir(parents=True)

        assert _leyline_src(plugin_root) is None


class TestFallbackWithoutLeyline:
    """What happens on a host with neither leyline nor the variable."""

    def test_the_previous_location_is_kept(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the shared resolver cannot be loaded and no host variable
        WHEN the default is resolved
        THEN the store stays under the plugin root.

        Keeping the old, version-scoped location is deliberate. A host
        this old cannot tell us where its data directory is, and guessing
        a third location would move data somewhere nothing else reads.
        """
        monkeypatch.setattr(
            "minister.project_tracker._load_shared_resolver", lambda _root: None
        )
        module_file = tmp_path / "src" / "minister" / "project_tracker.py"
        module_file.parent.mkdir(parents=True)
        monkeypatch.setattr("minister.project_tracker.__file__", str(module_file))

        assert _default_data_file() == tmp_path / "data" / "project-data.json"

    def test_the_host_variable_still_wins_without_leyline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN no leyline but CLAUDE_PLUGIN_DATA is set
        WHEN the default is resolved
        THEN the host's directory is used.

        This is the path that matters in practice: an installed plugin on
        a current host is safe even if leyline cannot be located.
        """
        monkeypatch.setattr(
            "minister.project_tracker._load_shared_resolver", lambda _root: None
        )
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))

        assert _default_data_file() == (
            tmp_path / "host" / "data" / "project-data.json"
        )
