"""Contract tests for the safety-critical-patterns skill.

The skill is Markdown that a model follows, so the shipped file is the
subject. Each test pins one statement the skill makes about the NASA
Power of 10 adaptation, and fails when that statement is edited away.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml

PENSIVE = Path(__file__).resolve().parents[1]
SKILL_FILE = PENSIVE / "skills" / "safety-critical-patterns" / "SKILL.md"
REFINEMENT_SKILL = PENSIVE / "skills" / "code-refinement" / "SKILL.md"
QUALITY_MODULE = (
    PENSIVE / "skills" / "code-refinement" / "modules" / "code-quality-analysis.md"
)

RULE_NAMES = [
    (1, "Restrict Control Flow"),
    (2, "Fixed Loop Bounds"),
    (3, "No Dynamic Memory After Initialization"),
    (4, "Function Length ~60 Lines"),
    (5, "Assertion Density"),
    (6, "Minimal Variable Scope"),
    (7, "Check Return Values and Parameters"),
    (8, "Limited Preprocessor/Metaprogramming"),
    (9, "Pointer/Reference Discipline"),
    (10, "Enable All Warnings"),
]


def _read(path: Path) -> str:
    if not path.exists():
        pytest.fail(f"missing: {path}")
    return path.read_text(encoding="utf-8")


def _rule_section(number: int) -> str:
    """Return the text under `### {number}. ...` up to the next heading."""
    skill = _read(SKILL_FILE)
    match = re.search(rf"^### {number}\. .*?(?=^##+ |\Z)", skill, re.M | re.S)
    if match is None:
        pytest.fail(f"rule {number} section not found in {SKILL_FILE.name}")
    return match.group(0)


def _python_blocks(section: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", section, re.S)


def _block_after(section: str, marker: str) -> str:
    """Return the code between a `# marker` comment and the next blank line."""
    match = re.search(rf"# {re.escape(marker)}[^\n]*\n(.*?)(?:\n\n|\Z)", section, re.S)
    if match is None:
        pytest.fail(f"no code under marker {marker!r}")
    return match.group(1)


def _frontmatter(path: Path) -> dict:
    text = _read(path)
    end = text.find("\n---\n", 4)
    return yaml.safe_load(text[4:end])


class TestSafetyCriticalRules:
    """The skill states ten numbered rules, each with checkable content."""

    @pytest.mark.unit
    @pytest.mark.parametrize(("number", "name"), RULE_NAMES)
    def test_rule_is_listed_under_its_number(self, number: int, name: str) -> None:
        assert f"### {number}. {name}\n" in _read(SKILL_FILE)

    @pytest.mark.unit
    def test_skill_has_exactly_ten_numbered_rules(self) -> None:
        headings = re.findall(r"^### (\d+)\. ", _read(SKILL_FILE), re.M)

        assert headings == [str(number) for number in range(1, 11)]

    @pytest.mark.unit
    def test_control_flow_rule_names_goto_setjmp_and_recursion(self) -> None:
        section = _rule_section(1)

        assert "`goto`" in section
        assert "`setjmp/longjmp`" in section
        assert "limit recursion" in section

    @pytest.mark.unit
    def test_control_flow_rule_allows_recursion_only_with_provable_termination(
        self,
    ) -> None:
        assert "Recursion acceptable with provable termination" in _rule_section(1)

    @pytest.mark.unit
    def test_loop_rule_shows_a_bounded_loop_as_good_and_while_as_risky(self) -> None:
        section = _rule_section(2)

        good = _block_after(section, "Good")
        risky = _block_after(section, "Risky")

        assert "min(len(items), MAX_ITEMS)" in good
        assert risky.startswith("while not_done:")

    @pytest.mark.unit
    def test_function_length_rule_sets_sixty_lines_and_relaxes_declarative_code(
        self,
    ) -> None:
        section = _rule_section(4)

        assert "~60 Lines" in section
        assert "Flexible for declarative code" in section

    @pytest.mark.unit
    def test_assertion_rule_example_asserts_three_invariants(self) -> None:
        (example,) = _python_blocks(_rule_section(5))

        function = ast.parse(example).body[0]
        assertions = [
            node for node in ast.walk(function) if isinstance(node, ast.Assert)
        ]

        assert len(assertions) == 3

    @pytest.mark.unit
    def test_scope_rule_good_example_declares_the_variable_inside_the_loop(
        self,
    ) -> None:
        (example,) = _python_blocks(_rule_section(6))
        good = _block_after(example, "Good")
        avoid = _block_after(example, "Avoid")

        good_tree = ast.parse(good)
        avoid_tree = ast.parse(avoid)
        # A name is tightly scoped when no assignment to it precedes the loop.
        good_top_level_targets = [
            target.id
            for node in good_tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
        avoid_top_level_targets = [
            target.id
            for node in avoid_tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        assert "total" not in good_top_level_targets
        assert "total" in avoid_top_level_targets

    @pytest.mark.unit
    def test_return_value_rule_good_example_raises_on_none_and_bad_ignores_it(
        self,
    ) -> None:
        (example,) = _python_blocks(_rule_section(7))
        good = _block_after(example, "Good")
        bad = _block_after(example, "Bad")

        assert "if result is None:" in good
        assert "raise ConfigError" in good
        assert "result" not in bad

    @pytest.mark.unit
    def test_warning_rule_requires_strictest_python_and_typescript_settings(
        self,
    ) -> None:
        section = _rule_section(10)

        assert "ruff check --select=ALL" in section
        assert "mypy --strict" in section
        assert "tsc --strict --noImplicitAny" in section


class TestRigorMatching:
    """The skill ties rule strictness to consequence level."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("level", "applies_to"),
        [
            ("Full rigor", "Safety-critical systems"),
            ("Selective application", "Business logic"),
            ("Light touch", "Scripts, prototypes"),
        ],
    )
    def test_rigor_level_is_assigned_to_its_context(
        self, level: str, applies_to: str
    ) -> None:
        line = next(
            ln for ln in _read(SKILL_FILE).splitlines() if ln.startswith(f"**{level}")
        )

        assert applies_to in line


