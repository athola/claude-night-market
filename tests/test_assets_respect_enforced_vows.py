"""Workflow assets must not instruct actions the hooks refuse.

A skill that hands the agent a commit template containing
`Co-Authored-By: Claude` is not a style problem. `vow_no_ai_attribution`
runs at PreToolUse and blocks that exact string, so the agent composes
the commit, the hook rejects it, and the agent has to rediscover the
project rule from a denial message. The instruction and the enforcement
disagree, and the enforcement wins every time.

`plugins/sanctum/skills/workflow-improvement/SKILL.md` shipped that
contradiction. This gate keeps the instruction side aligned with the
vow that is already enforced at runtime.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ASSET_GLOBS = (
    "plugins/*/skills/**/*.md",
    "plugins/*/commands/**/*.md",
    "plugins/*/agents/**/*.md",
    ".claude/rules/*.md",
)

# The trailer form vow_no_ai_attribution blocks. Matching the trailer
# rather than the bare word keeps prose that *discusses* the rule --
# the hook's own docstring, this file, the README -- out of scope.
AI_TRAILER = re.compile(
    r"(?:Co-?authored-by|Generated-by|Assisted-by)\s*:\s*"
    r"[^\n]*\b(?:claude|opus|sonnet|haiku|anthropic|gpt|copilot|cursor)\b",
    re.IGNORECASE,
)

# Assets whose subject *is* the rule, and so must quote the banned form.
DOCUMENTS_THE_RULE = {
    "plugins/imbue/skills/vow-enforcement/SKILL.md",
}


def _iter_assets() -> list[Path]:
    seen: list[Path] = []
    for pattern in ASSET_GLOBS:
        seen.extend(sorted(REPO_ROOT.glob(pattern)))
    return seen


ASSETS = _iter_assets()


def test_assets_are_discovered() -> None:
    """Guard the glob: an empty sweep would pass everything."""
    assert len(ASSETS) > 100, f"only {len(ASSETS)} workflow assets found"


@pytest.mark.parametrize("asset", ASSETS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_ai_attribution_trailer(asset: Path) -> None:
    """No asset may hand the agent an AI-attribution commit trailer."""
    rel = str(asset.relative_to(REPO_ROOT))
    if rel in DOCUMENTS_THE_RULE:
        pytest.skip("documents the banned form on purpose")
    hits = AI_TRAILER.findall(asset.read_text(encoding="utf-8", errors="replace"))
    assert not hits, (
        f"{rel} contains an AI-attribution trailer that "
        f"plugins/imbue/hooks/vow_no_ai_attribution.py blocks at "
        f"PreToolUse: {hits}"
    )
