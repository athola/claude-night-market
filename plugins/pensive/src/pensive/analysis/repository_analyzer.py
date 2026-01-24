"""Repository analyzer for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar


class RepositoryAnalyzer:
    """Analyze code repositories."""

    # Language detection mappings
    LANGUAGE_EXTENSIONS: ClassVar[dict[str, list[str]]] = {
        "rust": [".rs"],
        "python": [".py"],
        "javascript": [".js", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "c": [".c", ".h"],
    }

    LANGUAGE_CONFIG_FILES: ClassVar[dict[str, list[str]]] = {
        "rust": ["Cargo.toml"],
        "python": ["setup.py", "pyproject.toml", "requirements.txt"],
        "javascript": ["package.json"],
        "typescript": ["tsconfig.json"],
        "java": ["pom.xml", "build.gradle"],
        "go": ["go.mod"],
    }

    BUILD_SYSTEM_FILES: ClassVar[dict[str, str]] = {
        "Makefile": "make",
        "makefile": "make",
        "CMakeLists.txt": "cmake",
        "build.gradle": "gradle",
        "pom.xml": "maven",
        "Cargo.toml": "cargo",
        "package.json": "npm",
        "go.mod": "go",
    }

    TEST_FRAMEWORK_MARKERS: ClassVar[dict[str, str]] = {
        "Cargo.toml": "cargo",
        "pytest.ini": "pytest",
        "pyproject.toml": "pytest",
        "jest.config.js": "jest",
        "package.json": "jest",  # Often contains jest config
    }

    def __init__(self, repo_path: str | Path | None = None) -> None:
        """Initialize repository analyzer."""
        self.repo_path = Path(repo_path) if repo_path else None

    def analyze(self) -> dict[str, Any]:
        """Analyze the repository."""
        if not self.repo_path:
            return {"files": [], "languages": [], "findings": []}

        return {
            "files": self.get_files(),
            "languages": self.detect_languages(),
            "findings": [],
        }

    def analyze_repository(self, repo_path: Path | str) -> dict[str, Any]:
        """Analyze a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Analysis results including languages, build systems, and test frameworks
        """
        repo_path = Path(repo_path)

        # Detect languages
        languages = self._detect_languages_in_repo(repo_path)

        # Detect build systems
        build_systems = self._detect_build_systems(repo_path)

        # Detect test frameworks
        test_frameworks = self._detect_test_frameworks(repo_path)

        return {
            "languages": languages,
            "build_systems": build_systems,
            "test_frameworks": test_frameworks,
            "file_count": self._count_files(repo_path),
        }

    def _detect_languages_in_repo(self, repo_path: Path) -> dict[str, int]:
        """Detect programming languages in repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Dictionary of language names to file counts
        """
        languages: dict[str, int] = {}

        # Check config files first
        for lang, config_files in self.LANGUAGE_CONFIG_FILES.items():
            for config_file in config_files:
                if (repo_path / config_file).exists():
                    languages[lang] = languages.get(lang, 0)

        # Count files by extension
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            for ext in extensions:
                count = len(list(repo_path.rglob(f"*{ext}")))
                if count > 0:
                    languages[lang] = languages.get(lang, 0) + count

        return languages

    def _detect_build_systems(self, repo_path: Path) -> list[str]:
        """Detect build systems in repository.

        Args:
            repo_path: Path to the repository

        Returns:
            List of detected build system names
        """
        build_systems = []

        for filename, system in self.BUILD_SYSTEM_FILES.items():
            if (repo_path / filename).exists():
                if system not in build_systems:
                    build_systems.append(system)

        return build_systems

    def _detect_test_frameworks(self, repo_path: Path) -> list[str]:
        """Detect test frameworks in repository.

        Args:
            repo_path: Path to the repository

        Returns:
            List of detected test framework names
        """
        frameworks = []

        for filename, framework in self.TEST_FRAMEWORK_MARKERS.items():
            if (repo_path / filename).exists():
                if framework not in frameworks:
                    frameworks.append(framework)

        # Check for test directories
        if (repo_path / "tests").exists() or (repo_path / "test").exists():
            if "pytest" not in frameworks and any(repo_path.rglob("test_*.py")):
                frameworks.append("pytest")

        return frameworks

    def _count_files(self, repo_path: Path) -> int:
        """Count total code files in repository."""
        count = 0
        for extensions in self.LANGUAGE_EXTENSIONS.values():
            for ext in extensions:
                count += len(list(repo_path.rglob(f"*{ext}")))
        return count

    def get_files(self, pattern: str = "*") -> list[Path]:
        """Get files matching pattern."""
        if not self.repo_path:
            return []
        return list(self.repo_path.rglob(pattern))

    def detect_languages(self) -> list[str]:
        """Detect languages used in the repository."""
        if not self.repo_path:
            return []
        return list(self._detect_languages_in_repo(self.repo_path).keys())
