"""Unit tests for MetaEvaluator methods - targets uncovered lines.

Complements the integration-focused test_meta_evaluation.py by exercising
each MetaEvaluator instance method against synthetic plugin trees.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))
from meta_evaluation import (  # noqa: E402 - sys.path setup precedes import
    MetaEvaluator,
    main,
)

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def plugins_root(tmp_path: Path) -> Path:
    """A small synthetic plugins-root tree used by the evaluator."""
    return tmp_path / "plugins"


def _make_skill(
    plugins_root: Path,
    plugin: str,
    skill: str,
    content: str,
    *,
    extra_modules: dict[str, str] | None = None,
    extra_files: dict[str, str] | None = None,
) -> Path:
    skill_dir = plugins_root / plugin / "skills" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    if extra_modules:
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir(exist_ok=True)
        for name, body in extra_modules.items():
            (modules_dir / name).write_text(body, encoding="utf-8")
    if extra_files:
        for relpath, body in extra_files.items():
            target = skill_dir / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
    return skill_dir


# ----------------------------------------------------------------------
# basic file checks
# ----------------------------------------------------------------------


def test_check_file_exists_true_when_skill_md_present(plugins_root, tmp_path):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# x\n")
    e = MetaEvaluator(plugins_root)
    assert e.check_file_exists(skill) is True


def test_check_file_exists_false_when_missing(plugins_root):
    e = MetaEvaluator(plugins_root)
    assert e.check_file_exists(plugins_root / "missing" / "skills" / "x") is False


def test_read_skill_content_returns_text(plugins_root):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# hello\n")
    e = MetaEvaluator(plugins_root)
    content = e.read_skill_content(skill)
    assert content is not None
    assert "hello" in content


def test_read_skill_content_returns_none_on_error(plugins_root, capsys):
    e = MetaEvaluator(plugins_root, verbose=True)
    out = e.read_skill_content(plugins_root / "missing" / "skills" / "nope")
    assert out is None
    err_out = capsys.readouterr().out
    assert "Failed to read" in err_out


def test_check_toc_exists_returns_true():
    """ToC check is a no-op (skills don't benefit from anchor links)."""
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_toc_exists("anything", "skill") is True


# ----------------------------------------------------------------------
# verification, quick start, quality, anti-cargo
# ----------------------------------------------------------------------


def test_check_verification_steps_passes_with_no_code_blocks():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_verification_steps("just text", "x") is True


def test_check_verification_steps_passes_when_verification_present():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = (
        "```bash\necho 1\n```\n"
        "```bash\necho 2\n```\n"
        "```bash\necho 3\n```\n"
        "Verification: run pytest\n"
    )
    assert e.check_verification_steps(content, "x") is True
    assert e.issues == []


def test_check_verification_steps_fails_when_missing_and_threshold_exceeded():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "```bash\necho 1\n```\n```bash\necho 2\n```\n```bash\necho 3\n```\n"
    assert e.check_verification_steps(content, "x") is False
    assert any(i["type"] == "missing_verification" for i in e.issues)


def test_check_concrete_quick_start_no_section_passes():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_concrete_quick_start("# Title\nNo qs here", "x") is True


def test_check_concrete_quick_start_passes_with_code_block():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "## Quick Start\n```bash\nrun me\n```\n## Next\n"
    assert e.check_concrete_quick_start(content, "x") is True


def test_check_concrete_quick_start_flags_abstract_text():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "## Quick Start\nYou should configure things appropriately.\n"
    assert e.check_concrete_quick_start(content, "x") is False
    assert any(i["type"] == "abstract_quick_start" for i in e.issues)


def test_check_quality_criteria_defined_passes_with_quality_words():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_quality_criteria_defined("includes quality threshold", "x") is True


def test_check_quality_criteria_defined_flags_when_missing():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_quality_criteria_defined("plain prose", "x") is False
    assert any(i["type"] == "missing_quality_criteria" for i in e.issues)


def test_check_anti_cargo_cult_passes_when_present():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_anti_cargo_cult("warning about cargo cult patterns", "x") is True


def test_check_anti_cargo_cult_returns_false_when_missing():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e.check_anti_cargo_cult("plain prose", "x") is False
    # Non-verbose mode: no issue recorded
    assert all(i["type"] != "missing_anti_cargo_cult" for i in e.issues)


def test_check_anti_cargo_cult_records_issue_in_verbose_mode():
    e = MetaEvaluator(Path("/tmp"), verbose=True)  # noqa: S108 - test fixture path, not user input
    e.check_anti_cargo_cult("plain prose", "x")
    assert any(i["type"] == "missing_anti_cargo_cult" for i in e.issues)


# ----------------------------------------------------------------------
# tests_exist
# ----------------------------------------------------------------------


def test_check_tests_exist_returns_true_when_test_file_in_unit_skills(
    plugins_root, tmp_path
):
    test_dir = plugins_root / "abstract" / "tests" / "unit" / "skills"
    test_dir.mkdir(parents=True)
    (test_dir / "test_skills_eval.py").write_text("def test_x(): pass\n")
    e = MetaEvaluator(plugins_root)
    assert e.check_tests_exist("abstract", "skills-eval") is True


def test_check_tests_exist_records_issue_for_critical_missing(plugins_root):
    e = MetaEvaluator(plugins_root)
    assert e.check_tests_exist("abstract", "skills-eval") is False
    assert any(i["type"] == "missing_tests" for i in e.issues)


def test_check_tests_exist_returns_true_quietly_for_non_critical(plugins_root):
    """Non-critical skills with missing tests are tolerated (no issue, returns True)."""
    e = MetaEvaluator(plugins_root)
    before = list(e.issues)
    out = e.check_tests_exist("sanctum", "test-updates")
    # test-updates is NOT in critical_skills - source returns True
    # with no issue recorded for non-critical missing tests.
    assert out is True
    assert e.issues == before


# ----------------------------------------------------------------------
# frontmatter parsing
# ----------------------------------------------------------------------


def test_parse_frontmatter_returns_empty_for_no_frontmatter():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    assert e._parse_frontmatter("no frontmatter here") == {}


def test_parse_frontmatter_extracts_modules_via_yaml():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "---\nname: x\nmodules:\n  - mod-a\n  - modules/mod-b.md\n---\nbody\n"
    fm = e._parse_frontmatter(content)
    assert "modules" in fm
    assert "mod-a" in fm["modules"]


# ----------------------------------------------------------------------
# module path resolution
# ----------------------------------------------------------------------


def test_resolve_module_path_full_relative_path(plugins_root):
    skill = _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        "# x\n",
        extra_modules={"a.md": "x"},
    )
    e = MetaEvaluator(plugins_root)
    out = e._resolve_module_path(skill, "modules/a.md")
    assert out is not None and out.name == "a.md"


