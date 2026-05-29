"""Verify that an auto-promoted finding's locations still exist.

The Insight Engine promotes review findings into GitHub Issues.
Later work often resolves a finding incidentally, leaving a
phantom-open issue behind (a verify-then-close sweep in
2026-05 found 8 of 11 auto-promoted issues already resolved).

This module provides the shared, honest core for catching that
drift: given a finding's ``Where:`` string or a ``plugin:skill``
id, it resolves the referenced locations and checks whether they
still exist at the current HEAD.

Scope boundary (deliberate): this verifies *location existence*,
not *concern resolution*. File existence is a high-precision,
low-recall signal -- a missing file is strong evidence the area
was refactored away; a present file proves nothing about whether
the concern was addressed. Concern resolution requires reading
content and stays a human / ``/do-issue`` decision. The promotion
gate therefore skips only the clearest case (every referenced
location gone) and never auto-closes anything.

Consumers:
- ``auto_promote_learnings.py`` -- promotion gate (skip stale).
- ``/do-issue`` Step 1.4 -- documents the same verify-before-act
  pattern for the interactive workflow.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Closed string domains for the verification verdict. Bare ``str``
# would let a typo (``"mising"``) pass the type checker and silently
# defeat the gate, so both are constrained to their valid members.
Status = Literal["present", "missing", "stale_lines", "no_refs"]
Confidence = Literal["high", "medium", "low"]

# A bare token counts as a path if it has a directory separator or a
# short trailing extension, and contains at least one alphanumeric.
_EXTENSION_RE = re.compile(r"\.[A-Za-z0-9]{1,6}$")
_ALNUM_RE = re.compile(r"[A-Za-z0-9]")

# `path/to/file.md:20-22` -- embedded colon line range.
_COLON_RANGE_RE = re.compile(
    r"^(?P<path>[\w./-]+\.[A-Za-z0-9]{1,6}):(?P<start>\d+)(?:-(?P<end>\d+))?$"
)
# `L37-47` or `L45` -- an L-prefixed line marker.
_L_MARKER_RE = re.compile(r"^L(?P<start>\d+)(?:-(?P<end>\d+))?$")


@dataclass(frozen=True)
class FileRef:
    """A referenced location: a repo-relative path and optional lines.

    A pure value object, never mutated after construction (hence
    ``frozen``). ``line_end`` without ``line_start`` is an illegal
    state and is rejected at construction.
    """

    path: str
    line_start: int | None = None
    line_end: int | None = None

    def __post_init__(self) -> None:
        """Reject an end line with no start line (an illegal range)."""
        if self.line_end is not None and self.line_start is None:
            raise ValueError("line_end set without line_start")


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of checking a set of references against HEAD.

    Attributes:
        status: One of ``present`` (all locations exist),
            ``missing`` (one or more gone), ``stale_lines`` (file
            exists but the cited line range is out of bounds), or
            ``no_refs`` (nothing parseable to check).
        confidence: ``high`` / ``medium`` / ``low``.
        refs_checked: The references that were evaluated.
        missing: Paths that no longer exist.
        rationale: Short human-readable explanation.

    """

    status: Status
    confidence: Confidence
    refs_checked: list[FileRef] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    rationale: str = ""


def _looks_like_path(token: str) -> bool:
    """True if a bare token resembles a repo path."""
    if not _ALNUM_RE.search(token):
        return False
    return "/" in token or bool(_EXTENSION_RE.search(token))


def parse_where_refs(where: str) -> list[FileRef]:
    """Extract file references from a free-text ``Where:`` string.

    Handles the formats the Insight Engine emits in practice:
    backticked ``path:20-22`` ranges, ``path L37-47`` markers,
    repeated ``L45 / L87`` markers on one path, and bare paths
    trailed by prose ("... and 2 siblings").
    """
    text = where.replace("`", " ")
    paths: list[FileRef] = []
    line_markers: list[tuple[int, int | None]] = []

    for raw in text.split():
        token = raw.strip().strip(",.;()[]")
        if not token:
            continue

        marker = _L_MARKER_RE.match(token)
        if marker:
            end = int(marker["end"]) if marker["end"] else None
            line_markers.append((int(marker["start"]), end))
            continue

        colon = _COLON_RANGE_RE.match(token)
        if colon:
            end = int(colon["end"]) if colon["end"] else None
            paths.append(FileRef(colon["path"], int(colon["start"]), end))
            continue

        if _looks_like_path(token):
            paths.append(FileRef(token))

    # One path with trailing L-markers: distribute the markers across it
    # (e.g. "project-brief.md L45 / L87 / L147" -> three refs).
    if len(paths) == 1 and paths[0].line_start is None and line_markers:
        base = paths[0].path
        return [FileRef(base, start, end) for start, end in line_markers]

    return paths


def resolve_skill_refs(skill: str, repo_root: Path) -> list[FileRef]:
    """Map a ``plugin:name`` skill id to its on-disk skill directory.

    Returns an empty list for a bare name with no plugin prefix
    (nothing reliable to resolve). Existence is checked later by
    ``verify_refs``; this only builds the candidate path.
    """
    if ":" not in skill:
        return []
    plugin, _, name = skill.partition(":")
    if not plugin or not name:
        return []
    # A finding's "skill" may actually be a command or agent; probe
    # each conventional location and return the one that exists.
    candidates = [
        f"plugins/{plugin}/skills/{name}",
        f"plugins/{plugin}/commands/{name}.md",
        f"plugins/{plugin}/agents/{name}.md",
    ]
    for rel in candidates:
        if (repo_root / rel).exists():
            return [FileRef(rel)]
    # No conventional location resolved: the id may be renamed or use a
    # non-standard path. Return nothing (-> ``no_refs``, non-skipping)
    # rather than fabricating a missing path -- "unresolvable" must not
    # masquerade as "removed" and silently skip a live finding.
    return []


