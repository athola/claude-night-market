#!/usr/bin/env python3
"""Convert Python SDK hooks to hookify rules.

Analyzes Python hook files and extracts patterns that can be expressed
as declarative hookify rules. Supports regex patterns, string matching,
and simple conditional logic.

Event mapping:
    PreToolUse/PostToolUse hooks are mapped to hookify events based
    on the fields their patterns target:
    - Patterns on "command" -> event: bash
    - Patterns on "file_path"/"content"/"new_text"/"old_text" -> event: file
    - Mixed or unknown fields -> event: bash (safe default)
    SessionStart -> event: prompt
    Stop -> event: stop

Usage:
    python hook_to_hookify.py <hook_file.py> [--output rules.md]
    python hook_to_hookify.py --scan <hooks_dir> [--output rules.md]
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configurable thresholds for hook conversion decisions.
# Hooks with complexity > max are marked unconvertible.
# Patterns with confidence < min are filtered out.
DEFAULT_MAX_COMPLEXITY = 10
DEFAULT_MIN_CONFIDENCE = 0.7


@dataclass
class ExtractedPattern:
    """A pattern extracted from a Python hook."""

    pattern_type: str  # regex, contains, equals, starts_with, ends_with
    pattern: str
    field: str = "command"  # command, content, file_path, user_prompt
    action: str = "warn"  # warn, block
    message: str = ""
    confidence: float = 1.0  # How confident we are in extraction
    source_line: int = 0


@dataclass
class HookAnalysis:
    """Analysis results for a Python hook file."""

    file_path: Path
    hook_type: str = ""  # PreToolUse, PostToolUse, etc.
    patterns: list[ExtractedPattern] = field(default_factory=list)
    convertible: bool = True
    reason: str = ""
    complexity_score: int = 0  # Higher = harder to convert


class HookAnalyzer(ast.NodeVisitor):
    """AST visitor to extract patterns from Python hooks."""

    def __init__(self) -> None:
        self.patterns: list[ExtractedPattern] = []
        self.complexity = 0
        self.has_external_calls = False
        self.has_file_io = False
        self.has_network = False

    def visit_Call(self, node: ast.Call) -> Any:
        """Visit function calls to detect patterns."""
        # Check for re.search, re.match, re.findall
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ("search", "match", "findall"):
                self._extract_regex_pattern(node)
            elif node.func.attr in ("startswith", "endswith"):
                self._extract_string_method(node)
            elif node.func.attr in ("read", "write", "open"):
                self.has_file_io = True
                self.complexity += 2
            elif node.func.attr in ("get", "post", "request"):
                self.has_network = True
                self.complexity += 5

        # Check for 'in' operator in comparisons (handled in visit_Compare)
        self.generic_visit(node)
        return node

    def visit_Compare(self, node: ast.Compare) -> Any:
        """Visit comparisons to detect string containment checks."""
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, ast.In):
                self._extract_contains_pattern(node, comparator)
            elif isinstance(op, (ast.Eq, ast.NotEq)):
                self._extract_equals_pattern(node, comparator)
        self.generic_visit(node)
        return node

    def _extract_regex_pattern(self, node: ast.Call) -> None:
        """Extract regex pattern from re.search/match call."""
        if len(node.args) >= 1:
            pattern_arg = node.args[0]
            if isinstance(pattern_arg, ast.Constant) and isinstance(
                pattern_arg.value, str
            ):
                self.patterns.append(
                    ExtractedPattern(
                        pattern_type="regex",
                        pattern=pattern_arg.value,
                        field=self._guess_field(node),
                        source_line=node.lineno,
                        confidence=0.9,
                    )
                )

    def _extract_string_method(self, node: ast.Call) -> None:
        """Extract startswith/endswith patterns."""
        if (
            isinstance(node.func, ast.Attribute)
            and len(node.args) >= 1
            and isinstance(node.args[0], ast.Constant)
        ):
            method = node.func.attr
            pattern = node.args[0].value
            self.patterns.append(
                ExtractedPattern(
                    pattern_type="starts_with"
                    if method == "startswith"
                    else "ends_with",
                    pattern=str(pattern),
                    field=self._guess_field(node),
                    source_line=node.lineno,
                    confidence=0.95,
                )
            )

    def _extract_contains_pattern(
        self, node: ast.Compare, comparator: ast.expr
    ) -> None:
        """Extract 'x in string' containment patterns."""
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            self.patterns.append(
                ExtractedPattern(
                    pattern_type="contains",
                    pattern=node.left.value,
                    field=self._guess_field(comparator),
                    source_line=node.lineno,
                    confidence=0.85,
                )
            )

    def _extract_equals_pattern(self, node: ast.Compare, comparator: ast.expr) -> None:
        """Extract equality comparison patterns."""
        if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
            self.patterns.append(
                ExtractedPattern(
                    pattern_type="equals",
                    pattern=comparator.value,
                    field=self._guess_field(node.left),
                    source_line=node.lineno,
                    confidence=0.8,
                )
            )

    def _guess_field(self, node: ast.expr) -> str:
        """Guess which field a pattern applies to based on variable names."""
        # Try to find variable names in the AST
        names = self._collect_names(node)

        for name in names:
            name_lower = name.lower()
            if "command" in name_lower or "cmd" in name_lower:
                return "command"
            if "content" in name_lower or "text" in name_lower:
                return "content"
            if "path" in name_lower or "file" in name_lower:
                return "file_path"
            if "prompt" in name_lower:
                return "user_prompt"

        return "command"  # Default

    def _collect_names(self, node: ast.expr) -> list[str]:
        """Collect all Name nodes from an expression."""
        names = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.append(child.id)
            elif isinstance(child, ast.Attribute):
                names.append(child.attr)
        return names


def analyze_hook(
    file_path: Path,
    max_complexity: int = DEFAULT_MAX_COMPLEXITY,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> HookAnalysis:
    """Analyze a Python hook file and extract convertible patterns.

    Args:
        file_path: Path to the Python hook file
        max_complexity: Maximum allowed complexity score. Hooks with
            complexity above this value are marked unconvertible.
        min_confidence: Minimum confidence threshold. Patterns below
            this value are filtered out.

    Returns:
        HookAnalysis with extracted patterns and metadata
    """
    analysis = HookAnalysis(file_path=file_path)

    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except (SyntaxError, OSError) as e:
        analysis.convertible = False
        analysis.reason = f"Could not parse: {e}"
        return analysis

    # Detect hook type from filename or content
    analysis.hook_type = _detect_hook_type(file_path, content)

    if not analysis.hook_type:
        analysis.convertible = False
        analysis.reason = "Could not detect hook type"
        return analysis

    # Run AST analysis
    analyzer = HookAnalyzer()
    analyzer.visit(tree)

    # Filter patterns by confidence threshold
    analysis.patterns = [p for p in analyzer.patterns if p.confidence >= min_confidence]
    analysis.complexity_score = analyzer.complexity

    # Determine if fully convertible
    if analyzer.has_network:
        analysis.convertible = False
        analysis.reason = "Contains network calls - requires full Python hook"
    elif analyzer.has_file_io:
        analysis.convertible = False
        analysis.reason = "Contains file I/O - requires full Python hook"
    elif analyzer.complexity > max_complexity:
        analysis.convertible = False
        analysis.reason = "Too complex for declarative rules"
    elif not analysis.patterns:
        analysis.convertible = False
        analysis.reason = "No extractable patterns found"

    return analysis


def _detect_hook_type(file_path: Path, content: str) -> str:
    """Detect the hook type from filename or content."""
    name = file_path.stem.lower()

    if "pre" in name and "tool" in name:
        return "PreToolUse"
    if "post" in name and "tool" in name:
        return "PostToolUse"
    if "session" in name and "start" in name:
        return "SessionStart"
    if "stop" in name:
        return "Stop"

    # Check content for hook type hints
    if "PreToolUse" in content:
        return "PreToolUse"
    if "PostToolUse" in content:
        return "PostToolUse"

    return ""


def _detect_tool_event(analysis: HookAnalysis) -> str:
    """Detect the hookify event type from extracted pattern fields.

    PreToolUse and PostToolUse hooks can target different tools:
    Bash, Edit, Write, Read, etc. The hookify event model maps
    these to two categories:

    - "bash": for hooks targeting command execution (Bash tool).
      Detected when patterns reference the "command" field.
    - "file": for hooks targeting file operations (Edit, Write,
      MultiEdit, Read tools). Detected when patterns reference
      "file_path", "content", "new_text", or "old_text" fields.

    When a hook has patterns with mixed fields (some targeting
    commands, some targeting files), we fall back to "bash" since
    hookify rules can only have one event type per rule.

    This function only applies to PreToolUse and PostToolUse
    hooks. For SessionStart and Stop, the mapping is direct
    (prompt and stop, respectively).

    Args:
        analysis: Hook analysis with extracted patterns

    Returns:
        Hookify event string: "bash", "file", "prompt", or "stop"
    """
    # Direct mappings for non-tool-use hook types
    direct_map = {
        "SessionStart": "prompt",
        "Stop": "stop",
    }
    if analysis.hook_type in direct_map:
        return direct_map[analysis.hook_type]

    # For PreToolUse/PostToolUse, inspect pattern fields to
    # determine whether the hook targets bash commands or file
    # operations (Edit/Write/Read tools).
    file_fields = {"file_path", "content", "new_text", "old_text"}
    bash_fields = {"command"}

    has_file = False
    has_bash = False

    for pattern in analysis.patterns:
        if pattern.field in file_fields:
            has_file = True
        elif pattern.field in bash_fields:
            has_bash = True

    # If all patterns target file fields, use "file" event
    if has_file and not has_bash:
        return "file"

    # Default: "bash" covers command-targeting hooks and mixed
    # or indeterminate cases. This is the safe default because
    # most PreToolUse/PostToolUse hooks guard against dangerous
    # shell commands.
    return "bash"


def generate_hookify_rule(analysis: HookAnalysis) -> str:
    """Generate a hookify rule from analysis results.

    Args:
        analysis: Hook analysis results

    Returns:
        Hookify rule in markdown format
    """
    if not analysis.convertible or not analysis.patterns:
        return ""

    # Detect the appropriate hookify event by examining what
    # tool the hook targets (bash commands vs file operations)
    event = _detect_tool_event(analysis)

    # Build rule
    lines = [
        "---",
        f"name: {analysis.file_path.stem.replace('_', '-')}",
        f"event: {event}",
    ]

    # Add pattern or conditions
    if len(analysis.patterns) == 1:
        p = analysis.patterns[0]
        if p.pattern_type == "regex":
            lines.append(f"pattern: '{p.pattern}'")
        else:
            lines.extend(
                [
                    "conditions:",
                    f"  - field: {p.field}",
                    f"    operator: {p.pattern_type}",
                    f"    pattern: '{p.pattern}'",
                ]
            )
    else:
        lines.append("conditions:")
        for p in analysis.patterns:
            lines.extend(
                [
                    f"  - field: {p.field}",
                    f"    operator: {p.pattern_type if p.pattern_type != 'regex' else 'regex_match'}",
                    f"    pattern: '{p.pattern}'",
                ]
            )

    lines.extend(
        [
            "action: warn",
            "---",
            "",
            f"Converted from: {analysis.file_path.name}",
            "",
            "**Review this rule before using.** Automated conversion may miss nuances.",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Python SDK hooks to hookify rules"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Hook file or directory to analyze",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan directory for all Python hooks",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file for generated rules",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed analysis",
    )
    parser.add_argument(
        "--max-complexity",
        type=int,
        default=DEFAULT_MAX_COMPLEXITY,
        help=(
            "Maximum complexity score for convertible hooks "
            f"(default: {DEFAULT_MAX_COMPLEXITY})"
        ),
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help=(
            "Minimum confidence threshold for extracted patterns "
            f"(default: {DEFAULT_MIN_CONFIDENCE})"
        ),
    )

    args = parser.parse_args()

    # Collect files to analyze
    if args.scan or args.path.is_dir():
        files = list(args.path.rglob("*.py"))
    else:
        files = [args.path]

    results = []
    for f in files:
        if f.name.startswith("test_") or "/__pycache__/" in str(f):
            continue

        analysis = analyze_hook(
            f,
            max_complexity=args.max_complexity,
            min_confidence=args.min_confidence,
        )
        results.append(analysis)

        if args.verbose:
            status = "✓" if analysis.convertible else "✗"
            print(f"{status} {f.name}: {len(analysis.patterns)} patterns")
            if not analysis.convertible:
                print(f"  Reason: {analysis.reason}")

    # Generate output
    output_lines = ["# Converted Hookify Rules\n"]
    converted = 0

    for analysis in results:
        if analysis.convertible and analysis.patterns:
            rule = generate_hookify_rule(analysis)
            if rule:
                output_lines.append(f"\n## {analysis.file_path.stem}\n")
                output_lines.append(rule)
                converted += 1

    output = "\n".join(output_lines)

    if args.output:
        args.output.write_text(output)
        print(f"Wrote {converted} rules to {args.output}")
    else:
        print(output)

    print(f"\nSummary: {converted}/{len(results)} hooks convertible")
    return 0


if __name__ == "__main__":
    sys.exit(main())
