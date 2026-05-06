"""Tests for consolidation_planner.py script."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "consolidation_planner.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "sanctum_consolidation_planner", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_consolidation_planner"] = module
    spec.loader.exec_module(module)
    return module


# ---------------------- pure helpers ----------------------


def test_is_standard_location_true_for_standard_dirs():
    cp = _load_script()
    assert cp.is_standard_location("docs/foo.md")
    assert cp.is_standard_location("skills/x/SKILL.md")
    assert cp.is_standard_location("tests/test_x.py")


def test_is_standard_location_false_for_non_standard():
    cp = _load_script()
    assert not cp.is_standard_location("AUDIT_REPORT.md")
    assert not cp.is_standard_location("scratch.md")


def test_is_standard_name_true_for_repo_basics():
    cp = _load_script()
    assert cp.is_standard_name("README.md")
    assert cp.is_standard_name("LICENSE")
    assert cp.is_standard_name("CHANGELOG.md")


def test_is_allcaps_report_matches_patterns():
    cp = _load_script()
    assert cp.is_allcaps_report("AUDIT_REPORT.md")
    assert cp.is_allcaps_report("SECURITY_REVIEW.md")
    assert cp.is_allcaps_report("MIGRATION_FINDINGS.md")
    assert not cp.is_allcaps_report("readme.md")


def test_count_content_markers_strong_and_supporting():
    cp = _load_script()
    content = (
        "**Date**: 2026-04-01\n## Findings\n| col | col |\n- [ ] action\n## 1. First\n"
    )
    strong, supporting = cp.count_content_markers(content)
    assert strong >= 1
    assert supporting >= 2


def test_categorize_content_returns_known_category():
    cp = _load_script()
    assert cp.categorize_content("Action Items", "next steps to take") == "actionable"
    assert cp.categorize_content("Decision", "we chose option X") == "decisions"
    assert cp.categorize_content("API Changes", "deprecat the v1 endpoint") == (
        "api_changes"
    )
    # Default fallback
    assert cp.categorize_content("Random", "no patterns here") == "findings"


def test_score_value_high_for_substantial_content():
    cp = _load_script()
    long_content = (
        "Some prose " * 60
        + "\n\n```python\nx = 1\n```\n"
        + "| a | b |\n| - | - |\n| 1 | 2 |\n"
    )
    assert cp.score_value(long_content, "findings") == "high"


def test_score_value_low_for_short_overview():
    cp = _load_script()
    out = cp.score_value("This review was a generic overview.", "findings")
    assert out == "low"


def test_score_value_medium_default():
    cp = _load_script()
    out = cp.score_value("medium length prose " * 20, "findings")
    assert out == "medium"


def test_slugify_kebab_cases_and_truncates():
    cp = _load_script()
    assert cp.slugify("Some Header Title") == "some-header-title"
    long_input = "x" * 100
    assert len(cp.slugify(long_input)) <= 50


# ---------------------- chunking + routing ----------------------


def test_extract_chunks_splits_by_h2(tmp_path):
    cp = _load_script()
    f = tmp_path / "doc.md"
    f.write_text(
        "# Title\n\n"
        "## Findings\n\n"
        "Some finding content. " + ("words " * 60) + "\n"
        "## Decisions\n\n"
        "We chose X because it tradeoff favorably.\n"
    )
    chunks = cp.extract_chunks(str(f))
    headers = [c.header for c in chunks]
    assert "Findings" in headers
    assert "Decisions" in headers


def test_extract_chunks_returns_empty_for_missing_file():
    cp = _load_script()
    assert cp.extract_chunks("/nonexistent/sanctum-test.md") == []


def test_make_chunk_returns_none_for_empty_body():
    cp = _load_script()
    assert cp.make_chunk("Header", []) is None


def test_compute_relevance_returns_zero_for_unreadable():
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="Findings", content="x", category="findings", value="medium"
    )
    out = cp.compute_relevance(chunk, "/nonexistent/sanctum-test.md")
    assert out == 0.0


def test_compute_relevance_scores_header_match(tmp_path):
    cp = _load_script()
    doc = tmp_path / "guide.md"
    doc.write_text("Findings content includes findings about caching.")
    chunk = cp.ContentChunk(
        header="Findings",
        content="The findings cover caching",
        category="findings",
        value="medium",
    )
    score = cp.compute_relevance(chunk, str(doc))
    assert score >= 0.4


def test_route_chunk_uses_intelligent_weave_when_match(tmp_path):
    cp = _load_script()
    doc = tmp_path / "findings.md"
    doc.write_text("findings about " + " ".join([f"word{i}" for i in range(80)]))
    chunk = cp.ContentChunk(
        header="findings",
        content=" ".join([f"word{i}" for i in range(80)]),
        category="findings",
        value="high",
    )
    route = cp.route_chunk(chunk, [str(doc)], "AUDIT_REPORT.md")
    assert route.strategy == "INTELLIGENT_WEAVE"
    assert route.destination == str(doc)


def test_route_chunk_falls_back_to_create_new_for_no_match(tmp_path):
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="Action Items",
        content="todo list",
        category="actionable",
        value="medium",
    )
    route = cp.route_chunk(chunk, [], "scratch.md")
    assert route.strategy == "CREATE_NEW"
    assert route.destination.startswith("docs/plans/")


def test_route_chunk_api_changes_routes_to_changelog():
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="API",
        content="endpoint deprecation",
        category="api_changes",
        value="medium",
    )
    route = cp.route_chunk(chunk, [], "scratch.md")
    assert route.destination == "CHANGELOG.md"


def test_find_existing_docs_returns_empty_for_missing_dir():
    cp = _load_script()
    assert cp.find_existing_docs("/nonexistent/sanctum-test-docs") == []


def test_find_existing_docs_walks_md_and_rst(tmp_path):
    cp = _load_script()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("a")
    (docs / "b.rst").write_text("b")
    out = cp.find_existing_docs(str(docs))
    assert any(p.endswith("a.md") for p in out)
    assert any(p.endswith("b.rst") for p in out)


# ---------------------- planning + scanning ----------------------


def test_generate_plan_skips_low_value_chunks(tmp_path):
    cp = _load_script()
    src = tmp_path / "AUDIT_REPORT.md"
    src.write_text(
        "## Overview\n\n"
        "This review was a generic overview.\n\n"  # short low-value chunk
        "## Findings\n\n" + ("findings line " * 80) + "\n"
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = cp.generate_plan(str(src), str(docs))
    # The "Overview" low-value chunk should be skipped
    assert any("Overview" in s["header"] for s in plan.skipped)
    assert plan.summary["total_chunks"] >= 2


def test_format_plan_markdown_renders_tables(tmp_path):
    cp = _load_script()
    src = tmp_path / "AUDIT_REPORT.md"
    src.write_text("## Findings\n\n" + ("findings line " * 80) + "\n")
    plan = cp.generate_plan(str(src), str(tmp_path / "docs"))
    md = cp.format_plan_markdown(plan)
    assert "Consolidation Plan" in md
    assert "Summary" in md
    assert "Findings" in md


def test_git_untracked_files_returns_empty_outside_repo(tmp_path):
    cp = _load_script()
    out = cp.git_untracked_files(str(tmp_path))
    assert out == []


def test_git_untracked_files_lists_only_untracked(tmp_path):
    cp = _load_script()
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Tester"],
        check=True,
    )
    (tmp_path / "tracked.md").write_text("# tracked\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.md"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True
    )
    (tmp_path / "AUDIT_REPORT.md").write_text("\n")
    untracked = cp.git_untracked_files(str(tmp_path))
    assert "AUDIT_REPORT.md" in untracked
    assert "tracked.md" not in untracked


def test_scan_for_candidates_picks_up_allcaps_report(tmp_path):
    cp = _load_script()
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Tester"],
        check=True,
    )
    (tmp_path / "init.md").write_text("first")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "-m", "first"], check=True
    )
    (tmp_path / "AUDIT_REPORT.md").write_text(
        "**Date**: 2026-04-01\n## Findings\n## Action Items\n"
    )
    candidates = cp.scan_for_candidates(str(tmp_path))
    assert any(c.path == "AUDIT_REPORT.md" for c in candidates)


# ---------------------- main CLI ----------------------


def test_main_scan_human_output(tmp_path, monkeypatch):
    cp = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation_planner.py",
            "scan",
            "--repo-path",
            str(tmp_path),
        ],
    )
    rc = cp.main()
    assert rc == 0


def test_main_scan_json_output(tmp_path, monkeypatch, capsys):
    cp = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation_planner.py",
            "scan",
            "--repo-path",
            str(tmp_path),
            "--json",
        ],
    )
    rc = cp.main()
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list)


def test_main_analyze_human_output(tmp_path, monkeypatch, capsys):
    cp = _load_script()
    src = tmp_path / "REPORT.md"
    src.write_text("## Findings\n\n" + ("findings line " * 60))

    monkeypatch.setattr(
        sys,
        "argv",
        ["consolidation_planner.py", "analyze", str(src)],
    )
    rc = cp.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Findings" in out


def test_main_analyze_json_output(tmp_path, monkeypatch, capsys):
    cp = _load_script()
    src = tmp_path / "REPORT.md"
    src.write_text("## Findings\n\n" + ("findings line " * 60))

    monkeypatch.setattr(
        sys,
        "argv",
        ["consolidation_planner.py", "analyze", str(src), "--json"],
    )
    rc = cp.main()
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert isinstance(parsed, list)


def test_main_plan_human_output(tmp_path, monkeypatch, capsys):
    cp = _load_script()
    src = tmp_path / "REPORT.md"
    src.write_text(
        "## Findings\n\n" + ("findings " * 60) + "\n## Action Items\n\n- [ ] do thing\n"
    )
    docs = tmp_path / "docs"
    docs.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation_planner.py",
            "plan",
            str(src),
            "--docs-dir",
            str(docs),
        ],
    )
    rc = cp.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Consolidation Plan" in out
    assert "Summary" in out


def test_main_plan_json_output(tmp_path, monkeypatch, capsys):
    cp = _load_script()
    src = tmp_path / "REPORT.md"
    src.write_text(
        "## Findings\n\n" + ("findings " * 60) + "\n## Action Items\n\n- [ ] do thing\n"
    )
    docs = tmp_path / "docs"
    docs.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "consolidation_planner.py",
            "plan",
            str(src),
            "--docs-dir",
            str(docs),
            "--json",
        ],
    )
    rc = cp.main()
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert "routes" in parsed
    assert "summary" in parsed
