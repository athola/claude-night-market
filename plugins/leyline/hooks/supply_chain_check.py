#!/usr/bin/env python3
"""SessionStart hook: warn when known-compromised package versions are in lockfiles.

Reads the known-bad-versions.json blocklist from the supply-chain-advisory skill
and scans uv.lock / requirements.txt in the current working directory for matches.
Lightweight — only runs at session start, exits fast on no findings.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _find_blocklist() -> Path | None:
    """Locate the known-bad-versions.json relative to this hook."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        candidate = (
            Path(plugin_root)
            / "skills"
            / "supply-chain-advisory"
            / "known-bad-versions.json"
        )
        if candidate.exists():
            return candidate
    # Fallback: relative to this file
    candidate = (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "supply-chain-advisory"
        / "known-bad-versions.json"
    )
    if candidate.exists():
        return candidate
    return None


def _scan_uv_lock(lockfile: Path, blocklist: dict) -> list[dict]:
    """Check a uv.lock for known compromised versions."""
    findings = []
    content = lockfile.read_text()
    for pkg, entries in blocklist.items():
        for entry in entries:
            for ver in entry["versions"]:
                pattern = (
                    rf'name\s*=\s*"{re.escape(pkg)}"'
                    rf'.*?version\s*=\s*"{re.escape(ver)}"'
                )
                if re.search(pattern, content, re.DOTALL):
                    findings.append(
                        {
                            "package": pkg,
                            "version": ver,
                            "severity": entry["severity"],
                            "description": entry["description"],
                            "source": entry.get("source", ""),
                            "indicators": entry.get("indicators", []),
                        }
                    )
    return findings


def _scan_requirements(reqfile: Path, blocklist: dict) -> list[dict]:
    """Check a requirements.txt for known compromised pinned versions."""
    findings = []
    for raw_line in reqfile.read_text().splitlines():
        line = raw_line.strip()
        if "==" not in line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        name = name.strip().lower()
        version = version.strip().split(";")[0].strip()  # strip markers
        for pkg, entries in blocklist.items():
            if name != pkg.lower():
                continue
            for entry in entries:
                if version in entry["versions"]:
                    findings.append(
                        {
                            "package": pkg,
                            "version": version,
                            "severity": entry["severity"],
                            "description": entry["description"],
                            "source": entry.get("source", ""),
                            "indicators": entry.get("indicators", []),
                        }
                    )
    return findings


def main() -> None:
    """Scan lockfiles for known-compromised package versions and emit warnings."""
    blocklist_path = _find_blocklist()
    if not blocklist_path:
        return

    blocklist = json.loads(blocklist_path.read_text())
    blocklist.pop("_meta", None)
    if not blocklist:
        return

    cwd = Path.cwd()
    all_findings: list[dict] = []

    # Scan lockfiles in current project
    for lockfile in cwd.rglob("uv.lock"):
        if ".venv" in lockfile.parts:
            continue
        all_findings.extend(_scan_uv_lock(lockfile, blocklist))

    for reqfile in cwd.glob("requirements*.txt"):
        all_findings.extend(_scan_requirements(reqfile, blocklist))

    if not all_findings:
        return

    # Emit warning via hook additional_context
    warnings = []
    for f in all_findings:
        warnings.append(
            f"SUPPLY CHAIN ALERT: {f['package']}=={f['version']} "
            f"({f['severity'].upper()}) - {f['description'][:100]}"
        )
        if f["source"]:
            warnings.append(f"  Advisory: {f['source']}")
        if f["indicators"]:
            warnings.append(f"  Scan for: {', '.join(f['indicators'])}")
        warnings.append(
            "  ACTION: Remove this version, rotate credentials if"
            " it was ever installed."
        )

    result = {
        "additionalContext": "Supply Chain Warning: " + "\n".join(warnings),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Hook must never crash the session
        pass
    sys.exit(0)
