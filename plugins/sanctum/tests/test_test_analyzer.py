"""Tests for test_analyzer.py script."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "test_analyzer.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("sanctum_test_analyzer", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_test_analyzer"] = module
    spec.loader.exec_module(module)
    return module


def _build_codebase(root: Path) -> None:
    """Create a small codebase with mixed test coverage."""
    src_dir = root / "src"
    src_dir.mkdir()
    (src_dir / "covered.py").write_text(
        "def hello():\n    return 1\n\nclass Greeter:\n    def hi(self):\n        pass\n"
    )
    (src_dir / "uncovered.py").write_text(
        "def lonely():\n    return 0\n\nclass Solo:\n    pass\n"
    )
    (src_dir / "__init__.py").write_text("")

    test_dir = root / "tests"
    test_dir.mkdir()
    (test_dir / "test_covered.py").write_text(
        "def test_hello():\n    pass\n\ndef test_greeter():\n    pass\n"
    )


def test_test_analyzer_class_initializes():
    module = _load_script()
    analyzer = module.TestAnalyzer(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert analyzer.codebase_path == Path("/tmp")  # noqa: S108 - test fixture path, not user input
    assert "test_*.py" in analyzer.test_patterns
    assert "*.py" in analyzer.source_patterns


def test_get_test_name_adds_prefix():
    module = _load_script()
    a = module.TestAnalyzer(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert a._get_test_name(Path("foo.py")) == "test_foo"


def test_get_test_name_preserves_existing_prefix():
    module = _load_script()
    a = module.TestAnalyzer(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert a._get_test_name(Path("test_foo.py")) == "test_foo"


def test_scan_for_test_gaps_finds_uncovered_files(tmp_path):
    module = _load_script()
    _build_codebase(tmp_path)
    analyzer = module.TestAnalyzer(tmp_path)
    results = analyzer.scan_for_test_gaps()

    assert "source_files" in results
    assert "test_files" in results
    assert "uncovered_files" in results
    assert "coverage_gaps" in results
    # uncovered.py has no test_uncovered.py
    assert "test_uncovered" in results["uncovered_files"]


def test_scan_for_test_gaps_excludes_init_and_test_files(tmp_path):
    module = _load_script()
    _build_codebase(tmp_path)
    analyzer = module.TestAnalyzer(tmp_path)
    results = analyzer.scan_for_test_gaps()
    source_names = {f.name for f in results["source_files"]}
    assert "__init__.py" not in source_names
    assert all(not n.startswith("test_") for n in source_names)


def test_find_test_file_in_tests_dir(tmp_path):
    module = _load_script()
    _build_codebase(tmp_path)
    analyzer = module.TestAnalyzer(tmp_path)
    src = tmp_path / "src" / "covered.py"
    test_files = list((tmp_path / "tests").glob("test_*.py"))
    found = analyzer._find_test_file(src, test_files)
    assert found is not None
    assert found.name == "test_covered.py"


def test_find_test_file_returns_none_for_missing(tmp_path):
    module = _load_script()
    _build_codebase(tmp_path)
    analyzer = module.TestAnalyzer(tmp_path)
    src = tmp_path / "src" / "uncovered.py"
    test_files = list((tmp_path / "tests").glob("test_*.py"))
    assert analyzer._find_test_file(src, test_files) is None


def test_analyze_file_coverage_handles_syntax_error(tmp_path):
    module = _load_script()
    bad = tmp_path / "broken.py"
    bad.write_text("this is not :: valid python @@@@\n")
    analyzer = module.TestAnalyzer(tmp_path)
    out = analyzer._analyze_file_coverage(bad, [])
    # Syntax errors short-circuit to None
    assert out is None


def test_analyze_file_coverage_no_test_file(tmp_path):
    module = _load_script()
    src = tmp_path / "lonely.py"
    src.write_text("def lone(): pass\n")
    analyzer = module.TestAnalyzer(tmp_path)
    out = analyzer._analyze_file_coverage(src, [])
    assert out is not None
    assert out["test_file"] is None
    assert out["coverage_percentage"] == 0
    assert "lone" in out["missing_tests"]


def test_analyze_file_coverage_with_matching_test(tmp_path):
    module = _load_script()
    _build_codebase(tmp_path)
    src = tmp_path / "src" / "covered.py"
    tests = list((tmp_path / "tests").glob("test_*.py"))
    analyzer = module.TestAnalyzer(tmp_path)
    out = analyzer._analyze_file_coverage(src, tests)
    assert out is not None
    assert out["test_file"] is not None
    # Both `hello` and `Greeter` are tested by name match
    assert out["coverage_percentage"] > 0


def test_analyze_git_changes_outside_repo_returns_error(tmp_path):
    module = _load_script()
    analyzer = module.TestAnalyzer(tmp_path)
    out = analyzer.analyze_git_changes()
    assert "error" in out


def test_analyze_git_changes_in_real_repo(tmp_path):
    module = _load_script()
    # Initialize a tiny git repo with two commits so HEAD~1 exists
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Tester"],
        check=True,
    )
    (tmp_path / "first.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "first"],
        check=True,
    )
    (tmp_path / "second.py").write_text("y = 2\n")
    (tmp_path / "first.py").write_text("x = 99\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "second"],
        check=True,
    )

    analyzer = module.TestAnalyzer(tmp_path)
    out = analyzer.analyze_git_changes()
    assert "error" not in out
    cats = out["categories"]
    assert any("second.py" in p for p in cats["added"])
    assert any("first.py" in p for p in cats["modified"])


def test_generate_report_invalid_type():
    module = _load_script()
    a = module.TestAnalyzer(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    out = a.generate_report("nonsense")
    assert "Invalid" in out


def test_generate_report_changes_outside_repo_returns_error_json(tmp_path):
    module = _load_script()
    a = module.TestAnalyzer(tmp_path)
    out = a.generate_report("changes")
    parsed = json.loads(out)
    assert "error" in parsed


def test_make_serializable_handles_paths_dicts_lists():
    module = _load_script()
    obj = {
        "p": Path("/tmp/x"),  # noqa: S108 - test fixture path, not user input
        "items": [Path("/a"), {"nested": Path("/b")}],
        "raw": 42,
    }
    out = module._make_serializable(obj)
    assert out["p"] == "/tmp/x"  # noqa: S108 - test fixture path, not user input
    assert out["items"][0] == "/a"
    assert out["items"][1]["nested"] == "/b"
    assert out["raw"] == 42


def test_main_help_runs(monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setattr(sys, "argv", ["test_analyzer.py"])
    # No args -> prints help and returns
    module.main()
    out = capsys.readouterr().out
    assert "Analyze" in out or "scan" in out.lower()


def test_main_scan_human_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    _build_codebase(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_analyzer.py", "--scan", str(tmp_path)],
    )
    module.main()
    out = capsys.readouterr().out
    assert "Test Analysis Report" in out
    assert "Uncovered" in out


def test_main_scan_json_output(tmp_path, monkeypatch, capsys):
    module = _load_script()
    _build_codebase(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_analyzer.py", "--scan", str(tmp_path), "--output-json"],
    )
    module.main()
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert "uncovered_files" in parsed["data"]


def test_main_changes_in_real_repo(tmp_path, monkeypatch, capsys):
    module = _load_script()
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Tester"],
        check=True,
    )
    (tmp_path / "a.py").write_text("x=1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "a"], check=True)
    (tmp_path / "b.py").write_text("y=2\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "b"], check=True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_analyzer.py", "--changes", str(tmp_path), "--output-json"],
    )
    module.main()
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["success"] is True


def test_main_error_path_prints_failure(monkeypatch, capsys):
    """Main raises SystemExit when TestAnalyzer fails internally."""
    module = _load_script()

    # Force an exception by passing a path that won't resolve
    class _Boom:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            raise RuntimeError("boom")

    monkeypatch.setattr(module, "TestAnalyzer", _Boom)
    monkeypatch.setattr(
        sys,
        "argv",
        ["test_analyzer.py", "--scan", "/tmp"],  # noqa: S108 - test fixture path, not user input
    )
    raised = False
    try:
        module.main()
    except SystemExit:
        raised = True
    assert raised
    assert "boom" in (capsys.readouterr().out + capsys.readouterr().err)
