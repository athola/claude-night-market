"""The prose line-wrap ratchet, and the exclusions it must honour.

``.claude/rules/markdown-formatting.md`` requires prose to wrap at 80
columns and names what is exempt: tables, code blocks, headings,
frontmatter, HTML, link definitions and image references. Issue #681
recorded that nothing enforced any of it.

A checker that judged every long line would report thousands of findings
against constructs the rule already exempts, and a check that noisy stops
being run. So most of what is asserted here is what the guard must stay
quiet about.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_prose_wrap_drift.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_prose_wrap_drift", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_prose_wrap_drift"] = module
    spec.loader.exec_module(module)
    return module


mod = _load()

LONG = "x" * 95


class TestWhatCounts:
    """A prose line past 80 columns is the only thing this guard counts."""

    def test_a_long_prose_line_is_counted(self) -> None:
        assert mod.overlong_prose_lines(f"{LONG}\n") == [1]

    def test_a_line_at_the_limit_is_not_counted(self) -> None:
        assert mod.overlong_prose_lines("y" * 80 + "\n") == []

    def test_the_line_number_reported_is_one_based(self) -> None:
        assert mod.overlong_prose_lines(f"short\n{LONG}\n") == [2]


class TestWhatTheRuleExempts:
    """Each exemption is named by the rule. None of these may be counted."""

    @pytest.mark.parametrize(
        ("label", "text"),
        [
            ("fenced code", f"```python\n{LONG}\n```\n"),
            ("tilde fence", f"~~~\n{LONG}\n~~~\n"),
            ("table row", f"| {LONG} | b |\n"),
            ("atx heading", f"## {LONG}\n"),
            ("url in line", f"see https://example.com/{LONG}\n"),
            ("link definition", f"[ref]: https://example.com/{LONG}\n"),
            ("image reference", f"![alt]({LONG}.png)\n"),
            ("indented code", f"    {LONG}\n"),
            ("html block", f"<div class='{LONG}'>\n"),
        ],
    )
    def test_an_exempt_construct_is_not_counted(self, label: str, text: str) -> None:
        assert mod.overlong_prose_lines(text) == [], f"{label} must be exempt"

    def test_frontmatter_is_exempt(self) -> None:
        """A description key routinely runs past 80 and cannot be wrapped."""
        text = f"---\ndescription: {LONG}\n---\n\nbody\n"
        assert mod.overlong_prose_lines(text) == []

    def test_frontmatter_is_only_exempt_at_the_top_of_the_file(self) -> None:
        """A `---` rule mid-document is a thematic break, not frontmatter.

        Treating it as a fence opener would silence every prose line
        below the first horizontal rule in the document.
        """
        text = f"body\n\n---\n\n{LONG}\n"
        assert mod.overlong_prose_lines(text) == [5]

    def test_a_fence_inside_a_fence_does_not_reopen_it(self) -> None:
        """Prose after a closed fence is judged again."""
        text = f"```\ncode\n```\n{LONG}\n"
        assert mod.overlong_prose_lines(text) == [4]


class TestTheRatchet:
    """The gate reads a movement against the baseline, never a raw count."""

    def test_a_rise_above_the_baseline_fails(self) -> None:
        ok, message = mod.evaluate_drift(11, 10)
        assert not ok
        assert "11" in message and "10" in message

    def test_holding_at_the_baseline_passes(self) -> None:
        ok, _ = mod.evaluate_drift(10, 10)
        assert ok

    def test_a_drop_passes_and_asks_for_the_baseline_to_be_lowered(self) -> None:
        ok, message = mod.evaluate_drift(9, 10)
        assert ok
        assert "lower" in message.lower()


class TestScope:
    """What the guard governs, and what it leaves alone."""

    def test_changelog_is_excluded(self) -> None:
        """The slop rule's anti-goals forbid touching historical entries."""
        assert not mod.is_governed(Path("CHANGELOG.md"))

    def test_a_vendored_dot_directory_is_excluded(self) -> None:
        assert not mod.is_governed(Path("plugins/x/.venv/lib/README.md"))

    def test_a_plugin_skill_is_governed(self) -> None:
        assert mod.is_governed(Path("plugins/conjure/skills/x/SKILL.md"))

    def test_a_repo_rule_is_governed(self) -> None:
        assert mod.is_governed(Path(".claude/rules/markdown-formatting.md"))


class TestUnreadableFiles:
    """A file the ratchet cannot read must not quietly lower the count.

    Discussions #530 and #531 recorded this exact shape twice in this
    repository: a scan that drops what it cannot parse. In a ratchet it
    is worse than elsewhere. Every skipped file subtracts its findings
    from the total, so one unreadable document can absorb a genuine rise
    somewhere else and the gate reports a pass.
    """

    def test_a_file_deleted_from_the_worktree_counts_as_zero(
        self, tmp_path: Path
    ) -> None:
        """`git ls-files` lists tracked paths, including deleted ones.

        Its prose really is gone, so zero is the honest count and the run
        must not abort partway through the surface.
        """
        assert mod.count_overlong([tmp_path / "never-existed.md"]) == 0

    def test_an_undecodable_file_is_raised_not_skipped(self, tmp_path: Path) -> None:
        """A tracked document that is not UTF-8 is an anomaly, not a zero."""
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe not utf-8 " + b"x" * 200)
        with pytest.raises(UnicodeDecodeError):
            mod.count_overlong([bad])

    def test_an_unreadable_file_is_raised_not_skipped(self, tmp_path: Path) -> None:
        """A file present but denied is the case that masks a rise.

        A deleted file honestly has no lines. A file that is there and
        cannot be opened has an unknown count, and silently reading it as
        zero is what discussions #530 and #531 objected to.
        """
        denied = tmp_path / "denied.md"
        denied.write_text(f"{LONG}\n", encoding="utf-8")
        denied.chmod(0o000)
        try:
            if os.access(denied, os.R_OK):
                pytest.skip("running with privileges that ignore file modes")
            with pytest.raises(PermissionError):
                mod.count_overlong([denied])
        finally:
            denied.chmod(0o600)

    def test_the_ranking_path_absorbs_a_missing_file_too(self, tmp_path: Path) -> None:
        """`--top` and the gate must agree about what a deleted file is.

        They read files by separate routes once, and only the gate knew
        about the deleted case, so sizing the backlog raised on a tree
        the gate itself passed over without complaint.
        """
        assert mod.overlong_in(tmp_path / "gone.md") == []

    def test_a_readable_file_is_still_counted(self, tmp_path: Path) -> None:
        good = tmp_path / "good.md"
        good.write_text(f"{LONG}\n", encoding="utf-8")
        assert mod.count_overlong([good]) == 1


class TestTheBaselineIsHonest:
    """The committed baseline must match what the repository contains."""

    def test_the_baseline_matches_the_current_count(self) -> None:
        """A baseline above the real count is permission nobody granted.

        The exit-criteria ratchet's own docstring records that hazard: it
        sat at 127 long after the count fell to 1.
        """
        current = mod.count_overlong(mod.iter_markdown_files())
        baseline = mod.load_baseline()
        assert current <= baseline, (
            f"prose wrap findings rose to {current} (baseline {baseline})"
        )
        assert baseline - current <= mod.SLACK, (
            f"baseline {baseline} exceeds the real count {current} by more "
            f"than {mod.SLACK}; lower it to lock the win"
        )
