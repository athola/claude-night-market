"""Multi-repository support for egregore orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RepoConfig:
    """Configuration for a single repository in a multi-repo setup."""

    name: str
    path: str
    default_branch: str = "master"
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "default_branch": self.default_branch,
            "labels": list(self.labels),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoConfig:
        """Deserialize from a plain dictionary."""
        known = {"name", "path", "default_branch", "labels"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class CrossRepoDependency:
    """A dependency between work items across repositories."""

    source_item_id: str
    source_repo: str
    target_item_id: str
    target_repo: str
    dependency_type: str = "blocks"  # blocks, relates_to, triggers

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "source_item_id": self.source_item_id,
            "source_repo": self.source_repo,
            "target_item_id": self.target_item_id,
            "target_repo": self.target_repo,
            "dependency_type": self.dependency_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrossRepoDependency:
        """Deserialize from a plain dictionary."""
        known = {
            "source_item_id",
            "source_repo",
            "target_item_id",
            "target_repo",
            "dependency_type",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class MultiRepoManifest:
    """Extended manifest supporting multiple repositories."""

    repos: list[RepoConfig] = field(default_factory=list)
    cross_repo_deps: list[CrossRepoDependency] = field(default_factory=list)

    def add_repo(
        self,
        name: str,
        path: str,
        default_branch: str = "master",
    ) -> RepoConfig:
        """Add a repository to the multi-repo manifest."""
        repo = RepoConfig(name=name, path=path, default_branch=default_branch)
        self.repos.append(repo)
        return repo

    def get_repo(self, name: str) -> RepoConfig | None:
        """Look up a repo by name."""
        for repo in self.repos:
            if repo.name == name:
                return repo
        return None

    def add_dependency(
        self,
        source_item: str,
        source_repo: str,
        target_item: str,
        target_repo: str,
        dep_type: str = "blocks",
    ) -> CrossRepoDependency:
        """Add a cross-repo dependency."""
        dep = CrossRepoDependency(
            source_item_id=source_item,
            source_repo=source_repo,
            target_item_id=target_item,
            target_repo=target_repo,
            dependency_type=dep_type,
        )
        self.cross_repo_deps.append(dep)
        return dep

    def get_blocking_deps(
        self,
        item_id: str,
        repo_name: str,
    ) -> list[CrossRepoDependency]:
        """Get dependencies that block a specific work item."""
        return [
            dep
            for dep in self.cross_repo_deps
            if dep.target_item_id == item_id
            and dep.target_repo == repo_name
            and dep.dependency_type == "blocks"
        ]

    def is_item_blocked(
        self,
        item_id: str,
        repo_name: str,
        completed_items: set[str],
    ) -> bool:
        """Check if a work item is blocked by unresolved cross-repo deps."""
        blocking = self.get_blocking_deps(item_id, repo_name)
        for dep in blocking:
            key = f"{dep.source_repo}:{dep.source_item_id}"
            if key not in completed_items:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire manifest to a plain dictionary."""
        return {
            "repos": [r.to_dict() for r in self.repos],
            "cross_repo_deps": [d.to_dict() for d in self.cross_repo_deps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MultiRepoManifest:
        """Deserialize from a plain dictionary."""
        manifest = cls()
        manifest.repos = [RepoConfig.from_dict(r) for r in data.get("repos", [])]
        manifest.cross_repo_deps = [
            CrossRepoDependency.from_dict(d) for d in data.get("cross_repo_deps", [])
        ]
        return manifest


def save_multi_repo_manifest(manifest: MultiRepoManifest, path: Path) -> None:
    """Save multi-repo manifest to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n")


def load_multi_repo_manifest(path: Path) -> MultiRepoManifest:
    """Load multi-repo manifest from JSON.

    Returns an empty manifest if the file does not exist or is invalid.
    """
    if not path.exists():
        return MultiRepoManifest()
    try:
        data = json.loads(path.read_text())
        return MultiRepoManifest.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return MultiRepoManifest()
