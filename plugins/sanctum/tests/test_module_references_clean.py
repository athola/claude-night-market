"""Regression test: stale modules/X.md references stay at zero.

Issue #468 listed concrete stale module references in abstract,
imbue, and leyline that were resolved during the 1.9.4 / 1.9.5
release cycles. This test re-runs the audit script and asserts the
ecosystem remains clean. If anyone reintroduces a bad reference,
this fails fast.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT_SCRIPT = (
    REPO_ROOT / "plugins" / "sanctum" / "scripts" / "update_plugin_registrations.py"
)


def test_audit_script_reports_no_module_issues() -> None:
    """Scenario: audit reports zero module issues across all plugins.

    Given the live plugin tree
    When I run update_plugin_registrations.py --dry-run
    Then the summary reports 0 plugins with module issues.
    """
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout
    assert "Plugins with module issues: 0" in output, (
        f"Audit found module issues:\n{output}"
    )
