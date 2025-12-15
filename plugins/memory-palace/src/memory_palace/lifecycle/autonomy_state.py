"""Autonomy state management for Memory Palace governance loops."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

AUTONOMY_STATE_ENV_VAR = "MEMORY_PALACE_AUTONOMY_STATE"
_MIN_LEVEL = 0
_MAX_LEVEL = 5
_LEVEL_PARTIAL = 2
_LEVEL_ALL = 3


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_domain(domain: str) -> str:
    return domain.strip().lower()


@dataclass(slots=True)
class PerformanceMetrics:
    """Lightweight counters describing recent governance outcomes."""

    auto_approvals: int = 0
    flagged_requests: int = 0
    blocked_requests: int = 0
    promotions: int = 0
    demotions: int = 0
    last_decision: str | None = None
    last_domains: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to a dictionary."""
        return {
            "auto_approvals": self.auto_approvals,
            "flagged_requests": self.flagged_requests,
            "blocked_requests": self.blocked_requests,
            "promotions": self.promotions,
            "demotions": self.demotions,
            "last_decision": self.last_decision,
            "last_domains": self.last_domains,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> PerformanceMetrics:
        """Rehydrate metrics from a mapping."""
        if not data:
            return cls()
        return cls(
            auto_approvals=int(data.get("auto_approvals", 0) or 0),
            flagged_requests=int(data.get("flagged_requests", 0) or 0),
            blocked_requests=int(data.get("blocked_requests", 0) or 0),
            promotions=int(data.get("promotions", 0) or 0),
            demotions=int(data.get("demotions", 0) or 0),
            last_decision=data.get("last_decision"),
            last_domains=list(data.get("last_domains", []) or []),
        )


@dataclass(slots=True)
class DomainControl:
    """Per-domain override indicating custom autonomy expectations."""

    level: int
    locked: bool = False
    reason: str | None = None
    updated_at: str = field(default_factory=_iso_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize domain control to a dictionary."""
        return {
            "level": self.level,
            "locked": self.locked,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> DomainControl | None:
        """Rehydrate domain control from mapping data."""
        if not data:
            return None
        level = int(data.get("level", 0) or 0)
        return cls(
            level=max(_MIN_LEVEL, min(level, _MAX_LEVEL)),
            locked=bool(data.get("locked", False)),
            reason=data.get("reason"),
            updated_at=str(data.get("updated_at") or _iso_now()),
        )


@dataclass(slots=True)
class AutonomyState:
    """Persistent snapshot of the autonomy lifecycle."""

    current_level: int = 0
    domain_controls: dict[str, DomainControl] = field(default_factory=dict)
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    last_updated: str = field(default_factory=_iso_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize autonomy state to a dictionary."""
        return {
            "current_level": self.current_level,
            "domain_controls": {
                domain: control.to_dict()
                for domain, control in self.domain_controls.items()
            },
            "metrics": self.metrics.to_dict(),
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> AutonomyState:
        """Rehydrate autonomy state from mapping data."""
        if not data:
            return cls()
        controls: dict[str, DomainControl] = {}
        raw_controls = data.get("domain_controls", {}) or {}
        for domain, control_data in raw_controls.items():
            control = DomainControl.from_dict(control_data)
            if control:
                controls[_normalize_domain(domain)] = control
        level = int(data.get("current_level", 0) or 0)
        return cls(
            current_level=max(_MIN_LEVEL, min(level, _MAX_LEVEL)),
            domain_controls=controls,
            metrics=PerformanceMetrics.from_dict(data.get("metrics")),
            last_updated=str(data.get("last_updated") or _iso_now()),
        )


@dataclass(slots=True)
class AutonomyProfile:
    """Computed profile combining config defaults with persisted state."""

    global_level: int
    domain_controls: dict[str, DomainControl] = field(default_factory=dict)

    def effective_level_for(self, domains: Iterable[str] | None = None) -> int:
        """Return effective autonomy level considering domain overrides."""
        level = max(_MIN_LEVEL, min(self.global_level, _MAX_LEVEL))
        if not domains:
            return level

        normalized = [_normalize_domain(domain) for domain in domains if domain]
        locked_levels: list[int] = []
        for domain in normalized:
            control = self.domain_controls.get(domain)
            if not control:
                continue
            if control.locked:
                locked_levels.append(control.level)
            else:
                level = max(level, control.level)
        if locked_levels:
            return max(_MIN_LEVEL, min(*locked_levels, _MAX_LEVEL))
        return max(_MIN_LEVEL, min(level, _MAX_LEVEL))

    def should_auto_approve_duplicates(
        self, domains: Iterable[str] | None = None
    ) -> bool:
        """Allow automatic duplicate approvals when level >=1."""
        return self.effective_level_for(domains) >= 1

    def should_auto_approve_partial(self, domains: Iterable[str] | None = None) -> bool:
        """Allow partial overlap approvals when level >=2."""
        return self.effective_level_for(domains) >= _LEVEL_PARTIAL

    def should_auto_approve_all(self, domains: Iterable[str] | None = None) -> bool:
        """Allow all approvals when level >=3."""
        return self.effective_level_for(domains) >= _LEVEL_ALL

    def describe(self) -> dict[str, Any]:
        """Return dictionary description of profile."""
        return {
            "global_level": self.global_level,
            "domain_controls": {
                domain: control.to_dict()
                for domain, control in self.domain_controls.items()
            },
        }


class AutonomyStateStore:
    """Read/write helper around the autonomy state YAML file."""

    def __init__(
        self,
        *,
        state_path: str | Path | None = None,
        plugin_root: Path | None = None,
    ) -> None:
        """Initialize state store with optional explicit path or env override."""
        env_override = os.environ.get(AUTONOMY_STATE_ENV_VAR)
        if state_path:
            resolved = Path(state_path)
        elif env_override:
            resolved = Path(env_override)
        else:
            resolved = self._default_state_path(plugin_root)
        self.state_path = resolved
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _default_state_path(plugin_root: Path | None) -> Path:
        """Return default state file path under plugin data directory."""
        if plugin_root is None:
            plugin_root = Path(__file__).resolve().parents[3]
        return plugin_root / "data" / "state" / "autonomy-state.yaml"

    @staticmethod
    def _clamp_level(level: int) -> int:
        """Clamp level within allowed bounds."""
        return max(_MIN_LEVEL, min(level, _MAX_LEVEL))

    def load(self) -> AutonomyState:
        """Load autonomy state from disk, creating default if missing."""
        if not self.state_path.exists():
            state = AutonomyState()
            self.save(state)
            return state
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError:
            data = {}
        except FileNotFoundError:
            data = {}
        return AutonomyState.from_dict(data)

    def save(self, state: AutonomyState) -> AutonomyState:
        """Persist autonomy state to disk."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(state.to_dict(), handle, sort_keys=False)
        return state

    def snapshot(self, *, config_level: int | None = None) -> dict[str, Any]:
        """Return a summary snapshot including effective levels and locks."""
        state = self.load()
        profile = self.build_profile(config_level=config_level)
        locked = {
            domain: ctrl.to_dict()
            for domain, ctrl in state.domain_controls.items()
            if ctrl.locked
        }
        return {
            "state_file": str(self.state_path),
            "current_level": state.current_level,
            "effective_level": profile.global_level,
            "domain_controls": {
                domain: ctrl.to_dict() for domain, ctrl in state.domain_controls.items()
            },
            "locked_domains": locked,
            "metrics": state.metrics.to_dict(),
            "last_updated": state.last_updated,
        }

    def set_level(
        self,
        level: int,
        *,
        domain: str | None = None,
        lock: bool | None = None,
        reason: str | None = None,
    ) -> AutonomyState:
        """Set global or domain-specific level and persist."""
        state = self.load()
        next_level = self._clamp_level(level)
        if domain:
            key = _normalize_domain(domain)
            control = state.domain_controls.get(key)
            if control is None:
                control = DomainControl(
                    level=next_level, locked=bool(lock), reason=reason
                )
            else:
                control.level = next_level
                if lock is not None:
                    control.locked = lock
                if reason is not None:
                    control.reason = reason
                control.updated_at = _iso_now()
            state.domain_controls[key] = control
        else:
            state.current_level = next_level
            if lock is not None and not domain:
                # Ignore lock toggles without domain context on global level
                pass
        state.last_updated = _iso_now()
        return self.save(state)

    def promote(self, *, domain: str | None = None) -> AutonomyState:
        """Promote global or domain level by one."""
        state = self.load()
        if domain:
            key = _normalize_domain(domain)
            control = state.domain_controls.get(key) or DomainControl(
                level=state.current_level
            )
            control.level = self._clamp_level(control.level + 1)
            control.updated_at = _iso_now()
            state.domain_controls[key] = control
        else:
            state.current_level = self._clamp_level(state.current_level + 1)
        state.metrics.promotions += 1
        state.last_updated = _iso_now()
        return self.save(state)

    def demote(self, *, domain: str | None = None) -> AutonomyState:
        """Demote global or domain level by one."""
        state = self.load()
        if domain:
            key = _normalize_domain(domain)
            control = state.domain_controls.get(key) or DomainControl(
                level=state.current_level
            )
            control.level = self._clamp_level(control.level - 1)
            control.updated_at = _iso_now()
            state.domain_controls[key] = control
        else:
            state.current_level = self._clamp_level(state.current_level - 1)
        state.metrics.demotions += 1
        state.last_updated = _iso_now()
        return self.save(state)

    def build_profile(self, *, config_level: int | None = None) -> AutonomyProfile:
        """Build an AutonomyProfile combining persisted state and optional config override."""
        state = self.load()
        base_level = state.current_level
        if config_level is not None:
            with contextlib.suppress(TypeError, ValueError):
                base_level = max(base_level, int(config_level))
        return AutonomyProfile(
            global_level=self._clamp_level(base_level),
            domain_controls=dict(state.domain_controls),
        )

    def record_decision(
        self,
        *,
        auto_approved: bool,
        flagged: bool,
        blocked: bool,
        domains: Iterable[str] | None = None,
    ) -> None:
        """Record a decision outcome and update metrics/timestamps."""
        try:
            state = self.load()
        except Exception:
            return
        metrics = state.metrics
        if auto_approved:
            metrics.auto_approvals += 1
            metrics.last_decision = "auto_approved"
        elif flagged:
            metrics.flagged_requests += 1
            metrics.last_decision = "flagged"
        elif blocked:
            metrics.blocked_requests += 1
            metrics.last_decision = "blocked"
        else:
            metrics.last_decision = "neutral"
        metrics.last_domains = [
            _normalize_domain(domain) for domain in (domains or []) if domain
        ]
        state.metrics = metrics
        state.last_updated = _iso_now()
        self.save(state)
