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


class BlocklistMissingError(RuntimeError):
    """The blocklist is absent, so the scan has nothing to scan with.

    This scanner's entire content is that data file. Returning ``{}`` and
    exiting 0 meant the gate reported success in exactly the state where
    it was checking nothing.
    """


def load_blocklist(root: Path) -> dict:
    """Load the known-bad-versions blocklist."""
    path = root / "plugins/leyline/skills/supply-chain-advisory/known-bad-versions.json"
    if not path.exists():
        raise BlocklistMissingError(path)
    data = json.loads(path.read_text())
    data.pop("_meta", None)
    return data


_PACKAGE_HEADER = re.compile(r"(?m)^\[\[package\]\]\s*$")


def _skipped(path: Path, root: Path) -> bool:
    """Skip .venv, caches and node_modules inside the repo.

    Only the parts below ``root`` are tested: a repo checked out under a
    dot-directory (``.claude/worktrees/``) is still scanned.
    """
    return any(
        p.startswith(".") or p in ("node_modules", "__pycache__")
        for p in path.relative_to(root).parts
    )


def scan_lockfiles(root: Path, blocklist: dict) -> list[str]:
    """Check all uv.lock files for known compromised versions."""
    findings = []
    for lockfile in root.rglob("uv.lock"):
        if _skipped(lockfile, root):
            continue
        # One block per [[package]]: name and version are matched inside
        # the same block, and a `{ name = ... }` dependency entry is not
        # at the start of a line, so it never counts as the package.
        blocks = _PACKAGE_HEADER.split(lockfile.read_text())
        for pkg, entries in blocklist.items():
            name_line = re.compile(rf'^name\s*=\s*"{re.escape(pkg)}"\s*$', re.M)
            pkg_blocks = [b for b in blocks if name_line.search(b)]
            for entry in entries:
                for ver in entry["versions"]:
                    version_line = re.compile(
                        rf'^version\s*=\s*"{re.escape(ver)}"\s*$', re.M
                    )
                    if any(version_line.search(b) for b in pkg_blocks):
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
            if _skipped(match, root):
                continue
            findings.append(f"  CRITICAL: Found malicious artifact: {match}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    try:
        blocklist = load_blocklist(root)
    except BlocklistMissingError as exc:
        print(f"  BLOCKED: blocklist not found at {exc.args[0]}", file=sys.stderr)
        print(
            "  The blocklist is this scanner's only content. Without it no "
            "lockfile was checked, so success cannot be reported.",
            file=sys.stderr,
        )
        return 1
    if not blocklist:
        print(
            "  BLOCKED: blocklist parsed to zero entries, so nothing was checked",
            file=sys.stderr,
        )
        return 1

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
