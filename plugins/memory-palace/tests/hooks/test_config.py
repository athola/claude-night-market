"""Tests for config module."""

from __future__ import annotations

import os
import sys

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../hooks'))

from shared.config import (
    CONFIG_DEFAULTS,
    get_config,
    is_knowledge_path,
    is_path_excluded,
    is_path_safe,
    should_process_path,
)


class TestConfigDefaults:
    """Tests for default configuration values."""

    def test_defaults_exist(self) -> None:
        """Default config should have required keys."""
        assert "enabled" in CONFIG_DEFAULTS
        assert "local_knowledge_paths" in CONFIG_DEFAULTS
        assert "exclude_patterns" in CONFIG_DEFAULTS
        assert "safety" in CONFIG_DEFAULTS

    def test_safety_defaults(self) -> None:
        """Safety settings should have sensible defaults."""
        safety = CONFIG_DEFAULTS["safety"]
        assert safety["max_content_size_kb"] > 0
        assert safety["max_line_length"] > 0
        assert safety["parsing_timeout_ms"] > 0


class TestGetConfig:
    """Tests for config loading."""

    def test_returns_dict(self) -> None:
        """Config should return a dictionary."""
        config = get_config()
        assert isinstance(config, dict)

    def test_has_required_keys(self) -> None:
        """Config should have all required keys."""
        config = get_config()
        assert "enabled" in config
        assert "local_knowledge_paths" in config
        assert "safety" in config


class TestIsPathExcluded:
    """Tests for path exclusion logic."""

    def test_git_excluded(self) -> None:
        """Git directories should be excluded."""
        assert is_path_excluded(".git/config") is True
        assert is_path_excluded("project/.git/HEAD") is True

    def test_node_modules_excluded(self) -> None:
        """node_modules should be excluded."""
        assert is_path_excluded("node_modules/package/index.js") is True

    def test_venv_excluded(self) -> None:
        """Virtual environments should be excluded."""
        assert is_path_excluded(".venv/lib/python3.11/site.py") is True
        assert is_path_excluded("venv/bin/activate") is True

    def test_env_files_excluded(self) -> None:
        """Environment files should be excluded."""
        assert is_path_excluded(".env") is True
        assert is_path_excluded(".env.local") is True

    def test_lock_files_excluded(self) -> None:
        """Lock files should be excluded."""
        assert is_path_excluded("package-lock.json") is True
        assert is_path_excluded("uv.lock") is True
        assert is_path_excluded("poetry.lock") is True

    def test_normal_paths_not_excluded(self) -> None:
        """Normal paths should not be excluded."""
        assert is_path_excluded("docs/readme.md") is False
        assert is_path_excluded("src/main.py") is False


class TestIsKnowledgePath:
    """Tests for knowledge path detection."""

    def test_docs_is_knowledge(self) -> None:
        """docs/ should be a knowledge path."""
        assert is_knowledge_path("docs/guide.md") is True
        assert is_knowledge_path("docs/api/reference.md") is True

    def test_knowledge_corpus_is_knowledge(self) -> None:
        """knowledge-corpus/ should be a knowledge path."""
        assert is_knowledge_path("knowledge-corpus/article.md") is True

    def test_references_is_knowledge(self) -> None:
        """references/ should be a knowledge path."""
        assert is_knowledge_path("references/paper.md") is True

    def test_src_not_knowledge(self) -> None:
        """src/ should not be a knowledge path."""
        assert is_knowledge_path("src/main.py") is False

    def test_random_files_not_knowledge(self) -> None:
        """Random files should not be knowledge paths."""
        assert is_knowledge_path("README.md") is False
        assert is_knowledge_path("config.yaml") is False


class TestIsPathSafe:
    """Tests for path traversal validation."""

    def test_normal_path_safe(self) -> None:
        """Normal paths should be safe."""
        assert is_path_safe("/home/user/docs/file.md") is True
        assert is_path_safe("docs/guide.md") is True

    def test_traversal_unsafe(self) -> None:
        """Path traversal attempts should be unsafe."""
        assert is_path_safe("../../../etc/passwd") is False
        assert is_path_safe("docs/../../../etc/passwd") is False

    def test_sensitive_paths_unsafe(self) -> None:
        """Sensitive system paths should be unsafe."""
        assert is_path_safe("/etc/passwd") is False
        assert is_path_safe("/root/.bashrc") is False
        assert is_path_safe("/var/log/syslog") is False


class TestShouldProcessPath:
    """Tests for combined processing decision."""

    def test_knowledge_path_processed(self) -> None:
        """Knowledge paths should be processed."""
        assert should_process_path("docs/guide.md") is True

    def test_excluded_not_processed(self) -> None:
        """Excluded paths should not be processed."""
        assert should_process_path(".git/config") is False
        assert should_process_path("node_modules/readme.md") is False

    def test_non_knowledge_not_processed(self) -> None:
        """Non-knowledge paths should not be processed."""
        assert should_process_path("src/main.py") is False

    def test_traversal_not_processed(self) -> None:
        """Path traversal should not be processed."""
        assert should_process_path("docs/../../etc/passwd") is False

    def test_excluded_knowledge_not_processed(self) -> None:
        """Excluded paths in knowledge dirs should not be processed."""
        # If there was a .env in docs, it should still be excluded
        assert should_process_path("docs/.env") is False
