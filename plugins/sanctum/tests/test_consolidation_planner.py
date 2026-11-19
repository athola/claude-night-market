"""Tests for consolidation_planner.py script."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "consolidation_planner.py"

_CLEAN_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(*args: str) -> None:
    """Run git with GIT_* env vars stripped to prevent pre-commit hook leakage."""
    subprocess.run(["git", *args], check=True, env=_CLEAN_ENV)


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


def test_file_name_credit_needs_a_whole_header_word(tmp_path):
    """A header word must be a word of the file name, not a substring.

    "on" inside "configuration" earned +0.2
    and lifted identical content from 0.4 (CREATE_NEW) to 0.6
    (INTELLIGENT_WEAVE).
    """
    cp = _load_script()
    body = "Release checklist. Notes on the audit cadence live with the team.\n"
    chunk = cp.ContentChunk(
        header="Notes on the audit",
        content="Latency regressions measured in the checkout worker.",
        category="findings",
        value="high",
    )
    scores = {}
    for name in ("configuration.md", "release.md"):
        doc = tmp_path / name
        doc.write_text(body)
        scores[name] = cp.compute_relevance(chunk, str(doc))

    assert scores["configuration.md"] == scores["release.md"]
    route = cp.route_chunk(chunk, [str(tmp_path / "configuration.md")], "A.md")
    assert route.strategy == "CREATE_NEW"


def test_file_name_credit_for_a_matching_word(tmp_path):
    """A header word that names the file still earns the credit."""
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="Audit notes", content="zzzz", category="findings", value="low"
    )
    named = tmp_path / "audit-log.md"
    other = tmp_path / "release.md"
    for doc in (named, other):
        doc.write_text("unrelated text")

    gap = cp.compute_relevance(chunk, str(named)) - cp.compute_relevance(
        chunk, str(other)
    )
    assert abs(gap - 0.2) < 1e-9


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
    _git("init", "-q", "-b", "main", str(tmp_path))
    _git("-C", str(tmp_path), "config", "user.email", "t@example.com")
    _git("-C", str(tmp_path), "config", "user.name", "Tester")
    (tmp_path / "tracked.md").write_text("# tracked\n")
    _git("-C", str(tmp_path), "add", "tracked.md")
    _git("-C", str(tmp_path), "commit", "-q", "-m", "init")
    (tmp_path / "AUDIT_REPORT.md").write_text("\n")
    untracked = cp.git_untracked_files(str(tmp_path))
    assert "AUDIT_REPORT.md" in untracked
    assert "tracked.md" not in untracked


def test_scan_for_candidates_picks_up_allcaps_report(tmp_path):
    cp = _load_script()
    _git("init", "-q", "-b", "main", str(tmp_path))
    _git("-C", str(tmp_path), "config", "user.email", "t@example.com")
    _git("-C", str(tmp_path), "config", "user.name", "Tester")
    (tmp_path / "init.md").write_text("first")
    _git("-C", str(tmp_path), "add", ".")
    _git("-C", str(tmp_path), "commit", "-q", "-m", "first")
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


def test_git_untracked_files_returns_names_with_spaces_and_unicode_unquoted(tmp_path):
    """`git status --porcelain` quotes such names; callers need the real path."""
    cp = _load_script()
    _git("init", "-q", "-b", "main", str(tmp_path))
    _git("-C", str(tmp_path), "config", "user.email", "t@example.com")
    _git("-C", str(tmp_path), "config", "user.name", "Tester")
    (tmp_path / "seed.md").write_text("# seed\n")
    _git("-C", str(tmp_path), "add", "seed.md")
    _git("-C", str(tmp_path), "commit", "-q", "-m", "init")
    (tmp_path / "audit report.md").write_text("\n")
    (tmp_path / "café notes.md").write_text("\n")

    untracked = cp.git_untracked_files(str(tmp_path))

    assert "audit report.md" in untracked
    assert "café notes.md" in untracked


def test_ignored_fallback_destination_routes_to_an_issue():
    """A file under a gitignored path is never committed, so the item is lost."""
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="Action Items",
        content="todo list",
        category="actionable",
        value="medium",
    )
    route = cp.route_chunk(
        chunk, [], "scratch.md", is_ignored=lambda p: p.startswith("docs/plans/")
    )
    assert route.strategy == "FILE_ISSUE"
    assert route.destination == "github-issue"
    assert "gitignored" in route.rationale


def test_decision_fallback_takes_the_next_adr_number_without_a_date():
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="CLI Naming", content="we chose x", category="decisions", value="high"
    )
    existing = ["docs/adr/0029-a.md", "docs/adr/0030-b.md", "docs/guide.md"]
    route = cp.route_chunk(chunk, [], "scratch.md")
    assert route.destination == "docs/adr/0001-cli-naming.md"
    route = cp.route_chunk(chunk, existing, "scratch.md")
    assert route.destination == "docs/adr/0031-cli-naming.md"


_TWO_DECISIONS = (
    "## Decision on naming\nWe decided to name it x. Rationale chosen.\n\n"
    "## Decision on storage\nWe decided to store in sqlite. Rationale chosen.\n\n"
    "## Findings\nThe cache missed 40 percent of lookups.\n\n"
    "## Action Items\n- fix the cache\n"
)


def _plan_in_repo(cp, tmp_path, monkeypatch):
    _git("init", "-q", "-b", "main", str(tmp_path))
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0030-b.md").write_text("# b\n")
    (tmp_path / "docs" / "guide.md").write_text("# guide\n")
    (tmp_path / "AUDIT_REPORT.md").write_text(_TWO_DECISIONS)
    monkeypatch.chdir(tmp_path)
    return cp.generate_plan("AUDIT_REPORT.md")


def test_two_decisions_in_one_plan_get_distinct_adr_numbers(tmp_path, monkeypatch):
    """The number came from the docs on disk alone, so both were 0031."""
    cp = _load_script()
    plan = _plan_in_repo(cp, tmp_path, monkeypatch)
    adrs = [r.destination for r in plan.routes if r.category == "decisions"]
    assert adrs == [
        "docs/adr/0031-decision-on-naming.md",
        "docs/adr/0032-decision-on-storage.md",
    ]


def test_a_dated_adr_name_is_not_read_as_an_adr_number():
    """``\\d{4}`` matched the year in ``2026-11-17-foo.md`` and gave 2027."""
    cp = _load_script()
    assert cp._next_adr_number(["docs/adr/2026-11-17-foo.md"]) == 1
    assert (
        cp._next_adr_number(["docs/adr/2026-11-17-foo.md", "docs/adr/0004-x.md"]) == 5
    )


def test_plan_probes_each_path_for_ignore_rules_once(tmp_path, monkeypatch):
    """One ``git check-ignore`` per doc per chunk made 448 spawns for 4 chunks."""
    cp = _load_script()
    probed: list[str] = []
    real_run = subprocess.run

    def counting_run(cmd, *args, **kwargs):
        if "check-ignore" in cmd:
            probed.append(cmd[-1])
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(cp.subprocess, "run", counting_run)
    _plan_in_repo(cp, tmp_path, monkeypatch)
    assert probed
    assert len(probed) == len(set(probed)), probed


def test_git_ignored_probe_reads_the_repository_ignore_rules(tmp_path):
    cp = _load_script()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("docs/plans/\n")
    is_ignored = cp.git_ignored(str(tmp_path))
    assert is_ignored("docs/plans/2026-01-01-x.md") is True
    assert is_ignored("docs/adr/0001-x.md") is False


def test_git_ignored_probe_outside_a_repository_ignores_nothing(tmp_path):
    cp = _load_script()
    assert cp.git_ignored(str(tmp_path))("docs/plans/x.md") is False


def test_ignored_existing_doc_is_never_a_semantic_match(tmp_path):
    """Weaving into a gitignored file loses the content as surely as creating one."""
    cp = _load_script()
    plan_doc = tmp_path / "docs" / "plans" / "action-items-review.md"
    plan_doc.parent.mkdir(parents=True)
    plan_doc.write_text("# Action Items\n\nAction items todo list for the review.\n")
    chunk = cp.ContentChunk(
        header="Action Items",
        content="action items todo list review",
        category="actionable",
        value="medium",
    )
    route = cp.route_chunk(
        chunk, [str(plan_doc)], "scratch.md", is_ignored=lambda p: "/plans/" in p
    )
    assert route.strategy == "FILE_ISSUE"


def test_scan_finds_report_in_untracked_subdirectory(tmp_path):
    """Porcelain collapsed a new directory to `?? sub/`, hiding its files (SAN-2)."""
    cp = _load_script()
    _git("init", "-q", "-b", "main", str(tmp_path))
    _git("-C", str(tmp_path), "config", "user.email", "t@example.com")
    _git("-C", str(tmp_path), "config", "user.name", "Tester")
    (tmp_path / "init.md").write_text("first")
    _git("-C", str(tmp_path), "add", ".")
    _git("-C", str(tmp_path), "commit", "-q", "-m", "first")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "AUDIT_REPORT.md").write_text(
        "**Date**: 2026-04-01\n## Findings\n## Action Items\n"
    )
    candidates = cp.scan_for_candidates(str(tmp_path))
    assert any(c.path == "sub/AUDIT_REPORT.md" for c in candidates)


def test_route_chunk_uses_fallback_name_when_header_slug_is_empty():
    """A header like 概要 slugs to "", which routed to docs/.md (SAN-5)."""
    cp = _load_script()
    chunk = cp.ContentChunk(
        header="概要", content="x", category="finding", value="high"
    )
    route = cp.route_chunk(chunk, [], "AUDIT_REPORT.md")
    assert not route.destination.endswith("/.md")


def test_extract_chunks_ignores_header_like_lines_inside_code_fences(tmp_path):
    """A `## ` line in a fenced example split the real section (SAN-13)."""
    cp = _load_script()
    src = tmp_path / "R.md"
    src.write_text("## Findings\ntext\n```bash\n## not a header\n```\nmore\n")
    assert [c.header for c in cp.extract_chunks(str(src))] == ["Findings"]


def test_plan_skips_gitignored_doc_under_nested_docs_dir(tmp_path, monkeypatch):
    """The ignore probe ran in the docs dir's parent with cwd-relative paths,
    so an ignored doc under pkg/docs read as not ignored (SAN-4).
    """
    cp = _load_script()
    _git("init", "-q", "-b", "main", str(tmp_path))
    (tmp_path / ".gitignore").write_text("pkg/docs/secret.md\n")
    (tmp_path / "pkg" / "docs").mkdir(parents=True)
    (tmp_path / "pkg" / "docs" / "secret.md").write_text("# Findings notes\n")
    monkeypatch.chdir(tmp_path)
    built_for: list[str] = []
    real = cp.git_ignored

    def spy(repo: str):
        built_for.append(repo)
        return real(repo)

    monkeypatch.setattr(cp, "git_ignored", spy)
    (tmp_path / "AUDIT_REPORT.md").write_text("## Findings\nx\n")
    cp.generate_plan("AUDIT_REPORT.md", docs_dir="pkg/docs")
    assert real(built_for[0])("pkg/docs/secret.md") is True


def test_usage_lists_only_real_subcommands():
    """The module docstring named a `route` command that does not exist (SAN-12)."""
    cp = _load_script()
    documented = {
        line.split()[2]
        for line in (cp.__doc__ or "").splitlines()
        if line.strip().startswith("python consolidation_planner.py")
    }
    assert documented == {"scan", "analyze", "plan"}


def test_scan_from_a_subdirectory_reads_files_relative_to_it(tmp_path):
    """Status paths are root-relative, so joined to a subdirectory
    --repo-path they named files that do not exist (SAN-2).
    """
    cp = _load_script()
    _git("init", "-q", "-b", "main", str(tmp_path))
    _git("-C", str(tmp_path), "config", "user.email", "t@example.com")
    _git("-C", str(tmp_path), "config", "user.name", "Tester")
    (tmp_path / "init.md").write_text("first")
    _git("-C", str(tmp_path), "add", ".")
    _git("-C", str(tmp_path), "commit", "-q", "-m", "first")
    area = tmp_path / "area"
    area.mkdir()
    (area / "AUDIT_REPORT.md").write_text(
        "**Date**: 2026-04-01\n## Findings\n## Action Items\n"
    )
    candidates = cp.scan_for_candidates(str(area))
    assert [c.path for c in candidates] == ["AUDIT_REPORT.md"]
