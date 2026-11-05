"""The thread-count commands in sanctum's docs must run as written.

The count is read with ``.[].data...``, which only fits the array that
``gh api graphql --paginate --slurp`` returns. gh 2.86 refuses
``--slurp`` together with ``--jq``, so a slurped result has to be piped
to ``jq`` instead.
"""

from __future__ import annotations

import re
from pathlib import Path

COMMANDS = Path(__file__).resolve().parents[2] / "commands"
RESOLVE_THREADS = COMMANDS / "resolve-threads.md"
_FENCE = re.compile(r"```bash\n(.*?)```", re.S)


def _step(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start)
    return text[start : end if end != -1 else len(text)]


def test_the_verify_step_pages_threads_and_pipes_the_count_to_jq() -> None:
    block = _FENCE.search(
        _step(RESOLVE_THREADS.read_text(encoding="utf-8"), "### Step 4")
    )
    assert block, "Step 4 has no bash block"
    command = block.group(1)
    assert "--paginate --slurp" in command
    assert "$endCursor" in command and "pageInfo" in command
    assert "--jq" not in command
    assert "| jq '[.[].data.repository.pullRequest.reviewThreads" in command


def test_no_sanctum_command_passes_jq_to_a_slurped_graphql_call() -> None:
    offenders = [
        f"{doc.relative_to(COMMANDS)}"
        for doc in COMMANDS.rglob("*.md")
        for block in _FENCE.findall(doc.read_text(encoding="utf-8"))
        if "--slurp" in block and "--jq" in block
    ]
    assert offenders == []
