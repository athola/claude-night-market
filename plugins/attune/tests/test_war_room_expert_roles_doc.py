"""The war-room expert-roles module must name the experts conjure runs.

The module once carried a hand-copied registry with fields the code had
dropped (``dangerous``, ``command_resolver``) and panels it no longer
used, so a reader configuring an expert followed a shape that did not
exist. The table is pinned to ``EXPERT_CONFIGS`` by key.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DOC = _REPO / "plugins/attune/skills/war-room-playbook/modules/expert-roles.md"
_EXPERTS = _REPO / "plugins/conjure/scripts/war_room/experts.py"


def _registered_experts() -> set[str]:
    tree = ast.parse(_EXPERTS.read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "EXPERT_CONFIGS"
            and isinstance(node.value, ast.Dict)
        ):
            return {
                key.value for key in node.value.keys if isinstance(key, ast.Constant)
            }
    raise AssertionError("EXPERT_CONFIGS not found in experts.py")


def test_the_expert_table_lists_exactly_the_registered_experts() -> None:
    """A registry change without a doc change turns this red."""
    doc = _DOC.read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| `([a-z_]+)` \|", doc, flags=re.MULTILINE))
    assert listed == _registered_experts()


def test_the_module_names_no_field_the_config_lacks() -> None:
    """Fields ExpertConfig dropped must not reappear as configuration advice."""
    doc = _DOC.read_text(encoding="utf-8")
    for dropped in ('"dangerous"', "command_resolver", "fallback_command"):
        assert dropped not in doc, dropped
