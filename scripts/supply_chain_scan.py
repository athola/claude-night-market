#!/usr/bin/env python3
"""Scan lockfiles for known compromised package versions and malicious artifacts.

Uses the blocklist from plugins/leyline/skills/supply-chain-advisory/known-bad-versions.json
to detect compromised dependencies across all lockfiles in the repository.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load_blocklist(root: Path) -> dict:
    """Load the known-bad-versions blocklist."""
    path = root / "plugins/leyline/skills/supply-chain-advisory/known-bad-versions.json"
    if not path.exists():
        print("  Blocklist not found, skipping")
        return {}
    data = json.loads(path.read_text())
    data.pop("_meta", None)
    return data


def scan_lockfiles(root: Path, blocklist: dict) -> list[str]:
    """Check all uv.lock files for known compromised versions."""
    findings = []
    for lockfile in root.rglob("uv.lock"):
        # Skip .venv and cache directories
        parts = lockfile.parts
        if any(
            p.startswith(".") or p in ("node_modules", "__pycache__") for p in parts
        ):
            continue
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
                            f"  CRITICAL: {lockfile}: {pkg}=={ver} "
                            f"({entry['severity']}) - {entry['description'][:80]}"
                        )
    return findings


def scan_artifacts(root: Path, blocklist: dict) -> list[str]:
    """Search for known malicious file artifacts."""
    indicators: set[str] = set()
    for entries in blocklist.values():
        for entry in entries:
            indicators.update(entry.get("indicators", []))

    findings = []
    for ind in indicators:
        for match in root.rglob(ind):
            parts = match.parts
            if any(
                p.startswith(".") or p in ("node_modules", "__pycache__") for p in parts
            ):
                continue
            findings.append(f"  CRITICAL: Found malicious artifact: {match}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    blocklist = load_blocklist(root)
    if not blocklist:
        return 0

    exit_code = 0

    print(">>> Checking lockfiles against known-bad versions blocklist...")
    lockfile_findings = scan_lockfiles(root, blocklist)
    if lockfile_findings:
        print(f"  Found {len(lockfile_findings)} compromised version(s)!")
        for f in lockfile_findings:
            print(f)
        exit_code = 1
    else:
        print("  [OK] No known compromised versions in lockfiles")

    print()
    print(">>> Scanning for known malicious artifacts...")
    artifact_findings = scan_artifacts(root, blocklist)
    if artifact_findings:
        for f in artifact_findings:
            print(f)
        exit_code = 1
    else:
        print("  [OK] No malicious artifacts found")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
