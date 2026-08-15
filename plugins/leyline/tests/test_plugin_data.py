"""Runtime data must outlive the plugin version that wrote it.

Hooks execute from ``~/.claude/plugins/cache/<marketplace>/<plugin>/
<version>/``. A data path derived from ``__file__`` is therefore version
scoped: installing a new version starts a fresh tree and everything the
previous one accumulated stops being reachable. Nothing is corrupted or
deleted. The files just no longer have an address anyone holds.

Issue #661 measured the cost in memory-palace, which was the one plugin
actively writing user content at runtime: 200 staged captures stranded
on the reporting machine, 1,470 and 2,491 on the machine that fixed it,
every one of them awaiting curation. An audit of the other plugins
found two latent instances of the same write shape (minister's
initiative tracker, oracle's model directory) and, more usefully, five
false positives -- code that matches the pattern but correctly reads
shipped assets. This module exists so the resolution is written once and
the distinction is made in one place.

Precedence is env var, then derivation, then identity. Claude Code
provisions ``plugins/data/<plugin>-<marketplace>/`` per plugin and names
it in ``CLAUDE_PLUGIN_DATA`` (2.1.78+), so when it is present it is
authoritative. Derivation reproduces the same location for older hosts
that do not set it. Identity is what keeps a source checkout reading its
own fixtures instead of the operator's live data.

Feature: any plugin can resolve a data root that survives an update.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from leyline.plugin_data import plugin_data_dir


def _install(
    root: Path, plugin: str = "memory-palace", version: str = "1.9.18"
) -> Path:
    """Build the directory shape a real plugin install has."""
    plugin_root = root / "plugins" / "cache" / "claude-night-market" / plugin / version
    plugin_root.mkdir(parents=True)
    return plugin_root


class TestEnvironmentVariableWins:
    """The host tells us where the data goes; believe it."""

    def test_claude_plugin_data_is_authoritative(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN CLAUDE_PLUGIN_DATA names a directory
        WHEN a plugin's data root is resolved
        THEN that value is used verbatim.

        The variable is already per-plugin: ``plugins/data/`` holds one
        ``<plugin>-<marketplace>`` directory per install, and oracle's
        provisioner has consumed it this way since 2.1.78. No plugin
        name is appended.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "given"))

        assert plugin_data_dir(_install(tmp_path)) == tmp_path / "given"

    def test_an_empty_value_is_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN CLAUDE_PLUGIN_DATA is set but empty
        WHEN the root is resolved
        THEN resolution falls through rather than returning the cwd.

        An empty string is what an unset-but-exported variable looks
        like, and ``Path("")`` is ``.`` -- a plausible-looking answer
        that would scatter data wherever the hook happened to run.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "")
        plugin_root = _install(tmp_path)

        resolved = plugin_data_dir(plugin_root)

        assert resolved != Path()
        assert resolved.is_absolute()


class TestDerivationForOlderHosts:
    """No env var: reproduce the location from the install path."""

    def test_resolves_outside_the_version_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN an install tree and no CLAUDE_PLUGIN_DATA
        WHEN the root is resolved
        THEN it is not under the version directory, so an update cannot
        strand what was written there.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        plugin_root = _install(tmp_path)

        resolved = plugin_data_dir(plugin_root)

        assert plugin_root not in resolved.parents
        assert "1.9.18" not in resolved.parts

    def test_derivation_matches_what_the_host_provisions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN an install tree
        WHEN the root is derived
        THEN it is ``plugins/data/<plugin>-<marketplace>/``.

        The derivation has to agree with the env var, not merely avoid
        the version directory. If the two disagreed, upgrading the host
        would silently relocate a live palace.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)

        resolved = plugin_data_dir(_install(tmp_path))

        assert resolved == (
            tmp_path / "plugins" / "data" / "memory-palace-claude-night-market"
        )

    def test_two_versions_resolve_to_one_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN two installed versions of one plugin
        WHEN each resolves its root
        THEN both name the same directory. This is the property the
        whole module exists to establish.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        old = _install(tmp_path, version="1.9.17")
        new = _install(tmp_path, version="1.9.18")

        assert plugin_data_dir(old) == plugin_data_dir(new)

    def test_each_plugin_gets_its_own_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN two different plugins installed from one marketplace
        WHEN each resolves its root
        THEN the roots differ, so one plugin cannot read or overwrite
        another's state.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        palace = _install(tmp_path, plugin="memory-palace")
        minister = _install(tmp_path, plugin="minister")

        assert plugin_data_dir(palace) != plugin_data_dir(minister)


class TestSourceCheckout:
    """A developer or CI running from the repository itself."""

    def test_a_checkout_keeps_its_own_tree(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a plugin root outside any plugins/cache tree
        WHEN the root is resolved
        THEN it is returned unchanged.

        Tests and local development read fixtures from the checkout. If
        this redirected, a test run would read and write the operator's
        real data.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        plugin_root = tmp_path / "repo" / "plugins" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert plugin_data_dir(plugin_root) == plugin_root

    def test_a_cache_lookalike_is_not_treated_as_an_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a path containing 'cache' but not the install shape
        WHEN the root is resolved
        THEN it is returned unchanged rather than donating whatever sits
        above it as a marketplace name.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        plugin_root = tmp_path / "cache" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert plugin_data_dir(plugin_root) == plugin_root

    def test_a_shallow_path_is_not_treated_as_an_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a path too short to be an install tree
        WHEN the root is resolved
        THEN it is returned unchanged instead of indexing off the end of
        its own parents.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)

        assert plugin_data_dir(Path("/")) == Path("/")


class TestOverride:
    """A per-plugin override outranks everything."""

    def test_named_override_wins_over_the_host(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN both CLAUDE_PLUGIN_DATA and a plugin's own override
        WHEN the root is resolved
        THEN the plugin's override wins.

        An operator relocating one palace, or a migration tool pointing
        at a destination, needs a lever that does not move every plugin
        at once.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))
        monkeypatch.setenv("MY_PLUGIN_DIR", str(tmp_path / "mine"))

        resolved = plugin_data_dir(_install(tmp_path), env_override="MY_PLUGIN_DIR")

        assert resolved == tmp_path / "mine"

    def test_an_unset_override_falls_through(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN an override name that is not set in the environment
        WHEN the root is resolved
        THEN the host variable is used, so naming an override costs
        nothing when the operator has not set one.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "host"))
        monkeypatch.delenv("MY_PLUGIN_DIR", raising=False)

        resolved = plugin_data_dir(_install(tmp_path), env_override="MY_PLUGIN_DIR")

        assert resolved == tmp_path / "host"
