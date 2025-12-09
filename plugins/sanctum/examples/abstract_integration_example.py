"""Example: Sanctum plugin checking for and using Abstract functionality.

This example demonstrates how the Sanctum plugin can:
1. Check if Abstract plugin is installed
2. Use Abstract's skill analysis capabilities when available
3. Provide fallbacks when Abstract is not present
4. Enhance git operations with complexity analysis
"""

import json
import subprocess
from pathlib import Path
from typing import Any


class PluginDetector:
    """Utility class for detecting plugin installations."""

    @staticmethod
    def is_plugin_available(plugin_name: str) -> bool:
        """Check if a plugin is installed and available."""
        try:
            possible_paths = [
                Path.home() / ".claude" / "plugins" / plugin_name,
                Path.cwd() / "plugins" / plugin_name,
                Path(__file__).parent.parent.parent / plugin_name,
            ]

            for plugin_path in possible_paths:
                if plugin_path.exists():
                    required_files = ["plugin.json", "SKILL.md"]
                    if all((plugin_path / f).exists() for f in required_files):
                        return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_plugin_capabilities(plugin_name: str) -> list[str]:
        """Get the capabilities provided by a plugin."""
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
                        return manifest.get("provides", [])
            return []
        except Exception:
            return []


class AbstractIntegration:
    """Handles integration with Abstract plugin for skill analysis."""

    def __init__(self):
        self.abstract_available = PluginDetector.is_plugin_available("abstract")
        self.abstract_capabilities = (
            PluginDetector.get_plugin_capabilities("abstract")
            if self.abstract_available
            else []
        )
        self._abstract_module = None

    def _load_abstract(self) -> bool:
        """Lazy load Abstract module."""
        if not self.abstract_available:
            return False

        if self._abstract_module is not None:
            return True

        try:
            import sys

            abstract_path = self._find_abstract_path()
            if abstract_path:
                sys.path.insert(0, str(abstract_path / "src"))
                # In a real implementation, this would import actual Abstract modules
                # from abstract import skill_analyzer
                self._abstract_module = True  # Mock for example
                return True
        except ImportError:
            self.abstract_available = False
        except Exception:
            pass

        return False

    def _find_abstract_path(self) -> Path | None:
        """Find the Abstract plugin path."""
        possible_paths = [
            Path.home() / ".claude" / "plugins" / "abstract",
            Path.cwd() / "plugins" / "abstract",
            Path(__file__).parent.parent.parent / "abstract",
        ]

        for path in possible_paths:
            if path.exists() and (path / "src" / "abstract").exists():
                return path
        return None

    def analyze_skill_complexity(self, skill_file: Path) -> dict[str, Any]:
        """Analyze skill complexity using Abstract if available."""
        analysis = {
            "abstract_available": False,
            "complexity_score": None,
            "recommendations": [],
            "token_estimate": None,
            "fallback_analysis": None,
        }

        if not self._load_abstract():
            # Fallback analysis when Abstract is not available
            analysis["fallback_analysis"] = self._basic_complexity_analysis(skill_file)
            return analysis

        try:
            # Use Abstract's skill analysis
            # In a real implementation, this would call Abstract's API
            analysis.update(
                {
                    "abstract_available": True,
                    "complexity_score": self._mock_complexity_score(skill_file),
                    "recommendations": [
                        "Consider breaking into smaller functions",
                        "Add type hints for better clarity",
                        "Document complex algorithms",
                    ],
                    "token_estimate": len(skill_file.read_text())
                    * 1.3,  # Rough estimate
                }
            )
        except Exception as e:
            analysis["error"] = f"Failed to analyze with Abstract: {str(e)}"
            analysis["fallback_analysis"] = self._basic_complexity_analysis(skill_file)

        return analysis

    def _basic_complexity_analysis(self, skill_file: Path) -> dict[str, Any]:
        """Basic fallback complexity analysis."""
        try:
            content = skill_file.read_text()
            lines = len(content.splitlines())
            functions = content.count("def ")
            classes = content.count("class ")

            # Simple heuristic
            complexity = "low"
            if lines > 200 or functions > 10:
                complexity = "high"
            elif lines > 100 or functions > 5:
                complexity = "medium"

            return {
                "lines_of_code": lines,
                "functions": functions,
                "classes": classes,
                "complexity_level": complexity,
                "method": "basic_heuristic",
            }
        except Exception:
            return {"error": "Could not analyze file", "method": "failed"}

    def _mock_complexity_score(self, skill_file: Path) -> float:
        """Mock complexity score for demonstration."""
        # In real implementation, this would use Abstract's actual analysis
        content = skill_file.read_text()
        base_score = min(len(content) / 1000, 10.0)

        # Add complexity factors
        if "class" in content:
            base_score += 1
        if "async def" in content:
            base_score += 0.5
        if "@" in content:  # Decorators
            base_score += 0.3

        return round(base_score, 2)


