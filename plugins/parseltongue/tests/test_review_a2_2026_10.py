"""Regression tests for the A2 review findings (parseltongue analysis)."""

from __future__ import annotations

import ast
import json
import textwrap
from typing import TYPE_CHECKING

import pytest

from parseltongue.analysis.async_analysis import (
    analyze_complex_scenarios,
    analyze_event_loop_usage,
    analyze_performance,
    analyze_timeouts,
    detect_blocking_calls,
    detect_missing_await,
)
from parseltongue.analysis.code_transformation import CodeTransformationSkill
from parseltongue.analysis.compatibility_checker import CompatibilityChecker
from parseltongue.analysis.pattern_matching import PatternMatchingSkill
from parseltongue.analysis.testing_guide import TestingGuideSkill, analyze_testing
from parseltongue.cli import main

if TYPE_CHECKING:
    from pathlib import Path

skill = TestingGuideSkill()


# --- A2-4: async tests and async source functions are seen ------------------


@pytest.mark.unit
async def test_async_test_functions_are_counted() -> None:
    result = await analyze_testing(
        "async def load():\n    return 1\n\ndef parse():\n    return 2\n",
        "async def test_load():\n    assert await load() == 1\n",
    )

    assert result["findings"]["test_analysis"]["test_count"] == 1
    assert "load" in result["findings"]["source_analysis"]["public_functions"]
    missing = [
        r["function"] for r in result["recommendations"] if r["type"] == "missing_test"
    ]
    assert missing == ["parse"]


@pytest.mark.unit
def test_async_test_methods_appear_in_test_structure() -> None:
    structure = skill.analyze_test_structure("async def test_load():\n    pass\n")

    names = [m["name"] for m in structure["test_structure"]["test_methods"]]
    assert names == ["test_load"]


@pytest.mark.unit
def test_async_source_methods_count_in_coverage_gaps() -> None:
    result = skill.analyze_coverage_gaps(
        "async def load():\n    return 1\n",
        "async def test_load():\n    assert await load() == 1\n",
    )

    assert result["coverage_analysis"]["uncovered_methods"] == []
    assert result["coverage_analysis"]["estimated_coverage"] == 100


@pytest.mark.unit
def test_async_test_without_assert_is_flagged() -> None:
    result = skill.identify_anti_patterns("async def test_x():\n    pass\n")

    assert result["anti_patterns"]["no_assertions"] is True


# --- A2-5: "assert" in a name, comment or docstring is not an assertion -----


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        "def test_assert_nothing():\n    pass\n",
        "def test_x():\n    # assert later\n    pass\n",
        'def test_x():\n    """Does not assert."""\n',
    ],
)
def test_word_assert_outside_a_statement_does_not_count(source: str) -> None:
    result = skill.identify_anti_patterns(source)

    assert result["anti_patterns"]["no_assertions"] is True


@pytest.mark.unit
def test_pytest_raises_counts_as_an_assertion() -> None:
    source = (
        "import pytest\n\n"
        "def test_x():\n"
        "    with pytest.raises(ValueError):\n"
        "        int('a')\n"
    )

    result = skill.identify_anti_patterns(source)

    assert "no_assertions" not in result["anti_patterns"]


@pytest.mark.unit
def test_self_fail_counts_as_an_assertion() -> None:
    source = "def test_x(self):\n    self.fail('boom')\n"

    result = skill.identify_anti_patterns(source)

    assert "no_assertions" not in result["anti_patterns"]


# --- A2-6: missing_test needs a whole-token match ---------------------------


@pytest.mark.unit
async def test_test_name_containing_function_name_as_substring_is_not_coverage() -> (
    None
):
    result = await analyze_testing(
        "def add():\n    return 1\n",
        "def test_address_parsed():\n    assert True\n",
    )

    missing = [
        r["function"] for r in result["recommendations"] if r["type"] == "missing_test"
    ]
    assert missing == ["add"]


@pytest.mark.unit
async def test_test_name_with_function_as_underscore_run_is_coverage() -> None:
    result = await analyze_testing(
        "def add():\n    return 1\n",
        "def test_add_returns_one():\n    assert True\n",
    )

    assert not [r for r in result["recommendations"] if r["type"] == "missing_test"]


# --- A2-21: branch labels come from the source, not a keyword guess ---------


@pytest.mark.unit
def test_error_word_in_source_without_raise_adds_no_uncovered_branch() -> None:
    source = (
        "def f(x):\n    # ErrorCode lookup\n    if x:\n        return 1\n    return 2\n"
    )

    result = skill.analyze_coverage_gaps(source, "def test_f():\n    assert f(1)\n")

    assert result["coverage_analysis"]["uncovered_branches"] == []


