"""docs/plugin-dependencies.json must describe the imports that exist.

The committed manifest was generated on 2026-03-28 and then hand-kept.
By September it listed two providers where the source had six, and
omitted four live edges (conserve and gauntlet to leyline, pensive to
gauntlet, tome to memory-palace), so it could not answer the one
question it exists for. The generator is the authority; this pins the
file to it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "docs" / "plugin-dependencies.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from generate_dependency_map import (
    find_plugins,
    generate_map,  # noqa: E402 - scripts/ goes on sys.path first
    scan_python_imports,
)


def _reverse_index(manifest: dict) -> dict[str, list[str]]:
    return {plugin: sorted(deps) for plugin, deps in manifest["reverse_index"].items()}


def test_manifest_reverse_index_matches_the_generator() -> None:
    committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = generate_map(REPO_ROOT / "plugins")
    assert _reverse_index(committed) == _reverse_index(generated), (
        "docs/plugin-dependencies.json is stale; run "
        "`uv run python scripts/generate_dependency_map.py`"
    )


def test_manifest_names_only_real_plugins() -> None:
    """The generator drops plugins with no cross-plugin dependency (phantom
    stands alone), so the index is a subset of the plugin set, never wider.
    """
    committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugins = {
        p.name
        for p in (REPO_ROOT / "plugins").iterdir()
        if (p / ".claude-plugin" / "plugin.json").is_file()
    }
    assert set(committed["reverse_index"]) <= plugins
    assert set(committed["dependencies"]) <= plugins


def test_the_four_edges_the_review_found_are_declared() -> None:
    committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = _reverse_index(committed)
    assert "leyline" in index["conserve"]
    assert "leyline" in index["gauntlet"]
    assert "gauntlet" in index["pensive"]
    assert "memory-palace" in index["tome"]


def test_every_runtime_edge_is_declared_by_its_consumer() -> None:
    """ADR-0001: the manifest says what the code does.

    Build-time edges (abstract's tooling) are exempt by the ADR. A
    runtime import a consumer does not declare is invisible to anyone
    reading its plugin.json before changing the provider. The manifest
    merges edge types per provider, and abstract is "build+runtime", so
    the runtime edges come from the generator's import scan per consumer.
    """
    plugins_dir = REPO_ROOT / "plugins"
    names = find_plugins(plugins_dir)
    undeclared = []
    for consumer in names:
        plugin_dir = plugins_dir / consumer
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        declared = json.loads(manifest.read_text(encoding="utf-8"))
        for edge in scan_python_imports(plugin_dir, consumer, names):
            if edge["plugin"] not in declared.get("dependencies", []):
                undeclared.append(f"{consumer} -> {edge['plugin']} ({edge['reason']})")
    assert undeclared == []
