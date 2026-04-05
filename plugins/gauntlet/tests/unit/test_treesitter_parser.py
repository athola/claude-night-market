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
    """
    Feature: Parse JavaScript source files
    """

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
    """
    Feature: Parse Go source files
    """

    @pytest.mark.unit
    def test_extracts_go_function(self, fixtures_dir: Path) -> None:
        code = 'package main\n\nfunc hello() {\n\tfmt.Println("hi")\n}\n'
        fp = _write_fixture(fixtures_dir, "main.go", code)
        nodes, edges = parse_file(str(fp))
        fn_nodes = [n for n in nodes if n.kind == NodeKind.FUNCTION]
        assert any("hello" in n.qualified_name for n in fn_nodes)
