"""Example: Abstract plugin checking for and using Sanctum functionality.

This example demonstrates how the Abstract plugin can:
1. Check if Sanctum plugin is installed
2. Use Sanctum's git analysis capabilities when available
3. Provide fallbacks when Sanctum is not present
4. Enhance skill analysis with git context
"""

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Constants for magic numbers
FILE_CHANGES_THRESHOLD = 10
MULTIPLE_AUTHORS_THRESHOLD = 3


class PluginDetector:
    """Utility class for detecting plugin installations."""

    @staticmethod
    def is_plugin_available(plugin_name: str) -> bool:
        """Check if a plugin is installed and available."""
        try:
            # Check multiple possible installation locations
            possible_paths = [
                Path.home() / ".claude" / "plugins" / plugin_name,
                Path.cwd() / "plugins" / plugin_name,
                Path(__file__).parent.parent.parent / plugin_name,
            ]

            for plugin_path in possible_paths:
                if plugin_path.exists():
                    # Check for valid plugin structure
                    required_files = ["plugin.json", "SKILL.md"]
                    if all((plugin_path / f).exists() for f in required_files):
                        return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_plugin_version(plugin_name: str) -> str | None:
        """Get the version of an installed plugin."""
        try:
            possible_paths = [
                Path.home() / ".claude" / "plugins" / plugin_name,
                Path.cwd() / "plugins" / plugin_name,
                Path(__file__).parent.parent.parent / plugin_name,
            ]

            for plugin_path in possible_paths:
                manifest_path = plugin_path / "plugin.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        return manifest.get("version")
            return None
        except Exception:
            return None


class SanctumIntegration:
    """Handles integration with Sanctum plugin for git context."""

    def __init__(self) -> None:
        self.sanctum_available = PluginDetector.is_plugin_available("sanctum")
        self.sanctum_version = PluginDetector.get_plugin_version("sanctum")
        self._sanctum_module = None

    def _load_sanctum(self) -> bool:
        """Lazy load Sanctum module."""
        if not self.sanctum_available:
            return False

        if self._sanctum_module is not None:
            return True

        try:
            # Try to import Sanctum functionality
            # In a real implementation, this would use proper import paths
            sanctum_path = self._find_sanctum_path()
            if sanctum_path:
                sys.path.insert(0, str(sanctum_path / "src"))
                spec = importlib.util.spec_from_file_location(
                    "sanctum.git_analysis",
                    sanctum_path / "src" / "sanctum" / "git_analysis.py",
                )
                if spec and spec.loader:
                    git_analysis = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(git_analysis)
                    self._sanctum_module = git_analysis
                    return True
        except ImportError:
            self.sanctum_available = False
            logging.debug("Sanctum module not found during import")
        except Exception as e:
            logging.warning(f"Unexpected error loading Sanctum: {e}")

        return False

    def _find_sanctum_path(self) -> Path | None:
        """Find the Sanctum plugin path."""
        possible_paths = [
            Path.home() / ".claude" / "plugins" / "sanctum",
            Path.cwd() / "plugins" / "sanctum",
            Path(__file__).parent.parent.parent / "sanctum",
        ]

        for path in possible_paths:
            if path.exists() and (path / "src" / "sanctum").exists():
                return path
        return None

    def get_git_context_for_file(self, file_path: Path) -> dict[str, Any]:
        """Get git context for a file using Sanctum if available."""
        context = {"git_available": False, "sanctum_enhanced": False, "error": None}

        if not self._load_sanctum():
            context["error"] = "Sanctum plugin not available"
            return context

        try:
            # Use Sanctum's git analysis
            git_info = self._sanctum_module.analyze_file_git_history(file_path)
            context.update(
                {
                    "git_available": True,
                    "sanctum_enhanced": True,
                    "commit_history": git_info.get("commits", [])[:5],  # Last 5 commits
                    "current_branch": git_info.get("branch"),
                    "authors": git_info.get("authors", []),
                    "last_modified": git_info.get("last_modified"),
                    "file_changes": git_info.get("change_count", 0),
                },
            )
        except Exception as e:
            context["error"] = f"Failed to get git context: {e!s}"

        return context

    def get_workspace_context(self) -> dict[str, Any]:
        """Get overall workspace git context."""
        context = {"git_available": False, "sanctum_enhanced": False, "error": None}

        if not self._load_sanctum():
            context["error"] = "Sanctum plugin not available"
            return context

        try:
            workspace_info = self._sanctum_module.get_workspace_summary()
            context.update(
                {
                    "git_available": True,
                    "sanctum_enhanced": True,
                    "repository": workspace_info.get("repo_name"),
                    "branch": workspace_info.get("current_branch"),
                    "status": workspace_info.get("status", "clean"),
                    "recent_commits": workspace_info.get("recent_commits", [])[:3],
                },
            )
        except Exception as e:
            context["error"] = f"Failed to get workspace context: {e!s}"

        return context


