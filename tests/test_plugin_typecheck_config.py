"""Guard that every type-checked plugin owns the mypy it is checked with.

``scripts/run-plugin-typecheck.sh`` runs mypy over ``hooks/`` in every plugin
that has Python there. It used to invoke bare ``mypy`` through ``uv run``, which
falls back to whatever is on PATH when the project environment has none. A
plugin that never declared mypy therefore passed on any developer machine with a
global mypy installed, and failed on a clean CI runner with::

    error: Failed to spawn: `mypy`

The script now goes through ``uv run python -m mypy``, which resolves only from
the plugin's own environment, so the gate means the same thing in both places.
That fix is only load-bearing while every type-checked plugin actually declares
mypy, which is what this module pins.

A plugin with no pyproject.toml of its own is fine: ``uv run`` resolves it
against the repo root project, which does declare mypy. The broken combination
is a plugin that owns a pyproject and leaves mypy out of it, because that
pyproject is the environment mypy is then looked up in.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

PLUGIN_MANIFESTS = (".claude-plugin/plugin.json", "openpackage.yml")


def _is_plugin(path: Path) -> bool:
    return any((path / manifest).exists() for manifest in PLUGIN_MANIFESTS)


def _typechecked_plugins() -> list[Path]:
    """Plugins the typecheck script runs mypy over, that own a pyproject.

    Mirrors the script's own trigger: ``compgen -G "$plugin_dir/hooks/*.py"``.
    """
    plugins = []
    for path in sorted(PLUGINS_DIR.iterdir()):
        if not path.is_dir() or not _is_plugin(path):
            continue
        if not any((path / "hooks").glob("*.py")):
            continue
        if not (path / "pyproject.toml").exists():
            continue
        plugins.append(path)
    return plugins


def _declares_mypy(plugin: Path) -> bool:
    """True when mypy appears in the plugin's dependency groups or extras.

    Parsed rather than grepped: the file mentions mypy in prose comments, and a
    substring match would count those as a declaration.
    """
    with (plugin / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)

    groups = config.get("dependency-groups", {}).values()
    extras = config.get("project", {}).get("optional-dependencies", {}).values()
    runtime = config.get("project", {}).get("dependencies", [])

    for spec in [
        *runtime,
        *(d for group in groups for d in group),
        *(d for e in extras for d in e),
    ]:
        if isinstance(spec, str) and spec.lower().startswith("mypy"):
            return True
    return False


def test_discovery_finds_typechecked_plugins() -> None:
    """An empty parametrize list would make the gate below vacuously green."""
    assert len(_typechecked_plugins()) > 1


@pytest.mark.parametrize("plugin", _typechecked_plugins(), ids=lambda p: p.name)
def test_plugin_with_hooks_declares_mypy(plugin: Path) -> None:
    """A plugin whose hooks/ is type-checked must ship mypy in its own env."""
    assert _declares_mypy(plugin), (
        f"{plugin.name} has hooks/*.py and its own pyproject.toml but does not "
        f"declare mypy. run-plugin-typecheck.sh runs 'uv run python -m mypy "
        f"hooks/' in that environment, which will fail with 'No module named "
        f"mypy'. It may still pass on a machine with a global mypy installed, "
        f"which is exactly how this reached CI unnoticed."
    )
