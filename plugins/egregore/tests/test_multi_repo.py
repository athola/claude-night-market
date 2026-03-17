"""Tests for egregore multi-repository support."""

from __future__ import annotations

import json
from pathlib import Path

from multi_repo import (
    CrossRepoDependency,
    MultiRepoManifest,
    RepoConfig,
    load_multi_repo_manifest,
    save_multi_repo_manifest,
)


class TestRepoConfig:
    """Feature: Repository configuration.

    As an egregore operator
    I want to configure individual repositories
    So that multi-repo projects can be orchestrated.
    """

    def test_create_repo_config_with_defaults(self) -> None:
        """Scenario: Create a repo config with minimal fields.

        Given a repository name and path
        When I create a RepoConfig
        Then it has sensible defaults for branch and labels.
        """
        repo = RepoConfig(name="frontend", path="/repos/frontend")
        assert repo.name == "frontend"
        assert repo.path == "/repos/frontend"
        assert repo.default_branch == "master"
        assert repo.labels == []

    def test_create_repo_config_with_custom_values(self) -> None:
        """Scenario: Create a repo config with all fields specified.

        Given custom values for all fields
        When I create a RepoConfig
        Then all values are preserved.
        """
        repo = RepoConfig(
            name="api",
            path="/repos/api",
            default_branch="main",
            labels=["bug", "enhancement"],
        )
        assert repo.name == "api"
        assert repo.path == "/repos/api"
        assert repo.default_branch == "main"
        assert repo.labels == ["bug", "enhancement"]

    def test_to_dict_serialization(self) -> None:
        """Scenario: Serialize a RepoConfig to dict.

        Given a RepoConfig with labels
        When I call to_dict
        Then the output is a plain dictionary with all fields.
        """
        repo = RepoConfig(
            name="lib",
            path="/repos/lib",
            default_branch="main",
            labels=["core"],
        )
        d = repo.to_dict()
        assert d == {
            "name": "lib",
            "path": "/repos/lib",
            "default_branch": "main",
            "labels": ["core"],
        }

    def test_from_dict_deserialization(self) -> None:
        """Scenario: Deserialize a RepoConfig from dict.

        Given a dictionary with repo config data
        When I call from_dict
        Then a RepoConfig is created with matching fields.
        """
        data = {
            "name": "backend",
            "path": "/repos/backend",
            "default_branch": "develop",
            "labels": ["api", "v2"],
        }
        repo = RepoConfig.from_dict(data)
        assert repo.name == "backend"
        assert repo.path == "/repos/backend"
        assert repo.default_branch == "develop"
        assert repo.labels == ["api", "v2"]

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Scenario: Deserialize ignores extra keys.

        Given a dictionary with unknown extra fields
        When I call from_dict
        Then only known fields are used (no TypeError).
        """
        data = {
            "name": "x",
            "path": "/x",
            "unknown_field": "should be ignored",
        }
        repo = RepoConfig.from_dict(data)
        assert repo.name == "x"
        assert repo.path == "/x"

    def test_to_dict_roundtrip(self) -> None:
        """Scenario: Roundtrip through dict preserves all data.

        Given a fully populated RepoConfig
        When I serialize and deserialize
        Then the result matches the original.
        """
        original = RepoConfig(
            name="mono",
            path="/repos/mono",
            default_branch="trunk",
            labels=["infra", "deploy"],
        )
        restored = RepoConfig.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.path == original.path
        assert restored.default_branch == original.default_branch
        assert restored.labels == original.labels


class TestCrossRepoDependency:
    """Feature: Cross-repository dependency tracking.

    As an egregore operator
    I want to define dependencies between work items in different repos
    So that coordinated work proceeds in the right order.
    """

    def test_create_dependency_with_defaults(self) -> None:
        """Scenario: Create a dependency with default type.

        Given source and target item/repo pairs
        When I create a CrossRepoDependency
        Then the default type is 'blocks'.
        """
        dep = CrossRepoDependency(
            source_item_id="wrk_001",
            source_repo="api",
            target_item_id="wrk_003",
            target_repo="frontend",
        )
        assert dep.source_item_id == "wrk_001"
        assert dep.source_repo == "api"
        assert dep.target_item_id == "wrk_003"
        assert dep.target_repo == "frontend"
        assert dep.dependency_type == "blocks"

    def test_create_dependency_with_custom_type(self) -> None:
        """Scenario: Create a dependency with explicit type.

        Given a 'relates_to' dependency type
        When I create a CrossRepoDependency
        Then the custom type is stored.
        """
        dep = CrossRepoDependency(
            source_item_id="wrk_002",
            source_repo="lib",
            target_item_id="wrk_005",
            target_repo="app",
            dependency_type="relates_to",
        )
        assert dep.dependency_type == "relates_to"

    def test_to_dict_serialization(self) -> None:
        """Scenario: Serialize a dependency to dict.

        Given a CrossRepoDependency
        When I call to_dict
        Then the output contains all fields.
        """
        dep = CrossRepoDependency(
            source_item_id="wrk_001",
            source_repo="api",
            target_item_id="wrk_002",
            target_repo="web",
            dependency_type="triggers",
        )
        d = dep.to_dict()
        assert d == {
            "source_item_id": "wrk_001",
            "source_repo": "api",
            "target_item_id": "wrk_002",
            "target_repo": "web",
            "dependency_type": "triggers",
        }

    def test_from_dict_deserialization(self) -> None:
        """Scenario: Deserialize a dependency from dict.

        Given a dictionary with dependency data
        When I call from_dict
        Then a CrossRepoDependency is created with matching fields.
        """
        data = {
            "source_item_id": "wrk_010",
            "source_repo": "core",
            "target_item_id": "wrk_020",
            "target_repo": "ui",
            "dependency_type": "blocks",
        }
        dep = CrossRepoDependency.from_dict(data)
        assert dep.source_item_id == "wrk_010"
        assert dep.target_repo == "ui"
        assert dep.dependency_type == "blocks"

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Scenario: Deserialize ignores extra keys.

        Given a dictionary with unknown fields
        When I call from_dict
        Then only known fields are used.
        """
        data = {
            "source_item_id": "wrk_001",
            "source_repo": "a",
            "target_item_id": "wrk_002",
            "target_repo": "b",
            "extra": "ignored",
        }
        dep = CrossRepoDependency.from_dict(data)
        assert dep.source_item_id == "wrk_001"

    def test_to_dict_roundtrip(self) -> None:
        """Scenario: Roundtrip through dict preserves all data.

        Given a CrossRepoDependency
        When I serialize and deserialize
        Then the result matches the original.
        """
        original = CrossRepoDependency(
            source_item_id="wrk_001",
            source_repo="api",
            target_item_id="wrk_003",
            target_repo="web",
            dependency_type="triggers",
        )
        restored = CrossRepoDependency.from_dict(original.to_dict())
        assert restored.source_item_id == original.source_item_id
        assert restored.source_repo == original.source_repo
        assert restored.target_item_id == original.target_item_id
        assert restored.target_repo == original.target_repo
        assert restored.dependency_type == original.dependency_type


