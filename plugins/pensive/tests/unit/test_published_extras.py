"""Published extras must resolve from PyPI, not only from uv path sources.

``[tool.uv.sources]`` is honored by uv inside this checkout and dropped
from the built wheel's metadata. An extra naming a package that exists
only as a local path source is published as a bare name anyone can
register on PyPI.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11; pytest depends on tomli there
    import tomli as tomllib

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _requirement_name(requirement: str) -> str:
    return re.split(r"[\s\[<>=!~;]", requirement, maxsplit=1)[0].lower()


def test_no_extra_depends_on_a_path_only_package() -> None:
    config = tomllib.loads(PYPROJECT.read_text())
    path_sources = {
        name.lower()
        for name, source in config.get("tool", {})
        .get("uv", {})
        .get("sources", {})
        .items()
        if "path" in source
    }
    extras = config["project"].get("optional-dependencies", {})
    offenders = {
        extra: name
        for extra, requirements in extras.items()
        for name in map(_requirement_name, requirements)
        if name in path_sources
    }
    assert not offenders, f"extras name path-only packages: {offenders}"


def test_tiers_extra_installs_the_tree_sitter_grammars() -> None:
    config = tomllib.loads(PYPROJECT.read_text())
    tiers = config["project"]["optional-dependencies"]["tiers"]
    assert "tree-sitter-language-pack" in map(_requirement_name, tiers)