class AbstractSkillAnalyzer:
    """Abstract plugin skill analyzer with Sanctum integration."""

    def __init__(self) -> None:
        self.sanctum = SanctumIntegration()

    def analyze_skill_with_git_context(self, skill_path: Path) -> dict[str, Any]:
        """Analyze a skill with enhanced git context from Sanctum."""
        analysis = {
            "skill_path": str(skill_path),
            "abstract_analysis": None,
            "git_context": None,
            "enhanced_recommendations": [],
        }

        # Basic Abstract analysis (always available)
        analysis["abstract_analysis"] = self._basic_skill_analysis(skill_path)

        # Get git context from Sanctum if available
        analysis["git_context"] = self.sanctum.get_git_context_for_file(skill_path)

        # Generate enhanced recommendations based on git context
        if analysis["git_context"].get("sanctum_enhanced"):
            analysis["enhanced_recommendations"] = (
                self._generate_git_aware_recommendations(
                    analysis["abstract_analysis"],
                    analysis["git_context"],
                )
            )

        return analysis

    def _basic_skill_analysis(self, skill_path: Path) -> dict[str, Any]:
        """Perform basic Abstract skill analysis."""
        # This is simplified - in reality would analyze the skill file
        return {
            "skill_name": skill_path.name,
            "complexity": "medium",
            "estimated_tokens": 1500,
            "dependencies": [],
            "recommendations": [
                "Consider breaking into smaller functions",
                "Add more error handling",
            ],
        }

    def _generate_git_aware_recommendations(
        self,
        abstract_analysis: dict[str, Any],
        git_context: dict[str, Any],
    ) -> list:
        """Generate recommendations enhanced with git context."""
        recommendations = []

        # Add git-aware recommendations
        if git_context.get("file_changes", 0) > FILE_CHANGES_THRESHOLD:
            recommendations.append(
                "⚠️ File has been modified frequently - consider "
                "stabilizing the interface",
            )

        if len(git_context.get("authors", [])) > MULTIPLE_AUTHORS_THRESHOLD:
            recommendations.append(
                "👥 Multiple authors involved - ensure documentation is clear",
            )

        if git_context.get("status") == "modified":
            recommendations.append(
                "📝 File has uncommitted changes - ensure analysis is up to date",
            )

        # Combine with Abstract recommendations
        base_recs = abstract_analysis.get("recommendations", [])
        return recommendations + base_recs

    def analyze_plugin_suite(self, plugin_path: Path) -> dict[str, Any]:
        """Analyze an entire plugin suite with git context."""
        suite_analysis = {
            "plugin_name": plugin_path.name,
            "skills_analyzed": [],
            "workspace_context": None,
            "summary": {},
        }

        # Get workspace context
        suite_analysis["workspace_context"] = self.sanctum.get_workspace_context()

        # Analyze each skill in the plugin
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.py"):
                skill_analysis = self.analyze_skill_with_git_context(skill_file)
                suite_analysis["skills_analyzed"].append(skill_analysis)

        # Generate summary
        suite_analysis["summary"] = self._generate_suite_summary(suite_analysis)

        return suite_analysis

    def _generate_suite_summary(self, suite_analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of the plugin suite analysis."""
        skills = suite_analysis["skills_analyzed"]
        if not skills:
            return {"message": "No skills found to analyze"}

        summary = {
            "total_skills": len(skills),
            "skills_with_git_context": sum(
                1 for s in skills if s["git_context"].get("sanctum_enhanced")
            ),
            "average_complexity": "medium",  # Simplified
            "total_recommendations": sum(
                len(s.get("enhanced_recommendations", [])) for s in skills
            ),
        }

        # Add git-aware summary if available
        ws_context = suite_analysis.get("workspace_context", {})
        if ws_context.get("sanctum_enhanced"):
            summary.update(
                {
                    "repository": ws_context.get("repository"),
                    "branch": ws_context.get("branch"),
                    "git_status": ws_context.get("status"),
                },
            )

        return summary


# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = AbstractSkillAnalyzer()

    # Example 1: Analyze a single skill
    skill_path = Path("skills/analyze-skill.py")
    if skill_path.exists():
        result = analyzer.analyze_skill_with_git_context(skill_path)
        git_available = result["git_context"].get("sanctum_enhanced")
        enhanced_count = len(result.get("enhanced_recommendations", []))

    # Example 2: Analyze entire plugin suite
    plugin_path = Path()
    suite_result = analyzer.analyze_plugin_suite(plugin_path)
    git_context_skills = suite_result["summary"]["skills_with_git_context"]
    total_recs = suite_result["summary"]["total_recommendations"]

    # Example 3: Check Sanctum availability
    if not analyzer.sanctum.sanctum_available:
        pass
