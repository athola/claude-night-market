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


PLUGIN = Path(__file__).parent.parent


def _rule_file(path: Path) -> RuleEngine:
    return RuleEngine([ConfigLoader(include_bundled=False).load_rule(path)])


def _command_example(tmp_path: Path) -> RuleEngine:
    text = (PLUGIN / "commands" / "hookify.md").read_text(encoding="utf-8")
    block = re.search(r"```yaml\n(---\nname: require-tests\n.*?)```", text, re.DOTALL)
    assert block, "no require-tests yaml block in commands/hookify.md"
    rule_file = tmp_path / "rule.md"
    rule_file.write_text(block.group(1), encoding="utf-8")
    return _rule_file(rule_file)


def _bundled_example(tmp_path: Path) -> RuleEngine:
    source = PLUGIN / "examples" / "require-tests.local.md"
    # The example ships disabled; the copy is enabled to test its condition.
    rule_file = tmp_path / "rule.md"
    rule_file.write_text(
        source.read_text(encoding="utf-8").replace(
            "enabled: false", "enabled: true", 1
        ),
        encoding="utf-8",
    )
    return _rule_file(rule_file)


def test_command_require_tests_example_is_quiet_when_tests_ran(
    tmp_path: Path,
) -> None:
    """The /hookify example used the same literal `npm test|pytest`."""
    engine = _command_example(tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "ran pytest -q: 12 passed"})
    assert not any(r.matched for r in results)


def test_command_require_tests_example_warns_when_no_tests_ran(
    tmp_path: Path,
) -> None:
    engine = _command_example(tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "edited app.py"})
    assert any(r.matched for r in results)


def test_bundled_require_tests_example_is_quiet_when_tests_ran(
    tmp_path: Path,
) -> None:
    """examples/require-tests.local.md used `not_contains` with alternation."""
    engine = _bundled_example(tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "ran cargo test: ok"})
    assert not any(r.matched for r in results)


def test_bundled_require_tests_example_warns_when_no_tests_ran(
    tmp_path: Path,
) -> None:
    engine = _bundled_example(tmp_path)
    results = engine.evaluate_event("stop", {"transcript": "edited app.py"})
    assert any(r.matched for r in results)
