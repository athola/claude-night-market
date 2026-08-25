"""The JSONL estimate is cached, so the hot path re-reads nothing.

`context_warning.py` runs on PreToolUse for Write, Edit, Bash, Skill and
Task. Without `CLAUDE_CONTEXT_USAGE` set it falls back to reading up to
4MB off the tail of the session transcript and JSON-parsing every line,
and it did that once per tool call. Telemetry over 4,028 Bash calls put
the PreToolUse chain at a 26s worst case; a 4MB parse on a cold page
cache is a candidate for that shape of outlier.

Context does not move fast enough to need per-call resolution -- the
alert bands are 40%, 50% and 80% -- so the estimate is cached for
`_CACHE_TTL_SECONDS` and reused. These tests pin the cache: reused
inside the window, recomputed after it, and never shared between
sessions.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, tmp_path):
    """Point the hook at a private state dir and an empty environment."""
    monkeypatch.setenv("CONSERVE_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
    monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
    monkeypatch.delenv("CLAUDE_HOME", raising=False)


def _fake_session(monkeypatch, tmp_path, session_id: str = "session-a"):
    """Create a session transcript the estimator will resolve to."""
    home = tmp_path / "home"
    cwd = tmp_path / "work"
    cwd.mkdir(parents=True, exist_ok=True)
    project_dir = home / ".claude" / "projects" / str(cwd).replace("/", "-")
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / f"{session_id}.jsonl").write_text("x" * 80000)
    monkeypatch.setenv("CLAUDE_SESSION_ID", session_id)
    monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: cwd))
    monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
    return project_dir


class _EstimatorSpy:
    """Stand in for _estimate_from_recent_turns and count the reads."""

    def __init__(self, value: float = 0.42) -> None:
        self.value = value
        self.calls = 0

    def __call__(self, session_file) -> float:
        self.calls += 1
        return self.value


class TestEstimateIsCachedWithinTheWindow:
    """Feature: repeated tool calls reuse one transcript read."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_second_call_does_not_reread_the_transcript(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: two tool calls in a row share one transcript read."""
        module = context_warning_full_module
        _fake_session(monkeypatch, tmp_path)
        spy = _EstimatorSpy()
        monkeypatch.setattr(module, "_estimate_from_recent_turns", spy)

        first = module.estimate_context_from_session()
        second = module.estimate_context_from_session()

        assert first == second == spy.value
        assert spy.calls == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_estimate_is_recomputed_once_the_window_expires(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: the estimate goes stale and is taken again."""
        module = context_warning_full_module
        _fake_session(monkeypatch, tmp_path)
        spy = _EstimatorSpy()
        monkeypatch.setattr(module, "_estimate_from_recent_turns", spy)

        clock = [1000.0]
        monkeypatch.setattr(module.time, "time", lambda: clock[0])

        module.estimate_context_from_session()
        clock[0] += module._CACHE_TTL_SECONDS + 1
        module.estimate_context_from_session()

        assert spy.calls == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_a_different_session_does_not_read_the_first_cache(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: each transcript gets its own cache entry."""
        module = context_warning_full_module
        _fake_session(monkeypatch, tmp_path, session_id="session-a")
        spy = _EstimatorSpy()
        monkeypatch.setattr(module, "_estimate_from_recent_turns", spy)
        module.estimate_context_from_session()

        _fake_session(monkeypatch, tmp_path, session_id="session-b")
        module.estimate_context_from_session()

        assert spy.calls == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_env_var_path_never_touches_the_cache(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: CLAUDE_CONTEXT_USAGE short-circuits before any file work."""
        module = context_warning_full_module
        _fake_session(monkeypatch, tmp_path)
        spy = _EstimatorSpy()
        monkeypatch.setattr(module, "_estimate_from_recent_turns", spy)
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.31")

        usage, is_estimated = module.get_context_usage_from_env()

        assert usage == 0.31
        assert is_estimated is False
        assert spy.calls == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_an_unreadable_cache_falls_back_to_estimating(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """A corrupt cache must not take the hook's answer with it."""
        module = context_warning_full_module
        _fake_session(monkeypatch, tmp_path)
        spy = _EstimatorSpy()
        monkeypatch.setattr(module, "_estimate_from_recent_turns", spy)

        module.estimate_context_from_session()
        cached = next((tmp_path / "state").glob("context-estimate-*.json"))
        cached.write_text("{not json")

        assert module.estimate_context_from_session() == spy.value
        assert spy.calls == 2
