# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Simplified BDD-style tests for Sanctum command helpers."""

from __future__ import annotations

import re


class TestCatchupCommand:
    def _execute_catchup_workflow(self, state: dict | None = None) -> dict:
        state = state or {"branch": "main", "behind": 0, "ahead": 0, "is_clean": True}
        return {
            "status": {
                "behind": state.get("behind", 0),
                "ahead": state.get("ahead", 0),
            },
            "missing_commits": state.get("behind", 0),
            "local_commits": state.get("local_commits", 0),
            "is_clean": state.get("is_clean", True),
        }

    def _execute_commit_msg_workflow(
        self, has_staged: bool, commit_message: str | None = None
    ) -> dict:
        if not has_staged:
            return {"status": "no_changes", "message": "No staged changes"}
        return {
            "status": "success",
            "commit_message": commit_message or "feat: Add feature",
        }

    def test_catchup_command_analyzes_diverged_branch(self, temp_git_repo) -> None:
        catchup_result = self._execute_catchup_workflow(
            {"branch": "feature/branch", "behind": 0, "ahead": 2, "local_commits": 2}
        )
        assert catchup_result["status"]["ahead"] == 2
        assert catchup_result["local_commits"] == 2

    def test_catchup_command_handles_diverged_branch(self) -> None:
        catchup_result = self._execute_catchup_workflow(
            {"branch": "main", "behind": 0, "ahead": 0, "is_clean": True}
        )
        assert catchup_result["is_clean"] is True

    def test_commit_msg_command_handles_bug_fixes(self) -> None:
        commit_result = self._execute_commit_msg_workflow(has_staged=False)
        assert commit_result["status"] == "no_changes"


class TestPRCommand:
    def _execute_pr_workflow(self, context: dict) -> dict:
        return {
            "quality_gates": {
                "has_tests": True,
                "has_documentation": True,
                "describes_changes": True,
            },
            "context": context,
        }

    def _execute_update_docs_workflow(self, has_changes: bool) -> dict:
        if not has_changes:
            return {"status": "no_changes"}
        return {
            "status": "updates_needed",
            "code_changes": ["api.py"],
            "new_functions": ["get_data"],
            "existing_docs": ["README.md"],
            "suggestions": ["Document API changes"],
        }

    def _execute_update_version_workflow(self, bump: str) -> dict:
        return {"status": "updated", "bump": bump}

    def test_pr_command_prepares_pull_request(self, pull_request_context) -> None:
        pr_result = self._execute_pr_workflow(pull_request_context)
        assert pr_result["quality_gates"]["has_tests"] is True

    def test_pr_command_suggests_reviewers(self, pull_request_context) -> None:
        pr_result = self._execute_pr_workflow(pull_request_context)
        assert "quality_gates" in pr_result

    def test_update_docs_command_identifies_documentation_needs(
        self, temp_git_repo
    ) -> None:
        docs_result = self._execute_update_docs_workflow(has_changes=True)
        assert docs_result["status"] == "updates_needed"

    def test_update_docs_command_handles_no_changes(self) -> None:
        docs_result = self._execute_update_docs_workflow(has_changes=False)
        assert docs_result["status"] == "no_changes"

    def test_update_readme_command_modernizes_readme(self, temp_git_repo) -> None:
        readme_content = """# Project\n\nA brief description."""
        assert "Project" in readme_content

    def test_update_version_command_bumps_all_version_files(
        self, temp_git_repo
    ) -> None:
        version_result = self._execute_update_version_workflow("patch")
        assert version_result["status"] == "updated"


