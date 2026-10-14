"""Tests for the edit-narration vow hook.

The hook guards one register and leaves the other alone. Naming what
was skipped is required of a completion report, by the harness and by
`Skill(imbue:proof-of-work)`. A file has no session to report on. The
hook only ever sees a file write, so the split holds structurally.

The zero-baseline test is the load-bearing one. A guard that fires on
correct prose is instruction load, and `.claude/rules/bounded-autonomy.md`
cites what that costs. Pinning the count at zero means any future
pattern added here has to earn it against the whole repository.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import os
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
HOOK = REPO_ROOT / "plugins" / "imbue" / "hooks" / "vow_no_edit_narration.py"


def _module():
    """Load the hook as a module without registering it on sys.path."""
    spec = importlib.util.spec_from_file_location("vow_no_edit_narration", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(payload, shadow: str = "1") -> subprocess.CompletedProcess:
    """Run the hook with VOW_SHADOW_MODE pinned, not inherited."""
    stdin_text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "VOW_SHADOW_MODE": shadow},
    )


class TestNarrationIsDetected:
    """The shapes the hook exists to catch."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "# We renamed the handler.",
            "We removed the fallback.",
            "  // I replaced the parser.",
            "Reads the manifest instead of the old inline config.",
        ],
    )
    def test_edit_narration_is_found(self, text: str) -> None:
        """Scenario: A change event written into a file is caught."""
        assert _module().find_narration(text) is not None

    @pytest.mark.unit
    def test_a_write_warns_in_shadow_mode(self) -> None:
        """Scenario: The default posture warns and does not block."""
        completed = _run(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "sample.py",
                    "content": "# We renamed the handler.",
                },
            }
        )
        emitted = json.loads(completed.stdout)
        hook_out = emitted["hookSpecificOutput"]
        assert "permissionDecision" not in hook_out
        assert hook_out["additionalContext"]
        assert completed.returncode == 0


