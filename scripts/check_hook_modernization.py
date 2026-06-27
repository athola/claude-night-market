#!/usr/bin/env python3
"""Check hooks for outdated patterns against Claude Code SDK spec.

Scans all plugin hooks for known anti-patterns:
- PostToolUse hooks returning invalid decision values
- Hooks missing stdin error handling
- Hooks printing unnecessary stdout on no-op paths

Note: Both PreToolUse output forms are valid per the Claude Code SDK:
- Legacy: {"decision": "block"|"approve", "reason": "..."}
- Modern: {"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "allow"|"deny"|"ask", ...}}
Neither form is deprecated; the scanner does not flag either. See
issue #517 for the diagnosis history.

Exit codes:
    0 - no issues found (or --json mode)
    1 - issues detected (text mode only)
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    """A single modernization issue."""

    plugin: str
    file: str
    pattern: str
    severity: str  # "error" | "warning"
    message: str


@dataclass
class AuditResult:
    """Aggregated audit results."""

    findings: list[Finding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")


# --- Hook event to valid response fields mapping ---

# PostToolUse: decision can only be "block" or omitted.
# "ALLOW", "approve", "allow" are invalid.
_INVALID_POST_DECISION = {"ALLOW", "allow", "approve", "APPROVE"}


def find_hooks_json(repo_root: Path) -> list[Path]:
    """Find all hooks.json files in plugin directories."""
    return sorted(repo_root.glob("plugins/*/hooks/hooks.json"))


def find_hook_scripts(repo_root: Path) -> list[tuple[str, Path]]:
    """Find all Python hook scripts with their plugin name."""
    results = []
    for hooks_json in find_hooks_json(repo_root):
        plugin_dir = hooks_json.parent.parent
        plugin_name = plugin_dir.name
        for py_file in sorted(hooks_json.parent.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            results.append((plugin_name, py_file))
    return results


def get_hook_event_types(hooks_json: Path) -> dict[str, list[str]]:
    """Map script filenames to their hook event types from hooks.json.

    Returns dict like {"security_check.py": ["PreToolUse"]}.
    """
    try:
        raw = hooks_json.read_text()
    except OSError:
        # Missing/absent file: a plugin legitimately may have no
        # hooks.json next to a script. Treat as "no events".
        return {}
    # A malformed hooks.json is NOT "no events"; let JSONDecodeError
    # propagate so run_audit can surface it as an error rather than
    # silently skipping every event-gated check (issue #575, B1).
    data = json.loads(raw)

    script_events: dict[str, list[str]] = {}
    hooks = data.get("hooks", {})
    for event_name, matchers in hooks.items():
        if not isinstance(matchers, list):
            continue
        for matcher_group in matchers:
            for hook in matcher_group.get("hooks", []):
                cmd = hook.get("command", "")
                # Extract script filename from command
                for part in cmd.split():
                    if part.endswith(".py"):
                        filename = part.split("/")[-1]
                        script_events.setdefault(filename, []).append(event_name)
    return script_events


def check_python_source(
    source: str,
    plugin: str,
    filename: str,
    event_types: list[str],
) -> list[Finding]:
    """Check a Python hook source for anti-patterns."""
    findings: list[Finding] = []

    # Check for invalid PostToolUse decision values in source
    if "PostToolUse" in event_types or not event_types:
        for invalid in _INVALID_POST_DECISION:
            pattern = f'"decision": "{invalid}"'
            if pattern in source or f"'decision': '{invalid}'" in source:
                findings.append(
                    Finding(
                        plugin=plugin,
                        file=filename,
                        pattern="invalid-post-decision",
                        severity="error",
                        message=(
                            f"PostToolUse hook uses invalid decision "
                            f'value "{invalid}". '
                            f'Valid values: "block" or omit entirely.'
                        ),
                    )
                )

    # PreToolUse output forms: both legacy {"decision", "reason"} and
    # modern hookSpecificOutput.permissionDecision are valid per the SDK.
    # Neither is flagged. See issue #517 for the diagnosis history.

    # Check for missing stdin error handling
    if "sys.stdin" in source or "json.load" in source:
        has_try = "try:" in source
        has_json_except = "JSONDecodeError" in source or "ValueError" in source
        if not (has_try and has_json_except):
            findings.append(
                Finding(
                    plugin=plugin,
                    file=filename,
                    pattern="missing-stdin-error-handling",
                    severity="warning",
                    message=(
                        "Hook reads stdin but lacks try/except for "
                        "JSONDecodeError. Malformed input will crash "
                        "the hook."
                    ),
                )
            )

    # Check for unnecessary stdout on no-op paths
    # (printing JSON when there's nothing to report)
    if "PostToolUse" in event_types:
        # Count print/sys.stdout.write calls
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            # A source we cannot parse is unverifiable, not clean. Surface
            # an error so the CI gate fails instead of silently passing
            # (issue #575, B1).
            findings.append(
                Finding(
                    plugin=plugin,
                    file=filename,
                    pattern="unparseable-source",
                    severity="error",
                    message=(
                        f"Hook source could not be parsed: {exc}. "
                        "The file was not checked; fix the syntax error."
                    ),
                )
            )
            return findings

        print_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "print":
                    print_count += 1
                elif isinstance(func, ast.Attribute) and func.attr == "write":
                    # Check if it's sys.stdout.write (not stderr)
                    if (
                        isinstance(func.value, ast.Attribute)
                        and func.value.attr == "stdout"
                    ):
                        print_count += 1

        # If every code path prints, the no-op path is noisy
        # Heuristic: more than 3 print calls in a PostToolUse hook
        # likely means it prints on no-op paths too
        if print_count > 3:
            findings.append(
                Finding(
                    plugin=plugin,
                    file=filename,
                    pattern="noisy-no-op",
                    severity="warning",
                    message=(
                        f"PostToolUse hook has {print_count} stdout "
                        f"writes. Consider silent exit for no-op paths "
                        f"(no output = allow)."
                    ),
                )
            )

    return findings


def run_audit(repo_root: Path) -> AuditResult:
    """Run the full modernization audit."""
    result = AuditResult()

    reported_bad_json: set[Path] = set()
    for plugin_name, py_file in find_hook_scripts(repo_root):
        hooks_json = py_file.parent / "hooks.json"
        try:
            event_map = get_hook_event_types(hooks_json)
        except json.JSONDecodeError as exc:
            # A malformed hooks.json means we cannot know which events a
            # script handles, so the event-gated checks are skipped. That
            # is a checking failure, not a clean result (issue #575, B1).
            if hooks_json not in reported_bad_json:
                reported_bad_json.add(hooks_json)
                result.findings.append(
                    Finding(
                        plugin=plugin_name,
                        file="hooks.json",
                        pattern="unparseable-hooks-json",
                        severity="error",
                        message=(
                            f"hooks.json could not be parsed: {exc}. "
                            "Event-gated checks were skipped for this "
                            "plugin; fix the JSON."
                        ),
                    )
                )
            event_map = {}
        event_types = event_map.get(py_file.name, [])

        try:
            source = py_file.read_text()
        except OSError as exc:
            # Unreadable hook source is unverifiable, not clean. Surface
            # an error rather than continuing silently (issue #575, B1).
            result.findings.append(
                Finding(
                    plugin=plugin_name,
                    file=py_file.name,
                    pattern="unreadable-source",
                    severity="error",
                    message=(
                        f"Hook source could not be read: {exc}. "
                        "The file was not checked."
                    ),
                )
            )
            continue

        findings = check_python_source(source, plugin_name, py_file.name, event_types)
        result.findings.extend(findings)

    return result


def format_text(result: AuditResult) -> str:
    """Format findings as a human-readable table."""
    if not result.findings:
        return "No modernization issues found."

    lines = [
        "Hook Modernization Audit",
        "=" * 60,
        "",
    ]
    for f in result.findings:
        icon = "ERROR" if f.severity == "error" else "WARN "
        lines.append(f"  [{icon}] {f.plugin}/{f.file}")
        lines.append(f"          Pattern: {f.pattern}")
        lines.append(f"          {f.message}")
        lines.append("")

    lines.append(f"Total: {result.error_count} errors, {result.warning_count} warnings")
    return "\n".join(lines)


def format_json(result: AuditResult) -> str:
    """Format findings as JSON."""
    return json.dumps(
        {
            "success": True,
            "errors": result.error_count,
            "warnings": result.warning_count,
            "findings": [
                {
                    "plugin": f.plugin,
                    "file": f.file,
                    "pattern": f.pattern,
                    "severity": f.severity,
                    "message": f.message,
                }
                for f in result.findings
            ],
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]

    output_json = "--json" in args
    repo_root = Path(__file__).resolve().parent.parent

    # Allow overriding repo root for testing
    for i, arg in enumerate(args):
        if arg == "--root" and i + 1 < len(args):
            repo_root = Path(args[i + 1])

    result = run_audit(repo_root)

    if output_json:
        print(format_json(result))
        return 0

    print(format_text(result))
    return 1 if result.error_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
