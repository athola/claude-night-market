"""Skills run the capture wrapper from the plugin root, not the cwd.

A bare `python3 scripts/deferred_capture.py` resolves against the user's
project, where no such file exists, and each module's "skip if not present"
note turned that into a silent skip (ARCH-7).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BARE_CALL = re.compile(r"python3\s+scripts/deferred_capture\.py")


def test_no_skill_calls_the_capture_wrapper_by_a_cwd_relative_path() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{lineno}"
        for path in sorted((ROOT / "plugins").rglob("*.md"))
        for lineno, line in enumerate(path.read_text().splitlines(), 1)
        if BARE_CALL.search(line)
    ]
    assert offenders == []