@pytest.mark.unit
def test_untested_raised_exception_is_named_as_uncovered_branch() -> None:
    source = "def f(x):\n    if x < 0:\n        raise ValueError('neg')\n    return x\n"

    result = skill.analyze_coverage_gaps(source, "def test_f():\n    assert f(1)\n")

    assert result["coverage_analysis"]["uncovered_branches"] == ["ValueError"]


@pytest.mark.unit
def test_tested_raised_exception_is_not_uncovered() -> None:
    source = "def f(x):\n    if x < 0:\n        raise ValueError('neg')\n    return x\n"
    tests = (
        "import pytest\n\n"
        "def test_f():\n"
        "    with pytest.raises(ValueError):\n"
        "        f(-1)\n"
    )

    result = skill.analyze_coverage_gaps(source, tests)

    assert result["coverage_analysis"]["uncovered_branches"] == []


@pytest.mark.unit
def test_exception_and_stdlib_constructors_are_not_fixture_candidates() -> None:
    source = (
        "def test_a():\n"
        "    p = Path('x')\n"
        "    with pytest.raises(ValueError):\n"
        "        raise ValueError('a')\n"
        "    assert p\n"
    )

    result = skill.identify_anti_patterns(source)

    assert "no_fixture_reuse" not in result["anti_patterns"]


@pytest.mark.unit
def test_fixture_recommendation_is_not_repeated_per_instantiation() -> None:
    source = (
        "def test_a():\n"
        "    a = Service()\n"
        "    b = Service()\n"
        "    c = Service()\n"
        "    assert a and b and c\n"
    )

    result = skill.identify_anti_patterns(source)

    recs = result["anti_patterns"]["recommendations"]
    assert recs.count("Use fixtures for shared setup") == 1


# --- A2-20: generated test names are valid identifiers ----------------------


@pytest.mark.unit
def test_tdd_case_names_are_valid_identifiers() -> None:
    result = skill.recommend_tdd_workflow("- Validate: input\n- **Auth** works")

    for step in result["tdd_workflow"]["steps"]:
        for name in step["test_cases"]:
            assert name.isidentifier(), name


# --- A2-7: transform_code rewrites the AST and the output parses ------------


async def _transform(code: str) -> dict:
    return await CodeTransformationSkill().transform_code(code)


@pytest.mark.unit
async def test_dict_method_call_is_not_rewritten() -> None:
    result = await _transform("d = model.dict()\n")

    assert result["transformed_code"] == "d = model.dict()\n"


@pytest.mark.unit
async def test_bare_dict_call_becomes_literal() -> None:
    result = await _transform("d = dict()\n")

    assert result["transformed_code"] == "d = {}\n"


@pytest.mark.unit
async def test_dict_call_inside_string_literal_is_untouched() -> None:
    code = 'print("use dict() here")\n'

    result = await _transform(code)

    assert result["transformed_code"] == code


@pytest.mark.unit
async def test_format_with_two_placeholders_and_one_arg_is_left_alone() -> None:
    code = 'msg = "a {} b {}".format(x)\n'

    result = await _transform(code)

    ast.parse(result["transformed_code"])
    assert result["transformed_code"] == code


@pytest.mark.unit
async def test_single_placeholder_format_becomes_fstring() -> None:
    result = await _transform('msg = "hi {}!".format(name)\n')

    assert result["transformed_code"] == 'msg = f"hi {name}!"\n'


@pytest.mark.unit
async def test_matching_placeholder_count_becomes_fstring() -> None:
    result = await _transform('msg = "{} and {}".format(a, b)\n')

    assert result["transformed_code"] == 'msg = f"{a} and {b}"\n'


@pytest.mark.unit
async def test_percent_s_becomes_fstring() -> None:
    result = await _transform("msg = '%s' % name\n")

    assert result["transformed_code"] == "msg = f'{name}'\n"


@pytest.mark.unit
async def test_list_generator_becomes_comprehension() -> None:
    result = await _transform("xs = list(x for x in items)\n")

    assert result["transformed_code"] == "xs = [x for x in items]\n"


@pytest.mark.unit
async def test_list_generator_with_filter_is_left_alone() -> None:
    code = "xs = list(x for x in items if x)\n"

    result = await _transform(code)

    assert result["transformed_code"] == code


@pytest.mark.unit
async def test_transformed_code_always_parses() -> None:
    code = textwrap.dedent(
        """
        a = dict()
        b = model.dict()
        c = "x {}".format(a)
        d = "{} {}".format(a)
        e = tuple(x for x in a)
        s = "dict() list(x for x in y)"
        """
    )

    result = await _transform(code)

    ast.parse(result["transformed_code"])