class TestCorrectProsePasses:
    """The shapes that must never fire, each measured in this repo."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            # Quoted in plugins/imbue/skills/proof-of-work/modules/
            # iron-law-enforcement.md, and correct there.
            "What would break if I removed this line?",
            # Rationale citing the incident a guard defends. Required by
            # bounded-autonomy.md and measured at
            # plugins/minister/src/minister/dora_metrics.py:169.
            "Issue #527: None input maps to N/A rather than the previous"
            " silent misclassification.",
            "The lock is released once the writer has finished.",
            "A frontmatter that no longer parses fails here.",
        ],
    )
    def test_correct_prose_is_not_flagged(self, text: str) -> None:
        """Guard: rationale and quotation are not edit narration."""
        assert _module().find_narration(text) is None

    @pytest.mark.unit
    def test_an_unguarded_suffix_is_skipped(self) -> None:
        """Scenario: A scratch note is not a committed artifact."""
        completed = _run(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "notes.txt",
                    "content": "We removed the fallback.",
                },
            }
        )
        assert completed.stdout.strip() == ""


class TestOnlyInsertedTextIsScanned:
    """Residue is a property of new prose."""

    @pytest.mark.unit
    def test_an_untouched_narrating_line_is_not_reflagged(self) -> None:
        """Scenario: Editing beside old narration is not a violation.

        Charging a session for text it inherited would fire on the same
        line until someone rewrote a file they had not touched.
        """
        module = _module()
        added = module.inserted_text(
            "Edit",
            {
                "old_string": "# We renamed it.\nx = 1",
                "new_string": "# We renamed it.\nx = 2",
            },
        )
        assert module.find_narration(added) is None

    @pytest.mark.unit
    def test_narration_added_by_the_edit_is_found(self) -> None:
        """Scenario: The same edit that introduces narration is caught."""
        module = _module()
        added = module.inserted_text(
            "Edit",
            {
                "old_string": "x = 1",
                "new_string": "# We replaced the counter.\nx = 2",
            },
        )
        assert module.find_narration(added) is not None


class TestZeroBaselineOverTheRepository:
    """The hook's patterns match nothing committed here today.

    This is the empirical bar the broad `tier5.temporal_residue`
    category could not clear, which is why that one ships opt-in and
    this one ships as a guard.
    """

    @pytest.mark.unit
    def test_no_tracked_file_matches_the_hook_patterns(self) -> None:
        """Scenario: Every hit is text a session just introduced."""
        module = _module()
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()

        offenders = []
        for name in tracked:
            if name in _PATTERN_DEFINING_FILES:
                continue
            path = REPO_ROOT / name
            if path.suffix not in {".md", ".py"} or not path.exists():
                continue
            for line_no, text in _prose_of(path):
                if module.find_narration(text):
                    offenders.append(f"{name}:{line_no}")

        assert offenders == [], (
            "The hook's patterns must match nothing already committed, "
            "or every session pays for prose it did not write: "
            + ", ".join(offenders[:10])
        )


# A file that defines a pattern matches it. Each of these quotes the
# narration it exists to catch, the same exemption `.slop-config.yaml`
# grants the rule files and the slop-detector modules.
#
# The criterion is narrow on purpose: a file earns a place here only by
# documenting or implementing these two patterns, never by containing
# prose that happens to trip them. A file added for the second reason
# is the finding, and the fix belongs in the file.
_PATTERN_DEFINING_FILES = frozenset(
    {
        "plugins/imbue/hooks/vow_no_edit_narration.py",
        "plugins/imbue/tests/unit/hooks/test_vow_no_edit_narration.py",
        "plugins/scribe/skills/slop-detector/modules/structural-patterns.md",
    }
)


def _prose_of(path: Path):
    """Yield (line, text) for markdown, or for Python prose only."""
    source = path.read_text(errors="replace")
    if path.suffix == ".md":
        yield 1, source
        return
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                yield token.start[0], token.string
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    owners = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, owners):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                yield getattr(node, "lineno", 1), doc


class TestPatternDefiningFilesAreExempt:
    """The files that define these patterns must not trip them.

    The hook had no exclusion while this test file carried one, so
    editing plugins/scribe/skills/slop-detector/modules/structural-patterns.md,
    which documents the same tell, tripped the rule the module describes.
    """

    def test_the_hook_and_the_test_agree_on_the_exempt_set(self) -> None:
        """Two copies of a list drift; this is what notices."""
        assert set(_module()._PATTERN_DEFINING_FILES) == set(_PATTERN_DEFINING_FILES)

    @pytest.mark.parametrize("relative", sorted(_PATTERN_DEFINING_FILES))
    def test_an_absolute_path_to_a_defining_file_is_exempt(self, relative: str) -> None:
        """The hook receives an absolute path; the list is repo-relative."""
        assert _module()._defines_the_patterns(f"/Users/someone/repo/{relative}")

    def test_an_ordinary_file_is_not_exempt(self) -> None:
        """The exemption must stay narrow."""
        assert not _module()._defines_the_patterns("/repo/plugins/imbue/README.md")


class TestHookEntryPoint:
    """main() reads the PreToolUse payload and never crashes the agent."""

    @pytest.mark.unit
    def test_blocking_mode_denies_the_write(self) -> None:
        completed = _run(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "sample.py",
                    "content": "# We renamed the handler.",
                },
            },
            shadow="0",
        )
        hook_out = json.loads(completed.stdout)["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "deny"
        assert "We renamed" in hook_out["permissionDecisionReason"]
        assert completed.returncode == 0

    @pytest.mark.unit
    def test_multiedit_narration_in_any_edit_is_found(self) -> None:
        completed = _run(
            {
                "tool_name": "MultiEdit",
                "tool_input": {
                    "file_path": "sample.py",
                    "edits": [
                        {"old_string": "a = 1", "new_string": "a = 2"},
                        {"old_string": "b", "new_string": "# We removed the cache.\nb"},
                    ],
                },
            },
            shadow="0",
        )
        assert (
            json.loads(completed.stdout)["hookSpecificOutput"]["permissionDecision"]
            == "deny"
        )

    @pytest.mark.unit
    def test_a_non_write_tool_is_ignored(self) -> None:
        completed = _run(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "file_path": "sample.py",
                    "content": "# We renamed the handler.",
                },
            },
            shadow="0",
        )
        assert completed.stdout == ""

    @pytest.mark.unit
    def test_a_pattern_defining_file_is_not_flagged(self) -> None:
        completed = _run(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(HOOK),
                    "content": "# We renamed the handler.",
                },
            },
            shadow="0",
        )
        assert completed.stdout == ""

    @pytest.mark.unit
    def test_malformed_stdin_allows_the_write_silently(self) -> None:
        completed = _run("not json", shadow="0")
        assert completed.returncode == 0
        assert completed.stdout == ""

    @pytest.mark.unit
    def test_non_object_payload_is_an_internal_error_that_allows_the_write(
        self,
    ) -> None:
        completed = _run("[1, 2]", shadow="0")
        assert completed.returncode == 0
        assert completed.stdout == ""
        assert "internal error" in completed.stderr


class TestMainInProcess:
    """main() decisions, run in-process so the coverage gate measures them."""

    def _main(self, monkeypatch, capsys, payload, shadow="0"):
        module = _module()
        monkeypatch.setenv("VOW_SHADOW_MODE", shadow)
        text = payload if isinstance(payload, str) else json.dumps(payload)
        monkeypatch.setattr(module.sys, "stdin", io.StringIO(text))
        with pytest.raises(SystemExit) as exc:
            module.main()
        captured = capsys.readouterr()
        out = json.loads(captured.out) if captured.out.strip() else None
        return exc.value.code, out, captured.err

    @staticmethod
    def _write(content, path="sample.py", tool="Write"):
        return {
            "tool_name": tool,
            "tool_input": {"file_path": path, "content": content},
        }

    @pytest.mark.unit
    def test_narration_is_denied_when_blocking(self, monkeypatch, capsys) -> None:
        code, out, err = self._main(
            monkeypatch, capsys, self._write("# We renamed the handler.")
        )
        assert code == 0
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "BLOCK" in err

    @pytest.mark.unit
    def test_narration_warns_in_shadow_mode(self, monkeypatch, capsys) -> None:
        _, out, _ = self._main(
            monkeypatch, capsys, self._write("# We renamed the handler."), shadow="1"
        )
        assert "Shadow mode active" in out["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "payload",
        [
            {"tool_name": "Bash", "tool_input": {"command": "ls"}},
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "n.txt", "content": "We removed it."},
            },
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(HOOK), "content": "We removed it."},
            },
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "a.py", "content": "x = 1"},
            },
        ],
        ids=["non-write-tool", "unguarded-suffix", "defining-file", "clean-text"],
    )
    def test_silent_paths(self, monkeypatch, capsys, payload) -> None:
        code, out, _ = self._main(monkeypatch, capsys, payload)
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_edit_list_with_a_non_dict_entry_is_skipped(
        self, monkeypatch, capsys
    ) -> None:
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "a.py",
                "edits": ["junk", {"old_string": "", "new_string": "# We removed it."}],
            },
        }
        _, out, _ = self._main(monkeypatch, capsys, payload)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.unit
    @pytest.mark.parametrize("stdin_text", ["not json", "[1, 2]"])
    def test_bad_stdin_allows_the_write(self, monkeypatch, capsys, stdin_text) -> None:
        code, out, _ = self._main(monkeypatch, capsys, stdin_text)
        assert code == 0
        assert out is None