def test_resolve_module_path_bare_name_fallback(plugins_root):
    skill = _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        "# x\n",
        extra_modules={"foo.md": "x"},
    )
    e = MetaEvaluator(plugins_root)
    out = e._resolve_module_path(skill, "foo")
    assert out is not None and out.name == "foo.md"


def test_resolve_module_path_returns_none_for_missing(plugins_root):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# x\n")
    e = MetaEvaluator(plugins_root)
    assert e._resolve_module_path(skill, "no-such-thing") is None


# ----------------------------------------------------------------------
# module references
# ----------------------------------------------------------------------


def test_check_module_references_reports_missing(plugins_root):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# x\n")
    e = MetaEvaluator(plugins_root)
    out = e.check_module_references(skill, {"modules": ["does-not-exist"]}, "x")
    assert out is False
    assert any(i["type"] == "missing_module_file" for i in e.issues)


def test_check_module_references_reports_unlisted(plugins_root):
    skill = _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        "# x\n",
        extra_modules={"orphan.md": "x"},
    )
    e = MetaEvaluator(plugins_root)
    out = e.check_module_references(skill, {"modules": []}, "x")
    assert out is False
    assert any(i["type"] == "unlisted_module_file" for i in e.issues)


def test_check_module_references_passes_when_all_aligned(plugins_root):
    skill = _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        "# x\n",
        extra_modules={"good.md": "x"},
    )
    e = MetaEvaluator(plugins_root)
    out = e.check_module_references(skill, {"modules": ["modules/good.md"]}, "x")
    assert out is True


# ----------------------------------------------------------------------
# code examples
# ----------------------------------------------------------------------


def test_check_code_examples_passes_for_annotated_blocks():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "```python\nx = 1\ny = 2\nz = 3\n```\n"
    assert e.check_code_examples(content, "x") is True


def test_check_code_examples_skips_short_blocks():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "```\nshort\n```\n"
    assert e.check_code_examples(content, "x") is True


def test_check_code_examples_flags_unannotated_blocks():
    e = MetaEvaluator(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    content = "```\nline one\nline two\nline three\nline four\n```\n"
    assert e.check_code_examples(content, "x") is False
    assert any(i["type"] == "unannotated_code_block" for i in e.issues)


# ----------------------------------------------------------------------
# cross references
# ----------------------------------------------------------------------


def test_check_cross_references_skips_external_and_anchor_links(plugins_root):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# x\n")
    e = MetaEvaluator(plugins_root)
    content = "[ext](https://example.com) [anchor](#section)"
    assert e.check_cross_references(skill, content, "x") is True


def test_check_cross_references_passes_for_existing_relative_link(plugins_root):
    skill = _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        "# x\n",
        extra_files={"adjacent.md": "y"},
    )
    e = MetaEvaluator(plugins_root)
    assert e.check_cross_references(skill, "[a](adjacent.md)", "x") is True


def test_check_cross_references_flags_broken_link(plugins_root):
    skill = _make_skill(plugins_root, "abstract", "skills-eval", "# x\n")
    e = MetaEvaluator(plugins_root)
    out = e.check_cross_references(skill, "[a](missing.md)", "x")
    assert out is False
    assert any(i["type"] == "broken_cross_reference" for i in e.issues)


