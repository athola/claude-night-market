"""Convention codex loading and check engine for egregore quality stage."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class Convention:
    """A single review convention from the codex."""

    id: str
    name: str
    description: str
    check_type: str
    severity: str
    enabled: bool = True
    grep_pattern: str | None = None
    file_globs: list[str] = field(default_factory=list)
    exempt_paths: list[str] = field(default_factory=list)
    check_paths: list[str] = field(default_factory=list)
    checker: str | None = None


@dataclass
class Finding:
    """A single convention violation."""

    convention_id: str
    convention_name: str
    file: Path
    line: int
    message: str
    severity: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "convention_id": self.convention_id,
            "convention_name": self.convention_name,
            "file": str(self.file),
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
        }


_REQUIRED_FIELDS = {"id", "check_type"}


def _parse_convention(data: dict[str, Any]) -> Convention:
    """Parse a single convention entry from codex data."""
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"Convention missing required fields: {', '.join(sorted(missing))}"
        )
    return Convention(
        id=data["id"],
        name=data.get("name", data["id"]),
        description=data.get("description", ""),
        check_type=data["check_type"],
        severity=data.get("severity", "warning"),
        enabled=data.get("enabled", True),
        grep_pattern=data.get("grep_pattern"),
        file_globs=data.get("file_globs", []),
        exempt_paths=data.get("exempt_paths", []),
        check_paths=data.get("check_paths", []),
        checker=data.get("checker"),
    )


def load_codex(path: Path) -> list[Convention]:
    """Load and validate a convention codex YAML file.

    Returns only enabled conventions.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError on invalid YAML or missing fields.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Codex file not found: {path}")

    text = path.read_text()

    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in codex {path}: {exc}") from exc
    else:
        raise ValueError(
            "PyYAML is required to load codex YAML files. "
            "Install it with: pip install pyyaml"
        )

    if not isinstance(data, dict) or "conventions" not in data:
        raise ValueError(
            f"Codex {path} must have a top-level 'conventions' key"
        )

    raw_conventions = data["conventions"]
    if not isinstance(raw_conventions, list):
        raise ValueError(
            f"Codex {path}: 'conventions' must be a list"
        )

    conventions = []
    for entry in raw_conventions:
        conv = _parse_convention(entry)
        if conv.enabled:
            conventions.append(conv)

    return conventions


def _matches_any_glob(path: Path, globs: Sequence[str]) -> bool:
    """Check if a path matches any of the given glob patterns."""
    for pattern in globs:
        if PurePath(path).match(pattern):
            return True
    return False


def _check_grep(
    files: Sequence[Path],
    convention: Convention,
) -> list[Finding]:
    """Run a grep-pattern convention check against files."""
    if not convention.grep_pattern:
        return []

    pattern = re.compile(convention.grep_pattern)
    findings: list[Finding] = []

    for file_path in files:
        # Skip files that don't match the convention's file globs
        if convention.file_globs and not _matches_any_glob(
            file_path, convention.file_globs
        ):
            continue

        # Skip exempt paths
        if convention.exempt_paths and _matches_any_glob(
            file_path, convention.exempt_paths
        ):
            continue

        try:
            content = file_path.read_text(errors="replace")
        except (OSError, UnicodeDecodeError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line):
                findings.append(
                    Finding(
                        convention_id=convention.id,
                        convention_name=convention.name,
                        file=file_path,
                        line=line_num,
                        message=f"{convention.name}: {line.strip()}",
                        severity=convention.severity,
                    )
                )

    return findings


def check_doc_consolidation(
    files: Sequence[Path],
    base_dir: Path | None = None,
) -> list[Finding]:
    """C5 custom checker: flag new standalone markdown files.

    Markdown files inside skills/, modules/, or named README.md
    are allowed. All other new .md files are flagged.
    """
    allowed_dirs = {"skills", "modules", "templates", "commands"}
    allowed_names = {"README.md", "CHANGELOG.md", "LICENSE.md"}
    findings: list[Finding] = []

    for file_path in files:
        if file_path.suffix.lower() != ".md":
            continue

        if file_path.name in allowed_names:
            continue

        # Check if any parent directory is in the allowed set
        parts = file_path.parts
        if base_dir is not None:
            try:
                rel = file_path.relative_to(base_dir)
                parts = rel.parts
            except ValueError:
                parts = file_path.parts

        in_allowed = any(part in allowed_dirs for part in parts)
        if in_allowed:
            continue

        findings.append(
            Finding(
                convention_id="C5",
                convention_name="consolidate-docs",
                file=file_path,
                line=1,
                message=(
                    f"consolidate-docs: {file_path.name} is a new "
                    f"standalone markdown file. Consider consolidating "
                    f"into an existing document."
                ),
                severity="warning",
            )
        )

    return findings


