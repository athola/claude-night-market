"""Tests for Phase 2-4 phase methods + audit_all + main() in update_plugin_registrations.py.

Targets the previously uncovered phase summaries, audit orchestration,
and CLI entry-point branches.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "update_plugin_registrations.py"
)


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "sanctum_update_plugin_registrations", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_update_plugin_registrations"] = module
    spec.loader.exec_module(module)
    return module


def _make_plugin(plugins_root: Path, plugin: str) -> Path:
    """Create a minimal plugin tree with valid plugin.json."""
    plugin_dir = plugins_root / plugin
    (plugin_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": plugin,
                "version": "0.1.0",
                "commands": [],
                "skills": [],
                "agents": [],
                "hooks": [],
            },
            indent=2,
        )
    )
    return plugin_dir


def test_print_performance_summary_renders_sections(tmp_path, capsys):
    upr = _load_script()
    auditor = upr.PluginAuditor(tmp_path, dry_run=True)
    report = {
        "demo": {
            "unstable_skills": [
                {"skill": "alpha", "stability_gap": 0.45},
            ],
            "recent_failures": [
                {"skill": "alpha", "failures": 3},
            ],
            "low_success_rate": [
                {"skill": "alpha", "success_rate": 0.7},
            ],
        }
    }
    auditor._print_performance_summary(report)
    out = capsys.readouterr().out
    assert "PERFORMANCE & IMPROVEMENT" in out
    assert "Unstable" in out
    assert "Recent failures" in out
    assert "Low success" in out


def test_print_meta_eval_summary_renders_sections(tmp_path, capsys):
    upr = _load_script()
    auditor = upr.PluginAuditor(tmp_path, dry_run=True)
    report = {
        "demo": {
            "missing_toc": ["foo"],
            "missing_verification": ["bar"],
            "missing_tests": ["baz"],
        }
    }
    auditor._print_meta_eval_summary(report)
    out = capsys.readouterr().out
    assert "META-EVALUATION CHECK" in out
    assert "foo" in out
    assert "bar" in out
    assert "baz" in out


def test_print_queue_summary_truncates_long_lists(tmp_path, capsys):
    upr = _load_script()
    auditor = upr.PluginAuditor(tmp_path, dry_run=True)
    items = [{"priority": "p", "file": f"file{i}.md", "age_days": i} for i in range(15)]
    auditor._print_queue_summary(items)
    out = capsys.readouterr().out
    assert "QUEUE" in out
    assert "15" in out  # 15 pending items
    assert "and 5 more" in out  # 15 - 10 limit


def test_print_queue_summary_uses_today_for_zero_age(tmp_path, capsys):
    upr = _load_script()
    auditor = upr.PluginAuditor(tmp_path, dry_run=True)
    auditor._print_queue_summary([{"priority": "p", "file": "x.md", "age_days": 0}])
    out = capsys.readouterr().out
    assert "today" in out


def test_audit_all_returns_zero_when_clean(tmp_path, capsys, monkeypatch):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    auditor = upr.PluginAuditor(plugins_root, dry_run=True)
    # Stub out phase 2-4 to avoid heavy IO
    monkeypatch.setattr(auditor, "audit_plugin", lambda _name: False)
    monkeypatch.setattr(auditor, "analyze_skill_performance", lambda _n: {})
    monkeypatch.setattr(auditor, "check_meta_evaluation", lambda _p: {})
    monkeypatch.setattr(auditor, "check_knowledge_queue", lambda: [])

    rc = auditor.audit_all()
    assert rc == 0
    out = capsys.readouterr().out
    assert "AUDIT SUMMARY" in out


def test_audit_all_emits_phase_reports_when_data_present(tmp_path, capsys, monkeypatch):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    auditor = upr.PluginAuditor(plugins_root, dry_run=True)
    monkeypatch.setattr(auditor, "audit_plugin", lambda _name: False)
    monkeypatch.setattr(
        auditor,
        "analyze_skill_performance",
        lambda _n: {
            "unstable_skills": [{"skill": "x", "stability_gap": 0.4}],
            "recent_failures": [],
            "low_success_rate": [],
        },
    )
    monkeypatch.setattr(
        auditor,
        "check_meta_evaluation",
        lambda _p: {
            "missing_toc": ["x"],
            "missing_verification": [],
            "missing_tests": [],
        },
    )
    monkeypatch.setattr(
        auditor,
        "check_knowledge_queue",
        lambda: [{"priority": "high", "file": "x.md", "age_days": 0}],
    )

    rc = auditor.audit_all()
    assert rc == 0
    out = capsys.readouterr().out
    assert "PERFORMANCE & IMPROVEMENT" in out
    assert "META-EVALUATION CHECK" in out
    assert "QUEUE" in out


def test_audit_all_specific_plugin(tmp_path, capsys, monkeypatch):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    auditor = upr.PluginAuditor(plugins_root, dry_run=True)
    seen_calls = []
    monkeypatch.setattr(
        auditor,
        "audit_plugin",
        lambda name: seen_calls.append(name) or False,
    )
    monkeypatch.setattr(auditor, "analyze_skill_performance", lambda _n: {})
    monkeypatch.setattr(auditor, "check_meta_evaluation", lambda _p: {})
    monkeypatch.setattr(auditor, "check_knowledge_queue", lambda: [])

    auditor.audit_all("demo")
    assert seen_calls == ["demo"]


def test_audit_all_invokes_fix_for_discrepancies_when_not_dry(
    tmp_path, capsys, monkeypatch
):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    auditor = upr.PluginAuditor(plugins_root, dry_run=False)
    auditor.discrepancies = {"demo": {"missing_skills": ["x"]}}
    fixed = []
    monkeypatch.setattr(auditor, "audit_plugin", lambda _n: True)
    monkeypatch.setattr(auditor, "fix_plugin", lambda n: fixed.append(n))
    monkeypatch.setattr(auditor, "analyze_skill_performance", lambda _n: {})
    monkeypatch.setattr(auditor, "check_meta_evaluation", lambda _p: {})
    monkeypatch.setattr(auditor, "check_knowledge_queue", lambda: [])

    auditor.audit_all()
    out = capsys.readouterr().out
    assert "FIXING DISCREPANCIES" in out
    assert "demo" in fixed


def test_main_missing_root_exits_1(monkeypatch, tmp_path, capsys):
    upr = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_plugin_registrations.py",
            "--plugins-root",
            str(tmp_path / "missing"),
        ],
    )
    raised: int | None = None
    try:
        upr.main()
    except SystemExit as exc:
        raised = int(exc.code) if isinstance(exc.code, int) else 1
    assert raised == 1
    err = capsys.readouterr().out
    assert "Plugins root not found" in err


def test_main_clean_exit_zero(monkeypatch, tmp_path, capsys):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    # Patch PluginAuditor.audit_all to return 0 (clean).
    monkeypatch.setattr(upr.PluginAuditor, "audit_all", lambda self, plugin=None: 0)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_plugin_registrations.py",
            "--plugins-root",
            str(plugins_root),
        ],
    )
    raised: int | None = None
    try:
        upr.main()
    except SystemExit as exc:
        raised = int(exc.code) if isinstance(exc.code, int) else 1
    assert raised == 0
    out = capsys.readouterr().out
    assert "consistent registrations" in out


def test_main_dry_run_with_issues_exits_1_with_hint(monkeypatch, tmp_path, capsys):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    monkeypatch.setattr(upr.PluginAuditor, "audit_all", lambda self, plugin=None: 1)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_plugin_registrations.py",
            "--plugins-root",
            str(plugins_root),
        ],
    )
    raised: int | None = None
    try:
        upr.main()
    except SystemExit as exc:
        raised = int(exc.code) if isinstance(exc.code, int) else 1
    assert raised == 1
    out = capsys.readouterr().out
    assert "Run with --fix" in out


def test_main_fix_with_issues_exits_1_without_hint(monkeypatch, tmp_path, capsys):
    upr = _load_script()
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _make_plugin(plugins_root, "demo")

    monkeypatch.setattr(upr.PluginAuditor, "audit_all", lambda self, plugin=None: 1)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_plugin_registrations.py",
            "--plugins-root",
            str(plugins_root),
            "--fix",
        ],
    )
    raised: int | None = None
    try:
        upr.main()
    except SystemExit as exc:
        raised = int(exc.code) if isinstance(exc.code, int) else 1
    assert raised == 1
    out = capsys.readouterr().out
    # Hint is only shown for dry-run runs
    assert "Run with --fix" not in out


def test_phase_delegations(tmp_path, monkeypatch):
    """Phase 2/3/4 methods should delegate to their analyzer modules."""
    upr = _load_script()
    auditor = upr.PluginAuditor(tmp_path, dry_run=True)

    monkeypatch.setattr(
        auditor.performance_analyzer,
        "analyze_plugin",
        lambda name: {"plugin": name},
    )
    monkeypatch.setattr(
        auditor.meta_evaluator,
        "check_plugin",
        lambda path: {"path": str(path)},
    )
    monkeypatch.setattr(
        auditor.queue_checker,
        "check_queue",
        lambda: ["item"],
    )

    assert auditor.analyze_skill_performance("foo") == {"plugin": "foo"}
    assert auditor.check_meta_evaluation(Path("/tmp")) == {  # noqa: S108 - test fixture path, not user input
        "path": "/tmp"
    }
    assert auditor.check_knowledge_queue() == ["item"]
