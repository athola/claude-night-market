"""The writing-rules examples behave as their prose says.

A reader copies these blocks verbatim, so an example whose operator does
not do what its name suggests ships a broken rule to every copier.
"""

from __future__ import annotations

import re
from pathlib import Path

from hookify.core.config_loader import ConfigLoader
from hookify.core.rule_engine import RuleEngine

SKILL = Path(__file__).parent.parent / "skills" / "writing-rules" / "SKILL.md"


def _example(heading: str, tmp_path: Path) -> RuleEngine:
    text = SKILL.read_text(encoding="utf-8")
    section = text.split(f"### {heading}", 1)[1]
    block = re.search(r"```yaml\n(.*?)```", section, re.DOTALL)
    assert block, f"no yaml block under {heading}"
    rule_file = tmp_path / "rule.md"
    rule_file.write_text(block.group(1), encoding="utf-8")
    rule = ConfigLoader(include_bundled=False).load_rule(rule_file)
    return RuleEngine([rule])


def test_require_tests_is_quiet_when_tests_ran(tmp_path: Path) -> None:
    """`not_contains` is a substring test, so `pytest|npm test` never matched."""
    engine = _example("Require Tests", tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "ran pytest -q: 12 passed"})
    assert not any(r.matched for r in results)


def test_require_tests_warns_when_no_tests_ran(tmp_path: Path) -> None:
    """The rule still fires on a session that ran nothing."""
    engine = _example("Require Tests", tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "edited app.py\nlooks good"})
    assert any(r.matched for r in results)