class TestRuleAdaptations:
    """The skill lists the rules it relaxes and the context for each."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("rule", "relaxed_when"),
        [
            ("No recursion", "Tree traversal"),
            ("No dynamic memory", "GC languages"),
            ("60-line functions", "Declarative configs"),
            ("No function pointers", "Callbacks"),
        ],
    )
    def test_relaxation_table_row_names_when_the_rule_bends(
        self, rule: str, relaxed_when: str
    ) -> None:
        rows = [
            ln for ln in _read(SKILL_FILE).splitlines() if ln.startswith(f"| {rule} ")
        ]

        assert len(rows) == 1
        assert relaxed_when in rows[0]

    @pytest.mark.unit
    def test_dynamic_memory_rule_adapts_to_preallocated_pools(self) -> None:
        assert "Pre-allocate pools" in _rule_section(3)


class TestViolationReporting:
    """Every violation is reported in the shape the verifier can check."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "field", ["Rule N:", "Location:", "Anchor:", "Issue:", "Fix:"]
    )
    def test_violation_format_carries_field(self, field: str) -> None:
        skill = _read(SKILL_FILE)
        block = skill.split("## Violation Output Format", 1)[1].split("###", 1)[0]

        assert field in block

    @pytest.mark.unit
    def test_exit_criteria_require_a_verdict_for_each_of_the_ten_rules(self) -> None:
        exit_criteria = _read(SKILL_FILE).split("## Exit Criteria", 1)[1]

        assert "Each of the 10 rules has an explicit verdict" in exit_criteria


class TestIntegrationWithCodeRefinement:
    """Other pensive and sanctum surfaces reach this skill by name."""

    @pytest.mark.unit
    def test_code_refinement_declares_a_dependency_on_the_skill(self) -> None:
        dependencies = _frontmatter(REFINEMENT_SKILL)["dependencies"]

        assert "pensive:safety-critical-patterns" in dependencies

    @pytest.mark.unit
    def test_code_quality_module_cross_references_the_skill(self) -> None:
        assert (
            "**Safety-critical patterns**: `pensive:safety-critical-patterns`"
            in _read(QUALITY_MODULE)
        )

    @pytest.mark.unit
    def test_skill_lists_code_refinement_among_its_callers(self) -> None:
        integration = _read(SKILL_FILE).split("## Integration", 1)[1]

        assert "`pensive:code-refinement`" in integration.split("##", 1)[0]
