"""Runtime data must outlive the plugin version that wrote it.

Hooks execute from ``~/.claude/plugins/cache/<marketplace>/<plugin>/
<version>/``, so a data root derived from ``__file__`` is version
scoped. Installing a new version creates a new tree and everything the
previous one accumulated stops being reachable. Issue #661 measured it:
1,470 staged captures stranded under 1.9.17 while the version-
independent directory Claude Code provisions for exactly this purpose
sat empty. The filing machine reported 200 under 1.9.16; the counts
differ per machine, the defect does not.

The captures carry ``status: pending_review``, so they were awaiting
curation at the moment they were orphaned. That is the whole defect:
not corruption, not deletion, just an address nobody holds any more.

Feature: user data resolves to a location that survives an update.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from memory_palace.paths import (
    ENV_OVERRIDE,
    _leyline_src,
    _load_shared_resolver,
    _local_plugin_data_dir,
    persistent_root,
    user_data_dir,
)


@pytest.fixture(autouse=True)
def _no_host_data_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the host's data variable so derivation is what gets tested.

    ``CLAUDE_PLUGIN_DATA`` outranks derivation by design. Leaving it set
    would make these assertions depend on the developer's shell, and the
    failure would look like a bug in the resolution rather than in the
    environment.
    """
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)


def _cache_tree(root: Path, version: str = "1.9.18") -> Path:
    """Build the directory shape a real plugin install has."""
    plugin_root = (
        root
        / ".claude"
        / "plugins"
        / "cache"
        / "claude-night-market"
        / "memory-palace"
        / version
    )
    plugin_root.mkdir(parents=True)
    return plugin_root