# ----------------------------------------------------------------------
# evaluate_skill / evaluate_all / printers
# ----------------------------------------------------------------------


def test_evaluate_skill_records_missing_skill(plugins_root):
    e = MetaEvaluator(plugins_root)
    out = e.evaluate_skill("abstract", "no-such-skill")
    assert out["checks"]["exists"] is False
    assert any(i["type"] == "missing_skill" for i in e.issues)


def test_evaluate_skill_runs_full_set(plugins_root):
    skill_content = (
        "---\n"
        "name: skills-eval\n"
        "modules:\n"
        "  - modules/intro.md\n"
        "---\n"
        "## Quick Start\n"
        "```bash\nrun pytest\n```\n"
        "## Quality\n"
        "Defines quality criteria and threshold metrics.\n"
        "## Verification\n"
        "Verify by running pytest. Anti-pattern: testing theater.\n"
    )
    _make_skill(
        plugins_root,
        "abstract",
        "skills-eval",
        skill_content,
        extra_modules={"intro.md": "x"},
    )
    e = MetaEvaluator(plugins_root)
    result = e.evaluate_skill("abstract", "skills-eval")
    assert result["checks"]["exists"] is True
    # Most checks should pass on a well-formed synthetic skill
    assert result["checks"]["quality_criteria"] is True


def test_evaluate_all_filters_by_inventory(plugins_root, monkeypatch):
    e = MetaEvaluator(plugins_root)
    # Restrict inventory to one missing skill so we get deterministic counts
    monkeypatch.setattr(e, "EVALUATION_SKILLS", {"abstract": ["skills-eval"]})
    out = e.evaluate_all()
    assert out["skills_evaluated"] == 1
    assert out["skills_with_issues"] == 1


def test_print_results_emits_sections(plugins_root, capsys):
    e = MetaEvaluator(plugins_root, verbose=True)
    fake_results = {
        "skills_evaluated": 1,
        "skills_passed": 0,
        "skills_with_issues": 1,
        "total_issues": 1,
        "by_severity": {
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0,
        },
        "results": [{"plugin": "abstract", "skill": "skills-eval", "checks": {}}],
    }
    e.issues = [
        {
            "type": "missing_quality_criteria",
            "skill": "abstract:skills-eval",
            "severity": "high",
            "message": "msg",
            "fix": "do thing",
        }
    ]
    e.print_results(fake_results)
    out = capsys.readouterr().out
    assert "META-EVALUATION RESULTS" in out
    assert "DETAILED RESULTS" in out


def test_print_summary_zero_issues(plugins_root, capsys):
    e = MetaEvaluator(plugins_root)
    e.print_summary(
        {
            "total_issues": 0,
            "skills_evaluated": 1,
            "skills_passed": 1,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }
    )
    out = capsys.readouterr().out
    assert "All evaluation skills meet quality standards" in out


def test_print_summary_low_pass_rate_warning(plugins_root, capsys):
    e = MetaEvaluator(plugins_root)
    e.print_summary(
        {
            "total_issues": 5,
            "skills_evaluated": 5,
            "skills_passed": 1,
            "by_severity": {
                "critical": 1,
                "high": 1,
                "medium": 1,
                "low": 1,
            },
        }
    )
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "CRITICAL" in out


def test_print_summary_caution_band(plugins_root, capsys):
    e = MetaEvaluator(plugins_root)
    e.print_summary(
        {
            "total_issues": 1,
            "skills_evaluated": 10,
            "skills_passed": 6,  # 60% pass rate -> caution
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 1,
                "low": 0,
            },
        }
    )
    out = capsys.readouterr().out
    assert "CAUTION" in out


def test_print_summary_good_band(plugins_root, capsys):
    e = MetaEvaluator(plugins_root)
    e.print_summary(
        {
            "total_issues": 1,
            "skills_evaluated": 10,
            "skills_passed": 9,  # 90% pass rate -> good
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 1,
            },
        }
    )
    out = capsys.readouterr().out
    assert "GOOD" in out


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------


def test_main_missing_plugins_root_exits_1(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "meta_evaluation.py",
            "--plugins-root",
            str(tmp_path / "missing"),
        ],
    )
    raised = False
    try:
        main()
    except SystemExit as exc:
        raised = exc.code == 1
    assert raised


def test_main_runs_when_plugins_root_exists(monkeypatch, plugins_root, capsys):
    plugins_root.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "meta_evaluation.py",
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "abstract",
        ],
    )
    raised_code: int | None = None
    try:
        main()
    except SystemExit as exc:
        raised_code = int(exc.code) if isinstance(exc.code, int) else 1
    out = capsys.readouterr().out
    assert "META-EVALUATION RESULTS" in out
    # Critical issues -> exit 1
    assert raised_code in (None, 0, 1)


def test_main_unknown_plugin_warns(monkeypatch, plugins_root, capsys):
    plugins_root.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "meta_evaluation.py",
            "--plugins-root",
            str(plugins_root),
            "--plugin",
            "no-such-plugin",
        ],
    )
    try:
        main()
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "not in evaluation skills inventory" in out
