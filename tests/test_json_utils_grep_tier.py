"""get_json_field's grep -oP tier must return one value, as jq does.

grep -o prints every match on its own line. A hook payload whose
tool_input repeats a top-level key name came back as two lines, which a
caller comparing the value with `case` never matched.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COPIES = [
    "scripts/shared/json_utils.sh",
    "plugins/imbue/hooks/shared/json_utils.sh",
    "plugins/conserve/hooks/shared/json_utils.sh",
    "plugins/memory-palace/hooks/shared/json_utils.sh",
]
PAYLOAD = '{"tool_name":"Bash","tool_input":{"tool_name":"x"}}'


#: GNU ``grep -oP``, for the one pattern shape json_utils uses: it matches
#: the pattern against each stdin line and prints every match, so a probe
#: whose input cannot match fails here as it does on a real GNU grep.
#: ``\K`` has no Python equivalent, so the part after it is a group.
GREP_STAND_IN = """#!{python}
import re, sys
pattern = next(a for a in sys.argv[1:] if not a.startswith("-"))
head, _, tail = pattern.partition(r"\\K")
regex = re.compile(f"(?:{{head}})({{tail}})" if tail else f"({{head}})")
found = False
for line in sys.stdin:
    for match in regex.finditer(line):
        found = True
        print(match.group(1))
sys.exit(0 if found else 1)
"""


def _path_with_gnu_grep(tmp_path: Path) -> Path:
    """Stand in for GNU grep -oP, which macOS and BusyBox do not ship."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    grep = bin_dir / "grep"
    grep.write_text(GREP_STAND_IN.format(python=sys.executable))
    grep.chmod(0o755)
    (bin_dir / "sed").symlink_to("/usr/bin/sed")
    return bin_dir


@pytest.mark.parametrize("copy", COPIES)
def test_grep_tier_returns_the_first_match_only(copy: str, tmp_path: Path) -> None:
    bin_dir = _path_with_gnu_grep(tmp_path)
    proc = subprocess.run(
        [
            "/bin/bash",
            "-c",
            'source "$0"; get_json_field "$1" tool_name',
            copy,
            PAYLOAD,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": str(bin_dir)},
    )
    assert proc.stdout == "Bash"
