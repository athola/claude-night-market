"""PreCompact must read the session rows Claude Code actually writes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from pre_compact_preserve import extract_file_paths, extract_recent_content


def test_extract_recent_content_reads_rows_wrapped_in_message(tmp_path: Path) -> None:
    """Real session rows keep role and content under ``message``."""
    session = tmp_path / "session.jsonl"
    rows = [
        {"type": "attachment", "attachment": {"type": "hook_cancelled"}},
        {"type": "user", "message": {"role": "user", "content": "fix it"}},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "decided: use flock here"}],
            },
        },
    ]
    session.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    entries = extract_recent_content(session)

    assert [e["role"] for e in entries] == ["user", "assistant"]


def test_extract_file_paths_finds_every_path_in_a_space_separated_list(
    tmp_path: Path,
) -> None:
    """Adjacent paths share one separating space; none may be skipped."""
    names = ["a.py", "b.py", "c.py", "d.py"]
    for name in names:
        (tmp_path / name).write_text("")
    text = " ".join(str(tmp_path / name) for name in names)

    found = extract_file_paths([{"role": "assistant", "content": text}])

    assert sorted(Path(p).name for p in found) == names
