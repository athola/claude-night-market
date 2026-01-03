"""Detect and validate project types."""

from pathlib import Path


class ProjectDetector:
    """Detect project type and existing configurations."""

    def __init__(self, project_path: Path):
        """Initialize detector for a project path.

        Args:
            project_path: Path to project directory
        """
        self.project_path = Path(project_path)

    def detect_language(self) -> str | None:
        """Detect primary language of the project.

        Returns:
            Language name ("python", "rust", "typescript") or None
        """
        # Python indicators
        python_files = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
        ]

        # Rust indicators
        rust_files = ["Cargo.toml", "Cargo.lock"]

        # TypeScript indicators
        ts_files = ["package.json", "tsconfig.json"]

        # Check for language-specific files
        if any((self.project_path / f).exists() for f in python_files):
            return "python"

        if any((self.project_path / f).exists() for f in rust_files):
            return "rust"

        if any((self.project_path / f).exists() for f in ts_files):
            # Further check for TypeScript vs plain JavaScript
            if (self.project_path / "tsconfig.json").exists():
                return "typescript"
            # Could add more JS vs TS detection logic here

        # Check for source files
        src_path = self.project_path / "src"
        if src_path.exists():
            py_files = list(src_path.rglob("*.py"))
            rs_files = list(src_path.rglob("*.rs"))
            ts_files = list(src_path.rglob("*.ts")) + list(src_path.rglob("*.tsx"))

            if py_files:
                return "python"
            if rs_files:
                return "rust"
            if ts_files:
                return "typescript"

        return None

    def check_git_initialized(self) -> bool:
        """Check if git repository is initialized.

        Returns:
            True if .git directory exists
        """
        return (self.project_path / ".git").exists()

    def check_existing_files(self) -> dict[str, bool]:
        """Check which configuration files already exist.

        Returns:
            Dictionary mapping file names to existence status
        """
        files_to_check = [
            ".gitignore",
            "Makefile",
            ".pre-commit-config.yaml",
            "pyproject.toml",
            "Cargo.toml",
            "package.json",
            ".github/workflows/test.yml",
            ".github/workflows/lint.yml",
            ".github/workflows/typecheck.yml",
        ]

        return {
            filename: (self.project_path / filename).exists()
            for filename in files_to_check
        }

    def get_project_info(self) -> dict[str, any]:
        """Get comprehensive project information.

        Returns:
            Dictionary with project detection results
        """
        return {
            "path": str(self.project_path),
            "language": self.detect_language(),
            "git_initialized": self.check_git_initialized(),
            "existing_files": self.check_existing_files(),
        }

    def get_missing_configurations(self, language: str) -> list[str]:
        """Get list of missing configuration files for a language.

        Args:
            language: Target language ("python", "rust", "typescript")

        Returns:
            List of missing configuration file names
        """
        language_configs = {
            "python": [
                ".gitignore",
                "pyproject.toml",
                "Makefile",
                ".pre-commit-config.yaml",
                ".github/workflows/test.yml",
                ".github/workflows/lint.yml",
                ".github/workflows/typecheck.yml",
            ],
            "rust": [
                ".gitignore",
                "Cargo.toml",
                "Makefile",
                ".github/workflows/ci.yml",
            ],
            "typescript": [
                ".gitignore",
                "package.json",
                "tsconfig.json",
                ".github/workflows/test.yml",
                ".github/workflows/lint.yml",
            ],
        }

        required_files = language_configs.get(language, [])
        existing = self.check_existing_files()

        return [f for f in required_files if not existing.get(f, False)]