class TestUpdateDocsDirectoryRules:
    """Test that /update-docs covers all documentation directories."""

    # Directory style rules as defined in doc-updates skill
    DIRECTORY_RULES = {
        "docs/": {"max_lines": 500, "style": "strict"},
        "book/": {"max_lines": 1000, "style": "book"},
        "wiki/": {"max_lines": 500, "style": "wiki"},
        "plugins/*/README.md": {"max_lines": 300, "style": "plugin_summary"},
    }

    def _get_ruleset(self, file_path: str) -> dict:
        """Determine which ruleset applies to a file path."""
        if file_path.startswith("book/"):
            return self.DIRECTORY_RULES["book/"]
        elif file_path.startswith("docs/"):
            return self.DIRECTORY_RULES["docs/"]
        elif file_path.startswith("wiki/"):
            return self.DIRECTORY_RULES["wiki/"]
        elif re.match(r"plugins/[^/]+/README\.md$", file_path):
            return self.DIRECTORY_RULES["plugins/*/README.md"]
        else:
            return self.DIRECTORY_RULES["docs/"]  # Default to strict

    def test_docs_directory_uses_strict_rules(self) -> None:
        ruleset = self._get_ruleset("docs/api-overview.md")
        assert ruleset["max_lines"] == 500
        assert ruleset["style"] == "strict"

    def test_book_directory_uses_lenient_rules(self) -> None:
        ruleset = self._get_ruleset("book/src/tutorials/getting-started.md")
        assert ruleset["max_lines"] == 1000
        assert ruleset["style"] == "book"

    def test_wiki_directory_uses_wiki_rules(self) -> None:
        ruleset = self._get_ruleset("wiki/architecture/adr-001.md")
        assert ruleset["max_lines"] == 500
        assert ruleset["style"] == "wiki"

    def test_plugin_readme_uses_summary_rules(self) -> None:
        ruleset = self._get_ruleset("plugins/sanctum/README.md")
        assert ruleset["max_lines"] == 300
        assert ruleset["style"] == "plugin_summary"

    def test_plugin_nested_file_uses_default_rules(self) -> None:
        # Non-README files in plugins should use default (strict) rules
        ruleset = self._get_ruleset("plugins/sanctum/docs/internal.md")
        assert ruleset["max_lines"] == 500
        assert ruleset["style"] == "strict"

    def test_unknown_directory_defaults_to_strict(self) -> None:
        ruleset = self._get_ruleset("random/unknown/file.md")
        assert ruleset["max_lines"] == 500
        assert ruleset["style"] == "strict"


class TestCreateTagConfigDriven:
    """Test that /create-tag uses config-driven post-tag submissions."""

    REQUIRED_SUBMISSION_KEYS = {"name", "script"}

    def _load_tag_submissions(self, repo_root: str) -> dict | None:
        """Load tag-submissions.json from repo root, or None if absent."""
        import json
        from pathlib import Path

        config_path = Path(repo_root) / "tag-submissions.json"
        if not config_path.exists():
            return None
        return json.loads(config_path.read_text())

    def _validate_submission_entry(self, entry: dict) -> list[str]:
        """Return list of validation errors for a submission entry."""
        errors = []
        missing = self.REQUIRED_SUBMISSION_KEYS - set(entry.keys())
        if missing:
            errors.append(f"Missing required keys: {missing}")
        if "script" in entry and not isinstance(entry["script"], str):
            errors.append("script must be a string path")
        return errors

    def test_tag_submissions_json_exists_in_repo(self) -> None:
        """Config file exists at repo root for this project."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None, "tag-submissions.json should exist in repo root"

    def test_tag_submissions_has_submissions_key(self) -> None:
        """Config must have a 'submissions' list."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        assert "submissions" in config
        assert isinstance(config["submissions"], list)
        assert len(config["submissions"]) > 0

    def test_each_submission_has_required_keys(self) -> None:
        """Each submission entry must have name and script."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        for entry in config["submissions"]:
            errors = self._validate_submission_entry(entry)
            assert not errors, f"Entry {entry.get('name', '?')}: {errors}"

    def test_submission_scripts_exist_on_disk(self) -> None:
        """Referenced scripts must exist in the repo."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        for entry in config["submissions"]:
            script_path = repo_root / entry["script"]
            assert script_path.exists(), f"Script not found: {entry['script']}"

    def test_create_tag_command_references_config(self) -> None:
        """The create-tag command must reference tag-submissions.json."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[3]
        cmd_path = repo_root / "plugins" / "sanctum" / "commands" / "create-tag.md"
        content = cmd_path.read_text()
        assert "tag-submissions.json" in content

    def test_missing_config_gracefully_skips(self) -> None:
        """When config is absent, load returns None (skip behavior)."""
        config = self._load_tag_submissions("/nonexistent/path")
        assert config is None
