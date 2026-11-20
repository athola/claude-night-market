"""The watchdog and the hooks agree on what counts as remaining work.

The hooks counted `pending` and read an `items` list; the watchdog's jq
counted only `active` and `paused` under `work_items` (EGR-8).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from _manifest_utils import has_active_work

WATCHDOG = Path(__file__).resolve().parent.parent / "scripts" / "watchdog.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")

MANIFESTS = [
    {"work_items": [{"id": "a", "status": "pending"}]},
    {"work_items": [{"id": "a", "status": "active"}]},
    {"work_items": [{"id": "a", "status": "paused"}]},
    {"work_items": [{"id": "a", "status": "completed"}]},
    {"items": [{"id": "a", "status": "active"}]},
    {"work_items": []},
]


def _watchdog_filter() -> str:
    match = re.search(r"remaining=\$\(jq '([^']+)'", WATCHDOG.read_text())
    assert match, "watchdog.sh no longer counts remaining items with jq"
    return match.group(1)


@pytest.mark.parametrize("manifest", MANIFESTS, ids=json.dumps)
def test_watchdog_and_hooks_agree_on_active_work(tmp_path: Path, manifest) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    count = subprocess.run(
        ["jq", _watchdog_filter(), str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert (int(count) > 0) is has_active_work(path)
