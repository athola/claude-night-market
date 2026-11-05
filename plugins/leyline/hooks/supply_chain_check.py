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
from typing import Any

# Blocklist maps a package name to its list of known-bad-version entries.
Blocklist = dict[str, list[dict[str, Any]]]


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


def _scan_uv_lock(lockfile: Path, blocklist: Blocklist) -> list[dict[str, Any]]:
    """Check a uv.lock for known compromised versions."""
    findings = []
    content = lockfile.read_text()
    for pkg, entries in blocklist.items():
        for entry in entries:
            for ver in entry["versions"]:
                # name and version are adjacent lines of one [[package]]
                # block. A lazy span across blocks also matched a bare
                # ``{ name = "pkg" }`` dependency reference followed by some
                # other package's identical version.
                pattern = (
                    rf'^name\s*=\s*"{re.escape(pkg)}"[ \t]*\r?\n'
                    rf'version\s*=\s*"{re.escape(ver)}"'
                )
                if re.search(pattern, content, re.MULTILINE):
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


# ``name[extras] == version``, then a marker, comment, continuation or
# the end. Hash lines (``--hash=...``) and options never match.
_REQUIREMENT_PIN = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?"
    r"\s*==\s*(?P<version>[^\s;#\\]+)"
)


def _normalize(name: str) -> str:
    """PEP 503: case and runs of ``-``, ``_`` and ``.`` do not distinguish names."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _scan_requirements(reqfile: Path, blocklist: Blocklist) -> list[dict[str, Any]]:
    """Check a requirements.txt for known compromised pinned versions."""
    findings = []
    for raw_line in reqfile.read_text().splitlines():
        pin = _REQUIREMENT_PIN.match(raw_line)
        if not pin:
            continue
        name = _normalize(pin.group("name"))
        version = pin.group("version")
        for pkg, entries in blocklist.items():
            if name != _normalize(pkg):
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


# Not the project's own lockfiles, and large enough that walking them on
# every SessionStart risks the hook timeout.
_SKIPPED_DIRS = frozenset({".venv", "node_modules", ".git"})


def _project_lockfiles(root: Path) -> list[Path]:
    """Every ``uv.lock`` under ``root``, without descending skipped trees."""
    found = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in _SKIPPED_DIRS)
        if "uv.lock" in files:
            found.append(Path(directory) / "uv.lock")
    return found


def main() -> None:
    """Scan lockfiles for known-compromised package versions and emit warnings."""
    blocklist_path = _find_blocklist()
    if not blocklist_path:
        return

    try:
        blocklist = json.loads(blocklist_path.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"supply_chain_check: failed to parse blocklist {blocklist_path}: {exc}",
            file=sys.stderr,
        )
        return
    blocklist.pop("_meta", None)
    if not blocklist:
        return

    cwd = Path.cwd()
    all_findings: list[dict[str, Any]] = []

    # Scan lockfiles in current project
    for lockfile in _project_lockfiles(cwd):
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
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "Supply Chain Warning: " + "\n".join(warnings),
        },
    }
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (
        json.JSONDecodeError,
        OSError,
        KeyError,
        TypeError,
        AttributeError,
        ValueError,
        RuntimeError,
    ):
        import traceback

        print("supply_chain_check: unexpected error", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    sys.exit(0)
