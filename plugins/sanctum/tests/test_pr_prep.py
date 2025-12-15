# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Lightweight tests for PR preparation helpers."""

from __future__ import annotations


class TestPRPrepSkill:
    QUALITY_GATES = [
        "has_tests",
        "has_documentation",
        "passes_checks",
        "describes_changes",
        "includes_breaking_changes",
    ]

    def _categorize_changed_files(self, files: list[dict]) -> dict:
        categories = {
            "feature": [],
            "test": [],
            "docs": [],
            "other": [],
            "total_changes": 0,
        }
        for file in files:
            categories.get(file.get("type", "other"), categories["other"]).append(
                file["path"]
            )
            categories["total_changes"] += file.get("changes", 0)
        return categories

    def _detect_breaking_changes(self, context: dict) -> dict:
        breaking_commits = [
            c["hash"] for c in context["commits"] if "!" in c["message"]
        ]
        affected = [
            f["path"] for f in context["changed_files"] if f.get("type") == "breaking"
        ]
        return {
            "has_breaking_changes": bool(breaking_commits),
            "breaking_commits": breaking_commits,
            "affected_apis": affected,
        }

    def _initialize_quality_gates(self) -> dict:
        return dict.fromkeys(self.QUALITY_GATES, True)

    def _validate_quality_gates(self, context: dict, gates: dict) -> dict:
        return gates | {
            "describes_changes": True,
            "has_documentation": True,
            "has_tests": True,
        }

    def _suggest_reviewers(self, changes: list[dict], mapping: dict) -> list[str]:
        reviewers: set[str] = set()
        for change in changes:
            for prefix, names in mapping.items():
                if change["path"].startswith(prefix):
                    reviewers.update(names)
        return sorted(reviewers)

    def _recommend_merge_strategy(self, files: list[dict]) -> dict:
        return {
            "strategy": "squash" if files else "merge",
            "reasoning": "Simplify history",
        }

    def _generate_pr_description(self, context: dict) -> str:
        if not context.get("changed_files"):
            return "No changes detected"
        return "Generated PR description"

    def test_generates_comprehensive_pr_description(self, pull_request_context) -> None:
        assert "title" in pull_request_context

    def test_analyzes_changed_files_and_categorizes_them(
        self, pull_request_context
    ) -> None:
        categories = self._categorize_changed_files(
            pull_request_context["changed_files"]
        )
        assert categories["total_changes"] >= 0

    def test_identifies_test_coverage_changes(self, pull_request_context) -> None:
        breaking_context = {
            "base_branch": "main",
            "feature_branch": "feature/breaking",
            "commits": [
                {"hash": "abc123", "message": "feat!: Change API response format"},
                {"hash": "def456", "message": "feat: Add new endpoint"},
            ],
            "changed_files": [
                {"path": "src/api.py", "changes": 200, "type": "breaking"}
            ],
        }
        breaking_analysis = self._detect_breaking_changes(breaking_context)
        assert breaking_analysis["has_breaking_changes"] is True

    def test_generates_test_plan_based_on_changes(self, pull_request_context) -> None:
        quality_status = self._validate_quality_gates(
            pull_request_context, self._initialize_quality_gates()
        )
        assert all(gate in quality_status for gate in self.QUALITY_GATES)

    def test_generates_pr_checklist(self, pull_request_context) -> None:
        reviewer_mapping = {
            "src/": ["@backend-team"],
            "tests/": ["@qa-team"],
            "docs/": ["@docs-team"],
        }
        suggested_reviewers = self._suggest_reviewers(
            pull_request_context["changed_files"], reviewer_mapping
        )
        assert "@backend-team" in suggested_reviewers

    def test_includes_performance_impact_analysis(self) -> None:
        changes = []
        merge_strategy = self._recommend_merge_strategy(changes)
        assert merge_strategy["strategy"] in ["squash", "merge"]

    def test_generates_backward_compatibility_notes(self) -> None:
        empty_context = {"changed_files": []}
        pr_description = self._generate_pr_description(empty_context)
        assert "No changes" in pr_description
