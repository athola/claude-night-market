"""Code review workflow for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class CodeReviewWorkflow:
    """Orchestrates code review workflows."""

    def __init__(self, config: Any = None) -> None:
        """Initialize workflow."""
        self.config = config or {}
        self._skill_registry: dict[str, Any] = {}
        self._errors: list[str] = []
        self._skipped_skills: list[str] = []

    async def run(self, _context: Any) -> dict[str, Any]:
        """Run the code review workflow."""
        return {"findings": [], "summary": ""}

    def configure(self, settings: dict[str, Any]) -> None:
        """Configure the workflow."""
        self.config.update(settings)

    def execute_full_review(self, repo_path: Path | str) -> dict[str, Any]:
        """Execute a full code review on a repository.

        Args:
            repo_path: Path to the repository to review

        Returns:
            Dictionary with review results including findings, summary,
            recommendations, and metrics
        """
        repo_path = Path(repo_path)
        self._errors = []
        self._skipped_skills = []

        # Collect all files to analyze
        files = self._collect_files(repo_path)

        # Determine which skills to run
        skills_to_run = self._determine_skills(repo_path, files)

        # Execute skills and collect findings
        all_findings: list[dict[str, Any]] = []
        for skill_name in skills_to_run:
            try:
                skill = self._get_skill(skill_name)
                if skill:
                    # Create a simple context for the skill
                    context = _ReviewContext(repo_path, files)
                    result = skill.analyze(context, "")
                    if result and hasattr(result, "info"):
                        findings = result.info.get("findings", [])
                        all_findings.extend(findings)
                else:
                    self._skipped_skills.append(skill_name)
            except Exception as e:
                self._errors.append(f"{skill_name}: {e}")
                self._skipped_skills.append(skill_name)

        # Generate summary and recommendations
        summary = self._generate_summary(all_findings)
        recommendations = self._generate_recommendations(all_findings)

        return {
            "findings": all_findings,
            "summary": summary,
            "recommendations": recommendations,
            "metrics": {
                "files_analyzed": len(files),
                "skills_executed": len(skills_to_run) - len(self._skipped_skills),
                "total_findings": len(all_findings),
            },
            "errors": self._errors if self._errors else None,
            "skipped_skills": self._skipped_skills if self._skipped_skills else None,
        }

    def execute_skills(
        self,
        skill_names: list[str],
        context: Any,
    ) -> list[Any]:
        """Execute multiple review skills and collect results.

        Args:
            skill_names: List of skill names to execute
            context: Execution context

        Returns:
            List of results from each skill (None for failures)
        """
        results: list[Any] = []

        for skill_name in skill_names:
            try:
                skill = self._get_skill(skill_name)
                if skill:
                    result = skill.analyze(context, "")
                    results.append(result)
                else:
                    results.append(None)
            except Exception:
                # Partial failure - record error and continue
                results.append(None)

        return results

    def _collect_files(self, repo_path: Path) -> list[str]:
        """Collect files from repository."""
        files = []
        for ext in ["*.py", "*.rs", "*.js", "*.ts", "*.java", "*.go"]:
            files.extend(str(f.relative_to(repo_path)) for f in repo_path.rglob(ext))
        return files

    def _determine_skills(self, repo_path: Path, files: list[str]) -> list[str]:
        """Determine which skills to run based on repository contents."""
        skills = ["unified-review"]  # Always run unified review

        # Check for Rust
        if (repo_path / "Cargo.toml").exists() or any(f.endswith(".rs") for f in files):
            skills.append("rust-review")

        # Check for tests
        if any("test" in f.lower() for f in files):
            skills.append("test-review")

        # Check for API files
        if any("api" in f.lower() for f in files):
            skills.append("api-review")

        return skills

    def _generate_summary(self, findings: list[dict[str, Any]]) -> str:
        """Generate a summary of findings."""
        if not findings:
            return "No issues found during code review."

        critical = sum(1 for f in findings if f.get("severity") == "critical")
        high = sum(1 for f in findings if f.get("severity") == "high")
        medium = sum(1 for f in findings if f.get("severity") == "medium")
        low = sum(1 for f in findings if f.get("severity") == "low")

        return (
            f"Found {len(findings)} issues: "
            f"{critical} critical, {high} high, {medium} medium, {low} low"
        )

    def _generate_recommendations(self, findings: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        if any(f.get("severity") == "critical" for f in findings):
            recommendations.append("Address critical security issues immediately")

        if any(f.get("severity") == "high" for f in findings):
            recommendations.append("Review and fix high-priority issues")

        if not recommendations:
            recommendations.append("Code looks good - continue with best practices")

        return recommendations

    def _get_skill(self, skill_name: str) -> Any:
        """Get a skill by name.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill instance or None
        """
        # Check registry first
        if skill_name in self._skill_registry:
            return self._skill_registry[skill_name]

        # Try to import skill dynamically
        skill_map = {
            "rust-review": "pensive.skills.rust_review.RustReviewSkill",
            "api-review": "pensive.skills.api_review.ApiReviewSkill",
            "bug-review": "pensive.skills.bug_review.BugReviewSkill",
            "architecture-review": (
                "pensive.skills.architecture_review.ArchitectureReviewSkill"
            ),
            "test-review": "pensive.skills.test_review.TestReviewSkill",
            "unified-review": "pensive.skills.unified_review.UnifiedReviewSkill",
        }

        if skill_name in skill_map:
            module_path, class_name = skill_map[skill_name].rsplit(".", 1)
            try:
                import importlib

                module = importlib.import_module(module_path)
                skill_class = getattr(module, class_name)
                return skill_class()
            except (ImportError, AttributeError):
                return None

        return None

    def register_skill(self, name: str, skill: Any) -> None:
        """Register a skill for use in workflows.

        Args:
            name: Skill name
            skill: Skill instance
        """
        self._skill_registry[name] = skill


class _ReviewContext:
    """Simple context for skill execution."""

    def __init__(self, repo_path: Path, files: list[str]) -> None:
        self.repo_path = repo_path
        self.working_dir = repo_path
        self._files = files

    def get_files(self) -> list[str]:
        """Get list of files."""
        return self._files

    def get_file_content(self, filename: str) -> str:
        """Get file content."""
        file_path = self.repo_path / filename
        if file_path.exists():
            return file_path.read_text()
        return ""
