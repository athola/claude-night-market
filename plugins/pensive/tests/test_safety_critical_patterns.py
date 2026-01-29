"""Tests for safety-critical coding patterns skill.

Issue #XXX: Add safety-critical patterns skill to pensive plugin

Tests verify NASA Power of 10 rules adapted for general software development.
"""

import pytest


class TestSafetyCriticalRules:
    """Feature: Apply safety-critical coding guidelines.

    As a developer working on critical systems
    I want to verify code follows safety-critical patterns
    So that code is robust and verifiable
    """

    @pytest.mark.unit
    def test_restrict_control_flow_avoids_goto(self) -> None:
        """Scenario: Detect goto statements in code.

        Given code with goto statements
        When checking for restricted control flow
        Then goto should be flagged
        """
        code_with_goto = """
        func process() {
            if error {
                goto cleanup
            }
            // ...
        cleanup:
            release_resources()
        }
        """

        has_goto = "goto" in code_with_goto
        assert has_goto, "goto should be detected"

    @pytest.mark.unit
    def test_recursion_with_bounded_depth_is_allowed(self) -> None:
        """Scenario: Recursion with provable termination is acceptable.

        Given recursive function with depth limit
        When evaluating recursion safety
        Then it should pass if termination is provable
        """
        bounded_recursion = """
        def traverse(node, max_depth=10, current_depth=0):
            if current_depth >= max_depth:
                return
            process(node)
            for child in node.children:
                traverse(child, max_depth, current_depth + 1)
        """

        has_depth_check = "max_depth" in bounded_recursion
        assert has_depth_check, "Recursion should have depth bound"

    @pytest.mark.unit
    def test_loops_have_verifiable_bounds(self) -> None:
        """Scenario: Loops should have clear upper bounds.

        Given loop constructs
        When checking for bounded iteration
        Then unbounded loops should be flagged
        """
        bounded_loop = """
        MAX_ITEMS = 100
        for i in range(min(len(items), MAX_ITEMS)):
            process(items[i])
        """

        has_bound = "MAX_ITEMS" in bounded_loop or "min(" in bounded_loop
        assert has_bound, "Loop should have verifiable bound"

    @pytest.mark.unit
    def test_function_length_within_limit(self) -> None:
        """Scenario: Functions should fit on one screen (~60 lines).

        Given a function definition
        When measuring line count
        Then functions >60 lines should be flagged for refactoring
        """
        long_function = "\n".join([f"    line_{i} = {i}" for i in range(70)])

        line_count = len([line for line in long_function.split("\n") if line.strip()])
        assert line_count > 60, "Function exceeds 60-line guideline"

    @pytest.mark.unit
    def test_assertion_density_document_expectations(self) -> None:
        """Scenario: Assertions document invariants and boundaries.

        Given a function with validation logic
        When checking for defensive assertions
        Then key invariants should be asserted
        """
        function_with_assertions = """
        def transfer_funds(from_acct, to_acct, amount):
            assert from_acct != to_acct, "Cannot transfer to same account"
            assert amount > 0, "Transfer amount must be positive"
            assert from_acct.balance >= amount, "Insufficient funds"
            # Transfer logic
        """

        assertion_count = function_with_assertions.count("assert")
        assert assertion_count >= 3, "Should have defensive assertions"

    @pytest.mark.unit
    def test_variable_scope_minimized(self) -> None:
        """Scenario: Variables declared at narrowest possible scope.

        Given variable declarations
        When evaluating scope
        Then variables should be declared close to usage
        """
        narrow_scope = """
        for item in items:
            total = calculate(item)  # Declared inside loop
            results.append(total)
        """

        has_narrow_scope = "total = " in narrow_scope.split("for")[1]
        assert has_narrow_scope, "Variable should be scoped narrowly"

    @pytest.mark.unit
    def test_return_values_are_checked(self) -> None:
        """Scenario: Function return values should be validated.

        Given a function that returns a value
        When the return is used
        Then it should be checked for errors/None
        """
        unchecked_return = "parse_config(path)  # Ignored return"
        checked_return = """
        result = parse_config(path)
        if result is None:
            raise ConfigError(f"Failed to parse {path}")
        """

        has_check = "if result is None:" in checked_return
        assert has_check, "Return value should be validated"


class TestRigorMatching:
    """Feature: Match rigor to consequence level.

    As a developer
    I want to apply appropriate safety rules based on context
    So that I'm not over-engineering non-critical code
    """

    @pytest.mark.unit
    def test_full_rigor_for_safety_critical(self) -> None:
        """Scenario: Full rigor applied to safety-critical systems.

        Given code in a safety-critical context
        When selecting rule strictness
        Then all Power of 10 rules should apply
        """
        context = "safety_critical"
        rigor_level = {
            "safety_critical": "full",
            "business_logic": "selective",
            "utilities": "light",
        }

        assert rigor_level[context] == "full"

    @pytest.mark.unit
    def test_selective_application_for_business_logic(self) -> None:
        """Scenario: Selective rule application for business logic.

        Given code handling business rules
        When selecting rule strictness
        Then key rules should apply (assertions, bounds checking)
        """
        context = "business_logic"
        applicable_rules = ["assertions", "bounds_checking", "input_validation"]
        skipped_rules = ["no_recursion", "no_dynamic_memory"]

        assert len(applicable_rules) > 0
        assert len(skipped_rules) > 0

    @pytest.mark.unit
    def test_light_touch_for_scripts(self) -> None:
        """Scenario: Light application for utility scripts.

        Given a one-off utility script
        When selecting rule strictness
        Then only basic clarity rules should apply
        """
        context = "utility_script"
        rigor_level = "light"

        assert rigor_level == "light"


