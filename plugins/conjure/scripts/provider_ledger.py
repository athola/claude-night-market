"""What this machine already knows about its delegation providers.

``Delegator.verify_service`` spawns the CLI for a version probe and,
for four providers, an auth probe on top. With eight registered
services that is up to sixteen subprocesses to answer "who can take
this work", paid again on the next call because nothing was written
down.

This module writes it down. What it may remember is asymmetric, and
the asymmetry is the whole design:

``installed`` and ``version``
    Cheap to re-derive and stable between runs. Cached under a
    time-to-live.

``auth_confirmed_at``
    A timestamp, never a boolean. A token expires without touching the
    binary, so a cached "authenticated: true" would route work to a
    provider that has since started refusing it. Callers read the age
    and apply their own bar.

``last_error``
    Invalidates the entry. A recorded failure clears any standing
    confirmation immediately, which is what keeps a stale success from
    outliving the credential that earned it.

The file is a cache and is treated as one. A truncated or unreadable
ledger loads as empty and costs one round of probes, because the
alternative, refusing to run until an operator repairs a cache file,
is worse than the problem it solves.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path

#: Bumped when the on-disk shape changes incompatibly. A reader that
#: finds an unfamiliar version treats the file as absent.
LEDGER_VERSION = 1

#: Installed-fact freshness. Six hours is long enough that a working
#: session pays the probes once and short enough that an install or
#: uninstall is noticed the same day.
DEFAULT_TTL_SECONDS = 6 * 60 * 60

DEFAULT_LEDGER_PATH = (
    Path.home() / ".claude" / "hooks" / "delegation" / "provider-state.json"
)


@dataclass(frozen=True)
class ProviderRecord:
    """One provider's state as of ``recorded_at``."""

    name: str
    binary: str
    installed: bool
    version: str | None
    #: Epoch seconds when a credential was last confirmed working, or
    #: None when it never was or a failure has since cleared it.
    auth_confirmed_at: float | None
    recorded_at: float
    last_error: str | None = None


class ProviderLedger:
    """Read and write the provider-state cache."""

    def __init__(
        self,
        path: Path | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Load the ledger at ``path``, defaulting to the delegation config dir."""
        self.path = Path(path) if path is not None else DEFAULT_LEDGER_PATH
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, ProviderRecord] = self._load()

    def _load(self) -> dict[str, ProviderRecord]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            # A cache that cannot be read is a cache miss, not an outage.
            return {}

        if not isinstance(raw, dict) or raw.get("version") != LEDGER_VERSION:
            return {}

        records: dict[str, ProviderRecord] = {}
        for name, fields in (raw.get("providers") or {}).items():
            try:
                records[name] = ProviderRecord(**fields)
            except TypeError:
                # One malformed entry does not discard the others.
                continue
        return records

    def names(self) -> tuple[str, ...]:
        """Every provider the ledger has an entry for."""
        return tuple(sorted(self._records))

    def get(self, name: str) -> ProviderRecord:
        """Return the record for ``name``.

        Raises ``KeyError`` when absent. Callers that want a default
        should ask ``is_fresh`` first, which answers False for an
        unknown provider.
        """
        return self._records[name]

    def record(self, entry: ProviderRecord) -> None:
        """Store one probe result, replacing any earlier entry."""
        self._records[entry.name] = entry

    def record_failure(self, name: str, error: str, now: float | None = None) -> None:
        """Note that a provider refused work, and clear its confirmation.

        Creating an entry for a never-probed provider is deliberate: a
        failure is information about this machine whether or not a probe
        preceded it.
        """
        stamp = time.time() if now is None else now
        existing = self._records.get(name)
        if existing is None:
            self._records[name] = ProviderRecord(
                name=name,
                binary=name,
                installed=False,
                version=None,
                auth_confirmed_at=None,
                recorded_at=stamp,
                last_error=error,
            )
            return
        self._records[name] = replace(
            existing, auth_confirmed_at=None, last_error=error, recorded_at=stamp
        )

    def is_fresh(self, name: str, now: float | None = None) -> bool:
        """Whether the installed facts for ``name`` are inside the TTL."""
        entry = self._records.get(name)
        if entry is None:
            return False
        stamp = time.time() if now is None else now
        return (stamp - entry.recorded_at) <= self.ttl_seconds

    def available(self, now: float | None = None) -> tuple[str, ...]:
        """Return the providers conjure can call right now.

        Three conditions, all required: the entry is inside its TTL, the
        binary was present when probed, and a credential was confirmed
        with no failure recorded since.
        """
        stamp = time.time() if now is None else now
        return tuple(
            sorted(
                name
                for name, entry in self._records.items()
                if entry.installed
                and entry.auth_confirmed_at is not None
                and entry.last_error is None
                and self.is_fresh(name, now=stamp)
            )
        )

    def save(self) -> None:
        """Write the ledger, creating its directory if needed.

        Written to a sibling temporary file and renamed, so an
        interrupted write leaves the previous ledger intact instead of a
        truncated one. No permission is set: the file holds binary names,
        versions and timestamps, and nothing that would be a secret if
        read.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": LEDGER_VERSION,
            "providers": {
                name: asdict(entry) for name, entry in sorted(self._records.items())
            },
        }
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