def _count_lines(path: Path) -> int | None:
    """Return the line count of a file, or None if unreadable."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError as exc:
        # Fail open: skip the stale-line check, but make the abandoned
        # check visible rather than masking the I/O error.
        print(
            f"[finding_verifier] cannot read {path} for line count: {exc}",
            file=sys.stderr,
        )
        return None


def verify_refs(refs: list[FileRef], repo_root: Path) -> VerificationResult:
    """Check whether referenced locations exist at ``repo_root``."""
    if not refs:
        return VerificationResult(
            "no_refs", "low", [], [], "no parseable references in the finding"
        )

    missing: list[str] = []
    stale: list[str] = []
    present: list[str] = []

    for ref in refs:
        target = repo_root / ref.path
        if not target.exists():
            missing.append(ref.path)
            continue
        if ref.line_start is not None and target.is_file():
            count = _count_lines(target)
            if count is not None and ref.line_start > count:
                stale.append(ref.path)
                continue
        present.append(ref.path)

    missing = _dedup(missing)

    if missing:
        confidence: Confidence = "medium" if (present or stale) else "high"
        rationale = f"referenced location(s) no longer exist: {', '.join(missing)}"
        return VerificationResult("missing", confidence, refs, missing, rationale)

    if stale and not present:
        return VerificationResult(
            "stale_lines",
            "medium",
            refs,
            [],
            "file(s) exist but the cited line range is out of bounds",
        )

    if stale:
        return VerificationResult(
            "present",
            "medium",
            refs,
            [],
            "locations exist; some cited line ranges drifted",
        )

    return VerificationResult(
        "present", "high", refs, [], "all referenced locations exist"
    )


def should_skip_promotion(result: VerificationResult) -> bool:
    """Promotion gate: skip only when every location is gone.

    Weaker signals (``stale_lines``, ``no_refs``, ``present``) never
    block promotion -- they are surfaced for human review instead.
    Partial-missing (``medium``) also never blocks: a finding whose
    surviving files still exist may still apply.
    """
    return result.status == "missing" and result.confidence == "high"


def repo_root_is_valid(root: Path) -> bool:
    """True if ``root`` looks like the night-market repo root.

    The gate's correctness hinges on resolving locations against the
    real tree. A wrong root (relocated, symlinked, or installed copy)
    would report every finding ``missing`` and skip them all. Callers
    use this to disable the gate and promote normally when the root
    cannot be trusted, rather than failing silently.
    """
    return (root / ".git").exists() or (root / "plugins" / "abstract").exists()


def _dedup(items: list[str]) -> list[str]:
    """Order-preserving de-duplication."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _default_repo_root() -> Path:
    """Repo root inferred from this file: scripts/ -> abstract -> plugins -> root."""
    return Path(__file__).resolve().parents[3]


def _collect_refs(
    where: str | None, skill: str | None, repo_root: Path
) -> list[FileRef]:
    """Build the reference set from a Where: string and/or a skill id."""
    refs: list[FileRef] = []
    if where:
        refs.extend(parse_where_refs(where))
    if skill:
        refs.extend(resolve_skill_refs(skill, repo_root))
    return refs


def main(argv: list[str] | None = None) -> int:
    """Verify a finding's locations against a repo and print the verdict.

    A thin shell over the tested core: resolve ``--where`` / ``--skill``
    into references, check them against ``--repo-root``, and report the
    status, confidence, and whether the promotion gate would skip. Exit
    code is 0 on a completed check, 2 when the repo root is untrusted
    (gate disabled) so callers never silently skip live findings.
    """
    parser = argparse.ArgumentParser(
        description="Verify that a finding's referenced locations still exist.",
    )
    parser.add_argument("--where", help="Free-text 'Where:' string from a finding.")
    parser.add_argument("--skill", help="A 'plugin:name' id to resolve to a path.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_default_repo_root(),
        help="Repo root to resolve locations against (default: inferred).",
    )
    args = parser.parse_args(argv)

    if not args.where and not args.skill:
        parser.error("provide --where and/or --skill")

    repo_root = Path(args.repo_root)
    if not repo_root_is_valid(repo_root):
        print(
            f"[finding_verifier] repo root not trusted, gate disabled: {repo_root}",
            file=sys.stderr,
        )
        return 2

    result = verify_refs(_collect_refs(args.where, args.skill, repo_root), repo_root)

    print(f"status:         {result.status}")
    print(f"confidence:     {result.confidence}")
    print(f"refs_checked:   {len(result.refs_checked)}")
    if result.missing:
        print(f"missing:        {', '.join(result.missing)}")
    print(f"rationale:      {result.rationale}")
    print(f"skip_promotion: {should_skip_promotion(result)}")
    return 0


__all__ = [
    "FileRef",
    "VerificationResult",
    "main",
    "parse_where_refs",
    "resolve_skill_refs",
    "verify_refs",
    "should_skip_promotion",
]


if __name__ == "__main__":
    sys.exit(main())
