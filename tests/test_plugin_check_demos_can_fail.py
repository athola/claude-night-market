"""A plugin-check demo fails when the tool it demonstrates fails.

Root ``make plugin-check`` sums each plugin's exit status. conserve's
``demo-tokens`` fell back, inside ``../abstract``, to a skill path that
does not exist there and then to an ``echo`` that always succeeds.
abstract's ``demo-verify`` ended both verifier calls in ``|| true``. An
import error in either script still reported the plugin as passed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGINS = Path(__file__).resolve().parents[1] / "plugins"


def _recipe(plugin: str, target: str) -> str:
    text = (PLUGINS / plugin / "Makefile").read_text()
    match = re.search(rf"^{re.escape(target)}:.*\n((?:\t.*\n)+)", text, re.M)
    assert match, f"{plugin} has no {target} target"
    return match.group(1)


@pytest.mark.parametrize(
    ("plugin", "target"), [("conserve", "demo-tokens"), ("abstract", "demo-verify")]
)
def test_the_demo_does_not_mask_a_failure(plugin: str, target: str) -> None:
    recipe = _recipe(plugin, target)
    assert "|| true" not in recipe
    assert "|| \\" not in recipe
    assert "|| echo" not in recipe


def test_demo_verify_checks_each_verdict() -> None:
    recipe = _recipe("abstract", "demo-verify")
    assert "skip_promotion: False" in recipe
    assert "skip_promotion: True" in recipe
