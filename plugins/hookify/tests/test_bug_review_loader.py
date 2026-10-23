"""Regression tests for malformed rule files that crashed the loader."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import ConfigLoader  # noqa: E402 - path injected above

GOOD_RULE = """---
name: good-rule
enabled: true
event: bash
pattern: rm
---
msg
"""


def _write(directory: Path, name: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"hookify.{name}.local.md").write_text(text)


@pytest.mark.parametrize(
    "conditions",
    [
        "conditions:\n  - field: command\n    operator: contains\n",
        "conditions:\n",
        "conditions: nope\n",
    ],
)
def test_malformed_conditions_skip_only_that_rule(
    tmp_path: Path, conditions: str
) -> None:
    """One bad rule must not stop the rest from loading."""
    _write(tmp_path, "good", GOOD_RULE)
    _write(
        tmp_path,
        "bad",
        f"---\nname: bad\nenabled: true\nevent: bash\n{conditions}---\nmsg\n",
    )
    loader = ConfigLoader(user_rules_dir=tmp_path, include_bundled=False)

    rules = loader.load_all_rules()

    assert [r.name for r in rules] == ["good-rule"]
    assert len(loader.load_errors) == 1
