"""Tier 2 (tree-sitter) and Tier 3 (call graph) of the performance review.

Both tiers need the optional ``tiers`` extra (gauntlet plus tree-sitter),
which the dev dependency group installs so these tests run the real
parser and the real GraphStore.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from gauntlet.graph import GraphStore
from gauntlet.incremental import full_build
from pensive.skills import performance_review as pr_mod
from pensive.skills.performance_review import PerformanceReviewSkill

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


def _analyze(path: Path, code: str):
    context = Mock()
    context.get_file_content.return_value = code
    return PerformanceReviewSkill().analyze(context, str(path))


def _write(tmp_path: Path, name: str, code: str) -> Path:
    path = tmp_path / name
    path.write_text(code)
    return path


JS_NESTED = (
    "function pairs(xs) {\n"
    "  for (const a of xs) {\n"
    "    for (const b of xs) {\n"
    "      use(a, b);\n"
    "    }\n"
    "  }\n"
    "}\n"
)

GO_NESTED = (
    "package m\n"
    "func pairs(xs []int) {\n"
    "\tfor _, a := range xs {\n"
    "\t\tfor _, b := range xs {\n"
    "\t\t\tuse(a, b)\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


class TestTier2Detection:
    def test_analyze_reads_a_non_python_file_once(self, tmp_path) -> None:
        path = _write(tmp_path, "a.js", JS_NESTED)
        context = Mock()
        context.get_file_content.return_value = JS_NESTED
        PerformanceReviewSkill().analyze(context, str(path))
        context.get_file_content.assert_called_once_with(str(path))

    def test_js_nested_loop_same_iterable_is_high_time(self, tmp_path) -> None:
        path = _write(tmp_path, "a.js", JS_NESTED)
        result = _analyze(path, JS_NESTED)
        hits = [f for f in result.issues if f.category == "time"]
        assert len(hits) == 1, result.issues
        assert hits[0].severity == "HIGH"
        assert hits[0].line == 3
        assert "'xs'" in hits[0].message
        assert hits[0].file == str(path)

    def test_go_nested_range_same_iterable_is_high_time(self, tmp_path) -> None:
        code = GO_NESTED
        path = _write(tmp_path, "a.go", code)
        result = _analyze(path, code)
        hits = [f for f in result.issues if f.category == "time"]
        assert [(f.severity, f.line) for f in hits] == [("HIGH", 4)], result.issues

    def test_nested_loops_over_different_iterables_do_not_fire(self, tmp_path) -> None:
        code = "function f(xs, ys) {\n  for (const a of xs) {\n    for (const b of ys) { use(a, b); }\n  }\n}\n"
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    def test_single_loop_does_not_fire(self, tmp_path) -> None:
        code = "function f(xs) {\n  for (const a of xs) { use(a); }\n}\n"
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    def test_loop_inside_nested_function_does_not_inherit_outer_loop(
        self, tmp_path
    ) -> None:
        code = (
            "function f(xs) {\n"
            "  for (const a of xs) {\n"
            "    const g = () => { for (const b of xs) { use(b); } };\n"
            "  }\n"
            "}\n"
        )
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    @pytest.mark.parametrize("call", ["names.includes(x)", "names.indexOf(x)"])
    def test_js_list_scan_in_loop_is_high_time(self, tmp_path, call) -> None:
        code = f"function f(xs, names) {{\n  for (const x of xs) {{\n    if ({call}) {{}}\n  }}\n}}\n"
        path = _write(tmp_path, "a.js", code)
        hits = _analyze(path, code).issues
        assert [(f.severity, f.category, f.line) for f in hits] == [
            ("HIGH", "time", 3)
        ], hits

    def test_ts_list_scan_in_loop_fires(self, tmp_path) -> None:
        code = "function f(xs: string[], names: string[]) {\n  for (const x of xs) {\n    names.includes(x);\n  }\n}\n"
        path = _write(tmp_path, "a.ts", code)
        assert [f.line for f in _analyze(path, code).issues] == [3]

    def test_js_set_has_in_loop_does_not_fire(self, tmp_path) -> None:
        code = "function f(xs, names) {\n  for (const x of xs) {\n    if (names.has(x)) {}\n  }\n}\n"
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    def test_js_includes_outside_loop_does_not_fire(self, tmp_path) -> None:
        code = "function f(xs, x) {\n  return xs.includes(x);\n}\n"
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    @pytest.mark.parametrize(
        "call", ["slices.Contains(names, x)", "slices.Index(names, x)"]
    )
    def test_go_slices_scan_in_loop_is_high_time(self, tmp_path, call) -> None:
        code = (
            "package m\n"
            "func f(xs []string, names []string) {\n"
            "\tfor _, x := range xs {\n"
            f"\t\t_ = {call}\n"
            "\t}\n"
            "}\n"
        )
        path = _write(tmp_path, "a.go", code)
        hits = _analyze(path, code).issues
        assert [(f.severity, f.category, f.line) for f in hits] == [
            ("HIGH", "time", 4)
        ], hits

    def test_js_push_in_nested_loops_is_medium_space(self, tmp_path) -> None:
        code = (
            "function f(xs, ys, out) {\n"
            "  for (const a of xs) {\n"
            "    for (const b of ys) {\n"
            "      out.push([a, b]);\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        path = _write(tmp_path, "a.js", code)
        hits = _analyze(path, code).issues
        assert [(f.severity, f.category, f.line) for f in hits] == [
            ("MEDIUM", "space", 4)
        ], hits

    def test_js_push_in_single_loop_does_not_fire(self, tmp_path) -> None:
        code = "function f(xs, out) {\n  for (const a of xs) { out.push(a); }\n}\n"
        path = _write(tmp_path, "a.js", code)
        assert _analyze(path, code).issues == []

    def test_go_append_in_nested_loops_is_medium_space(self, tmp_path) -> None:
        code = (
            "package m\n"
            "func f(xs, ys []int, out []int) []int {\n"
            "\tfor _, a := range xs {\n"
            "\t\tfor _, b := range ys {\n"
            "\t\t\tout = append(out, a+b)\n"
            "\t\t}\n"
            "\t}\n"
            "\treturn out\n"
            "}\n"
        )
        path = _write(tmp_path, "a.go", code)
        hits = _analyze(path, code).issues
        assert [(f.severity, f.category, f.line) for f in hits] == [
            ("MEDIUM", "space", 5)
        ], hits

    def test_rust_push_in_nested_loops_and_same_iterable(self, tmp_path) -> None:
        code = (
            "fn f(xs: &Vec<i32>, out: &mut Vec<i32>) {\n"
            "    for a in xs {\n"
            "        for b in xs {\n"
            "            out.push(a + b);\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        path = _write(tmp_path, "a.rs", code)
        hits = _analyze(path, code).issues
        assert sorted((f.category, f.line) for f in hits) == [
            ("space", 4),
            ("time", 3),
        ], hits

    def test_java_nested_enhanced_for_same_iterable(self, tmp_path) -> None:
        code = (
            "class A {\n"
            "  void f(java.util.List<Integer> xs) {\n"
            "    for (int a : xs) {\n"
            "      for (int b : xs) { use(a, b); }\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        path = _write(tmp_path, "A.java", code)
        assert [(f.severity, f.line) for f in _analyze(path, code).issues] == [
            ("HIGH", 4)
        ]

    def test_cpp_push_back_in_nested_loops_is_medium_space(self, tmp_path) -> None:
        code = (
            "void f(std::vector<int>& xs, std::vector<int>& ys,"
            " std::vector<int>& out) {\n"
            "  for (int a : xs) {\n"
            "    for (int b : ys) {\n"
            "      out.push_back(a + b);\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        path = _write(tmp_path, "a.cpp", code)
        assert [
            (f.severity, f.category, f.line) for f in _analyze(path, code).issues
        ] == [("MEDIUM", "space", 4)]

    def test_unsupported_extension_is_ignored(self, tmp_path) -> None:
        path = _write(tmp_path, "a.txt", JS_NESTED)
        result = _analyze(path, JS_NESTED)
        assert result.issues == []
        assert result.warnings == []

    def test_python_files_stay_on_tier1(self, tmp_path, monkeypatch) -> None:
        def boom(_lang):
            raise AssertionError("tier 2 must not run for .py")

        monkeypatch.setattr(pr_mod, "_ts_get_parser", boom)
        code = "def f(xs):\n    for a in xs:\n        for b in xs:\n            pass\n"
        path = _write(tmp_path, "a.py", code)
        assert len(_analyze(path, code).issues) == 1


class TestTier2Warnings:
    def test_unparsable_file_adds_warning_and_no_findings(self, tmp_path) -> None:
        code = "function ( { for for for ]]] ))\n"
        path = _write(tmp_path, "bad.js", code)
        result = _analyze(path, code)
        assert result.issues == []
        assert len(result.warnings) == 1
        assert "bad.js" in result.warnings[0]

    def test_deeply_nested_file_adds_warning_instead_of_recursion_error(
        self, tmp_path
    ) -> None:
        code = "var x = " + "(" * 1500 + "1" + ")" * 1500 + ";\n"
        path = _write(tmp_path, "deep.js", code)
        result = _analyze(path, code)
        assert result.issues == []
        assert len(result.warnings) == 1
        assert "deep.js" in result.warnings[0]

    def test_parser_failure_adds_warning(self, tmp_path, monkeypatch) -> None:
        def broken(_lang):
            raise LookupError("no grammar")

        monkeypatch.setattr(pr_mod, "_ts_get_parser", broken)
        path = _write(tmp_path, "a.js", JS_NESTED)
        result = _analyze(path, JS_NESTED)
        assert result.issues == []
        assert "no grammar" in result.warnings[0]

    def test_missing_tree_sitter_is_silent_noop(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(pr_mod, "_ts_get_parser", None)
        path = _write(tmp_path, "a.js", JS_NESTED)
        result = _analyze(path, JS_NESTED)
        assert result.issues == []
        assert result.warnings == []

    def test_pack_without_error_class_still_enables_tier_two(self, tmp_path) -> None:
        """Python 3.9 resolves the 0.9.x pack, which exports no ``Error``.

        The parser must still load, with LookupError standing in for the
        pack's own error class.
        """
        fake = tmp_path / "tree_sitter_language_pack"
        fake.mkdir()
        (fake / "__init__.py").write_text("def get_parser(language):\n    pass\n")
        probe = (
            "import sys\n"
            f"sys.path.insert(0, {str(tmp_path)!r})\n"
            "from pensive.skills import performance_review as m\n"
            "print(m._ts_get_parser.__module__, m._TsPackError.__name__)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split() == ["tree_sitter_language_pack", "LookupError"]

    def test_local_extension_map_used_when_gauntlet_detect_missing(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setattr(pr_mod, "_gt_detect_language", None)
        path = _write(tmp_path, "a.js", JS_NESTED)
        assert len(_analyze(path, JS_NESTED).issues) == 1


CALLER = (
    "from callee import helper\n"
    "\n"
    "\n"
    "def entry(rows):\n"
    "    total = 0\n"
    "    for row in rows:\n"
    "        total += 1\n"
    "    return helper(rows)\n"
    "\n"
    "\n"
    "def slow_here(items):\n"
    "    for x in items:\n"
    "        for y in items:\n"
    "            pass\n"
    "    return helper(items)\n"
)

HOT_CALLEE = (
    "def helper(items):\n"
    "    count = 0\n"
    "    for a in items:\n"
    "        for b in items:\n"
    "            count += 1\n"
    "    return count\n"
)

CLEAN_CALLEE = "def helper(items):\n    return len(items)\n"


def _build_graph(root: Path) -> None:
    (root / ".gauntlet").mkdir()
    with GraphStore(root / ".gauntlet" / "graph.db") as graph:
        full_build(str(root), graph)


@pytest.fixture
def project(tmp_path):
    root = tmp_path.resolve()
    return root


class TestTier3Upgrade:
    def test_high_finding_upgrades_to_critical_when_callee_is_hotspot(
        self, project
    ) -> None:
        caller = _write(project, "caller.py", CALLER)
        _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)

        result = _analyze(caller, CALLER)

        assert len(result.issues) == 1, result.issues
        finding = result.issues[0]
        assert finding.severity == "CRITICAL"
        assert "helper" in finding.message
        assert finding.message.count("Severity raised") == 1

    def test_upgrade_is_one_step_only(self, project) -> None:
        caller_code = (
            "from callee import helper\n"
            "\n"
            "\n"
            "def entry(items, out):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            out.append(x)\n"
            "    return helper(items)\n"
        )
        caller = _write(project, "caller.py", caller_code)
        _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)

        severities = {
            f.category: f.severity for f in _analyze(caller, caller_code).issues
        }

        assert severities == {"time": "CRITICAL", "space": "HIGH"}

    def test_no_upgrade_when_callee_is_clean(self, project) -> None:
        caller = _write(project, "caller.py", CALLER)
        _write(project, "callee.py", CLEAN_CALLEE)
        _build_graph(project)

        result = _analyze(caller, CALLER)

        assert [f.severity for f in result.issues] == ["HIGH"]
        assert "Severity raised" not in result.issues[0].message

    def test_finding_not_upgraded_by_unrelated_hot_function(self, project) -> None:
        caller_code = (
            "def entry(items):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            pass\n"
            "\n"
            "\n"
            "def unrelated():\n"
            "    return 1\n"
        )
        caller = _write(project, "caller.py", caller_code)
        _write(project, "other.py", HOT_CALLEE)
        _build_graph(project)

        assert [f.severity for f in _analyze(caller, caller_code).issues] == ["HIGH"]

    def test_transitive_callee_two_hops_away_upgrades(self, project) -> None:
        caller_code = (
            "from mid import middle\n"
            "\n"
            "\n"
            "def entry(items):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            pass\n"
            "    return middle(items)\n"
        )
        mid = "from callee import helper\n\n\ndef middle(items):\n    return helper(items)\n"
        caller = _write(project, "caller.py", caller_code)
        _write(project, "mid.py", mid)
        _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)

        assert [f.severity for f in _analyze(caller, caller_code).issues] == [
            "CRITICAL"
        ]

    def test_call_cycle_terminates(self, project) -> None:
        cycle = (
            "def ping(items):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            pass\n"
            "    return pong(items)\n"
            "\n"
            "\n"
            "def pong(items):\n"
            "    return ping(items)\n"
        )
        path = _write(project, "cycle.py", cycle)
        _build_graph(project)

        result = _analyze(path, cycle)

        # pong reaches ping only, and the seed is excluded: no upgrade.
        assert [f.severity for f in result.issues] == ["HIGH"]

    def test_cycle_between_two_hot_callees_terminates_and_upgrades(
        self, project
    ) -> None:
        caller_code = (
            "from callee import helper\n"
            "\n"
            "\n"
            "def entry(items):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            pass\n"
            "    return helper(items)\n"
        )
        callee = HOT_CALLEE + "\n\ndef other(items):\n    return helper(items)\n"
        callee = callee.replace(
            "    return count\n", "    return other(items) + count\n", 1
        )
        caller = _write(project, "caller.py", caller_code)
        _write(project, "callee.py", callee)
        _build_graph(project)

        assert [f.severity for f in _analyze(caller, caller_code).issues] == [
            "CRITICAL"
        ]

    def test_critical_stays_critical(self) -> None:
        assert pr_mod._upgrade_severity("CRITICAL") == "CRITICAL"

    @pytest.mark.parametrize(
        ("before", "after"),
        [("LOW", "MEDIUM"), ("MEDIUM", "HIGH"), ("HIGH", "CRITICAL")],
    )
    def test_upgrade_ladder_moves_one_step(self, before, after) -> None:
        assert pr_mod._upgrade_severity(before) == after

    def test_no_graph_db_returns_findings_unchanged(self, project) -> None:
        caller = _write(project, "caller.py", CALLER)
        _write(project, "callee.py", HOT_CALLEE)

        assert [f.severity for f in _analyze(caller, CALLER).issues] == ["HIGH"]

    def test_finding_outside_any_function_is_left_alone(self, project) -> None:
        module_level = (
            "items = [1, 2]\nfor x in items:\n    for y in items:\n        pass\n"
        )
        caller = _write(project, "caller.py", module_level)
        _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)

        # Module-level code has no Function node, so Tier 1 flags it alone.
        assert [f.severity for f in _analyze(caller, module_level).issues] == ["HIGH"]

    def test_js_finding_upgrades_through_tier2_hotspots(self, project) -> None:
        caller_code = (
            "import { helper } from './callee.js';\n"
            "function entry(xs) {\n"
            "  for (const a of xs) {\n"
            "    for (const b of xs) { use(a, b); }\n"
            "  }\n"
            "  return helper(xs);\n"
            "}\n"
        )
        callee_code = (
            "export function helper(xs) {\n"
            "  for (const a of xs) {\n"
            "    for (const b of xs) { use(a, b); }\n"
            "  }\n"
            "}\n"
        )
        caller = _write(project, "caller.js", caller_code)
        _write(project, "callee.js", callee_code)
        _build_graph(project)

        assert [f.severity for f in _analyze(caller, caller_code).issues] == [
            "CRITICAL"
        ]

    def test_graph_db_found_by_walking_up_from_scanned_file(self, project) -> None:
        sub = project / "pkg" / "inner"
        sub.mkdir(parents=True)
        caller = _write(sub, "caller.py", CALLER)
        _write(sub, "callee.py", HOT_CALLEE)
        _build_graph(project)

        assert [f.severity for f in _analyze(caller, CALLER).issues] == ["CRITICAL"]

    def test_graph_node_outside_the_db_project_is_not_read(
        self, project, tmp_path_factory
    ) -> None:
        # graph.db sits in the reviewed repository, so its file paths are
        # repository-controlled. A node pointing outside the project must
        # not make the review read that file.
        caller = _write(project, "caller.py", CALLER)
        callee = _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)
        outside = tmp_path_factory.mktemp("outside").resolve() / "callee.py"
        outside.write_text(HOT_CALLEE)
        callee.write_text(CLEAN_CALLEE)
        db = sqlite3.connect(project / ".gauntlet" / "graph.db")
        with db:
            db.execute(
                "UPDATE nodes SET file_path = ? WHERE file_path = ?",
                (str(outside), str(callee)),
            )
        db.close()

        assert [f.severity for f in _analyze(caller, CALLER).issues] == ["HIGH"]

    def test_corrupt_graph_db_adds_warning_and_keeps_findings(self, project) -> None:
        caller = _write(project, "caller.py", CALLER)
        (project / ".gauntlet").mkdir()
        (project / ".gauntlet" / "graph.db").write_bytes(b"not a sqlite database" * 50)

        result = _analyze(caller, CALLER)

        assert [f.severity for f in result.issues] == ["HIGH"]
        assert any("graph unreadable" in w for w in result.warnings)

    def test_callee_that_no_longer_parses_is_not_a_hotspot(self, project) -> None:
        caller = _write(project, "caller.py", CALLER)
        callee = _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)
        callee.write_text("def helper(items:\n")

        assert [f.severity for f in _analyze(caller, CALLER).issues] == ["HIGH"]

    def test_callee_file_deleted_after_build_is_not_a_hotspot(self, project) -> None:
        caller = _write(project, "caller.py", CALLER)
        callee = _write(project, "callee.py", HOT_CALLEE)
        _build_graph(project)
        callee.unlink()

        assert [f.severity for f in _analyze(caller, CALLER).issues] == ["HIGH"]


TSX_NESTED = (
    "export function Grid({ rows }: { rows: number[] }) {\n"
    "  for (const a of rows) {\n"
    "    for (const b of rows) {\n"
    "      use(a, b);\n"
    "    }\n"
    "  }\n"
    "  return <div>{rows.length}</div>;\n"
    "}\n"
)


class TestTierEdges:
    def test_tsx_file_is_parsed_with_the_tsx_grammar(self, tmp_path) -> None:
        """
        GIVEN a .tsx file with JSX and a nested loop over one iterable
        WHEN the file is analyzed
        THEN the nested loop is reported and no parse warning is added
        """
        path = _write(tmp_path, "grid.tsx", TSX_NESTED)

        result = _analyze(path, TSX_NESTED)

        hits = [f for f in result.issues if f.category == "time"]
        assert [(f.severity, f.line) for f in hits] == [("HIGH", 3)], result.issues
        assert not result.warnings

    def test_language_for_tsx_returns_tsx_not_typescript(self) -> None:
        """
        GIVEN a .tsx path
        WHEN the Tier 2 grammar is chosen
        THEN it is "tsx", even though gauntlet maps the suffix to typescript
        """
        assert pr_mod._language_for("app/view.tsx") == "tsx"

    def test_unknown_severity_is_returned_unchanged(self) -> None:
        """
        GIVEN a severity string outside the ladder
        WHEN it is upgraded
        THEN it comes back unchanged
        """
        assert pr_mod._upgrade_severity("UNRANKED") == "UNRANKED"

    def test_hot_callee_beyond_the_call_depth_cap_is_not_found(self, project) -> None:
        """
        GIVEN a seed whose only hot callee sits 11 call hops away
        WHEN Tier 3 searches the call graph
        THEN the search stops at the depth cap and the finding stays HIGH
        """
        hops = pr_mod._MAX_CALL_DEPTH + 1
        parts = [
            "def entry(items):\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            pass\n"
            "    return hop1(items)\n"
        ]
        parts += [
            f"def hop{n}(items):\n    return hop{n + 1}(items)\n"
            for n in range(1, hops)
        ]
        parts.append(HOT_CALLEE.replace("helper", f"hop{hops}"))
        code = "\n\n".join(parts)
        path = _write(project, "chain.py", code)
        _build_graph(project)

        entry = [f for f in _analyze(path, code).issues if f.line == 3]
        assert [f.severity for f in entry] == ["HIGH"]