class TestInstalledPlugin:
    """A plugin running from the versioned cache tree."""

    def test_data_root_is_outside_the_version_directory(self, tmp_path: Path) -> None:
        """GIVEN a hook running from cache/<marketplace>/<plugin>/<version>
        WHEN the user data root is resolved
        THEN it is not under the version directory
        AND so an update cannot strand what was written there.
        """
        plugin_root = _cache_tree(tmp_path)

        resolved = user_data_dir(plugin_root)

        assert plugin_root not in resolved.parents
        assert "1.9.18" not in resolved.parts

    def test_data_root_is_the_directory_claude_code_provisions(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the same install
        WHEN the root is resolved
        THEN it is ``plugins/data/<plugin>-<marketplace>/``, the location
        Claude Code already creates, rather than a path of our own.
        """
        plugin_root = _cache_tree(tmp_path)

        resolved = persistent_root(plugin_root)

        expected = (
            tmp_path
            / ".claude"
            / "plugins"
            / "data"
            / "memory-palace-claude-night-market"
        )
        assert resolved == expected

    def test_two_versions_resolve_to_one_root(self, tmp_path: Path) -> None:
        """GIVEN two installed versions of the same plugin
        WHEN each resolves its data root
        THEN both name the same directory, which is the property the
        whole change exists to establish.
        """
        old = _cache_tree(tmp_path, "1.9.17")
        new = _cache_tree(tmp_path, "1.9.18")

        assert persistent_root(old) == persistent_root(new)


class TestSourceCheckout:
    """A developer or CI running from the repository itself."""

    def test_checkout_keeps_its_own_data_directory(self, tmp_path: Path) -> None:
        """GIVEN a plugin root that is not inside a plugins/cache tree
        WHEN the root is resolved
        THEN it stays ``<plugin_root>/data``.

        Tests and local development read fixtures from the checkout. If
        this redirected to the user's real palace, a test run would read
        and write the operator's captures.
        """
        plugin_root = tmp_path / "repo" / "plugins" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert persistent_root(plugin_root) == plugin_root
        assert user_data_dir(plugin_root) == plugin_root / "data"

    def test_cache_lookalike_without_a_marketplace_is_not_treated_as_installed(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a path containing 'cache' but not the install shape
        WHEN the root is resolved
        THEN it falls back to the local data directory rather than
        inventing a marketplace name from whatever sits above it.
        """
        plugin_root = tmp_path / "cache" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert user_data_dir(plugin_root) == plugin_root / "data"


class TestOverride:
    """An explicit environment override wins over both branches."""

    def test_env_var_overrides_resolution(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN MEMORY_PALACE_DATA_DIR is set
        WHEN the root is resolved
        THEN that value is used verbatim.

        The migration tool and any operator moving a palace need one
        lever that does not depend on where the code happens to live.
        """
        plugin_root = _cache_tree(tmp_path)
        override = tmp_path / "elsewhere"
        monkeypatch.setenv("MEMORY_PALACE_DATA_DIR", str(override))

        assert persistent_root(plugin_root) == override


class TestStoredAtCompatibility:
    """The index records paths relative to the root this module returns."""

    def test_relative_stored_at_keeps_its_shape_in_both_layouts(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a capture written under the data directory
        WHEN its path is expressed relative to the persistent root
        THEN it reads ``data/staging/<file>`` in an install exactly as it
        does in a checkout.

        Index entries are resolved as ``root / stored_at``. If the two
        layouts disagreed on that string, every pre-existing entry would
        report as an orphan the first time a migrated palace was read.
        """
        installed = _cache_tree(tmp_path)
        checkout = tmp_path / "repo" / "plugins" / "memory-palace"
        checkout.mkdir(parents=True)

        shapes = {
            str(
                (user_data_dir(root) / "staging" / "x.md").relative_to(
                    persistent_root(root)
                )
            )
            for root in (installed, checkout)
        }

        assert shapes == {"data/staging/x.md"}


class TestHostVariable:
    """Claude Code 2.1.78+ names the directory it provisions."""

    def test_claude_plugin_data_is_honored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the host sets CLAUDE_PLUGIN_DATA
        WHEN the root is resolved
        THEN that value is used.

        Derivation exists for hosts that do not set it. Where the host
        does, its answer is authoritative, and the two agree: both name
        ``plugins/data/<plugin>-<marketplace>/``.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))

        assert persistent_root(_cache_tree(tmp_path)) == tmp_path / "host"

    def test_the_palace_override_outranks_the_host(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN both variables are set
        WHEN the root is resolved
        THEN MEMORY_PALACE_DATA_DIR wins, so relocating this palace does
        not require relocating every plugin's data.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))
        monkeypatch.setenv("MEMORY_PALACE_DATA_DIR", str(tmp_path / "palace"))

        assert persistent_root(_cache_tree(tmp_path)) == tmp_path / "palace"


class TestFallbackMatchesLeyline:
    """The local copy stands in when leyline is absent, so it must agree.

    leyline's src is not on sys.path when a hook runs from an install
    tree, which is exactly the situation the whole fix targets. A
    fallback that resolved differently from the shared helper would mean
    captures landing in one place with leyline installed and another
    without it -- the same defect, keyed on a dependency instead of a
    version.
    """

    @staticmethod
    def _both(plugin_root: Path) -> tuple[Path, Path]:
        """Resolve through the shared helper and the local copy.

        memory-palace's own suite runs from its plugin directory, where
        leyline is not an installed dependency, so the sibling checkout
        is put on the path the way ``abstract.tokens`` does it. The skip
        fires only where the source tree is genuinely absent.
        """
        leyline_src = Path(__file__).resolve().parents[3] / "leyline" / "src"
        if not leyline_src.is_dir():
            pytest.skip("leyline source not present; nothing to compare against")
        if str(leyline_src) not in sys.path:
            sys.path.insert(0, str(leyline_src))

        # Loaded dynamically: the sys.path entry above is what makes
        # leyline reachable, so a module-scope import would fail.
        plugin_data_dir = importlib.import_module("leyline.plugin_data").plugin_data_dir

        return (
            plugin_data_dir(plugin_root, env_override=ENV_OVERRIDE),
            _local_plugin_data_dir(plugin_root, env_override=ENV_OVERRIDE),
        )

    def test_they_agree_on_an_install_tree(self, tmp_path: Path) -> None:
        """GIVEN an install tree
        WHEN both resolvers run
        THEN they return the same path.
        """
        shared, local = self._both(_cache_tree(tmp_path))

        assert shared == local

    def test_they_agree_on_a_checkout(self, tmp_path: Path) -> None:
        """GIVEN a plugin root outside any cache tree
        WHEN both resolvers run
        THEN they return the same path.
        """
        checkout = tmp_path / "repo" / "plugins" / "memory-palace"
        checkout.mkdir(parents=True)

        shared, local = self._both(checkout)

        assert shared == local

    def test_they_agree_when_the_host_sets_the_variable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN CLAUDE_PLUGIN_DATA is set
        WHEN both resolvers run
        THEN they return the same path, so precedence matches too and
        not merely the derivation branch.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))

        shared, local = self._both(_cache_tree(tmp_path))

        assert shared == local == tmp_path / "host"

    def test_they_agree_on_the_palace_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN MEMORY_PALACE_DATA_DIR is set
        WHEN both resolvers run
        THEN they return the same path.
        """
        monkeypatch.setenv("MEMORY_PALACE_DATA_DIR", str(tmp_path / "mine"))

        shared, local = self._both(_cache_tree(tmp_path))

        assert shared == local == tmp_path / "mine"


class TestSharedResolverIsActuallyUsed:
    """A guarded import that always fails moves code, not behavior.

    leyline sits beside this plugin in a checkout and under its own
    version in an install. If only the first were handled, every
    installed hook would take the fallback -- which is exactly where the
    stranding happened, so the hoist would be cosmetic there.
    """

    def test_the_shared_resolver_loads_in_this_checkout(self) -> None:
        """GIVEN the repository layout
        WHEN the resolver is loaded
        THEN it comes from leyline rather than the local copy.
        """
        resolver = _load_shared_resolver()

        assert resolver is not None
        assert resolver.__module__ == "leyline.plugin_data"

    def test_the_install_layout_is_found(self, tmp_path: Path) -> None:
        """GIVEN an install where leyline sits under its own version
        WHEN the source is located
        THEN that path is returned.

        This is the case ``add_plugin_src_to_path`` misses: it resolves
        ``plugins/<name>/src`` and an install has
        ``plugins/cache/<marketplace>/<name>/<version>/src``.
        """
        marketplace = tmp_path / "plugins" / "cache" / "claude-night-market"
        (marketplace / "leyline" / "1.9.18" / "src").mkdir(parents=True)
        plugin_root = marketplace / "memory-palace" / "1.9.18"
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
        plugin_root = marketplace / "memory-palace" / "1.9.17"
        plugin_root.mkdir(parents=True)

        assert _leyline_src(plugin_root) == (marketplace / "leyline" / "1.9.17" / "src")

    def test_absent_leyline_reports_nothing_rather_than_guessing(
        self, tmp_path: Path
    ) -> None:
        """GIVEN neither layout present
        WHEN the source is located
        THEN None is returned, so no non-existent path joins sys.path.
        """
        plugin_root = tmp_path / "plugins" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert _leyline_src(plugin_root) is None

    def test_resolution_still_works_without_the_shared_helper(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN the shared resolver cannot be loaded
        WHEN a root is resolved
        THEN the local copy answers identically.

        The captures matter more than the tidiness of the dependency, so
        a missing leyline degrades to a duplicated rule rather than to a
        version-scoped path.
        """
        monkeypatch.setattr("memory_palace.paths._load_shared_resolver", lambda: None)

        resolved = persistent_root(_cache_tree(tmp_path))

        assert resolved == (
            tmp_path
            / ".claude"
            / "plugins"
            / "data"
            / "memory-palace-claude-night-market"
        )
