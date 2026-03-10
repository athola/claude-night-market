"""Utility classes for parseltongue."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


class FileReader:
    """Read and return file contents with error handling."""

    def read_file(self, path: Path) -> str:
        """Read a file and return its contents.

        Args:
            path: Path to the file

        Returns:
            File contents or error description
        """
        try:
            return path.read_text()
        except PermissionError:
            return "Error: permission denied"
        except OSError as exc:
            return f"Error: {exc}"


class FileUtils:
    """File system utility methods."""

    def is_python_file(self, path: Path) -> bool:
        """Check whether a path points to a Python file.

        Args:
            path: Path to check

        Returns:
            True if the file has a .py suffix
        """
        return path.suffix == ".py"


class HttpClient:
    """Minimal HTTP client with timeout handling."""

    def fetch_remote_analysis(self, url: str) -> Any:
        """Fetch analysis results from a remote URL.

        Args:
            url: URL to fetch

        Returns:
            Response data or None on failure
        """
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception:
            return None


class MemoryManager:
    """Manage analysis strategies under memory pressure."""

    def get_optimal_strategy(self, file_count: int) -> dict[str, Any]:
        """Return an analysis strategy based on memory.

        Args:
            file_count: Number of files to process

        Returns:
            Strategy dictionary
        """
        try:
            if psutil is None:
                available_mb = 500.0
            else:
                mem = psutil.virtual_memory()
                available_mb = mem.available / (1024 * 1024)
        except Exception:
            available_mb = 500.0

        if available_mb < 500 or file_count > 500:
            return {
                "concurrent": False,
                "batch_size": min(file_count, 50),
            }
        return {
            "concurrent": True,
            "batch_size": file_count,
        }


class ResourceMonitor:
    """Monitor system resources."""

    def check_resources(self) -> dict[str, Any]:
        """Check current resource usage.

        Returns:
            Status dictionary with pressure indicators
        """
        try:
            if psutil is None:
                rss = 0
            else:
                process = psutil.Process()
                rss = process.memory_info().rss
        except Exception:
            rss = 0

        threshold = 4 * 1024 * 1024 * 1024  # 4 GB
        pressure = rss > threshold
        result: dict[str, Any] = {"memory_pressure": pressure}
        if pressure:
            result["recommendations"] = ["Reduce batch size or disable concurrency"]
        else:
            result["recommendations"] = []
        return result


class ResultStorage:
    """Persist analysis results to a database."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def save_results(self, data: dict[str, Any]) -> None:
        """Save results to the configured database.

        Args:
            data: Results to persist

        Raises:
            Exception: If the database connection fails
        """
        import sqlite3

        db_path = self.connection_string.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS results (key TEXT, value TEXT)")
            import json

            for k, v in data.items():
                conn.execute(
                    "INSERT INTO results VALUES (?, ?)",
                    (k, json.dumps(v)),
                )
            conn.commit()
        finally:
            conn.close()


class DependencyAnalyzer:
    """Analyze code dependencies including circular refs."""

    def analyze_dependencies(self, code: str) -> dict[str, Any]:
        """Analyze dependencies in code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with dependency analysis
        """
        import re

        imports: dict[str, list[str]] = {}
        current_module = None

        for line in code.split("\n"):
            mod_match = re.match(r"#\s*(\w+\.py)", line)
            if mod_match:
                current_module = mod_match.group(1).replace(".py", "")
                imports.setdefault(current_module, [])
                continue

            imp_match = re.match(r"import\s+(\w+)", line)
            if imp_match and current_module:
                imports[current_module].append(imp_match.group(1))

        circular: list[tuple[str, str]] = []
        for mod, deps in imports.items():
            for dep in deps:
                if dep in imports and mod in imports.get(dep, []):
                    pair = tuple(sorted([mod, dep]))
                    if pair not in circular:
                        circular.append(pair)

        return {"circular_dependencies": circular}


class ParseltongLogger:
    """Logging wrapper for parseltongue."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("parseltongue")
        if not self._logger.handlers:
            handler = logging.NullHandler()
            self._logger.addHandler(handler)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(msg, **kwargs)


class PluginLoader:
    """Discover and load plugins."""

    def discover_plugins(self, path: Path) -> list[str]:
        """Discover plugins in a directory.

        Args:
            path: Directory to search

        Returns:
            List of discovered plugin names
        """
        if not path.exists():
            return []
        return [
            p.stem
            for p in path.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()
        ]
