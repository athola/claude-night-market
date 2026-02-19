"""
Tests for leyline:git-platform - Git platform detection hook and skill.

Feature: Git Platform Detection
  As a plugin ecosystem user
  I want automatic detection of whether my project uses GitHub, GitLab, or Bitbucket
  So that forge-related commands use the correct CLI and terminology
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

# Hook script location
HOOK_SCRIPT = Path(__file__).parents[3] / "hooks" / "detect-git-platform.sh"
SKILL_FILE = Path(__file__).parents[3] / "skills" / "git-platform" / "SKILL.md"


class TestPlatformDetectionHook:
    """
    Feature: SessionStart hook detects git platform from project signals.
    """

    @pytest.mark.unit
    def test_hook_script_exists_and_is_executable(self):
        """
        Scenario: Hook script is properly installed
        Given the leyline plugin is installed
        When checking the hook script
        Then it exists and is executable
        """
        assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"
        assert os.access(HOOK_SCRIPT, os.X_OK), "Hook script is not executable"

    @pytest.mark.unit
    def test_hook_outputs_valid_json(self, tmp_path):
        """
        Scenario: Hook always outputs valid JSON
        Given any directory (even non-git)
        When the hook runs
        Then it outputs valid JSON with hookSpecificOutput
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    @pytest.mark.unit
    def test_non_git_directory_returns_empty_context(self, tmp_path):
        """
        Scenario: Non-git directory produces no platform context
        Given a directory that is not a git repository
        When the hook runs
        Then additionalContext is empty
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_github_detected_from_remote_url(self, tmp_path):
        """
        Scenario: GitHub detected from git remote URL
        Given a git repo with origin pointing to github.com
        When the hook runs
        Then platform is detected as github
        """
        # Set up a git repo with a github remote
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "git_platform: github" in context
        assert "cli: gh" in context

    @pytest.mark.unit
    def test_gitlab_detected_from_remote_url(self, tmp_path):
        """
        Scenario: GitLab detected from git remote URL
        Given a git repo with origin pointing to gitlab.com
        When the hook runs
        Then platform is detected as gitlab with correct MR terminology
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://gitlab.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "git_platform: gitlab" in context
        assert "cli: glab" in context
        assert "mr_term: merge request" in context

    @pytest.mark.unit
    def test_bitbucket_detected_from_remote_url(self, tmp_path):
        """
        Scenario: Bitbucket detected from git remote URL
        Given a git repo with origin pointing to bitbucket.org
        When the hook runs
        Then platform is detected as bitbucket
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://bitbucket.org/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "git_platform: bitbucket" in context

    @pytest.mark.unit
    def test_github_detected_from_directory_marker(self, tmp_path):
        """
        Scenario: GitHub detected from .github/ directory when no remote
        Given a git repo with .github/ directory but no remote
        When the hook runs
        Then platform is detected as github
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".github").mkdir()

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "git_platform: github" in context

    @pytest.mark.unit
    def test_gitlab_detected_from_ci_file(self, tmp_path):
        """
        Scenario: GitLab detected from .gitlab-ci.yml when no remote
        Given a git repo with .gitlab-ci.yml but no remote
        When the hook runs
        Then platform is detected as gitlab
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".gitlab-ci.yml").touch()

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "git_platform: gitlab" in context
        assert "merge request" in context

    @pytest.mark.unit
    def test_hook_completes_under_timeout(self, tmp_path):
        """
        Scenario: Hook performance meets <200ms requirement
        Given any environment
        When the hook runs
        Then it completes within 1 second (generous CI margin)
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=1,
        )
        assert result.returncode == 0

    @pytest.mark.unit
    def test_ci_system_detected_for_github_actions(self, tmp_path):
        """
        Scenario: GitHub Actions CI detected from workflows directory
        Given a git repo with .github/workflows/
        When the hook runs
        Then ci system is reported as github-actions
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )
        (tmp_path / ".github" / "workflows").mkdir(parents=True)

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "ci: github-actions" in context


class TestGitPlatformSkill:
    """
    Feature: git-platform skill provides correct cross-platform command mapping.
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: Skill file is properly structured
        Given the leyline plugin
        When checking the git-platform skill
        Then SKILL.md exists with required frontmatter
        """
        assert SKILL_FILE.exists()
        content = SKILL_FILE.read_text()
        assert "name: git-platform" in content
        assert "category: infrastructure" in content

    @pytest.mark.unit
    def test_skill_has_command_mapping_module(self):
        """
        Scenario: Command mapping module exists
        Given the git-platform skill
        When checking modules
        Then command-mapping.md exists
        """
        module = SKILL_FILE.parent / "modules" / "command-mapping.md"
        assert module.exists()

    @pytest.mark.unit
    def test_skill_covers_all_platforms(self):
        """
        Scenario: Skill documents all supported platforms
        Given the git-platform skill
        When reading the content
        Then it covers GitHub, GitLab, and Bitbucket
        """
        content = SKILL_FILE.read_text()
        assert "GitHub" in content
        assert "GitLab" in content
        assert "Bitbucket" in content

    @pytest.mark.unit
    def test_skill_maps_gh_and_glab_commands(self):
        """
        Scenario: Skill provides command equivalents
        Given the git-platform skill
        When reading the command reference
        Then both gh and glab equivalents are documented
        """
        content = SKILL_FILE.read_text()
        assert "`gh issue view" in content
        assert "`glab issue view" in content
        assert "`gh pr create" in content
        assert "`glab mr create" in content

    @pytest.mark.unit
    def test_skill_declares_authentication_dependency(self):
        """
        Scenario: Skill depends on authentication-patterns
        Given the git-platform skill
        When checking dependencies
        Then authentication-patterns is listed
        """
        content = SKILL_FILE.read_text()
        assert "authentication-patterns" in content

    @pytest.mark.unit
    def test_command_mapping_module_has_graphql_examples(self):
        """
        Scenario: Command mapping covers GraphQL for both platforms
        Given the command-mapping module
        When reading advanced operations
        Then GraphQL examples exist for both GitHub and GitLab
        """
        module = SKILL_FILE.parent / "modules" / "command-mapping.md"
        content = module.read_text()
        assert "gh api graphql" in content
        assert "glab api graphql" in content

    @pytest.mark.unit
    def test_command_mapping_has_discussion_operations(self):
        """
        Scenario: Command mapping documents GitHub Discussion CRUD operations
        Given the command-mapping module
        When reading the Discussion Operations section
        Then it covers create, comment, search, mark-as-answer, and get operations
        And it notes that Discussions are GitHub-only (N/A for GitLab/Bitbucket).
        """
        module = SKILL_FILE.parent / "modules" / "command-mapping.md"
        content = module.read_text()
        assert "## Discussion Operations" in content
        assert "createDiscussion" in content
        assert "addDiscussionComment" in content
        assert "markDiscussionCommentAsAnswer" in content
        assert "search(query:" in content or "type: DISCUSSION" in content
        assert "GitHub only" in content

    @pytest.mark.unit
    def test_command_mapping_has_category_resolution(self):
        """
        Scenario: Command mapping documents category resolution for Discussions
        Given the command-mapping module
        When reading the Discussion prerequisites
        Then it shows how to resolve category nodeIds from slugs.
        """
        module = SKILL_FILE.parent / "modules" / "command-mapping.md"
        content = module.read_text()
        assert "discussionCategories" in content
        assert "slug" in content
        assert "hasDiscussionsEnabled" in content
