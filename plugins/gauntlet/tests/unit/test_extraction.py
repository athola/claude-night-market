"""Tests for AST-based knowledge extraction."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from gauntlet.extraction import extract_from_directory, extract_from_file

# ---------------------------------------------------------------------------
# Feature: Extracting knowledge from Python source files
# ---------------------------------------------------------------------------


class TestExtractFromFile:
    """
    Feature: AST-based extraction from a single Python file

    As a gauntlet plugin
    I want to extract knowledge entries from Python source files
    So that developers can be challenged on real code in the codebase
    """

    @pytest.mark.unit
    def test_extracts_functions(self, sample_python_file: Path):
        """
        Scenario: Extract public functions
        Given a Python file with a public function 'calculate_discount'
        When extract_from_file() is called
        Then a KnowledgeEntry with concept='calculate_discount' is returned
        """
        entries = extract_from_file(sample_python_file)

        concepts = [e.concept for e in entries]
        assert "calculate_discount" in concepts

    @pytest.mark.unit
    def test_extracts_docstring_as_detail(self, sample_python_file: Path):
        """
        Scenario: Docstring becomes the detail field
        Given a Python file with a function that has a docstring
        When extract_from_file() is called
        Then the entry's detail contains text from the docstring
        """
        entries = extract_from_file(sample_python_file)

        discount_entry = next(
            (e for e in entries if e.concept == "calculate_discount"), None
        )
        assert discount_entry is not None
        assert "discount" in discount_entry.detail.lower()

    @pytest.mark.unit
    def test_assigns_difficulty_in_valid_range(self, sample_python_file: Path):
        """
        Scenario: Difficulty is between 1 and 5
        Given any Python file
        When extract_from_file() is called
        Then every entry has difficulty between 1 and 4 inclusive
        """
        entries = extract_from_file(sample_python_file)

        assert len(entries) > 0
        for entry in entries:
            assert 1 <= entry.difficulty <= 4

    @pytest.mark.unit
    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        """
        Scenario: Graceful handling of a missing file
        Given a path that does not exist on disk
        When extract_from_file() is called
        Then an empty list is returned (no exception raised)
        """
        result = extract_from_file(tmp_path / "does_not_exist.py")

        assert result == []

    @pytest.mark.unit
    def test_syntax_error_file_returns_empty(self, tmp_path: Path):
        """
        Scenario: Graceful handling of a file with a syntax error
        Given a Python file containing invalid syntax
        When extract_from_file() is called
        Then an empty list is returned (no exception raised)
        """
        bad_file = tmp_path / "broken.py"
        bad_file.write_text("def foo(\n    this is not valid python\n")

        result = extract_from_file(bad_file)

        assert result == []

    @pytest.mark.unit
    def test_assigns_unique_ids(self, tmp_path: Path):
        """
        Scenario: Each entry gets a unique stable ID
        Given a Python file with two distinct public functions
        When extract_from_file() is called
        Then each entry has a distinct id
        """
        py_file = tmp_path / "multi.py"
        py_file.write_text(
            textwrap.dedent("""\
            from __future__ import annotations


            def alpha():
                \"\"\"Alpha function.\"\"\"
                return 1


            def beta():
                \"\"\"Beta function.\"\"\"
                return 2
        """)
        )

        entries = extract_from_file(py_file)

        ids = [e.id for e in entries]
        assert len(ids) == len(set(ids))

    @pytest.mark.unit
    def test_skips_private_functions(self, tmp_path: Path):
        """
        Scenario: Private functions (prefixed with _) are skipped
        Given a Python file with one public and one private function
        When extract_from_file() is called
        Then only the public function produces an entry
        """
        py_file = tmp_path / "mixed.py"
        py_file.write_text(
            textwrap.dedent("""\
            from __future__ import annotations


            def public_func():
                \"\"\"Public.\"\"\"
                pass


            def _private_func():
                \"\"\"Private.\"\"\"
                pass
        """)
        )

        entries = extract_from_file(py_file)

        concepts = [e.concept for e in entries]
        assert "public_func" in concepts
        assert "_private_func" not in concepts

    @pytest.mark.unit
    def test_includes_dunder_init(self, tmp_path: Path):
        """
        Scenario: __init__ methods are extracted
        Given a Python class with an __init__ method
        When extract_from_file() is called
        Then an entry for __init__ is included
        """
        py_file = tmp_path / "cls.py"
        py_file.write_text(
            textwrap.dedent("""\
            from __future__ import annotations


            class MyService:
                \"\"\"A service class.\"\"\"

                def __init__(self, value: int) -> None:
                    \"\"\"Initialise the service.\"\"\"
                    self.value = value
        """)
        )

        entries = extract_from_file(py_file)

        concepts = [e.concept for e in entries]
        assert "__init__" in concepts or "MyService" in concepts


# ---------------------------------------------------------------------------
# Feature: Category inference from docstring keywords
# ---------------------------------------------------------------------------


class TestCategoryInference:
    """
    Feature: Automatic category assignment

    As a gauntlet plugin
    I want each extracted entry to have a meaningful category
    So that challenge generation can target specific knowledge domains
    """

    @pytest.mark.unit
    def test_business_logic_keyword_assigns_business_logic_category(
        self, tmp_path: Path
    ):
        """
        Scenario: 'business' keyword triggers business_logic category
        Given a function whose docstring contains 'business'
        When extract_from_file() is called
        Then the entry's category is 'business_logic'
        """
        py_file = tmp_path / "biz.py"
        py_file.write_text(
            textwrap.dedent("""\
            def apply_rules(x):
                \"\"\"Apply business rules to compute the result.\"\"\"
                return x
        """)
        )

        entries = extract_from_file(py_file)

        assert len(entries) == 1
        assert entries[0].category == "business_logic"

    @pytest.mark.unit
    def test_pipeline_keyword_assigns_data_flow_category(self, tmp_path: Path):
        """
        Scenario: 'pipeline' keyword triggers data_flow category
        Given a function whose docstring contains 'pipeline'
        When extract_from_file() is called
        Then the entry's category is 'data_flow'
        """
        py_file = tmp_path / "pipe.py"
        py_file.write_text(
            textwrap.dedent("""\
            def run_pipeline(data):
                \"\"\"Execute the data pipeline transform.\"\"\"
                return data
        """)
        )

        entries = extract_from_file(py_file)

        assert len(entries) == 1
        assert entries[0].category == "data_flow"

    @pytest.mark.unit
    def test_endpoint_keyword_assigns_api_contract_category(self, tmp_path: Path):
        """
        Scenario: 'endpoint' keyword triggers api_contract category
        Given a function whose docstring contains 'endpoint'
        When extract_from_file() is called
        Then the entry's category is 'api_contract'
        """
        py_file = tmp_path / "api.py"
        py_file.write_text(
            textwrap.dedent("""\
            def handle_request(req):
                \"\"\"Handle the HTTP endpoint request.\"\"\"
                return req
        """)
        )

        entries = extract_from_file(py_file)

        assert len(entries) == 1
        assert entries[0].category == "api_contract"

    @pytest.mark.unit
    def test_error_keyword_assigns_error_handling_category(self, tmp_path: Path):
        """
        Scenario: 'error' keyword triggers error_handling category
        Given a function whose docstring contains 'error'
        When extract_from_file() is called
        Then the entry's category is 'error_handling'
        """
        py_file = tmp_path / "err.py"
        py_file.write_text(
            textwrap.dedent("""\
            def retry_on_error(fn):
                \"\"\"Retry the function on error up to three times.\"\"\"
                return fn
        """)
        )

        entries = extract_from_file(py_file)

        assert len(entries) == 1
        assert entries[0].category == "error_handling"

    @pytest.mark.unit
    def test_no_keyword_defaults_to_architecture(self, tmp_path: Path):
        """
        Scenario: No matching keyword defaults to architecture
        Given a function whose docstring has no category keywords
        When extract_from_file() is called
        Then the entry's category is 'architecture'
        """
        py_file = tmp_path / "misc.py"
        py_file.write_text(
            textwrap.dedent("""\
            def compute(x):
                \"\"\"Compute something generic.\"\"\"
                return x
        """)
        )

        entries = extract_from_file(py_file)

        assert len(entries) == 1
        assert entries[0].category == "architecture"


# ---------------------------------------------------------------------------
# Feature: Extracting knowledge from a directory
# ---------------------------------------------------------------------------


class TestExtractFromDirectory:
    """
    Feature: Recursive extraction from a directory tree

    As a gauntlet plugin
    I want to scan a directory for Python files and extract knowledge
    So that the knowledge base is built automatically from the codebase
    """

    @pytest.mark.unit
    def test_extracts_from_multiple_files(self, tmp_path: Path):
        """
        Scenario: Two Python files in a directory
        Given a directory with two Python source files each containing
        one public function
        When extract_from_directory() is called
        Then entries from both files are returned
        """
        (tmp_path / "a.py").write_text(
            textwrap.dedent("""\
            def func_a():
                \"\"\"Function A.\"\"\"
                pass
        """)
        )
        (tmp_path / "b.py").write_text(
            textwrap.dedent("""\
            def func_b():
                \"\"\"Function B.\"\"\"
                pass
        """)
        )

        entries = extract_from_directory(tmp_path)

        concepts = [e.concept for e in entries]
        assert "func_a" in concepts
        assert "func_b" in concepts

    @pytest.mark.unit
    def test_skips_non_python_files(self, tmp_path: Path):
        """
        Scenario: Non-Python files are ignored
        Given a directory containing a .py file and a .txt file
        When extract_from_directory() is called
        Then no entries are produced from the .txt file
        """
        (tmp_path / "code.py").write_text(
            textwrap.dedent("""\
            def real_func():
                \"\"\"Real function.\"\"\"
                pass
        """)
        )
        (tmp_path / "notes.txt").write_text("just some notes")

        entries = extract_from_directory(tmp_path)

        assert len(entries) == 1
        assert entries[0].concept == "real_func"

    @pytest.mark.unit
    def test_skips_dunder_py_files(self, tmp_path: Path):
        """
        Scenario: __init__.py and similar dunder files are skipped
        Given a directory with __init__.py and a regular module
        When extract_from_directory() is called
        Then no entries come from __init__.py
        """
        (tmp_path / "__init__.py").write_text(
            textwrap.dedent("""\
            def init_helper():
                \"\"\"Init helper.\"\"\"
                pass
        """)
        )
        (tmp_path / "module.py").write_text(
            textwrap.dedent("""\
            def module_func():
                \"\"\"Module function.\"\"\"
                pass
        """)
        )

        entries = extract_from_directory(tmp_path)

        concepts = [e.concept for e in entries]
        assert "init_helper" not in concepts
        assert "module_func" in concepts

    @pytest.mark.unit
    def test_empty_directory_returns_empty_list(self, tmp_path: Path):
        """
        Scenario: Empty directory
        Given a directory with no Python files
        When extract_from_directory() is called
        Then an empty list is returned
        """
        result = extract_from_directory(tmp_path)

        assert result == []
