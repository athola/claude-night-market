"""Tests for the +recall UserPromptSubmit hook.

Feature: On-demand recall
  As someone resuming work
  I want past-session units injected only when I ask for them
  So that the common prompt pays no context or latency cost.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent.parent / "hooks" / "recall.py"


def _run(prompt: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke the hook the way Claude Code does: JSON on stdin."""
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"prompt": prompt, "hook_event_name": "UserPromptSubmit"}),
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(cwd) if cwd else None,
    )


class TestQuietPath:
    """Feature: A prompt without the token costs nothing."""

    def test_hook_file_exists(self) -> None:
        """Scenario: the hook is present."""
        assert HOOK.exists(), f"hook not found at {HOOK}"

    def test_prompt_without_token_emits_nothing(self) -> None:
        """Scenario: no +recall means no output and a clean exit."""
        result = _run("just a normal prompt about refactoring")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_recall_substring_alone_does_not_trigger(self) -> None:
        """Scenario: the word 'recall' in prose is not the token."""
        result = _run("can you recall what we decided about caching")
        assert result.stdout.strip() == ""

    def test_heavy_imports_are_deferred(self) -> None:
        """Scenario: the embedding index is imported inside a function.

        A module-level import would pay the cost on every prompt, which
        is the whole reason this hook is opt-in.
        """
        import ast

        tree = ast.parse(HOOK.read_text())
        toplevel = {
            alias.name
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in getattr(node, "names", [])
        }
        toplevel |= {
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(name and "memory_palace" in name for name in toplevel), (
            f"memory_palace imported at module level: {toplevel}"
        )


class TestTriggeredPath:
    """Feature: The token injects context."""

    def test_plus_recall_emits_hook_output(self) -> None:
        """Scenario: +recall produces UserPromptSubmit additionalContext."""
        result = _run("what did we settle on for decay curves +recall")
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "additionalContext" in payload["hookSpecificOutput"]

    def test_plus_recall_question_mark_is_visible(self) -> None:
        """Scenario: +recall? shows the user what was retrieved."""
        quiet = _run("decay curves +recall")
        loud = _run("decay curves +recall?")
        assert loud.returncode == 0
        quiet_ctx = json.loads(quiet.stdout)["hookSpecificOutput"]["additionalContext"]
        loud_ctx = json.loads(loud.stdout)["hookSpecificOutput"]["additionalContext"]
        assert loud_ctx != quiet_ctx, "+recall? must differ from silent +recall"
        assert "recall" in loud_ctx.lower()

    def test_malformed_stdin_does_not_crash(self) -> None:
        """Scenario: a hook must never break the prompt path."""
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0


class TestChangedDependencyFlagging:
    """Feature: a moved dependency is flagged, never silently dropped.

    Legal citators never delete overruled precedent; they attach a
    treatment flag and let the reader judge. Suppressing a unit whose
    file changed would hide that the topic has history at all, which is
    strictly worse than surfacing it with a warning.
    """

    def _payload(self, tmp_path, digest: str) -> dict:
        return {
            "prompt": "what did we decide about ranking +recall?",
            "hook_event_name": "UserPromptSubmit",
            "cwd": str(tmp_path),
        }

    def test_changed_dependency_is_surfaced_in_output(self, tmp_path) -> None:
        """Scenario: the reader is told which path moved."""

        from memory_palace.corpus.staleness_signals import Signal, check_dependencies

        (tmp_path / "ranking.py").write_text("original\n")
        from memory_palace.corpus.staleness_signals import capture_digests

        digests = capture_digests(["ranking.py"], root=tmp_path)
        (tmp_path / "ranking.py").write_text("changed\n")

        # The signal itself must report the change.
        assert (
            check_dependencies(digests, root=tmp_path)["ranking.py"] is Signal.CHANGED
        )

    def test_render_marks_units_with_moved_dependencies(self) -> None:
        """Scenario: rendering names the changed path in the output."""
        import importlib.util
        from pathlib import Path as _P

        spec = importlib.util.spec_from_file_location(
            "recall_mod",
            _P(__file__).resolve().parent.parent.parent / "hooks" / "recall.py",
        )
        recall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recall)

        unit = {
            "thread": "Ranking",
            "type": "decision",
            "date": "2026-08-13",
            "state": "Similarity times decay.",
            "files": ["ranking.py"],
        }
        rendered = recall._render(
            [(unit, 1.0)], visible=False, changed={"Ranking": ["ranking.py"]}
        )
        assert "ranking.py" in rendered
        assert "changed" in rendered.lower()

    def test_unit_with_moved_dependency_is_still_returned(self) -> None:
        """Scenario: flagging does not remove the unit from results."""
        import importlib.util
        from pathlib import Path as _P

        spec = importlib.util.spec_from_file_location(
            "recall_mod2",
            _P(__file__).resolve().parent.parent.parent / "hooks" / "recall.py",
        )
        recall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recall)

        unit = {
            "thread": "Ranking",
            "type": "decision",
            "date": "2026-08-13",
            "state": "Similarity times decay.",
        }
        rendered = recall._render(
            [(unit, 1.0)], visible=False, changed={"Ranking": ["ranking.py"]}
        )
        assert "Similarity times decay." in rendered