# Registry of custom checkers
_CUSTOM_CHECKERS: dict[str, Callable[..., list[Finding]]] = {
    "check_doc_consolidation": check_doc_consolidation,
}


def _check_custom(
    files: Sequence[Path],
    convention: Convention,
    base_dir: Path | None = None,
) -> list[Finding]:
    """Run a custom checker function."""
    if not convention.checker:
        return []

    checker = _CUSTOM_CHECKERS.get(convention.checker)
    if checker is None:
        return [
            Finding(
                convention_id=convention.id,
                convention_name=convention.name,
                file=Path("<unknown>"),
                line=0,
                message=f"Unknown custom checker: {convention.checker}",
                severity="warning",
            )
        ]

    return checker(files, base_dir=base_dir)


def check_conventions(
    files: Sequence[Path],
    conventions: Sequence[Convention],
    base_dir: Path | None = None,
) -> list[Finding]:
    """Run all convention checks against the given files.

    Returns a list of Finding objects, one per violation.
    """
    all_findings: list[Finding] = []

    for conv in conventions:
        if not conv.enabled:
            continue

        if conv.check_type == "grep":
            all_findings.extend(_check_grep(files, conv))
        elif conv.check_type == "custom":
            all_findings.extend(_check_custom(files, conv, base_dir))
        elif conv.check_type == "paths":
            all_findings.append(
                Finding(
                    convention_id=conv.id,
                    convention_name=conv.name,
                    file=Path("<skipped>"),
                    line=0,
                    message="Paths checks handled at orchestration level",
                    severity="skipped",
                )
            )
        elif conv.check_type == "skill":
            all_findings.append(
                Finding(
                    convention_id=conv.id,
                    convention_name=conv.name,
                    file=Path("<skipped>"),
                    line=0,
                    message="Skill checks handled at orchestration level",
                    severity="skipped",
                )
            )

    return all_findings


# ── Quality gate orchestration logic ────────────────────

# Maps each quality step to the convention IDs it should check.
STEP_CONVENTIONS: dict[str, list[str]] = {
    "code-review": ["C1", "C2", "C3", "C4", "C5"],
    "unbloat": [],
    "code-refinement": [],
    "update-tests": [],
    "update-docs": ["C5"],
}


def conventions_for_step(
    step: str,
    all_conventions: Sequence[Convention],
) -> list[Convention]:
    """Filter conventions to those mapped to a quality step."""
    allowed_ids = set(STEP_CONVENTIONS.get(step, []))
    return [c for c in all_conventions if c.id in allowed_ids]


@dataclass
class Verdict:
    """Result of a quality step evaluation."""

    status: str
    blocking_count: int
    warning_count: int
    summary: str

    def to_decision(self, step: str) -> dict[str, str]:
        """Convert to a manifest decision entry."""
        return {
            "step": step,
            "chose": self.status,
            "why": self.summary,
        }


def calculate_verdict(findings: Sequence[Finding]) -> Verdict:
    """Calculate a verdict from a list of findings."""
    blocking = sum(1 for f in findings if f.severity == "blocking")
    warnings = sum(1 for f in findings if f.severity == "warning")

    if blocking > 0:
        status = "fix-required"
    elif warnings > 0:
        status = "pass-with-warnings"
    else:
        status = "pass"

    parts = []
    if blocking:
        parts.append(f"{blocking} blocking")
    if warnings:
        parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
    if not parts:
        parts.append("no findings")
    summary = ", ".join(parts)

    return Verdict(
        status=status,
        blocking_count=blocking,
        warning_count=warnings,
        summary=summary,
    )


def filter_steps(
    all_steps: Sequence[str],
    quality_config: dict[str, Any],
) -> list[str]:
    """Filter quality steps based on work item config.

    If quality_config has "only", keep only those steps.
    If quality_config has "skip", remove those steps.
    "only" takes precedence over "skip".
    Preserves pipeline order from all_steps.
    """
    only = quality_config.get("only")
    if only is not None:
        only_set = set(only)
        return [s for s in all_steps if s in only_set]

    skip = quality_config.get("skip")
    if skip is not None:
        skip_set = set(skip)
        return [s for s in all_steps if s not in skip_set]

    return list(all_steps)