class SanctumGitOperations:
    """Sanctum git operations enhanced with Abstract analysis."""

    def __init__(self):
        self.abstract = AbstractIntegration()

    def analyze_commit_with_skill_analysis(self, commit_hash: str) -> dict[str, Any]:
        """Analyze a commit with skill complexity analysis for any changed skills."""
        commit_info = {
            "hash": commit_hash,
            "files_changed": [],
            "skill_analysis": {},
            "complexity_summary": {},
        }

        try:
            # Get changed files in commit
            changed_files = self._get_changed_files(commit_hash)

            # Filter for skill files
            skill_files = [
                f for f in changed_files if f.endswith(".py") and "skill" in f
            ]

            for skill_file in skill_files:
                # Get git info for the file
                file_info = self._get_file_commit_info(skill_file, commit_hash)
                commit_info["files_changed"].append(file_info)

                # Use Abstract to analyze skill complexity
                skill_path = Path(skill_file)
                if skill_path.exists():
                    analysis = self.abstract.analyze_skill_complexity(skill_path)
                    commit_info["skill_analysis"][skill_file] = analysis

            # Generate complexity summary
            commit_info["complexity_summary"] = self._generate_complexity_summary(
                commit_info["skill_analysis"]
            )

        except Exception as e:
            commit_info["error"] = str(e)

        return commit_info

    def _get_changed_files(self, commit_hash: str) -> list[str]:
        """Get list of files changed in a commit."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    commit_hash,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return []

    def _get_file_commit_info(self, file_path: str, commit_hash: str) -> dict[str, Any]:
        """Get git information for a file in a specific commit."""
        try:
            # Get file stats from commit
            result = subprocess.run(
                ["git", "show", "--stat", "--format=", f"{commit_hash}:{file_path}"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Get author and date
            log_result = subprocess.run(
                ["git", "log", "-1", "--format=%an|%ad", commit_hash, "--", file_path],
                capture_output=True,
                text=True,
                check=True,
            )

            author, date = log_result.stdout.split("|")

            return {
                "path": file_path,
                "author": author,
                "date": date,
                "lines_changed": result.stdout.count("\n"),
            }
        except subprocess.CalledProcessError:
            return {"path": file_path, "error": "Could not get git info"}

    def _generate_complexity_summary(
        self, skill_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a summary of skill complexities."""
        if not skill_analysis:
            return {"message": "No skill files analyzed"}

        total_files = len(skill_analysis)
        abstract_available = any(
            analysis.get("abstract_available", False)
            for analysis in skill_analysis.values()
        )

        if abstract_available:
            # Use Abstract's detailed analysis
            scores = [
                analysis.get("complexity_score", 0)
                for analysis in skill_analysis.values()
                if analysis.get("complexity_score") is not None
            ]
            avg_complexity = sum(scores) / len(scores) if scores else 0

            return {
                "analysis_method": "abstract_plugin",
                "total_skills": total_files,
                "average_complexity_score": round(avg_complexity, 2),
                "complex_skills": sum(1 for s in scores if s > 5),
                "total_recommendations": sum(
                    len(analysis.get("recommendations", []))
                    for analysis in skill_analysis.values()
                ),
            }
        else:
            # Use fallback analysis
            complexities = [
                analysis.get("fallback_analysis", {}).get("complexity_level", "unknown")
                for analysis in skill_analysis.values()
                if analysis.get("fallback_analysis")
            ]

            return {
                "analysis_method": "fallback_heuristic",
                "total_skills": total_files,
                "complexity_distribution": {
                    level: complexities.count(level) for level in set(complexities)
                },
            }

    def generate_pr_description_with_analysis(
        self, from_branch: str, to_branch: str = "main"
    ) -> dict[str, Any]:
        """Generate PR description enhanced with Abstract analysis."""
        pr_info = {
            "branches": {"from": from_branch, "to": to_branch},
            "commits": [],
            "skill_summary": {},
            "recommendations": [],
        }

        try:
            # Get commits in PR
            commits = self._get_commits_between_branches(from_branch, to_branch)

            for commit in commits:
                commit_analysis = self.analyze_commit_with_skill_analysis(commit)
                pr_info["commits"].append(commit_analysis)

            # Aggregate skill analysis
            all_skill_analysis = {}
            for commit in pr_info["commits"]:
                for skill_file, analysis in commit["skill_analysis"].items():
                    if skill_file not in all_skill_analysis:
                        all_skill_analysis[skill_file] = analysis
                    else:
                        # Use most recent analysis
                        all_skill_analysis[skill_file] = analysis

            pr_info["skill_summary"] = self._generate_complexity_summary(
                all_skill_analysis
            )

            # Generate PR recommendations
            pr_info["recommendations"] = self._generate_pr_recommendations(
                pr_info["commits"], all_skill_analysis
            )

        except Exception as e:
            pr_info["error"] = str(e)

        return pr_info

    def _get_commits_between_branches(
        self, from_branch: str, to_branch: str
    ) -> list[str]:
        """Get commit hashes between two branches."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%H", f"{to_branch}..{from_branch}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return []

    def _generate_pr_recommendations(
        self, commits: list[dict[str, Any]], skill_analysis: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations for the PR."""
        recommendations = []

        # Check for complex changes
        if skill_analysis:
            abstract_available = any(
                analysis.get("abstract_available", False)
                for analysis in skill_analysis.values()
            )

            if abstract_available:
                avg_complexity = skill_analysis.get("complexity_summary", {}).get(
                    "average_complexity_score", 0
                )
                if avg_complexity > 5:
                    recommendations.append(
                        "⚠️ High complexity skills modified - consider additional testing"
                    )
            else:
                # Fallback recommendations
                total_files = len(skill_analysis)
                if total_files > 5:
                    recommendations.append(
                        "📝 Multiple skills modified - ensure comprehensive review"
                    )

        # Check commit patterns
        if len(commits) > 10:
            recommendations.append(
                "🔄 Many commits in PR - consider squashing for cleaner history"
            )

        return recommendations