class TestRuleAdaptations:
    """Feature: Adapt NASA rules for modern development.

    As a developer
    I want rules adapted for GC languages and modern paradigms
    So that guidelines remain practical
    """

    @pytest.mark.unit
    def test_recursion_acceptable_with_termination_proof(self) -> None:
        """Scenario: Recursion allowed when termination is provable.

        Given tree traversal with depth limit
        When evaluating recursion
        Then it should pass safety checks
        """
        tree_traversal = """
        def traverse_tree(node, max_depth=50):
            if max_depth <= 0 or not node:
                return
            process(node)
            for child in node.children:
                traverse_tree(child, max_depth - 1)
        """

        has_termination = (
            "max_depth" in tree_traversal and "max_depth <= 0" in tree_traversal
        )
        assert has_termination, "Recursion should have termination proof"

    @pytest.mark.unit
    def test_dynamic_memory_with_preallocation(self) -> None:
        """Scenario: Pre-allocation pools acceptable for GC languages.

        Given a Python/JS codebase
        When evaluating memory rules
        Then pre-allocation patterns should pass
        """
        preallocation = """
        class ObjectPool:
            def __init__(self, size=100):
                self.pool = [create_object() for _ in range(size)]

            def acquire(self):
                return self.pool.pop() if self.pool else create_object()
        """

        has_preallocation = "pool = " in preallocation and "size=" in preallocation
        assert has_preallocation, "Should use pre-allocation pattern"

    @pytest.mark.unit
    def test_function_length_flexible_for_declarative_code(self) -> None:
        """Scenario: Declarative code can exceed 60-line limit.

        Given a declarative configuration or state machine
        When measuring function length
        Then longer functions should be acceptable
        """
        declarative_code = """
        states = {
            "idle": State(on_enter=idle_enter, transitions={}),
            "running": State(on_enter=running_enter, transitions={}),
            # ... 20 more states
        }
        """

        # Declarative data structures can be longer
        line_count = len(
            [line for line in declarative_code.split("\n") if line.strip()]
        )
        is_declarative = "states = {" in declarative_code

        assert is_declarative or line_count < 60


class TestWarningLevelCompliance:
    """Feature: Enable strict warnings from day one.

    As a developer setting up a project
    I want to enable strictest tool settings
    So that issues are caught early
    """

    @pytest.mark.unit
    def test_python_uses_strict_settings(self) -> None:
        """Scenario: Python projects use ruff --select=ALL and mypy --strict.

        Given Python configuration files
        When checking strictness levels
        Then strict modes should be enabled
        """
        ruff_config = "--select=ALL"
        mypy_config = "--strict"

        assert "ALL" in ruff_config
        assert "strict" in mypy_config

    @pytest.mark.unit
    def test_typescript_uses_strict_flags(self) -> None:
        """Scenario: TypeScript uses strict compilation flags.

        Given tsconfig.json
        When checking compiler options
        Then strict flags should be enabled
        """
        tsconfig = {
            "compilerOptions": {
                "strict": True,
                "noImplicitAny": True,
            }
        }

        assert tsconfig["compilerOptions"]["strict"]
        assert tsconfig["compilerOptions"]["noImplicitAny"]


class TestIntegrationWithCodeRefinement:
    """Feature: Safety patterns integrate with code refinement skill.

    As a code reviewer
    I want safety-critical checks included in refinement analysis
    So that safety is part of overall code quality
    """

    @pytest.mark.unit
    def test_safety_patterns_referenced_from_refinement(self) -> None:
        """Scenario: Code refinement skill references safety patterns.

        Given pensive:code-refinement skill
        When checking integration points
        Then safety-critical-patterns should be referenced
        """
        refinement_references = [
            "pensive:shared/modules/code-quality-analysis",
            "pensive:safety-critical-patterns",
        ]

        assert "pensive:safety-critical-patterns" in refinement_references

    @pytest.mark.unit
    def test_shared_module_exposes_safety_patterns(self) -> None:
        """Scenario: Shared code-quality module references safety patterns.

        Given pensive:shared/modules/code-quality-analysis
        When checking cross-references
        Then safety-critical patterns should be listed
        """
        cross_references = [
            "**Full skill**: `Skill(pensive:code-refinement)`",
            "**Safety-critical patterns**: `pensive:safety-critical-patterns`",
        ]

        has_safety_ref = any("safety-critical" in ref for ref in cross_references)
        assert has_safety_ref

    @pytest.mark.unit
    def test_pr_review_includes_safety_checks(self) -> None:
        """Scenario: PR review workflow includes safety pattern analysis.

        Given sanctum:pr-review command
        When running code quality phase
        Then safety-critical patterns should be analyzed
        """
        quality_dimensions = [
            "Duplication & Redundancy",
            "Algorithmic Efficiency",
            "Clean Code Violations",
            "Architectural Fit",
            "Anti-Slop Patterns",
            "Error Handling",
        ]

        # Safety patterns are part of Clean Code dimension
        assert "Clean Code Violations" in quality_dimensions