# --- A2-8: check_compatibility ----------------------------------------------


@pytest.mark.unit
def test_unparseable_code_uses_regex_features_for_minimum_version() -> None:
    report = CompatibilityChecker().check_compatibility(
        "match x:\n case 1: pass\n", ["3.8", "3.9", "3.10", "3.11"]
    )

    # Parses on 3.10+, fails on older interpreters; either way the
    # match statement fixes the minimum.
    assert report["minimum_version"] == "3.10"
    assert report["compatible_versions"] == ["3.10", "3.11"]


@pytest.mark.unit
def test_unparseable_code_without_features_reports_error() -> None:
    report = CompatibilityChecker().check_compatibility("def (:\n", ["3.9"])

    assert report["error"]
    assert report["compatible_versions"] == []


@pytest.mark.unit
def test_bitwise_or_dict_value_is_not_a_union_type() -> None:
    report = CompatibilityChecker().check_compatibility('FLAGS = {"a": X | Y}\n')

    assert report["minimum_version"] == "3.0"


@pytest.mark.unit
def test_union_annotation_requires_310() -> None:
    report = CompatibilityChecker().check_compatibility("def f(x: int | str): ...\n")

    assert report["minimum_version"] == "3.10"


@pytest.mark.unit
def test_union_return_annotation_requires_310() -> None:
    report = CompatibilityChecker().check_compatibility("def f() -> int | None: ...\n")

    assert report["minimum_version"] == "3.10"


@pytest.mark.unit
def test_malformed_target_version_raises_named_error() -> None:
    with pytest.raises(ValueError, match="py39"):
        CompatibilityChecker().check_compatibility("x = 1\n", ["py39"])


# --- A2-9: call matching and missing-await ----------------------------------


@pytest.mark.unit
async def test_receiver_get_calls_are_not_requests() -> None:
    code = (
        "async def f(self):\n    x = os.environ.get('A')\n    y = self.cache.get('k')\n"
    )

    result = await detect_blocking_calls(code)

    assert "requests" not in result["blocking_patterns"]


@pytest.mark.unit
async def test_bare_get_call_is_not_requests() -> None:
    result = await detect_blocking_calls("async def f():\n    get('k')\n")

    assert "requests" not in result["blocking_patterns"]


@pytest.mark.unit
async def test_requests_get_is_still_blocking() -> None:
    result = await detect_blocking_calls(
        "async def f():\n    requests.get('http://x')\n"
    )

    assert "requests" in result["blocking_patterns"]


@pytest.mark.unit
async def test_asyncio_sleep_is_not_blocking() -> None:
    result = await detect_blocking_calls("async def f():\n    await asyncio.sleep(1)\n")

    assert "time_sleep" not in result["blocking_patterns"]


@pytest.mark.unit
async def test_missing_await_ignores_calls_to_non_async_names() -> None:
    code = "async def f():\n    x = budget(1)\n    y = d.get('k')\n"

    result = await detect_missing_await(code)

    assert result["missing_awaits"] == {}


@pytest.mark.unit
async def test_missing_await_flags_bare_coroutine_call_statement() -> None:
    code = "async def fetch():\n    return 1\n\nasync def f():\n    fetch()\n"

    result = await detect_missing_await(code)

    assert result["missing_awaits"]["f"]["line_number"] == 5


@pytest.mark.unit
async def test_missing_await_flags_assignment_from_coroutine() -> None:
    code = "async def fetch():\n    return 1\n\nasync def f():\n    x = fetch()\n"

    result = await detect_missing_await(code)

    assert result["missing_awaits"]["f"]["line_number"] == 5


@pytest.mark.unit
async def test_missing_await_keeps_every_line_for_a_function() -> None:
    code = (
        "async def fetch():\n    return 1\n\n"
        "async def f():\n    a = fetch()\n    b = fetch()\n"
    )

    result = await detect_missing_await(code)

    assert result["missing_awaits"]["f"]["line_numbers"] == [5, 6]


@pytest.mark.unit
async def test_awaited_coroutine_is_not_flagged() -> None:
    code = "async def fetch():\n    return 1\n\nasync def f():\n    x = await fetch()\n"

    result = await detect_missing_await(code)

    assert result["missing_awaits"] == {}


# --- A2-10: cache stampede -------------------------------------------------


@pytest.mark.unit
async def test_future_import_is_not_stampede_protection() -> None:
    result = await analyze_complex_scenarios(
        "from __future__ import annotations\nclass Cache: pass\n"
    )

    cache = result["complex_analysis"]["cache_anti_pattern"]
    assert cache["prevents_cache_stampede"] is False
    assert cache["uses_futures"] is False