# Example usage
if __name__ == "__main__":
    # Create Sanctum operations handler
    git_ops = SanctumGitOperations()

    # Example 1: Analyze a specific commit
    print("Commit Analysis Example:")
    print(f"Abstract plugin available: {git_ops.abstract.abstract_available}")
    print(f"Abstract capabilities: {git_ops.abstract.abstract_capabilities}")

    # Get latest commit hash for demo
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        latest_commit = result.stdout.strip()

        commit_analysis = git_ops.analyze_commit_with_skill_analysis(latest_commit)
        print(f"\nLatest commit ({latest_commit[:8]}):")
        print(f"  Files changed: {len(commit_analysis['files_changed'])}")
        print(f"  Skills analyzed: {len(commit_analysis['skill_analysis'])}")
        print(
            f"  Analysis method: {commit_analysis['complexity_summary'].get('analysis_method', 'none')}"
        )
    except subprocess.CalledProcessError:
        print("Not in a git repository")

    # Example 2: Generate PR description
    print("\nPR Description Example:")
    # This would analyze between current branch and main
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()

        if current_branch != "main":
            pr_info = git_ops.generate_pr_description_with_analysis(current_branch)
            print(f"PR from {current_branch} to main:")
            print(f"  Commits: {len(pr_info['commits'])}")
            print(f"  Recommendations: {len(pr_info['recommendations'])}")
        else:
            print("Currently on main branch")
    except subprocess.CalledProcessError:
        print("Could not determine current branch")
