"""Behavior tests for the bundled block-force-push rule.

The rule ANDed two unanchored regexes, so a `-f` inside a branch name and a
`main` anywhere else in the command chain combined into a block.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hookify.core.config_loader import ConfigLoader
from hookify.core.rule_engine import RuleEngine

RULE_FILE = (
    Path(__file__).parent.parent
    / "skills"
    / "rule-catalog"
    / "rules"
    / "git"
    / "block-force-push.md"
)


@pytest.fixture()
def engine() -> RuleEngine:
    rule = ConfigLoader(include_bundled=True).load_rule(RULE_FILE, source="bundled")
    return RuleEngine([rule])


def _blocked(engine: RuleEngine, command: str) -> bool:
    return any(r.matched for r in engine.evaluate_event("bash", {"command": command}))


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin docs/imbue-feature-flags && git checkout main",
        "git push origin docs-fix",
        "git push --force-with-lease origin main",
        "git push -f origin feature/x && git log main",
        "git push origin remaster",
        "git push --follow-tags origin main",
    ],
)
def test_force_push_rule_allows_ordinary_and_lease_pushes(
    engine: RuleEngine, command: str
) -> None:
    assert not _blocked(engine, command)


@pytest.mark.parametrize(
    "command",
    [
        "git push -f origin main",
        "git push --force origin master",
        "git push origin main --force",
        "git push origin +main",
        "git push origin +HEAD:master",
        "git push -uf origin main",
        "cd repo && git push --force origin main",
        "git push -f origin refs/heads/main",
        "git push --force origin HEAD:refs/heads/master",
        "git push origin +refs/heads/main",
    ],
)
def test_force_push_rule_blocks_force_pushes_to_main(
    engine: RuleEngine, command: str
) -> None:
    assert _blocked(engine, command)