@pytest.mark.unit
async def test_create_task_counts_as_futures_and_stampede_protection() -> None:
    code = "import asyncio\nclass Cache:\n    def f(self):\n        asyncio.create_task(g())\n"

    result = await analyze_complex_scenarios(code)

    cache = result["complex_analysis"]["cache_anti_pattern"]
    assert cache["prevents_cache_stampede"] is True
    assert cache["uses_futures"] is True


@pytest.mark.unit
async def test_lock_prevents_stampede_without_using_futures() -> None:
    code = "import asyncio\nclass Cache:\n    lock = asyncio.Lock()\n"

    result = await analyze_complex_scenarios(code)

    cache = result["complex_analysis"]["cache_anti_pattern"]
    assert cache["prevents_cache_stampede"] is True
    assert cache["uses_futures"] is False


# --- A2-18: heuristics that cannot fail or mis-report -----------------------


@pytest.mark.unit
async def test_file_close_is_not_event_loop_close() -> None:
    result = await analyze_event_loop_usage("def f(fh):\n    fh.close()\n")

    cleanup = result["event_loop_analysis"]["cleanup_patterns"]
    assert cleanup["proper_loop_close"] is False


@pytest.mark.unit
async def test_loop_close_is_event_loop_close() -> None:
    code = "def f():\n    loop = asyncio.new_event_loop()\n    loop.close()\n"

    result = await analyze_event_loop_usage(code)

    cleanup = result["event_loop_analysis"]["cleanup_patterns"]
    assert cleanup["proper_loop_close"] is True


@pytest.mark.unit
async def test_tuple_handler_with_timeout_error_is_detected() -> None:
    code = (
        "async def f():\n"
        "    try:\n"
        "        await asyncio.wait_for(g(), 1)\n"
        "    except (asyncio.TimeoutError, OSError):\n"
        "        pass\n"
    )

    result = await analyze_timeouts(code)

    assert result["timeout_analysis"]["functions"]["f"]["handles_timeout_error"]


@pytest.mark.unit
def test_match_patterns_confidence_is_none_when_nothing_matched() -> None:
    result = PatternMatchingSkill().match_patterns("x = 1")

    assert result["patterns"] == []
    assert result["confidence"] is None


@pytest.mark.unit
async def test_dataclass_frozen_false_is_not_frozen() -> None:
    code = (
        "from dataclasses import dataclass\n\n"
        "@dataclass(frozen=False, eq=True)\n"
        "class Order:\n"
        "    id: int\n"
        "    def ship(self):\n"
        "        pass\n"
    )

    result = PatternMatchingSkill().recognize_ddd_patterns(code)

    assert "Order" in json.dumps(result["ddd_patterns"])


@pytest.mark.unit
async def test_sequential_loop_reports_no_invented_speedup() -> None:
    code = "async def f(items):\n    for i in items:\n        await g(i)\n"

    result = await analyze_performance(code)

    assert "sequential_processing" in result["performance_analysis"]["issues"]
    assert "improvement_potential" not in result["performance_analysis"]


@pytest.mark.unit
async def test_async_for_with_await_body_is_sequential() -> None:
    code = "async def f(items):\n    async for i in items:\n        await g(i)\n"

    result = await analyze_performance(code)

    assert "sequential_processing" in result["performance_analysis"]["issues"]


# --- A2-19: directory mode analyzes each file -------------------------------


@pytest.mark.unit
def test_directory_mode_reports_per_file_line_numbers(tmp_path: Path, capsys) -> None:
    (tmp_path / "a.py").write_text("async def one():\n    pass\n")
    (tmp_path / "b.py").write_text("\n\n\nasync def one():\n    pass\n")

    assert main(["analyze-async", str(tmp_path)]) == 0

    report = json.loads(capsys.readouterr().out)
    assert set(report["files"]) == {"a.py", "b.py"}
    lines = {
        name: [f["line_number"] for f in entry["async_functions"]]
        for name, entry in report["files"].items()
    }
    assert lines == {"a.py": [1], "b.py": [4]}


@pytest.mark.unit
def test_directory_mode_skips_hidden_and_venv_directories(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    for hidden in (".venv", ".git", "venv", "node_modules"):
        (tmp_path / hidden).mkdir()
        (tmp_path / hidden / "dep.py").write_text("y = 2\n")

    assert main(["analyze-async", str(tmp_path)]) == 0

    report = json.loads(capsys.readouterr().out)
    assert set(report["files"]) == {"a.py"}


@pytest.mark.unit
def test_directory_mode_fails_when_any_file_has_an_error(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "bad.py").write_text("def (:\n")

    assert main(["analyze-async", str(tmp_path)]) == 1
    capsys.readouterr()
