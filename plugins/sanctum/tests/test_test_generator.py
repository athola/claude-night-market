"""Tests for test_generator.py script."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "test_generator.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("sanctum_test_generator", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_test_generator"] = module
    spec.loader.exec_module(module)
    return module


def _make_source(tmp_path: Path) -> Path:
    src = tmp_path / "calculator.py"
    src.write_text(
        "def add(x, y):\n"
        "    return x + y\n"
        "\n"
        "def _hidden():\n"
        "    return 0\n"
        "\n"
        "class Calculator:\n"
        "    def multiply(self, a, b):\n"
        "        return a * b\n"
        "\n"
        "    def _internal(self):\n"
        "        return 1\n"
    )
    return src


def test_test_style_enum_values():
    module = _load_script()
    assert module.TestStyle.PYTEST_BDD.value == "pytest_bdd"
    assert module.TestStyle.DOCSTRING_BDD.value == "docstring_bdd"
    assert module.TestStyle.GHERKIN.value == "gherkin"


def test_test_config_defaults_true():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    assert cfg.include_fixtures
    assert cfg.include_edge_cases
    assert cfg.include_error_cases
    assert cfg.output_path is None


def test_extract_functions_skips_underscored(tmp_path):
    module = _load_script()
    src = _make_source(tmp_path)
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    tree = _ast.parse(src.read_text())
    functions = g._extract_functions(tree)
    names = {f.name for f in functions}
    assert "add" in names
    assert "_hidden" not in names
    assert "multiply" in names  # public method walked from tree
    assert "_internal" not in names


def test_extract_classes_returns_top_level(tmp_path):
    module = _load_script()
    src = _make_source(tmp_path)
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    tree = _ast.parse(src.read_text())
    classes = g._extract_classes(tree)
    assert any(c.name == "Calculator" for c in classes)


def test_extract_function_params_lists_arg_names():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    func = _ast.parse("def f(a, b, c): pass").body[0]
    assert g._extract_function_params(func) == ["a", "b", "c"]


def test_generate_test_header_pytest_bdd():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    out = g._generate_test_header("calc")
    assert "import pytest" in out
    assert "from calc import *" in out


def test_generate_test_header_docstring_bdd():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.DOCSTRING_BDD)
    g = module.TestGenerator(cfg)
    out = g._generate_test_header("calc")
    assert "BDD" in out
    assert "from calc import *" in out


def test_generate_test_header_gherkin():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.GHERKIN)
    g = module.TestGenerator(cfg)
    out = g._generate_test_header("calc")
    assert "behave" in out
    assert "Feature: calc" in out


def test_generate_fixtures_pytest_bdd_uses_pytest_fixture():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    out = g._generate_fixtures()
    assert "@pytest.fixture" in out


def test_generate_fixtures_gherkin_uses_steps():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.GHERKIN)
    g = module.TestGenerator(cfg)
    out = g._generate_fixtures()
    assert "@given" in out
    assert "@when" in out
    assert "@then" in out


def test_generate_pytest_bdd_test_includes_error_case():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    out = g._generate_pytest_bdd_test("foo", ["x"])
    assert "test_foo_with_valid_input" in out
    assert "test_foo_with_invalid_input" in out  # error case included


def test_generate_pytest_bdd_test_omits_error_case_when_disabled():
    module = _load_script()
    cfg = module.TestConfig(
        style=module.TestStyle.PYTEST_BDD, include_error_cases=False
    )
    g = module.TestGenerator(cfg)
    out = g._generate_pytest_bdd_test("foo", [])
    assert "test_foo_with_valid_input" in out
    assert "test_foo_with_invalid_input" not in out


def test_generate_docstring_test_uses_docstring_format():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.DOCSTRING_BDD)
    g = module.TestGenerator(cfg)
    out = g._generate_docstring_test("baz", ["a", "b"])
    assert "def test_baz_behavior" in out
    assert "GIVEN" in out
    assert "WHEN calling baz(a, b)" in out


def test_generate_gherkin_scenario_phrasing():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.GHERKIN)
    g = module.TestGenerator(cfg)
    out = g._generate_gherkin_scenario("login", ["user"])
    assert "Scenario: login with valid user" in out


def test_generate_gherkin_scenario_default_when_no_params():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.GHERKIN)
    g = module.TestGenerator(cfg)
    out = g._generate_gherkin_scenario("ping", [])
    assert "required parameters" in out


def test_generate_class_test_emits_setup_method():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    cls = _ast.parse(
        "class Foo:\n    def bar(self): pass\n    def _hidden(self): pass\n"
    ).body[0]
    out = g._generate_class_test(cls)
    assert "class TestFoo" in out
    assert "self.instance = Foo()" in out
    assert "test_bar_behavior" in out


def test_generate_method_test_pytest_bdd():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    method = _ast.parse("def bar(self): pass").body[0]
    out = g._generate_method_test(method, "Foo")
    assert "test_bar_behavior" in out
    assert "Foo()" in out


def test_generate_method_test_docstring_bdd():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.DOCSTRING_BDD)
    g = module.TestGenerator(cfg)
    import ast as _ast

    method = _ast.parse("def bar(self): pass").body[0]
    out = g._generate_method_test(method, "Foo")
    assert "test_bar_behavior" in out
    assert "GIVEN" in out


def test_generate_method_test_gherkin_placeholder():
    module = _load_script()
    cfg = module.TestConfig(style=module.TestStyle.GHERKIN)
    g = module.TestGenerator(cfg)
    import ast as _ast

    method = _ast.parse("def bar(self): pass").body[0]
    out = g._generate_method_test(method, "Foo")
    assert "Scenario:" in out


def test_generate_from_source_end_to_end(tmp_path):
    module = _load_script()
    src = _make_source(tmp_path)
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    out = g.generate_from_source(src)
    # Top-level function `add` produces a valid-input test
    assert "test_add_with_valid_input" in out
    assert "TestCalculator" in out


def test_save_test_file_writes_to_default_location(tmp_path):
    module = _load_script()
    src = _make_source(tmp_path)
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD)
    g = module.TestGenerator(cfg)
    out_path = g.save_test_file("# generated\n", src)
    assert out_path.exists()
    assert out_path.name == "test_calculator.py"
    assert out_path.parent.name == "tests"


def test_save_test_file_honors_explicit_output_path(tmp_path):
    module = _load_script()
    src = _make_source(tmp_path)
    out_target = tmp_path / "custom_output.py"
    cfg = module.TestConfig(style=module.TestStyle.PYTEST_BDD, output_path=out_target)
    g = module.TestGenerator(cfg)
    out_path = g.save_test_file("# generated\n", src)
    assert out_path == out_target
    assert out_target.read_text() == "# generated\n"


def test_main_no_args_prints_help(monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(sys, "argv", ["test_generator.py"])
    module.main()
    out = capsys.readouterr().out
    assert "Generate test scaffolding" in out


def test_main_source_human_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    src = _make_source(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_generator.py", "--source", str(src)],
    )
    module.main()
    out = capsys.readouterr().out
    assert "Generated test file" in out
    assert "Style: pytest_bdd" in out


def test_main_source_json_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    src = _make_source(tmp_path)
    output = tmp_path / "out.py"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "test_generator.py",
            "--source",
            str(src),
            "--output",
            str(output),
            "--style",
            "docstring_bdd",
            "--no-fixtures",
            "--no-edge-cases",
            "--no-error-cases",
            "--output-json",
        ],
    )
    module.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload.get("success") is True
    assert payload["data"]["fixtures_included"] is False
    assert payload["data"]["edge_cases_included"] is False
    assert payload["data"]["error_cases_included"] is False


def test_main_source_missing_human_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_generator.py", "--source", str(tmp_path / "missing.py")],
    )
    module.main()
    out = capsys.readouterr().out
    assert "Source file not found" in out


def test_main_source_missing_json_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "test_generator.py",
            "--source",
            str(tmp_path / "missing.py"),
            "--output-json",
        ],
    )
    module.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload.get("success") is False
    assert "not found" in (payload.get("error", "") or json.dumps(payload))


def test_main_module_emits_not_implemented(monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_generator.py", "--module", "anything"],
    )
    module.main()
    out = capsys.readouterr().out
    assert "not yet implemented" in out.lower()


def test_main_handles_internal_exception(tmp_path, monkeypatch, capsys):
    module = _load_script()
    src = _make_source(tmp_path)

    def _boom(self, source_path):  # noqa: ARG001 - test stub matches mocked interface
        raise RuntimeError("kaboom")

    monkeypatch.setattr(module.TestGenerator, "generate_from_source", _boom)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_generator.py", "--source", str(src)],
    )
    module.main()
    out = capsys.readouterr().out
    assert "kaboom" in out
