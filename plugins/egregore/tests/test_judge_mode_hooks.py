"""A judge session must not be steered back into the orchestration loop.

claude_babysitter sets EGREGORE_BABYSITTER_MODE=true on the `claude --print`
it runs as a verdict judge, and documents that this stops a judge from
spawning a judge. No hook read it, so under a tree with an active item the
Stop hook blocked the judge and handed it the relaunch prompt.
"""

from __future__ import annotations

import json
from io import StringIO

import pytest
import session_start_hook
import stop_hook
import user_prompt_hook


@pytest.fixture()
def active_tree(tmp_path, monkeypatch):
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(
        json.dumps({"work_items": [{"id": "wrk_001", "status": "active"}]})
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    monkeypatch.setenv("EGREGORE_BABYSITTER_MODE", "true")
    return tmp_path


def test_stop_hook_approves_in_judge_mode(active_tree, capsys):
    with pytest.raises(SystemExit):
        stop_hook.main()
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"


@pytest.mark.parametrize("hook", [session_start_hook, user_prompt_hook])
def test_context_hooks_inject_nothing_in_judge_mode(active_tree, capsys, hook):
    with pytest.raises(SystemExit) as exc_info:
        hook.main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == ""
