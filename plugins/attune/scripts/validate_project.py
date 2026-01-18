#!/usr/bin/env python3
"""Validate project structure against best practices."""

import argparse
import sys
from pathlib import Path

from project_detector import ProjectDetector  # type: ignore[import]


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, name: str, passed: bool, message: str, category: str):
        self.name = name
        self.passed = passed
        self.message = message
        self.category = category


class ProjectValidator:
    """Validator for project structure and configuration."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.detector = ProjectDetector(project_path)
        self.results: list[ValidationResult] = []

    def validate_git(self) -> None:
        """Validate git configuration."""
        # Git initialized
        if self.detector.check_git_initialized():
            self.results.append(
                ValidationResult("git-init", True, "Git repository initialized", "git")
            )
        else:
            self.results.append(
                ValidationResult(
                    "git-init",
                    False,
                    "Git repository not initialized (run: git init)",
                    "git",
                )
            )

        # .gitignore exists
        gitignore = self.project_path / ".gitignore"
        if gitignore.exists():
            lines = len(gitignore.read_text().splitlines())
            self.results.append(
                ValidationResult(
                    "gitignore", True, f".gitignore present ({lines} patterns)", "git"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "gitignore",
                    False,
                    ".gitignore missing (run: /attune:init or /attune:upgrade-project)",
                    "git",
                )
            )

    def validate_build_config(self, language: str) -> None:
        """Validate build configuration files."""
        if language == "python":
            pyproject = self.project_path / "pyproject.toml"
            if pyproject.exists():
                self.results.append(
                    ValidationResult(
                        "pyproject", True, "pyproject.toml present", "build"
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "pyproject", False, "pyproject.toml missing", "build"
                    )
                )

        elif language == "rust":
            cargo_toml = self.project_path / "Cargo.toml"
            if cargo_toml.exists():
                self.results.append(
                    ValidationResult("cargo-toml", True, "Cargo.toml present", "build")
                )
            else:
                self.results.append(
                    ValidationResult("cargo-toml", False, "Cargo.toml missing", "build")
                )

        elif language == "typescript":
            package_json = self.project_path / "package.json"
            tsconfig = self.project_path / "tsconfig.json"

            if package_json.exists():
                self.results.append(
                    ValidationResult(
                        "package-json", True, "package.json present", "build"
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "package-json", False, "package.json missing", "build"
                    )
                )

            if tsconfig.exists():
                self.results.append(
                    ValidationResult("tsconfig", True, "tsconfig.json present", "build")
                )
            else:
                self.results.append(
                    ValidationResult(
                        "tsconfig", False, "tsconfig.json missing", "build"
                    )
                )

        # Check for Makefile
        makefile = self.project_path / "Makefile"
        if makefile.exists():
            content = makefile.read_text()
            targets = len(
                [
                    line
                    for line in content.splitlines()
                    if line.strip() and ":" in line and not line.startswith("#")
                ]
            )
            self.results.append(
                ValidationResult(
                    "makefile", True, f"Makefile with {targets} targets", "build"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "makefile",
                    False,
                    "Makefile missing (run: /attune:upgrade-project --component makefile)",
                    "build",
                )
            )

    def validate_code_quality(self, language: str) -> None:
        """Validate code quality tools configuration."""
        precommit = self.project_path / ".pre-commit-config.yaml"
        if precommit.exists():
            content = precommit.read_text()
            hooks = content.count("- id:")
            self.results.append(
                ValidationResult(
                    "pre-commit",
                    True,
                    f"Pre-commit hooks configured ({hooks} hooks)",
                    "quality",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "pre-commit", False, "Pre-commit hooks not configured", "quality"
                )
            )

        if language == "python":
            # Check for type checking config
            has_mypy_config = (
                self.project_path / "pyproject.toml"
            ).exists() and "[tool.mypy]" in (
                self.project_path / "pyproject.toml"
            ).read_text()
            self.results.append(
                ValidationResult(
                    "type-checking",
                    has_mypy_config,
                    "Type checker configured (mypy)"
                    if has_mypy_config
                    else "Type checker not configured",
                    "quality",
                )
            )

    def validate_ci_cd(self, language: str) -> None:
        """Validate CI/CD workflows."""
        workflows_dir = self.project_path / ".github" / "workflows"

        if not workflows_dir.exists():
            self.results.append(
                ValidationResult(
                    "workflows-dir",
                    False,
                    ".github/workflows/ directory missing",
                    "ci-cd",
                )
            )
            return

        if language == "python":
            required_workflows = ["test.yml", "lint.yml", "typecheck.yml"]
        elif language == "rust":
            required_workflows = ["ci.yml"]
        elif language == "typescript":
            required_workflows = ["test.yml", "lint.yml", "build.yml"]
        else:
            required_workflows = []

        for workflow in required_workflows:
            workflow_path = workflows_dir / workflow
            if workflow_path.exists():
                self.results.append(
                    ValidationResult(
                        f"workflow-{workflow}",
                        True,
                        f"Workflow configured: {workflow}",
                        "ci-cd",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        f"workflow-{workflow}",
                        False,
                        f"Missing workflow: {workflow} (run: /attune:upgrade-project --component workflows)",
                        "ci-cd",
                    )
                )

    def validate_structure(self, language: str) -> None:
        """Validate project directory structure."""
        src_dir = self.project_path / "src"
        if src_dir.exists():
            self.results.append(
                ValidationResult(
                    "src-dir", True, "Source directory present (src/)", "structure"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "src-dir", False, "Source directory missing", "structure"
                )
            )

        # Check for tests
        tests_dir = self.project_path / "tests"
        test_dir = self.project_path / "test"

        if tests_dir.exists() or test_dir.exists():
            self.results.append(
                ValidationResult(
                    "test-dir", True, "Test directory present", "structure"
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    "test-dir", False, "Test directory missing", "structure"
                )
            )

        # Check for README
        readme = self.project_path / "README.md"
        if readme.exists():
            self.results.append(
                ValidationResult("readme", True, "README.md present", "structure")
            )
        else:
            self.results.append(
                ValidationResult("readme", False, "README.md missing", "structure")
            )

    def run_validation(self, language: str | None = None) -> list[ValidationResult]:
        """Run all validations.

        Args:
            language: Project language (auto-detected if None)

        Returns:
            List of validation results

        """
        if not language:
            language = self.detector.detect_language()

        if not language:
            print("Error: Could not detect project language", file=sys.stderr)
            sys.exit(1)

        self.validate_git()
        self.validate_build_config(language)
        self.validate_code_quality(language)
        self.validate_ci_cd(language)
        self.validate_structure(language)

        return self.results

    def print_report(self, verbose: bool = False) -> None:
        """Print validation report.

        Args:
            verbose: Show detailed information

        """
        categories = {
            "git": "Git Configuration",
            "build": "Build Configuration",
            "quality": "Code Quality",
            "ci-cd": "CI/CD",
            "structure": "Project Structure",
        }

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        score = int((passed / total) * 100) if total > 0 else 0

        print("\nProject Validation Report")
        print("=" * 60)
        print(f"Project: {self.project_path.name}")
        print(f"Language: {self.detector.detect_language()}")
        print(f"Path: {self.project_path}")
        print()

        for category_key, category_name in categories.items():
            category_results = [r for r in self.results if r.category == category_key]
            if not category_results:
                continue

            print(f"{category_name}")
            for result in category_results:
                icon = "✅" if result.passed else "❌"
                print(f"  {icon} {result.message}")

        print()
        print(f"Score: {passed}/{total} ({score}%)")
        print()

        # Recommendations
        failed = [r for r in self.results if not r.passed]
        if failed:
            print("Recommendations:")
            for i, result in enumerate(failed, 1):
                print(f"  {i}. {result.message}")
        else:
            print("✅ All checks passed!")

        print("=" * 60)

    def get_exit_code(self) -> int:
        """Get exit code based on results.

        Returns:
            0 if all passed, 1 if any warnings, 2 if critical failures

        """
        failed = [r for r in self.results if not r.passed]

        if not failed:
            return 0

        # Check for critical failures
        critical = ["git-init", "pyproject", "cargo-toml", "package-json"]
        if any(f.name in critical for f in failed):
            return 2

        return 1


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate project structure")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Project path (default: current directory)",
    )
    parser.add_argument(
        "--lang",
        "--language",
        choices=["python", "rust", "typescript"],
        help="Project language (auto-detected if not specified)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any check fails",
    )

    args = parser.parse_args()

    validator = ProjectValidator(args.path)
    validator.run_validation(args.lang)
    validator.print_report(args.verbose)

    exit_code = validator.get_exit_code()

    if args.strict and exit_code != 0:
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
