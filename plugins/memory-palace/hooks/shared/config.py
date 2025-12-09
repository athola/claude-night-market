"""Configuration management for memory-palace hooks.

Optimized for speed with singleton caching and lazy loading.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Singleton cache
_config_cache: dict[str, Any] | None = None
_config_mtime: float = 0

CONFIG_DEFAULTS: dict[str, Any] = {
    "enabled": True,
    # Research interception mode
    # - cache_only: Never hit web, use local knowledge
    # - cache_first: Check cache, fall back to web (default)
    # - augment: Always combine cache + web
    # - web_only: Skip cache, use web (current behavior)
    "research_mode": "cache_first",
    "local_knowledge_paths": [
        "docs/",
        "knowledge-corpus/",
        "references/",
    ],
    "exclude_patterns": [
        # Version control
        ".git/",
        ".gitignore",
        ".gitattributes",
        ".gitmodules",
        # Dependencies & builds
        "node_modules/",
        "__pycache__/",
        ".venv/",
        "venv/",
        ".uv-cache/",
        "dist/",
        "build/",
        "target/",
        "*.egg-info/",
        # IDE & editor
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        # Test artifacts
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        # Lock files
        "*.lock",
        "package-lock.json",
        "yarn.lock",
        "uv.lock",
        # Secrets & env
        ".env",
        ".env.*",
        "*.pem",
        "*.key",
        "credentials.*",
        "secrets.*",
        # Generated docs
        "_build/",
        "site/",
        ".docusaurus/",
    ],
    "respect_gitignore": True,
    "safety": {
        "max_content_size_kb": 500,
        "max_line_length": 10000,
        "max_lines": 50000,
        "detect_repetition_bombs": True,
        "repetition_threshold": 0.95,
        "detect_unicode_bombs": True,
        "max_combining_chars": 10,
        "block_bidi_override": True,
        "parsing_timeout_ms": 5000,
    },
    "index_file": "memory-palace-index.yaml",
    "indexes_dir": "data/indexes",
    "corpus_dir": "docs/knowledge-corpus/",
    "embedding_provider": "none",  # none|local|api
    # New governance + lifecycle controls
    "autonomy_level": 0,
    "intake_threshold": 70,
    "domains_of_interest": [],
    "tending_frequency": "weekly",
    "telemetry": {
        "enabled": True,
        "file": "data/telemetry/memory-palace.csv",
    },
    "feature_flags": {
        "cache_intercept": True,
        "autonomy": True,
        "lifecycle": True,
    },
}


def _get_config_path() -> Path:
    """Get path to config file."""
    plugin_root = Path(__file__).parent.parent
    return plugin_root / "memory-palace-config.yaml"


def get_config() -> dict[str, Any]:
    """Get configuration with caching.

    Reloads only if file modification time changed.
    Falls back to defaults if file doesn't exist.
    """
    global _config_cache, _config_mtime

    config_path = _get_config_path()

    try:
        current_mtime = config_path.stat().st_mtime
        if _config_cache is not None and current_mtime <= _config_mtime:
            return _config_cache

        # Lazy import yaml only when needed
        import yaml

        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}

        # Merge with defaults
        _config_cache = {**CONFIG_DEFAULTS, **user_config}

        # Deep merge nested sections
        if "safety" in user_config:
            _config_cache["safety"] = {**CONFIG_DEFAULTS["safety"], **user_config["safety"]}

        if "telemetry" in user_config:
            _config_cache["telemetry"] = {
                **CONFIG_DEFAULTS["telemetry"],
                **user_config["telemetry"],
            }

        if "feature_flags" in user_config:
            _config_cache["feature_flags"] = {
                **CONFIG_DEFAULTS["feature_flags"],
                **user_config["feature_flags"],
            }

        if "embedding_provider" in user_config:
            _config_cache["embedding_provider"] = user_config["embedding_provider"]

        _config_mtime = current_mtime
        return _config_cache

    except FileNotFoundError:
        if _config_cache is None:
            _config_cache = CONFIG_DEFAULTS.copy()
        return _config_cache
    except Exception:
        # On any error, use defaults
        if _config_cache is None:
            _config_cache = CONFIG_DEFAULTS.copy()
        return _config_cache


def is_path_excluded(path: str) -> bool:
    """Fast check if path matches exclusion patterns."""
    config = get_config()
    path_lower = path.lower()

    for pattern in config["exclude_patterns"]:
        pattern_lower = pattern.lower()

        # Directory pattern (ends with /)
        if pattern_lower.endswith("/"):
            if f"/{pattern_lower}" in f"/{path_lower}/" or path_lower.startswith(pattern_lower):
                return True
        # Wildcard pattern
        elif pattern_lower.startswith("*"):
            if path_lower.endswith(pattern_lower[1:]):
                return True
        # Exact match
        elif pattern_lower in path_lower:
            return True

    return False


def is_knowledge_path(path: str) -> bool:
    """Check if path is in configured knowledge paths."""
    config = get_config()
    path_lower = path.lower()

    for knowledge_path in config["local_knowledge_paths"]:
        knowledge_lower = knowledge_path.lower()

        # Directory pattern
        if knowledge_lower.endswith("/"):
            if path_lower.startswith(knowledge_lower) or f"/{knowledge_lower}" in f"/{path_lower}":
                return True
        # Wildcard pattern
        elif knowledge_lower.startswith("*"):
            if path_lower.endswith(knowledge_lower[1:]):
                return True
        # Exact match
        elif path_lower == knowledge_lower:
            return True

    return False


def is_path_safe(path: str) -> bool:
    """Check if path is safe (no traversal attacks).

    Validates that path doesn't escape expected boundaries.
    """
    try:
        # Resolve to absolute path
        resolved = Path(path).resolve()

        # Check for path traversal indicators
        path_str = str(resolved)
        if ".." in path or path_str != os.path.normpath(path_str):
            return False

        # Ensure path doesn't escape to sensitive locations
        sensitive_paths = ["/etc/", "/root/", "/var/log/", "/.ssh/"]
        return all(not path_str.startswith(sensitive) for sensitive in sensitive_paths)
    except (ValueError, OSError):
        return False


def should_process_path(path: str) -> bool:
    """Determine if a path should be processed for knowledge intake.

    Returns True only if path is safe, in knowledge paths, AND not excluded.
    """
    # Security: validate path first
    if not is_path_safe(path):
        return False

    if is_path_excluded(path):
        return False
    return is_knowledge_path(path)
