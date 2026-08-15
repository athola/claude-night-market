"""Change-driven staleness signals for stored claims.

Elapsed time is a proxy for staleness. The signal that actually matters
is whether the world a claim describes has changed since the claim was
written, and that question has a direct answer: fingerprint the files
the claim depends on at capture time, compare at read time.

Timestamps were considered and rejected. Filesystem mtime is rewritten
by clone, checkout, rebase, and archive extraction, so it reports change
where there was none. Git commit time is stable but blind to
uncommitted work, and there is no single git invocation that returns
per-path last-touch times for a set of unrelated paths. A digest of the
bytes needs no subprocess, survives every timestamp-rewriting
operation, and works on files git has never seen.

The tradeoff accepted: reformatting a file changes its digest and will
raise the signal. Since the signal flags rather than suppresses, a
false positive costs a verification prompt, not a lost memory.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path

# Bounds the work a single unit can demand. Recall runs inside a hook
# with a low timeout budget, and a unit declaring hundreds of
# dependencies is malformed rather than thorough.
MAX_TRACKED_PATHS = 25

_READ_CHUNK = 65536


class Signal(Enum):
    """What is known about a dependency since a claim was captured."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    # Distinct from UNCHANGED on purpose. Reporting a dependency we
    # could not inspect as unchanged is what makes a staleness check
    # worse than having none.
    UNKNOWN = "unknown"


def _resolve(path: str, root: Path) -> Path | None:
    """Resolve *path* under *root*, refusing anything that escapes it.

    Declared paths come from model-authored unit text, so they are
    untrusted input at this boundary.
    """
    try:
        root_resolved = root.resolve()
        candidate = (root_resolved / path).resolve()
    except (OSError, ValueError, RuntimeError):
        return None
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    return candidate


def digest_path(path: str, root: Path) -> str | None:
    """Return a content digest for *path*, or None when unreadable.

    None means no fingerprint could be taken. It never means the file
    is empty or unchanged.
    """
    resolved = _resolve(path, root)
    if resolved is None or not resolved.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with resolved.open("rb") as handle:
            while chunk := handle.read(_READ_CHUNK):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def capture_digests(files: list[str], root: Path) -> dict[str, str]:
    """Fingerprint each declared dependency at capture time.

    Paths that cannot be read are omitted rather than recorded with a
    placeholder, so a later comparison reports UNKNOWN instead of
    inventing a change.
    """
    captured: dict[str, str] = {}
    for path in files[:MAX_TRACKED_PATHS]:
        digest = digest_path(path, root)
        if digest is not None:
            captured[path] = digest
    return captured


def check_dependencies(digests: dict[str, str], root: Path) -> dict[str, Signal]:
    """Compare stored fingerprints against the tree as it stands now."""
    signals: dict[str, Signal] = {}
    for path, stored in list(digests.items())[:MAX_TRACKED_PATHS]:
        if not stored:
            # A unit captured before fingerprinting existed.
            signals[path] = Signal.UNKNOWN
            continue
        current = digest_path(path, root)
        if current is None:
            # The dependency is gone. Deletion is a change, and it is
            # the change most likely to invalidate the claim.
            signals[path] = Signal.CHANGED
        elif current != stored:
            signals[path] = Signal.CHANGED
        else:
            signals[path] = Signal.UNCHANGED
    return signals


def changed_paths(signals: dict[str, Signal]) -> list[str]:
    """Names of dependencies that moved, for surfacing to a reader."""
    return [p for p, s in signals.items() if s is Signal.CHANGED]
