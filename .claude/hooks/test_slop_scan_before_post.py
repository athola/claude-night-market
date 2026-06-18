"""Tests for the slop-scan-before-post PreToolUse hook.

The hook blocks `gh` content-posting commands (issues, PR/MR comments,
discussions) whose payload carries AI-slop markers, so slop never reaches
a public channel. Tests drive the contract: detection, body extraction
across flag styles, two-tier scanning, and fail-open behavior.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR))

import slop_scan_before_post as hook  # noqa: E402 - sys.path insert above must run before this import

# --- posting-command detection -------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        'gh issue create --title "x" --body "y"',
        'gh issue comment 42 --body "y"',
        'gh pr comment 7 --body "y"',
        'gh pr create --title "x" --body "y"',
        'gh pr review 7 --body "y" --comment',
        'gh issue edit 42 --body "y"',
        "gh api repos/o/r/discussions -f body='y'",
    ],
)
def test_detects_posting_commands(command):
    assert hook.is_posting_command(command) is True


@pytest.mark.parametrize(
    "command",
    [
        "ls -la",
        "git commit -m 'x'",
        'echo "an em-dash — here"',
        "gh pr list",
        "gh issue view 42",
        "gh repo clone o/r",
    ],
)
def test_ignores_non_posting_commands(command):
    assert hook.is_posting_command(command) is False


# --- clean payloads pass --------------------------------------------------


def test_clean_inline_body_passes():
    cmd = 'gh issue create --title "Bug" --body "The parser drops null keys. Fix adds a guard."'
    assert hook.scan_command(cmd) == []


def test_non_posting_command_with_marker_is_not_scanned():
    # An em-dash in an unrelated command must not block the agent.
    assert hook.scan_command('echo "before — after"') == []


# --- slop in inline body blocks ------------------------------------------


def test_em_dash_in_inline_body_blocks():
    cmd = 'gh issue create --title "x" --body "fast parser — now safe"'
    findings = hook.scan_command(cmd)
    assert findings, "em-dash in body should produce a finding"


def test_smart_quotes_in_inline_body_blocks():
    cmd = 'gh pr comment 7 --body "the “fix” landed"'
    assert hook.scan_command(cmd)


def test_tier1_word_in_inline_body_blocks():
    cmd = 'gh issue create --title "x" --body "a comprehensive and seamless overhaul"'
    assert hook.scan_command(cmd)


def test_unicode_arrow_in_inline_body_blocks():
    cmd = 'gh issue comment 1 --body "input → output"'
    assert hook.scan_command(cmd)


# --- body-file resolution -------------------------------------------------


def test_body_file_is_resolved_and_scanned(tmp_path):
    body = tmp_path / "body.md"
    body.write_text("This release is a comprehensive overhaul — finally.\n")
    cmd = f'gh issue create --title "x" --body-file {body}'
    findings = hook.scan_command(cmd, repo_root=tmp_path)
    assert findings, "slop inside --body-file must be detected"


def test_clean_body_file_passes(tmp_path):
    body = tmp_path / "body.md"
    body.write_text("The guard rejects null keys. A test covers it.\n")
    cmd = f'gh pr create --title "x" --body-file {body}'
    assert hook.scan_command(cmd, repo_root=tmp_path) == []


# --- gh api field extraction ---------------------------------------------


def test_gh_api_field_body_blocks():
    cmd = "gh api repos/o/r/discussions -f body='a — slopful note'"
    assert hook.scan_command(cmd)


# --- whole-command fallback (body cannot be extracted) -------------------


def test_unextractable_body_falls_back_to_unambiguous_markers():
    # No recognizable body flag, but an em-dash rides in the command.
    cmd = 'gh issue create --title "x" --notes-from-stdin <<< "a — b"'
    assert hook.scan_command(cmd)


# --- main(): exit codes ---------------------------------------------------


def _run_main(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK_DIR / "slop_scan_before_post.py")],
        input=payload,
        capture_output=True,
        text=True,
    )


def test_main_blocks_dirty_post_with_exit_2():
    res = _run_main('gh issue create --title "x" --body "a — b"')
    assert res.returncode == 2
    assert res.stderr.strip(), "blocking must explain itself on stderr"


def test_main_allows_clean_post():
    res = _run_main('gh issue create --title "x" --body "a clean note"')
    assert res.returncode == 0


def test_main_allows_non_posting_command():
    res = _run_main('echo "an em-dash — here"')
    assert res.returncode == 0


def test_main_fails_open_on_malformed_stdin():
    res = subprocess.run(
        [sys.executable, str(HOOK_DIR / "slop_scan_before_post.py")],
        input="not json",
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, "a broken payload must never wedge the agent"
