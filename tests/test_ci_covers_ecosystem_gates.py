"""Guard that the ecosystem CI trigger covers everything its gates read.

``ecosystem-tests.yml`` runs the root ``tests/`` suite, but only when a
changed file matches one of its ``paths:`` entries. Two gates in that
suite sweep the repository with their own globs:

- ``test_cited_paths_resolve.py`` reads every skill, command, agent, and
  project-rule document and fails on a citation that does not resolve.
- ``test_assets_respect_enforced_vows.py`` reads the same set and fails
  on an instruction a PreToolUse vow blocks.

Nothing kept the two lists in step, and they had already drifted:

- The gates read ``.claude/rules/*.md``. The workflow filter did not
  mention ``.claude/`` at all, so a rule file could gain a phantom
  citation and no PR would run the gate that catches it.
- The gates read ``plugins/*/skills/**/*.md``, which is every module
  file under a skill. The filter listed only ``plugins/**/SKILL.md``,
  so an edit confined to ``modules/`` skipped the gate.

Both gaps are silent by construction. A path filter that is too narrow
does not fail; it reports success by not running, which is the same
shape as the auto-fixing pre-commit hook in discussion #614 and the
canary assertion in #626. The check has to be that the *trigger* covers
the *sweep*, not that either one looks reasonable alone.

This test derives both sides from their sources rather than restating
them. Adding a glob to a gate, or narrowing the workflow filter, fails
here until the two agree.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ecosystem-tests.yml"

# Gates whose module-level ASSET_GLOBS define what the suite reads.
GATE_MODULES = (
    "test_cited_paths_resolve.py",
    "test_assets_respect_enforced_vows.py",
)


def _load_asset_globs() -> dict[str, tuple[str, ...]]:
    """Import each gate by file path and read its ASSET_GLOBS."""
    globs: dict[str, tuple[str, ...]] = {}
    for name in GATE_MODULES:
        path = Path(__file__).parent / name
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        globs[name] = tuple(module.ASSET_GLOBS)
    return globs


def _github_glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a GitHub ``paths:`` filter into an anchored regex.

    ``**`` crosses directory separators, ``*`` and ``?`` do not. A
    pattern ending in ``/`` or ``**`` matches everything beneath it.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    body = "".join(out)
    if pattern.endswith("/"):
        body += ".*"
    return re.compile(rf"^{body}$")


def _workflow_path_filters() -> list[re.Pattern[str]]:
    config = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML parses the unquoted key `on:` as the boolean True.
    triggers = config.get("on", config.get(True))
    assert triggers, f"{WORKFLOW.name} declares no triggers"

    patterns: list[str] = []
    for event in ("push", "pull_request"):
        spec = triggers.get(event)
        if isinstance(spec, dict):
            patterns.extend(spec.get("paths", []))
    assert patterns, f"{WORKFLOW.name} declares no path filters"
    return [_github_glob_to_regex(p) for p in patterns]


def _swept_files() -> dict[str, list[str]]:
    """Repo-relative files each gate reads, keyed by gate module."""
    swept: dict[str, list[str]] = {}
    for name, globs in _load_asset_globs().items():
        found: list[str] = []
        for pattern in globs:
            found.extend(
                str(p.relative_to(REPO_ROOT))
                for p in REPO_ROOT.glob(pattern)
                if p.is_file()
            )
        swept[name] = sorted(set(found))
    return swept


def test_gate_sweeps_are_not_empty() -> None:
    """Guard the globs themselves: an empty sweep would pass vacuously."""
    for name, files in _swept_files().items():
        assert len(files) > 100, f"{name} swept only {len(files)} files"


def test_workflow_filters_are_not_empty() -> None:
    """Guard the other side: no filters would match every file trivially."""
    assert len(_workflow_path_filters()) > 1


@pytest.mark.parametrize("gate", GATE_MODULES)
def test_ci_trigger_covers_every_file_the_gate_reads(gate: str) -> None:
    """Every file a gate reads must be able to trigger the gate."""
    filters = _workflow_path_filters()
    uncovered = [
        path for path in _swept_files()[gate] if not any(f.match(path) for f in filters)
    ]

    assert not uncovered, (
        f"{gate} reads {len(uncovered)} file(s) that no `paths:` entry in "
        f"{WORKFLOW.name} matches, so changing them runs no gate:\n  "
        + "\n  ".join(uncovered[:20])
        + (f"\n  ... and {len(uncovered) - 20} more" if len(uncovered) > 20 else "")
    )
