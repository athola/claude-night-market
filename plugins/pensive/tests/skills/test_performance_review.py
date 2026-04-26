"""Unit tests for the performance review skill.

Detects time-complexity and space-complexity hotspots via Python
AST (Tier 1). Optionally enriches via gauntlet's tree-sitter parser
(Tier 2) and code knowledge graph (Tier 3) when those are
importable; falls back gracefully otherwise.

Iron Law: these tests are written BEFORE the implementation. They
should fail with ImportError until performance_review.py exists.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pensive.skills.performance_review import PerformanceReviewSkill


class TestPerformanceReviewSkill:
    """
    Feature: detect time/space complexity hotspots in Python source.

    As a code reviewer,
    I want a skill that flags O(n^2) and unbounded-allocation
    patterns at specific lines,
    So that hot paths can be fixed before they bottleneck production.
    """

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = PerformanceReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    # -----------------------------------------------------------------
    # Tier 1: Time complexity (T1-T6)
    # -----------------------------------------------------------------

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t1_nested_loops_same_iterable(self, mock_skill_context) -> None:
        """
        Scenario: T1 nested for over the same iterable
        Given a function with `for x in items: for y in items:`
        When the skill analyzes the file
        Then a HIGH-severity time finding is emitted at the inner loop
        """
        code = (
            "def find_pairs(items):\n"
            "    out = []\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            if x != y:\n"
            "                out.append((x, y))\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        time_findings = [f for f in result.issues if f.category == "time"]
        assert any(f.severity == "HIGH" and f.line == 4 for f in time_findings), (
            f"T1 not flagged at line 4: {time_findings}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_list_in_lookup_in_loop(self, mock_skill_context) -> None:
        """
        Scenario: T2 `x in list_var` inside a loop body
        Given `for x in xs: if x in ys: ...` where ys is a list
        When the skill analyzes the file
        Then a HIGH-severity time finding suggests using a set
        """
        code = (
            "def overlap(xs, ys):\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        if x in ys:\n"
            "            out.append(x)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert any(f.line == 4 and f.severity == "HIGH" for f in t2), (
            f"T2 not flagged at line 4 with set suggestion: {t2}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_lhs_is_string_literal(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: substring match with a string literal LHS
        Given `for s in items: if 'foo' in s:` where the LHS is a
          string literal and the RHS is therefore a string
        When the skill analyzes the file
        Then NO T2 (set suggestion) finding is emitted: substring
          matching against a string is O(m+n), not O(n^2)
        """
        code = (
            "def matches(items):\n"
            "    out = []\n"
            "    for s in items:\n"
            "        if 'foo' in s:\n"
            "            out.append(s)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], f"T2 false-positive on string-literal substring match: {t2}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_rhs_is_dict_literal(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: RHS is a dict literal
        Given `counts = {'a': 0}; for x in xs: if x in counts:`
        When the skill analyzes the file
        Then NO T2 finding fires: in-on-dict is O(1)
        """
        code = (
            "def tally(xs):\n"
            "    counts = {'a': 0, 'b': 0}\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        if x in counts:\n"
            "            out.append(x)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], f"T2 false-positive when RHS is a dict literal: {t2}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_rhs_is_set_literal(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: RHS is a frozenset / set literal
        Given a module-level frozenset constant used inside a loop
        When the skill analyzes the file
        Then NO T2 finding fires: in-on-set is already O(1)
        """
        code = (
            "_KNOWN = frozenset({'a', 'b', 'c'})\n"
            "def filter_known(xs):\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        if x in _KNOWN:\n"
            "            out.append(x)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], f"T2 false-positive when RHS is a frozenset: {t2}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_rhs_is_string_var(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: RHS is a string variable
        Given `content = '...'; for kw in kws: if kw in content:`
        When the skill analyzes the file
        Then NO T2 finding fires: substring match is O(m+n)
        """
        code = (
            "def find_keywords(keywords, doc):\n"
            "    content = doc.read()\n"
            "    found = []\n"
            "    for kw in keywords:\n"
            "        if kw in content:\n"
            "            found.append(kw)\n"
            "    return found\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")
        # `content` here is from `.read()`. The detector tracks
        # known string-returning methods (.lower/.upper/.strip/.read/
        # .replace/.format/.title/.casefold/.encode/.decode/.join)
        # so the RHS classifies as 'string' and the finding suppresses.
        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], (
            f"T2 false-positive when RHS is from a string-returning method: {t2}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_rhs_is_str_annotated_param(
        self, mock_skill_context
    ) -> None:
        """
        Scenario: T2 negative: RHS is a function param annotated `str`
        Given `def f(content: str): for kw in kws: if kw in content:`
        When the skill analyzes the file
        Then NO T2 finding fires: param is provably a string
        """
        code = (
            "def find_keywords(keywords: list[str], content: str):\n"
            "    out = []\n"
            "    for kw in keywords:\n"
            "        if kw in content:\n"
            "            out.append(kw)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], f"T2 false-positive on str-annotated param: {t2}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_iter_var_is_split_result(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: iter var from `.split()`
        Given `lines = content.split('\\n'); for line in lines: if c in line:`
        When the skill analyzes the file
        Then NO T2 finding fires: each line element is a string
        """
        # Use Name LHS so this test actually exercises iter-var
        # classification (string-literal LHS would be suppressed by v1
        # rules without exercising iter-var tracking).
        code = (
            "def strip(content, comment_char):\n"
            "    lines = content.split('\\n')\n"
            "    out = []\n"
            "    for line in lines:\n"
            "        if comment_char in line:\n"
            "            line = line[:line.index(comment_char)]\n"
            "        out.append(line)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")
        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], f"T2 false-positive on iter var from .split(): {t2}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t2_skipped_when_iter_var_is_str_setcomp(self, mock_skill_context) -> None:
        """
        Scenario: T2 negative: iter var from a string-element set-comp
        Given `names = {x.lower() for x in xs}; for n in names: if k in n:`
        When the skill analyzes the file
        Then NO T2 finding fires: set-comp element type is string
        """
        code = (
            "def find_names(needles, xs):\n"
            "    names = {x.lower() for x in xs}\n"
            "    out = []\n"
            "    for n in names:\n"
            "        for k in needles:\n"
            "            if k in n:\n"
            "                out.append(n)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")
        t2 = [
            f
            for f in result.issues
            if f.category == "time" and "set" in f.suggestion.lower()
        ]
        assert t2 == [], (
            f"T2 false-positive on iter var from string-element setcomp: {t2}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t3_re_compile_inside_loop(self, mock_skill_context) -> None:
        """
        Scenario: T3 `re.compile()` inside a loop body
        Given a regex compiled per iteration instead of hoisted
        When the skill analyzes the file
        Then a MEDIUM-severity time finding flags uncached compilation
        """
        code = (
            "import re\n"
            "def matches(items):\n"
            "    out = []\n"
            "    for s in items:\n"
            "        pat = re.compile(r'\\d+')\n"
            "        if pat.search(s):\n"
            "            out.append(s)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t3 = [
            f
            for f in result.issues
            if f.category == "time" and "compile" in f.message.lower()
        ]
        assert any(f.severity == "MEDIUM" and f.line == 5 for f in t3), (
            f"T3 not flagged at line 5: {t3}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t4_string_concat_in_loop(self, mock_skill_context) -> None:
        """
        Scenario: T4 string accumulation via `s += ...` in a loop
        Given a function building a string with += in a loop
        When the skill analyzes the file
        Then a MEDIUM-severity time finding flags quadratic concat
        """
        code = (
            "def to_csv(rows):\n"
            "    out = ''\n"
            "    for r in rows:\n"
            "        out += ','.join(r) + '\\n'\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t4 = [
            f
            for f in result.issues
            if f.category == "time" and "string" in f.message.lower()
        ]
        assert any(f.severity == "MEDIUM" and f.line == 4 for f in t4), (
            f"T4 not flagged at line 4: {t4}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t5_recursive_without_memoization(self, mock_skill_context) -> None:
        """
        Scenario: T5 recursive function without `@cache` / `@lru_cache`
        Given a recursive fibonacci with no memoization decorator
        When the skill analyzes the file
        Then a LOW-severity time finding suggests memoization
        """
        code = (
            "def fib(n):\n"
            "    if n < 2:\n"
            "        return n\n"
            "    return fib(n - 1) + fib(n - 2)\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t5 = [
            f
            for f in result.issues
            if f.category == "time" and "memo" in f.suggestion.lower()
        ]
        assert any(f.severity == "LOW" for f in t5), (
            f"T5 not flagged with memoization suggestion: {t5}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t5_skipped_when_lru_cache_present(self, mock_skill_context) -> None:
        """
        Scenario: T5 negative — function decorated with @lru_cache
        Given a recursive function with @lru_cache decorator
        When the skill analyzes the file
        Then no T5 memoization warning is emitted
        """
        code = (
            "from functools import lru_cache\n"
            "@lru_cache\n"
            "def fib(n):\n"
            "    if n < 2:\n"
            "        return n\n"
            "    return fib(n - 1) + fib(n - 2)\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t5 = [
            f
            for f in result.issues
            if f.category == "time" and "memo" in f.suggestion.lower()
        ]
        assert t5 == [], f"T5 false-positive on @lru_cache function: {t5}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_t6_list_comp_inside_reducer(self, mock_skill_context) -> None:
        """
        Scenario: T6 list comprehension passed to a reducer
        Given `sum([x*2 for x in xs])`
        When the skill analyzes the file
        Then a LOW-severity time finding suggests a generator
        """
        code = "def double_sum(xs):\n    return sum([x * 2 for x in xs])\n"
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        t6 = [
            f
            for f in result.issues
            if f.category == "time" and "generator" in f.suggestion.lower()
        ]
        assert any(f.severity == "LOW" and f.line == 2 for f in t6), (
            f"T6 not flagged at line 2: {t6}"
        )

    # -----------------------------------------------------------------
    # Tier 1: Space complexity (S1-S4)
    # -----------------------------------------------------------------

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_s1_append_to_external_target_in_nested_loop(
        self, mock_skill_context
    ) -> None:
        """
        Scenario: S1 fires when appending to an EXTERNAL target
        Given nested loops appending to `self.findings` (class attr,
          not a same-function freshly-initialized list)
        When the skill analyzes the file
        Then a MEDIUM-severity space finding flags the accumulation:
          the target's growth is harder to reason about because it
          is not local
        """
        code = (
            "class Collector:\n"
            "    def collect(self, xs):\n"
            "        for x in xs:\n"
            "            for y in xs:\n"
            "                self.findings.append((x, y))\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        s1 = [f for f in result.issues if f.category == "space"]
        assert any(f.severity == "MEDIUM" and f.line == 5 for f in s1), (
            f"S1 not flagged at line 5 for external-target append: {s1}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_s1_skipped_for_local_empty_list_accumulator(
        self, mock_skill_context
    ) -> None:
        """
        Scenario: S1 negative: canonical accumulator pattern
        Given a function that initializes `out = []` then appends
          to it from nested loops, returning the result
        When the skill analyzes the file
        Then S1 does NOT fire: this is THE Python accumulator
          pattern, not a hotspot. The growth is bounded by the
          function's input and the consumer expects the full list
        """
        code = (
            "def all_pairs(xs):\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        for y in xs:\n"
            "            out.append((x, y))\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        s1 = [f for f in result.issues if f.category == "space"]
        assert s1 == [], f"S1 false-positive on canonical accumulator pattern: {s1}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_s2_list_wrapping_generator_in_reducer(self, mock_skill_context) -> None:
        """
        Scenario: S2 `max(list(g))` — list materializes generator
        Given a generator wrapped in list/dict/tuple inside a reducer
        When the skill analyzes the file
        Then a LOW-severity space finding suggests dropping the wrapper
        """
        code = "def biggest(xs):\n    return max(list(x * 2 for x in xs))\n"
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        s2 = [
            f
            for f in result.issues
            if f.category == "space" and "wrapper" in f.suggestion.lower()
        ]
        assert any(f.severity == "LOW" and f.line == 2 for f in s2), (
            f"S2 not flagged at line 2: {s2}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_s3_copy_inside_loop(self, mock_skill_context) -> None:
        """
        Scenario: S3 `.copy()` or `dict()/list()` cast inside a loop
        Given a loop body that copies a collection per iteration
        When the skill analyzes the file
        Then a MEDIUM-severity space finding flags repeat allocation
        """
        code = (
            "def transforms(items, base):\n"
            "    out = []\n"
            "    for x in items:\n"
            "        snapshot = base.copy()\n"
            "        snapshot['key'] = x\n"
            "        out.append(snapshot)\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        s3 = [
            f
            for f in result.issues
            if f.category == "space" and "alloc" in f.message.lower()
        ]
        assert any(f.severity == "MEDIUM" and f.line == 4 for f in s3), (
            f"S3 not flagged at line 4: {s3}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_clean_code_emits_no_findings(self, mock_skill_context) -> None:
        """
        Scenario: clean code produces zero findings (no false positives)
        Given a function with no detectable hotspots
        When the skill analyzes the file
        Then result.issues is empty
        """
        code = "def add(a, b):\n    return a + b\n"
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        assert result.issues == [], f"false positives on clean code: {result.issues}"

    # -----------------------------------------------------------------
    # Tier 2/3: gauntlet integration fallback
    # -----------------------------------------------------------------

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tier2_returns_empty_when_gauntlet_missing(
        self, mock_skill_context, monkeypatch
    ) -> None:
        """
        Scenario: gauntlet's treesitter_parser is unimportable
        Given _gt_parse sentinel is None
        When _tier2_findings is invoked
        Then it returns [] without raising
        """
        from pensive.skills import performance_review as pr_mod

        monkeypatch.setattr(pr_mod, "_gt_parse", None)
        skill = pr_mod.PerformanceReviewSkill()
        # Tier 2 helper must not raise even with an unsupported file
        out = skill._tier2_findings(mock_skill_context, "module.go")
        assert out == [], f"tier 2 should return [] when gauntlet is missing: {out}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tier3_returns_empty_when_graphstore_missing(
        self, mock_skill_context, monkeypatch
    ) -> None:
        """
        Scenario: gauntlet's GraphStore is unimportable OR no graph.db exists
        Given _GraphStore sentinel is None
        When _tier3_findings is invoked
        Then it returns [] without raising
        """
        from pensive.skills import performance_review as pr_mod

        monkeypatch.setattr(pr_mod, "_GraphStore", None)
        skill = pr_mod.PerformanceReviewSkill()
        out = skill._tier3_findings(mock_skill_context, [], "module.py")
        assert out == [], f"tier 3 should return [] when GraphStore is missing: {out}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_full_analyze_with_gauntlet_blocked_returns_tier1_only(
        self, mock_skill_context, monkeypatch
    ) -> None:
        """
        Scenario: full analyze() when both gauntlet sentinels are None
        Given _gt_parse and _GraphStore are both None
        When analyze() is called on Python source with T1 hotspot
        Then it still returns the T1 finding (Tier 1 always works)
        And does NOT raise ModuleNotFoundError
        """
        from pensive.skills import performance_review as pr_mod

        monkeypatch.setattr(pr_mod, "_gt_parse", None)
        monkeypatch.setattr(pr_mod, "_GraphStore", None)

        code = (
            "def find_pairs(items):\n"
            "    out = []\n"
            "    for x in items:\n"
            "        for y in items:\n"
            "            out.append((x, y))\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        skill = pr_mod.PerformanceReviewSkill()
        result = skill.analyze(mock_skill_context, "module.py")

        time_findings = [f for f in result.issues if f.category == "time"]
        assert any(f.severity == "HIGH" for f in time_findings), (
            f"T1 should still fire when gauntlet is blocked: {result.issues}"
        )

    # -----------------------------------------------------------------
    # Output shape contract
    # -----------------------------------------------------------------

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_findings_carry_required_fields(self, mock_skill_context) -> None:
        """
        Scenario: every finding has file/line/severity/category/message
        Given any code that triggers a finding
        When result.issues is inspected
        Then every ReviewFinding has the contract fields populated
        """
        code = (
            "def f(xs):\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        for y in xs:\n"
            "            out.append((x, y))\n"
            "    return out\n"
        )
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze(mock_skill_context, "module.py")

        assert result.issues, "expected at least one finding"
        for f in result.issues:
            assert f.file, "missing .file"
            assert f.line > 0, "missing .line"
            assert f.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL"), (
                f"bad severity: {f.severity}"
            )
            assert f.category in ("time", "space"), f"bad category: {f.category}"
            assert f.message, "missing .message"