class TestMultiRepoManifest:
    """Feature: Multi-repo manifest orchestration.

    As an egregore operator
    I want a manifest that tracks multiple repos and their dependencies
    So that cross-repo projects can be coordinated.
    """

    def test_empty_manifest(self) -> None:
        """Scenario: Create an empty multi-repo manifest.

        Given no arguments
        When I create a MultiRepoManifest
        Then it has empty repos and deps lists.
        """
        manifest = MultiRepoManifest()
        assert manifest.repos == []
        assert manifest.cross_repo_deps == []

    def test_add_repo(self) -> None:
        """Scenario: Add a repository to the manifest.

        Given an empty manifest
        When I add a repo with name and path
        Then the repo appears in the manifest repos list.
        """
        manifest = MultiRepoManifest()
        repo = manifest.add_repo("frontend", "/repos/frontend")
        assert repo.name == "frontend"
        assert repo.path == "/repos/frontend"
        assert repo.default_branch == "master"
        assert len(manifest.repos) == 1

    def test_add_repo_with_custom_branch(self) -> None:
        """Scenario: Add a repo with a custom default branch.

        Given an empty manifest
        When I add a repo with default_branch='main'
        Then the repo stores the custom branch.
        """
        manifest = MultiRepoManifest()
        repo = manifest.add_repo("api", "/repos/api", default_branch="main")
        assert repo.default_branch == "main"

    def test_add_multiple_repos(self) -> None:
        """Scenario: Add several repos.

        Given an empty manifest
        When I add three repos
        Then all three appear in the repos list.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("a", "/a")
        manifest.add_repo("b", "/b")
        manifest.add_repo("c", "/c")
        assert len(manifest.repos) == 3

    def test_get_repo_found(self) -> None:
        """Scenario: Look up a repo by name.

        Given a manifest with two repos
        When I look up by name
        Then the correct repo is returned.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api")
        manifest.add_repo("web", "/repos/web")
        result = manifest.get_repo("web")
        assert result is not None
        assert result.name == "web"
        assert result.path == "/repos/web"

    def test_get_repo_not_found(self) -> None:
        """Scenario: Look up a non-existent repo.

        Given a manifest with repos
        When I look up a name that does not exist
        Then None is returned.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api")
        result = manifest.get_repo("nonexistent")
        assert result is None

    def test_add_dependency(self) -> None:
        """Scenario: Add a cross-repo dependency.

        Given a manifest
        When I add a dependency between items in two repos
        Then the dependency appears in the cross_repo_deps list.
        """
        manifest = MultiRepoManifest()
        dep = manifest.add_dependency(
            source_item="wrk_001",
            source_repo="api",
            target_item="wrk_002",
            target_repo="web",
        )
        assert dep.source_item_id == "wrk_001"
        assert dep.source_repo == "api"
        assert dep.target_item_id == "wrk_002"
        assert dep.target_repo == "web"
        assert dep.dependency_type == "blocks"
        assert len(manifest.cross_repo_deps) == 1

    def test_add_dependency_custom_type(self) -> None:
        """Scenario: Add a dependency with custom type.

        Given a manifest
        When I add a 'relates_to' dependency
        Then the custom type is stored.
        """
        manifest = MultiRepoManifest()
        dep = manifest.add_dependency(
            source_item="wrk_001",
            source_repo="a",
            target_item="wrk_002",
            target_repo="b",
            dep_type="relates_to",
        )
        assert dep.dependency_type == "relates_to"

    def test_get_blocking_deps(self) -> None:
        """Scenario: Retrieve blocking dependencies for a work item.

        Given a manifest with mixed dependency types
        When I query blocking deps for a specific item
        Then only 'blocks' dependencies targeting that item are returned.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        manifest.add_dependency(
            "wrk_002",
            "api",
            "wrk_010",
            "web",
            dep_type="relates_to",
        )
        manifest.add_dependency("wrk_003", "lib", "wrk_010", "web")
        manifest.add_dependency("wrk_004", "api", "wrk_099", "web")

        blocking = manifest.get_blocking_deps("wrk_010", "web")
        assert len(blocking) == 2
        source_ids = {d.source_item_id for d in blocking}
        assert source_ids == {"wrk_001", "wrk_003"}

    def test_get_blocking_deps_empty(self) -> None:
        """Scenario: No blocking deps for an item.

        Given a manifest with no relevant dependencies
        When I query blocking deps for an item
        Then an empty list is returned.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        blocking = manifest.get_blocking_deps("wrk_099", "other")
        assert blocking == []

    def test_is_item_blocked_true(self) -> None:
        """Scenario: Item is blocked by an incomplete dependency.

        Given a blocking dependency where the source is not completed
        When I check if the target item is blocked
        Then it returns True.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        completed: set[str] = set()
        assert manifest.is_item_blocked("wrk_010", "web", completed) is True

    def test_is_item_blocked_false_when_source_completed(self) -> None:
        """Scenario: Item is unblocked when source is completed.

        Given a blocking dependency where the source IS completed
        When I check if the target item is blocked
        Then it returns False.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        completed = {"api:wrk_001"}
        assert manifest.is_item_blocked("wrk_010", "web", completed) is False

    def test_is_item_blocked_false_when_no_deps(self) -> None:
        """Scenario: Item with no dependencies is never blocked.

        Given a manifest with no deps for the queried item
        When I check if it is blocked
        Then it returns False.
        """
        manifest = MultiRepoManifest()
        completed: set[str] = set()
        assert manifest.is_item_blocked("wrk_099", "web", completed) is False

    def test_is_item_blocked_partial_completion(self) -> None:
        """Scenario: Item is blocked when only some deps are completed.

        Given two blocking deps where only one source is completed
        When I check if the target is blocked
        Then it returns True.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        manifest.add_dependency("wrk_002", "lib", "wrk_010", "web")
        completed = {"api:wrk_001"}
        assert manifest.is_item_blocked("wrk_010", "web", completed) is True

    def test_is_item_blocked_all_completed(self) -> None:
        """Scenario: Item is unblocked when all deps are completed.

        Given two blocking deps where both sources are completed
        When I check if the target is blocked
        Then it returns False.
        """
        manifest = MultiRepoManifest()
        manifest.add_dependency("wrk_001", "api", "wrk_010", "web")
        manifest.add_dependency("wrk_002", "lib", "wrk_010", "web")
        completed = {"api:wrk_001", "lib:wrk_002"}
        assert manifest.is_item_blocked("wrk_010", "web", completed) is False

    def test_to_dict_serialization(self) -> None:
        """Scenario: Serialize a full manifest to dict.

        Given a manifest with repos and dependencies
        When I call to_dict
        Then the output contains all data.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api", default_branch="main")
        manifest.add_repo("web", "/repos/web")
        manifest.add_dependency("wrk_001", "api", "wrk_002", "web")

        d = manifest.to_dict()
        assert len(d["repos"]) == 2
        assert len(d["cross_repo_deps"]) == 1
        assert d["repos"][0]["name"] == "api"
        assert d["repos"][0]["default_branch"] == "main"
        assert d["cross_repo_deps"][0]["source_item_id"] == "wrk_001"

    def test_from_dict_deserialization(self) -> None:
        """Scenario: Deserialize a manifest from dict.

        Given a dictionary with repos and deps data
        When I call from_dict
        Then the manifest is populated correctly.
        """
        data = {
            "repos": [
                {"name": "api", "path": "/repos/api"},
                {"name": "web", "path": "/repos/web", "default_branch": "main"},
            ],
            "cross_repo_deps": [
                {
                    "source_item_id": "wrk_001",
                    "source_repo": "api",
                    "target_item_id": "wrk_002",
                    "target_repo": "web",
                    "dependency_type": "blocks",
                },
            ],
        }
        manifest = MultiRepoManifest.from_dict(data)
        assert len(manifest.repos) == 2
        assert manifest.repos[1].default_branch == "main"
        assert len(manifest.cross_repo_deps) == 1
        assert manifest.cross_repo_deps[0].source_item_id == "wrk_001"

    def test_to_dict_roundtrip(self) -> None:
        """Scenario: Roundtrip through dict preserves all data.

        Given a manifest with repos and dependencies
        When I serialize and deserialize
        Then the restored manifest matches the original.
        """
        original = MultiRepoManifest()
        original.add_repo("api", "/repos/api", default_branch="main")
        original.add_repo("web", "/repos/web")
        original.add_dependency("wrk_001", "api", "wrk_002", "web")
        original.add_dependency(
            "wrk_003",
            "api",
            "wrk_004",
            "web",
            dep_type="triggers",
        )

        restored = MultiRepoManifest.from_dict(original.to_dict())
        assert len(restored.repos) == 2
        assert restored.repos[0].name == "api"
        assert restored.repos[0].default_branch == "main"
        assert restored.repos[1].name == "web"
        assert len(restored.cross_repo_deps) == 2
        assert restored.cross_repo_deps[1].dependency_type == "triggers"


class TestSaveLoadMultiRepoManifest:
    """Feature: Persistence for multi-repo manifests.

    As an egregore operator
    I want to save and load multi-repo manifests from disk
    So that state persists across sessions.
    """

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Scenario: Save creates the manifest file.

        Given a multi-repo manifest
        When I save it to a path
        Then the file exists on disk.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api")
        path = tmp_path / "multi_repo.json"
        save_multi_repo_manifest(manifest, path)
        assert path.exists()

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Scenario: Save creates parent directories.

        Given a path with non-existent parent dirs
        When I save a manifest
        Then parent directories are created automatically.
        """
        manifest = MultiRepoManifest()
        path = tmp_path / "a" / "b" / "manifest.json"
        save_multi_repo_manifest(manifest, path)
        assert path.exists()

    def test_save_produces_valid_json(self, tmp_path: Path) -> None:
        """Scenario: Saved file contains valid JSON.

        Given a manifest with data
        When I save and read the file
        Then the content parses as valid JSON.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api")
        manifest.add_dependency("wrk_001", "api", "wrk_002", "web")
        path = tmp_path / "manifest.json"
        save_multi_repo_manifest(manifest, path)

        data = json.loads(path.read_text())
        assert "repos" in data
        assert "cross_repo_deps" in data

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """Scenario: Full save/load roundtrip preserves data.

        Given a manifest with repos and dependencies
        When I save and load it
        Then all data is preserved.
        """
        manifest = MultiRepoManifest()
        manifest.add_repo("api", "/repos/api", default_branch="main")
        manifest.add_repo("web", "/repos/web")
        manifest.add_dependency("wrk_001", "api", "wrk_002", "web")

        path = tmp_path / "manifest.json"
        save_multi_repo_manifest(manifest, path)
        loaded = load_multi_repo_manifest(path)

        assert len(loaded.repos) == 2
        assert loaded.repos[0].name == "api"
        assert loaded.repos[0].default_branch == "main"
        assert len(loaded.cross_repo_deps) == 1
        assert loaded.cross_repo_deps[0].source_item_id == "wrk_001"

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Loading a non-existent file returns empty manifest.

        Given a path that does not exist
        When I load a multi-repo manifest
        Then an empty manifest is returned.
        """
        path = tmp_path / "nonexistent.json"
        loaded = load_multi_repo_manifest(path)
        assert loaded.repos == []
        assert loaded.cross_repo_deps == []

    def test_load_invalid_json_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Loading invalid JSON returns empty manifest.

        Given a file with invalid JSON content
        When I load a multi-repo manifest
        Then an empty manifest is returned.
        """
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        loaded = load_multi_repo_manifest(path)
        assert loaded.repos == []
        assert loaded.cross_repo_deps == []