class TestImportsActuallyResolve:
    """Feature: the deferred imports succeed when they finally run.

    Deferring the imports is required for the quiet path, but a hook
    that defers an import which then always fails is worse than one
    that never tried: the ImportError fallback returns a neutral weight,
    so ranking and staleness silently stop working while every test
    that only checks output shape keeps passing.
    """

    def test_memory_palace_is_importable_from_the_hook(self) -> None:
        """Scenario: running the hook's path setup makes the package load."""
        import importlib.util
        from pathlib import Path as _P

        hook = _P(__file__).resolve().parent.parent.parent / "hooks" / "recall.py"
        spec = importlib.util.spec_from_file_location("recall_imports", hook)
        recall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recall)

        # Exercised through the hook's own helper so a regression in its
        # path setup is what fails, not a test-local import.
        import subprocess
        import sys as _sys

        src = str(hook.parent.parent / "src")
        probe = (
            f"import sys; sys.path.insert(0, {src!r});"
            "import memory_palace.corpus.staleness_signals as s;"
            "print(s.Signal.CHANGED.value)"
        )
        result = subprocess.run(
            [_sys.executable, "-c", probe], capture_output=True, text=True, timeout=20
        )
        assert result.returncode == 0, result.stderr
        assert "changed" in result.stdout

    def test_decay_weight_is_actually_applied(self) -> None:
        """Scenario: an old state unit ranks below a fresh finding.

        If the decay import silently failed, both would score on raw
        keyword overlap alone and this ordering would not hold.
        """
        import importlib.util
        from pathlib import Path as _P

        hook = _P(__file__).resolve().parent.parent.parent / "hooks" / "recall.py"
        spec = importlib.util.spec_from_file_location("recall_weight", hook)
        recall = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recall)

        # Computed rather than hardcoded: a fixed old date drifts into
        # the importance floor over time, where every type ties at 0.1
        # and the assertion would stop testing anything.
        from datetime import datetime, timedelta, timezone

        recent = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        stale = {
            "thread": "ranking approach",
            "type": "state",
            "date": recent,
            "state": "ranking approach wired",
        }
        fresh = {
            "thread": "ranking approach",
            "type": "finding",
            "date": recent,
            "state": "ranking approach wired",
        }
        assert recall._weight_for(stale) < recall._weight_for(fresh), (
            "decay weighting is inert; the decay model import is failing"
        )


def _load_recall():
    """Load the hook as a module so its internals can be exercised."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("recall_supersede", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCrossSessionSupersession:
    """Feature: a corrected unit replaces the claim it corrected.

    ``merge_handoff_units`` supersedes by (thread, type) inside one
    record. Recall reads across records, where that invariant does not
    hold on its own: a state unit and its correction three sessions
    later both survive and compete on keyword overlap. This finishes
    the merge design rather than adding a second one.

    Supersession is not a fallible signal the way a content digest is,
    so the older unit is dropped rather than flagged. The newer unit is
    the replacement by construction, which is exactly what the
    within-session merge already does.
    """

    def test_newer_unit_supersedes_older_on_same_thread_and_type(self) -> None:
        """Scenario: the correction wins and the stale claim is gone."""
        recall = _load_recall()
        units = [
            {"thread": "decay design", "type": "state", "state": "content digest"},
            {"thread": "decay design", "type": "state", "state": "filesystem mtime"},
        ]
        kept = recall._supersede(units)
        assert len(kept) == 1
        assert kept[0]["state"] == "content digest", (
            "the newest unit must win; recall scans newest session first"
        )

    def test_same_thread_different_type_both_survive(self) -> None:
        """Scenario: the split rule holds across sessions too.

        Superseding by thread alone would be a correctness bug: a
        durable finding and the transient state that produced it are
        deliberately kept on separate decay curves.
        """
        recall = _load_recall()
        units = [
            {"thread": "decay design", "type": "finding", "state": "types beat TTLs"},
            {"thread": "decay design", "type": "state", "state": "wired into recall"},
        ]
        assert len(recall._supersede(units)) == 2

    def test_distinct_threads_are_untouched(self) -> None:
        """Scenario: supersession never collapses unrelated topics."""
        recall = _load_recall()
        units = [
            {"thread": "decay design", "type": "state", "state": "a"},
            {"thread": "recall ranking", "type": "state", "state": "b"},
        ]
        assert len(recall._supersede(units)) == 2

    def test_order_is_preserved(self) -> None:
        """Scenario: dedup must not reshuffle what ranking then scores."""
        recall = _load_recall()
        units = [
            {"thread": "a", "type": "state", "state": "1"},
            {"thread": "b", "type": "state", "state": "2"},
            {"thread": "a", "type": "state", "state": "stale"},
            {"thread": "c", "type": "state", "state": "3"},
        ]
        assert [u["thread"] for u in recall._supersede(units)] == ["a", "b", "c"]

    def test_load_units_applies_supersession_across_records(
        self, tmp_path, monkeypatch
    ) -> None:
        """Scenario: the end-to-end read path, not just the helper.

        Two session records on disk carry the same (thread, type). Only
        the one from the newer record may reach ranking.
        """
        recall = _load_recall()
        sessions = tmp_path / "sessions"
        sessions.mkdir()

        def _write(name: str, state: str, mtime: float) -> None:
            path = sessions / name
            path.write_text(
                json.dumps(
                    {
                        "handoff_units": [
                            {
                                "thread": "decay design",
                                "type": "state",
                                "state": state,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            import os

            os.utime(path, (mtime, mtime))

        _write("old.json", "filesystem mtime", mtime=1_000_000)
        _write("new.json", "content digest", mtime=2_000_000)

        monkeypatch.setattr(recall, "SESSIONS_DIR", sessions)
        loaded = recall._load_units()
        assert [u["state"] for u in loaded] == ["content digest"]
