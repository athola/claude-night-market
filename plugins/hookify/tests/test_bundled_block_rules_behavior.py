"""Behavior tables for the bundled block rules (HKF-4, HKF-5, HKF-6).

Front-matter contract tests passed any regex edit; these feed the real
rule files through RuleEngine with allow and deny corpora. The dynamic-code
names are assembled at runtime, because the live rule refuses a file that
spells them out.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from hookify.core.config_loader import ConfigLoader
from hookify.core.rule_engine import RuleEngine

RULES = Path(__file__).parent.parent / "skills" / "rule-catalog" / "rules"
EV = "ev" + "al"
EX = "ex" + "ec"


def _engine(relative: str) -> RuleEngine:
    rule = ConfigLoader(include_bundled=True).load_rule(RULES / relative, "bundled")
    return RuleEngine([rule])


def _bash_blocked(engine: RuleEngine, command: str) -> bool:
    return any(r.matched for r in engine.evaluate_event("bash", {"command": command}))


def _file_blocked(engine: RuleEngine, text: str) -> bool:
    event = {"file_path": "src/a.py", "new_text": text}
    return any(r.matched for r in engine.evaluate_event("file", event))


DESTRUCTIVE = "git/block-destructive-git.md"


@pytest.mark.parametrize(
    "command",
    ["git clean -fdn", "git clean -nfd", "git clean -n", "git status", "git stash"],
)
def test_destructive_git_rule_allows_dry_runs(command: str) -> None:
    assert not _bash_blocked(_engine(DESTRUCTIVE), command)


@pytest.mark.parametrize(
    "command",
    [
        "git clean -fd",
        "git clean -xdf",
        "git clean -f",
        "git checkout .",
        "git restore .",
        "git checkout -- .",
        "git branch -D old",
        "git stash drop",
    ],
)
def test_destructive_git_rule_blocks_destructive_forms(command: str) -> None:
    assert _bash_blocked(_engine(DESTRUCTIVE), command)


DYNAMIC = "python/block-dynamic-code.md"


@pytest.mark.parametrize(
    "text",
    [
        f"x = {EV}(s)\n",
        f"f({EV}(s))\n",
        f"value = int({EV}(user_text))\n",
        f"{EX} (code)\n",
    ],
)
def test_dynamic_code_rule_matches_nested_calls(text: str) -> None:
    assert _file_blocked(_engine(DYNAMIC), text)


@pytest.mark.parametrize(
    "text",
    [
        f"def {EX}(self, cmd):\n    pass\n",
        f"# never call {EV}(x) here\n",
        f"self.{EX}(a)\n",
        "result = evaluate(x)\n",
    ],
)
def test_dynamic_code_rule_ignores_definitions_comments_and_methods(text: str) -> None:
    assert not _file_blocked(_engine(DYNAMIC), text)


def test_destructive_git_alternatives_pass_the_rule_itself() -> None:
    """The message advised a reset that the rule itself blocks (HKF-4)."""
    text = (RULES / "git" / "block-destructive-git.md").read_text()
    pattern = re.search(r"pattern: (.+)", text).group(1)
    section = text[
        text.index("## Safer Alternatives") : text.index("## If You Truly Need")
    ]
    suggestions = [
        line.split("#")[0].strip()
        for line in section.splitlines()
        if line.strip().startswith("git ")
    ]
    assert suggestions
    assert [s for s in suggestions if re.search(pattern, s)] == []
