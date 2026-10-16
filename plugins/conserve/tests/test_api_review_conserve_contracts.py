"""Contract tests for API-review findings on conserve hooks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "permission_request.py"


def _decision(command: str) -> str:
    payload = {
        "hook_event_name": "PermissionRequest",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout)["hookSpecificOutput"]
    return output.get("decision", {}).get("behavior", "none")


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "head .env",
        "tail -n 5 ~/.ssh/id_rsa",
        "grep -r KEY ~/.aws/credentials",
        "rg . .env",
        "ag token ~/.ssh/config",
    ],
)
def test_credential_paths_are_denied_for_every_reader_command(command: str) -> None:
    assert _decision(command) == "deny"


@pytest.mark.parametrize(
    "command",
    ["head README.md", "tail -n 20 src/app.py", "grep -r TODO src", "rg pattern ."],
)
def test_readers_on_ordinary_paths_stay_auto_allowed(command: str) -> None:
    assert _decision(command) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "grep -rn os.environ plugins/",
        "rg -n get_credentials src/",
        "git log --grep credentials",
        "rg -n 'load_dotenv' src/",
    ],
)
def test_searching_for_credential_words_is_not_denied(command: str) -> None:
    """A search term that mentions credentials is not a credential file.

    Widening the deny rule from cat to every reader matched the search
    pattern as well as the path: `.env` inside `os.environ`, `credentials`
    inside `get_credentials`, and `grep` inside `git log --grep`. Master
    allowed all of these.
    """
    assert _decision(command) != "deny"
