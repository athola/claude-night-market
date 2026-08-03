"""Every repo path cited in a workflow asset must exist on disk.

`.claude/rules/slop-scan-for-docs.md` Layer 0 makes this a P0 rule:
"every cited file path ... must resolve to a real thing". Nothing
enforced it, so the same defect kept arriving through review instead of
through a gate. Discussions #604, #610, #623, and PR findings B3/B4 on
PR #417 are five instances of one bug: a SKILL.md pointing at a file
that was renamed, never written, or deleted underneath it.

A phantom citation is worse than a missing one. An agent that follows
`plugins/gauntlet/hooks/pr_blast_radius.py:52-56` for the "exact code
shape" gets nothing back and has no signal that the instruction was
wrong rather than its own lookup.

Scope: skills, commands, agents, and project rules -- the documents an
agent reads as instructions. Prose docs and the changelog are excluded;
they narrate history, and history legitimately references files that no
longer exist.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories whose markdown an agent consumes as instructions.
ASSET_GLOBS = (
    "plugins/*/skills/**/*.md",
    "plugins/*/commands/**/*.md",
    "plugins/*/agents/**/*.md",
    ".claude/rules/*.md",
)

# Path-shaped tokens are only checked when rooted at one of these, so
# that `foo/bar` in prose and `os/path` in a docstring stay out of it.
TRACKED_ROOTS = (
    "plugins/",
    "scripts/",
    "tests/",
    "docs/",
    ".claude/",
    ".github/",
)

# A backticked token: a rooted path, optional :line or :line-line suffix.
CITATION = re.compile(
    r"`(?P<path>(?:" + "|".join(re.escape(r) for r in TRACKED_ROOTS) + r")[^`\s]+)`"
)

# Tokens carrying any of these are templates, globs, or prose, not paths.
PLACEHOLDER_CHARS = set("<>{}*?|$")

# Paths a workflow *writes* rather than reads, and paths that are worked
# examples rather than references. A citation only earns a place here by
# being one of those two things -- "it does not exist yet" is the defect
# this gate catches, not an excuse for entering it here.
#
# Directories and pytest node IDs are filtered structurally below, so
# this list holds only file paths.
ALLOWLIST = {
    # --- Artifacts the workflow creates on the user's machine ---
    # The decision journal's two logs; created on first write, and
    # lessons-learned.md is already present. See leyline:decision-journal.
    "docs/tradeoffs.md",
    # doc-consolidation routes content here; a destination, not a source.
    "docs/migration-guide.md",
    # Scaffolded into *target* projects by attune, never into this repo.
    ".github/workflows/test.yml",
    ".github/workflows/validate-hooks.yml",
    "docs/project-brief.md",
    "docs/specification.md",
    "docs/implementation-plan.md",
    "docs/quickstart.md",
    "docs/crypto-inventory.md",
    "docs/benchmarks.md",
    "docs/tutorials/quickstart.md",
    "docs/knowledge-corpus/queue/README.md",
    "docs/playbooks/release-train-health.md",
    ".claude/hookify.block-force-push.local.md",
    ".claude/hookify.dangerous-rm.local.md",
    # Runtime state written by hooks and the continuation agent.
    ".claude/scheduled_tasks.json",
    ".claude/session-state.md.bak",
    # Config attune tells the user to add to *their* project.
    ".claude/config.md",
    # Component-level pre-commit scripts attune scaffolds downstream.
    "scripts/run-component-lint.sh",
    "scripts/run-component-tests.sh",
    "scripts/run-component-typecheck.sh",
    # --- Worked examples in authoring guides ---
    "plugins/your-plugin/skills/your-skill/SKILL.md",
    "docs/adr/0001-architecture-choice.md",
    "docs/api.md",
    "docs/specs/feature-user-authentication.md",
    "docs/plans/component-authentication.md",
    "docs/modular-skills/guide.md",
    "tests/test_foo.py",
    "tests/test_file1.py",
    "tests/conftest.py",
    "tests/integration/test_full_flow.py",
    "tests/unit/x.py",
}


def _iter_assets() -> list[Path]:
    seen: list[Path] = []
    for pattern in ASSET_GLOBS:
        seen.extend(sorted(REPO_ROOT.glob(pattern)))
    return seen


def _strip_code_blocks(text: str) -> str:
    """Drop fenced blocks: shell examples cite paths that need not exist."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def _citations(text: str) -> set[str]:
    found = set()
    for match in CITATION.finditer(_strip_code_blocks(text)):
        raw = match.group("path")
        # Trim a trailing :12 or :12-30 line reference, then an anchor.
        path = re.sub(r":\d+(?:-\d+)?$", "", raw)
        path = path.split("#", 1)[0]
        path = path.rstrip(".,;:)")
        if PLACEHOLDER_CHARS & set(path):
            continue
        # A pytest node ID names a test, not a file to read.
        if "::" in path:
            path = path.split("::", 1)[0]
        # Directory citations are conventions ("drop reports in tests/"),
        # not instructions to open a specific document.
        if path.endswith("/"):
            continue
        if path in ALLOWLIST:
            continue
        found.add(path)
    return found


def _owning_plugin(asset: Path) -> Path | None:
    """Return the plugin root that owns ``asset``, if any."""
    rel = asset.relative_to(REPO_ROOT).parts
    if len(rel) >= 2 and rel[0] == "plugins":
        return REPO_ROOT / "plugins" / rel[1]
    return None


def _resolves(citation: str, asset: Path) -> bool:
    """A citation resolves against the repo root or its own plugin.

    Inside `plugins/foo/skills/bar/SKILL.md`, `scripts/x.py` means
    `plugins/foo/scripts/x.py` -- every plugin carries its own scripts/
    and hooks/ directories, and the docs address them unprefixed. Both
    readings are checked so the convention is not reported as a defect.
    """
    if (REPO_ROOT / citation).exists():
        return True
    plugin = _owning_plugin(asset)
    return plugin is not None and (plugin / citation).exists()


def _phantoms(asset: Path) -> list[str]:
    text = asset.read_text(encoding="utf-8", errors="replace")
    return sorted(c for c in _citations(text) if not _resolves(c, asset))


ASSETS = _iter_assets()


def test_assets_are_discovered() -> None:
    """Guard the glob itself: an empty sweep would pass everything."""
    assert len(ASSETS) > 100, f"only {len(ASSETS)} workflow assets found"


@pytest.mark.parametrize("asset", ASSETS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_cited_paths_resolve(asset: Path) -> None:
    """Every rooted repo path cited outside a code block must exist."""
    phantoms = _phantoms(asset)
    assert not phantoms, (
        f"{asset.relative_to(REPO_ROOT)} cites "
        f"{len(phantoms)} path(s) that do not exist: " + ", ".join(phantoms)
    )
