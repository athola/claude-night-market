#!/usr/bin/env python3
"""Check hooks for outdated patterns against Claude Code SDK spec.

Scans all plugin hooks for known anti-patterns:
- PostToolUse hooks returning invalid decision values
- PreToolUse hooks using deprecated decision/reason fields
- Hooks missing stdin error handling
- Hooks printing unnecessary stdout on no-op paths
- Deprecated hookSpecificOutput structures

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

# PreToolUse: deprecated fields
_DEPRECATED_PRE_FIELDS = {"decision", "reason"}


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
        data = json.loads(hooks_json.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

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

    # Check for deprecated PreToolUse decision/reason fields
    if "PreToolUse" in event_types:
        for dep_field in _DEPRECATED_PRE_FIELDS:
            # Look for top-level decision/reason in JSON output
            pattern = f'"{dep_field}":'
            if pattern in source:
                # Exclude hookSpecificOutput nested usage
                lines = source.split("\n")
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if pattern in stripped and "hookSpecificOutput" not in stripped:
                        # Check surrounding context for hookSpecificOutput
                        context = "\n".join(lines[max(0, i - 3) : i + 1])
                        if "hookSpecificOutput" not in context:
                            findings.append(
                                Finding(
                                    plugin=plugin,
                                    file=filename,
                                    pattern="deprecated-pre-decision",
                                    severity="warning",
                                    message=(
                                        f"PreToolUse hook uses deprecated "
                                        f'"{dep_field}" field. Use '
                                        f'"hookSpecificOutput.'
                                        f'permissionDecision" instead.'
                                    ),
                                )
                            )
                            break

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
        except SyntaxError:
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

    for plugin_name, py_file in find_hook_scripts(repo_root):
        hooks_json = py_file.parent / "hooks.json"
        event_map = get_hook_event_types(hooks_json)
        event_types = event_map.get(py_file.name, [])

        try:
            source = py_file.read_text()
        except OSError:
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
