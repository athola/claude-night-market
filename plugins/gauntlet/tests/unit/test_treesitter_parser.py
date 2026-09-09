"""Tests for Tree-sitter AST extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("tree_sitter")

from gauntlet.models import EdgeKind, NodeKind  # noqa: E402 - must follow importorskip
from gauntlet.treesitter_parser import (  # noqa: E402 - must follow importorskip
    detect_language,
    parse_file,
)


@pytest.fixture()
def fixtures_dir(tmp_path: Path) -> Path:
    return tmp_path / "fixtures"


def _function_symbols(nodes: list) -> list[str]:
    """Return each Function node name with its file path stripped off.

    `qualified_name` embeds the absolute file path, and pytest builds
    `tmp_path` out of the test's own name. Matching a symbol against the
    whole string therefore passes whenever the test is named after the
    symbol it is looking for, which is a test that cannot fail.
    """
    return [
        node.qualified_name.split("::", 1)[1]
        for node in nodes
        if node.kind == NodeKind.FUNCTION and "::" in node.qualified_name
    ]


def _write_fixture(fixtures_dir: Path, name: str, content: str) -> Path:
    fixtures_dir.mkdir(exist_ok=True)
    fp = fixtures_dir / name
    fp.write_text(content)
    return fp


class TestLanguageDetection:
    """
    Feature: Language detection from file extension

    As a parser
    I want to detect the programming language from file extensions
    So that I use the correct Tree-sitter grammar
    """

    @pytest.mark.unit
    def test_python_detected(self) -> None:
        assert detect_language("app.py") == "python"

    @pytest.mark.unit
    def test_javascript_detected(self) -> None:
        assert detect_language("app.js") == "javascript"

    @pytest.mark.unit
    def test_typescript_detected(self) -> None:
        assert detect_language("app.ts") == "typescript"

    @pytest.mark.unit
    def test_go_detected(self) -> None:
        assert detect_language("main.go") == "go"

    @pytest.mark.unit
    def test_rust_detected(self) -> None:
        assert detect_language("lib.rs") == "rust"

    @pytest.mark.unit
    def test_unknown_returns_none(self) -> None:
        assert detect_language("data.xyz") is None


class TestParsePythonFile:
    """
    Feature: Parse Python source files

    As a graph builder
    I want to extract classes, functions, and imports from Python
    So that I can build a structural code graph
    """

    @pytest.mark.unit
    def test_extracts_function_node(self, fixtures_dir: Path) -> None:
        """
        Scenario: Extract a standalone function
        Given a Python file with a function definition
        When I parse it
        Then a Function node is created with correct line range
        """
        fp = _write_fixture(fixtures_dir, "simple.py", "def hello():\n    pass\n")
        nodes, edges = parse_file(str(fp))
        fn_nodes = [n for n in nodes if n.kind == NodeKind.FUNCTION]
        assert len(fn_nodes) >= 1
        assert any(n.qualified_name.endswith("::hello") for n in fn_nodes)

    @pytest.mark.unit
    def test_extracts_class_node(self, fixtures_dir: Path) -> None:
        """
        Scenario: Extract a class definition
        Given a Python file with a class
        When I parse it
        Then a Class node is created
        """
        fp = _write_fixture(fixtures_dir, "cls.py", "class MyClass:\n    pass\n")
        nodes, edges = parse_file(str(fp))
        cls_nodes = [n for n in nodes if n.kind == NodeKind.CLASS]
        assert len(cls_nodes) >= 1
        assert any("MyClass" in n.qualified_name for n in cls_nodes)

    @pytest.mark.unit
    def test_extracts_method_with_parent(self, fixtures_dir: Path) -> None:
        """
        Scenario: Extract a method inside a class
        Given a Python file with a class method
        When I parse it
        Then the method node has the class as parent
        """
        code = "class Foo:\n    def bar(self):\n        pass\n"
        fp = _write_fixture(fixtures_dir, "method.py", code)
        nodes, edges = parse_file(str(fp))
        methods = [n for n in nodes if n.kind == NodeKind.FUNCTION and n.parent_name]
        assert len(methods) >= 1
        assert any("Foo" in m.parent_name for m in methods)

    @pytest.mark.unit
    def test_extracts_a_nested_function(self, fixtures_dir: Path) -> None:
        """
        Scenario: A local helper defined inside a function
        Given a Python file with a function defined in another function
        When I parse it
        Then the inner function is a node too

        Closures and local helpers are ordinary Python. A graph that
        omits them reports a call site inside the helper as belonging
        to the enclosing function, which is what blast-radius analysis
        then reasons from.
        """
        code = "def outer():\n    def inner():\n        pass\n    return inner\n"
        fp = _write_fixture(fixtures_dir, "nested_fn.py", code)
        nodes, edges = parse_file(str(fp))
        symbols = _function_symbols(nodes)
        assert "outer" in symbols
        assert any(sym.endswith("inner") for sym in symbols), symbols

    @pytest.mark.unit
    def test_extracts_a_helper_nested_in_a_method(self, fixtures_dir: Path) -> None:
        """
        Scenario: A helper defined inside a class method
        Given a class whose method defines a local function
        When I parse it
        Then the helper is a node under that method
        """
        code = (
            "class Foo:\n"
            "    def method(self):\n"
            "        def helper():\n"
            "            pass\n"
            "        return helper\n"
        )
        fp = _write_fixture(fixtures_dir, "nested_method.py", code)
        nodes, edges = parse_file(str(fp))
        symbols = _function_symbols(nodes)
        assert "Foo.method" in symbols
        assert any(sym.endswith("helper") for sym in symbols), symbols

    @pytest.mark.unit
    def test_a_nested_call_is_not_attributed_to_the_parent(
        self, fixtures_dir: Path
    ) -> None:
        """
        Scenario: A call made only inside a nested function
        Given a helper that calls target() and an outer that does not
        When I parse it
        Then the CALLS edge belongs to the helper alone

        Recursing into a function body without stopping the call walk
        at the nested boundary records the call twice, once against
        each enclosing scope, and inflates the caller's blast radius.
        """
        code = "def outer():\n    def helper():\n        target()\n    return helper\n"
        fp = _write_fixture(fixtures_dir, "nested_call.py", code)
        nodes, edges = parse_file(str(fp))
        calls = [
            e for e in edges if e.kind == EdgeKind.CALLS and e.target_qn == "target"
        ]
        assert len(calls) == 1, f"expected one CALLS edge, got {calls}"
        assert "helper" in calls[0].source_qn

    @pytest.mark.unit
    def test_a_class_nested_in_a_function_is_extracted(
        self, fixtures_dir: Path
    ) -> None:
        """
        Scenario: A class defined inside a function
        Given a factory function that defines a class in its body
        When I parse it
        Then the class is a node

        GIVEN _extract_calls stops at both function and class
        boundaries
        WHEN only the function half was covered by a test
        THEN the class half of that condition was unguarded, and a
        regex or set change could drop it silently.
        """
        code = (
            "def make():\n"
            "    class Inner:\n"
            "        def method(self):\n"
            "            pass\n"
            "    return Inner\n"
        )
        fp = _write_fixture(fixtures_dir, "nested_class.py", code)
        nodes, edges = parse_file(str(fp))
        class_symbols = [
            n.qualified_name.split("::", 1)[1]
            for n in nodes
            if n.kind == NodeKind.CLASS and "::" in n.qualified_name
        ]
        assert any(sym.endswith("Inner") for sym in class_symbols), class_symbols

    @pytest.mark.unit
    def test_a_call_two_levels_deep_belongs_to_the_innermost_scope(
        self, fixtures_dir: Path
    ) -> None:
        """
        Scenario: Three nested function scopes, one call at the bottom
        Given outer contains middle contains inner, and inner calls
        When I parse it
        Then exactly one CALLS edge exists and it names inner

        GIVEN recursion and the call-walk boundary interact
        WHEN nesting goes deeper than one level
        THEN a boundary that stopped only at the first descent would
        record the call twice, so depth is the case that separates a
        correct fix from a partial one.
        """
        code = (
            "def outer():\n"
            "    def middle():\n"
            "        def inner():\n"
            "            target()\n"
            "        return inner\n"
            "    return middle\n"
        )
        fp = _write_fixture(fixtures_dir, "deep_nest.py", code)
        nodes, edges = parse_file(str(fp))
        calls = [
            e for e in edges if e.kind == EdgeKind.CALLS and e.target_qn == "target"
        ]
        assert len(calls) == 1, f"expected exactly one CALLS edge, got {calls}"
        assert calls[0].source_qn.endswith("inner"), calls[0].source_qn

    @pytest.mark.unit
    def test_extracts_import_edges(self, fixtures_dir: Path) -> None:
        """
        Scenario: Extract import relationships
        Given a Python file with import statements
        When I parse it
        Then IMPORTS_FROM edges are created
        """
        code = "import os\nfrom pathlib import Path\n"
        fp = _write_fixture(fixtures_dir, "imports.py", code)
        nodes, edges = parse_file(str(fp))
        import_edges = [e for e in edges if e.kind == EdgeKind.IMPORTS_FROM]
        assert len(import_edges) >= 1

    @pytest.mark.unit
    def test_extracts_contains_edges(self, fixtures_dir: Path) -> None:
        """
        Scenario: Class contains method creates CONTAINS edge
        Given a class with methods
        When I parse it
        Then CONTAINS edges link class to methods
        """
        code = "class Svc:\n    def run(self):\n        pass\n"
        fp = _write_fixture(fixtures_dir, "contains.py", code)
        nodes, edges = parse_file(str(fp))
        contains = [e for e in edges if e.kind == EdgeKind.CONTAINS]
        assert len(contains) >= 1

    @pytest.mark.unit
    def test_detects_test_function(self, fixtures_dir: Path) -> None:
        """
        Scenario: Functions named test_* are marked as tests
        Given a file with test_something function
        When I parse it
        Then the node has is_test=True and kind=Test
        """
        code = "def test_something():\n    assert True\n"
        fp = _write_fixture(fixtures_dir, "test_example.py", code)
        nodes, edges = parse_file(str(fp))
        test_nodes = [n for n in nodes if n.is_test]
        assert len(test_nodes) >= 1

    @pytest.mark.unit
    def test_file_node_created(self, fixtures_dir: Path) -> None:
        """
        Scenario: A File node is always created
        Given any parseable source file
        When I parse it
        Then a File node exists with the file path
        """
        fp = _write_fixture(fixtures_dir, "any.py", "x = 1\n")
        nodes, edges = parse_file(str(fp))
        file_nodes = [n for n in nodes if n.kind == NodeKind.FILE]
        assert len(file_nodes) == 1

    @pytest.mark.unit
    def test_returns_empty_for_unsupported_extension(self, fixtures_dir: Path) -> None:
        """
        Scenario: Unsupported file extension returns empty
        Given a file with unknown extension
        When I parse it
        Then empty lists are returned
        """
        fp = _write_fixture(fixtures_dir, "data.xyz", "stuff")
        nodes, edges = parse_file(str(fp))
        assert nodes == []
        assert edges == []


class TestParseJavaScriptFile:
    """Feature: Parse JavaScript source files"""

    @pytest.mark.unit
    def test_extracts_js_function(self, fixtures_dir: Path) -> None:
        code = "function greet(name) {\n  return 'Hello ' + name;\n}\n"
        fp = _write_fixture(fixtures_dir, "app.js", code)
        nodes, edges = parse_file(str(fp))
        fn_nodes = [n for n in nodes if n.kind == NodeKind.FUNCTION]
        assert any("greet" in n.qualified_name for n in fn_nodes)

    @pytest.mark.unit
    def test_extracts_js_class(self, fixtures_dir: Path) -> None:
        code = "class Widget {\n  constructor() {}\n  render() {}\n}\n"
        fp = _write_fixture(fixtures_dir, "widget.js", code)
        nodes, edges = parse_file(str(fp))
        cls_nodes = [n for n in nodes if n.kind == NodeKind.CLASS]
        assert any("Widget" in n.qualified_name for n in cls_nodes)


class TestParseGoFile:
    """Feature: Parse Go source files"""

    @pytest.mark.unit
    def test_extracts_go_function(self, fixtures_dir: Path) -> None:
        code = 'package main\n\nfunc hello() {\n\tfmt.Println("hi")\n}\n'
        fp = _write_fixture(fixtures_dir, "main.go", code)
        nodes, edges = parse_file(str(fp))
        fn_nodes = [n for n in nodes if n.kind == NodeKind.FUNCTION]
        assert any("hello" in n.qualified_name for n in fn_nodes)
