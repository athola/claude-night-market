"""Precision cases for the Tier 1 scan, from the 2026-11-25 full-repo run.

Each scenario is a receiver or call shape the scan reported on this
repository's own source although the code cannot be slow in the way the
finding says: a membership test against a set or dict, or a method that
delegates to a module function of the same name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from pensive.skills.performance_review import PerformanceReviewSkill

if TYPE_CHECKING:
    from pathlib import Path


def _membership_findings(code: str, file_path: str = "module.py") -> list[str]:
    context = Mock()
    context.get_file_content.return_value = code
    result = PerformanceReviewSkill().analyze(context, file_path)
    return [f.message for f in result.issues if f.message.startswith("Membership")]


def _recursion_findings(code: str) -> list[str]:
    context = Mock()
    context.get_file_content.return_value = code
    result = PerformanceReviewSkill().analyze(context, "module.py")
    return [f.message for f in result.issues if f.message.startswith("Recursive")]


@pytest.mark.unit
@pytest.mark.parametrize(
    "annotation",
    ["set[str]", "frozenset[str]", "dict[str, int]", "Mapping[str, int]", "Set[str]"],
)
def test_membership_against_a_param_annotated_as_hashed_is_not_reported(
    annotation: str,
) -> None:
    code = (
        f"def pick(names: list[str], seen: {annotation}) -> list[str]:\n"
        "    out = []\n"
        "    for name in names:\n"
        "        if name in seen:\n"
        "            out.append(name)\n"
        "    return out\n"
    )
    assert _membership_findings(code) == []


@pytest.mark.unit
def test_membership_against_an_annotated_local_set_is_not_reported() -> None:
    code = (
        "def pick(names, load):\n"
        "    seen: set[str] = load()\n"
        "    return [n for n in names if n in seen]\n"
        "def walk(names, load):\n"
        "    seen: set[str] = load()\n"
        "    for n in names:\n"
        "        if n in seen:\n"
        "            yield n\n"
    )
    assert _membership_findings(code) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "binding",
    [
        "allowed = base | extra",
        "allowed = base - removed",
        "allowed = base & extra",
        "allowed = loaded or {}",
        "allowed = loaded or frozenset()",
        "allowed = mapping.get(key, set())",
    ],
)
def test_membership_against_set_algebra_or_an_empty_hashed_fallback_is_not_reported(
    binding: str,
) -> None:
    code = (
        "def pick(names, base, extra, removed, loaded, mapping, key):\n"
        f"    {binding}\n"
        "    for name in names:\n"
        "        if name in allowed:\n"
        "            yield name\n"
    )
    assert _membership_findings(code) == []


@pytest.mark.unit
def test_membership_against_a_list_fallback_is_still_reported() -> None:
    code = (
        "def pick(names, loaded):\n"
        "    allowed = loaded or []\n"
        "    for name in names:\n"
        "        if name in allowed:\n"
        "            yield name\n"
    )
    assert len(_membership_findings(code)) == 1


@pytest.mark.unit
def test_membership_against_a_set_imported_from_a_sibling_module_is_not_reported(
    tmp_path: Path,
) -> None:
    (tmp_path / "models.py").write_text(
        'EXCLUDED: set[str] = {".git", "node_modules"}\n'
        'SKIP = frozenset({"build"})\n'
        'ORDERED = [".git", "dist"]\n',
        encoding="utf-8",
    )
    code = (
        "from .models import EXCLUDED, ORDERED\n"
        "from models import SKIP\n"
        "def scan(entries):\n"
        "    for entry in entries:\n"
        "        if entry in EXCLUDED or entry in SKIP:\n"
        "            continue\n"
        "        if entry in ORDERED:\n"
        "            yield entry\n"
    )
    found = _membership_findings(code, str(tmp_path / "scanner.py"))
    assert len(found) == 1
    assert "in ORDERED" in found[0]


@pytest.mark.unit
def test_a_method_delegating_to_a_same_named_function_is_not_recursion() -> None:
    code = (
        "def load_session(store, key):\n"
        "    return store[key]\n"
        "class Orchestrator:\n"
        "    def load_session(self, key):\n"
        "        return load_session(self.store, key)\n"
        "    @staticmethod\n"
        "    def list_sessions(store):\n"
        "        return list_sessions(store)\n"
    )
    assert _recursion_findings(code) == []


@pytest.mark.unit
def test_a_function_nested_in_a_method_that_calls_itself_is_still_recursion() -> None:
    code = (
        "class Walker:\n"
        "    def run(self, node):\n"
        "        def visit(n):\n"
        "            for child in n.children:\n"
        "                visit(child)\n"
        "        visit(node)\n"
    )
    assert len(_recursion_findings(code)) == 1


@pytest.mark.unit
@pytest.mark.parametrize(
    "binding",
    [
        "allowed = given if given is not None else DEFAULTS",
        "allowed = data.get('weights', {}) if isinstance(data, dict) else None",
        "rows, allowed, total = [], set(), 0",
        "allowed = load_table(text)",
    ],
)
def test_membership_against_a_conditional_unpacked_or_typed_return_is_not_reported(
    binding: str,
) -> None:
    code = (
        "DEFAULTS: frozenset[str] = frozenset({'a'})\n"
        "def load_table(text: str) -> dict[str, int]:\n"
        "    return {}\n"
        "def pick(names, given: set[str] | None, data, text):\n"
        f"    {binding}\n"
        "    for name in names:\n"
        "        if name in allowed:\n"
        "            yield name\n"
    )
    assert _membership_findings(code) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "binding",
    [
        "allowed = given if given is not None else []",
        "rows, allowed = set(), []",
        "allowed = load_rows(text)",
    ],
)
def test_membership_against_a_possible_list_is_still_reported(binding: str) -> None:
    code = (
        "def load_rows(text: str) -> list[str]:\n"
        "    return []\n"
        "def pick(names, given: set[str] | None, text):\n"
        f"    {binding}\n"
        "    for name in names:\n"
        "        if name in allowed:\n"
        "            yield name\n"
    )
    assert len(_membership_findings(code)) == 1
