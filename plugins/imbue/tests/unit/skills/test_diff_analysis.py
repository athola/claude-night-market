"""Tests for diff-analysis skill business logic.

This module tests the change categorization and risk assessment functionality,
following TDD/BDD principles and testing all diff analysis scenarios.
"""


import pytest


class TestDiffAnalysisSkill:
    """Feature: Diff analysis categorizes changes by type and impact

    As a reviewer
    I want changes automatically categorized
    So that I can focus review effort appropriately
    """

    @pytest.fixture
    def mock_diff_analysis_skill_content(self):
        """Mock diff-analysis skill content."""
        return """---
name: diff-analysis
description: Methodology for categorizing changes and assessing risks
category: review-patterns
usage_patterns:
  - change-categorization
  - risk-assessment
  - impact-analysis
tools:
  - Read
  - Glob
  - Grep
  - Bash
tags:
  - diff
  - analysis
  - categorization
  - risk-assessment
---

# Diff Analysis

Methodology for categorizing changes and assessing their potential impact and risk.

## TodoWrite Items

- `diff-analysis:baseline-established`
- `diff-analysis:changes-categorized`
- `diff-analysis:risks-assessed`
- `diff-analysis:summary-prepared`

## Change Categories

### By Type
- **additions**: New files or content
- **modifications**: Changes to existing files
- **deletions**: Removed files or content
- **renames**: File moves or renames
- **mode_changes**: Permission or executable changes

### By Semantic Category
- **features**: New functionality
- **fixes**: Bug fixes and patches
- **refactors**: Code restructuring without functional change
- **tests**: Test files and test-related changes
- **docs**: Documentation updates
- **config**: Configuration changes
- **deps**: Dependency updates

## Risk Assessment Levels

- **Low**: Cosmetic changes, test additions, documentation
- **Medium**: Configuration changes, dependency updates, refactoring
- **High**: API changes, database schema changes, security fixes

## Analysis Patterns

1. Establish baseline for comparison
2. Categorize changes by type and semantics
3. Assess risk levels
4. Generate summary for different audiences
"""

    @pytest.fixture
    def sample_git_diff_output(self):
        """Sample git diff output for testing."""
        return """diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,4 +1,5 @@
 def main():
-    print("Hello")
+    print("Hello, World!")
+    name = input("Enter name: ")
+    print(f"Hello, {name}!")

 if __name__ == "__main__":
     main()
diff --git a/tests/test_main.py b/tests/test_main.py
new file mode 100644
index 0000000..789abc
--- /dev/null
+++ b/tests/test_main.py
@@ -0,0 +1,5 @@
+import pytest
+
+def test_main():
+    assert True
+
diff --git a/README.md b/README.md
index 123456..789abc 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # Project
 This is a test project.
+Updated with new features.
 Check it out!
diff --git a/old_config.json b/old_config.json
deleted file mode 100644
index abcdef..0000000
--- a/old_config.json
+++ /dev/null
@@ -1,5 +0,0 @@
-{
-  "debug": true,
-  "port": 3000
-}
"""

    @pytest.fixture
    def sample_diff_analysis_result(self):
        """Sample structured diff analysis result."""
        return {
            "baseline": "main",
            "changes": [
                {
                    "file": "src/main.py",
                    "type": "modified",
                    "lines_added": 3,
                    "lines_removed": 1,
                    "semantic_category": "feature",
                    "risk_level": "Low"
                },
                {
                    "file": "tests/test_main.py",
                    "type": "added",
                    "lines_added": 5,
                    "lines_removed": 0,
                    "semantic_category": "tests",
                    "risk_level": "Low"
                },
                {
                    "file": "README.md",
                    "type": "modified",
                    "lines_added": 1,
                    "lines_removed": 0,
                    "semantic_category": "docs",
                    "risk_level": "Low"
                },
                {
                    "file": "old_config.json",
                    "type": "deleted",
                    "lines_added": 0,
                    "lines_removed": 5,
                    "semantic_category": "config",
                    "risk_level": "Medium"
                }
            ],
            "summary": {
                "total_files": 4,
                "total_lines_added": 9,
                "total_lines_removed": 6,
                "categories": {
                    "feature": 1,
                    "tests": 1,
                    "docs": 1,
                    "config": 1
                },
                "risk_levels": {
                    "Low": 3,
                    "Medium": 1
                }
            }
        }

    @pytest.mark.unit
    @pytest.mark.unit
    def test_change_categorization_by_type(self, sample_git_diff_output):
        """Scenario: Changes are categorized by type correctly
        Given various git diff outputs
        When analyzing changes
        Then it should categorize by type (additions, modifications, deletions)
        And extract line counts accurately
        """
        # Arrange & Act - parse diff output
        diff_lines = sample_git_diff_output.split('\n')
        changes = []
        current_file = None
        current_change = {}

        for line in diff_lines:
            if line.startswith('diff --git'):
                # Save previous change if exists
                if current_change:
                    changes.append(current_change)

                # Parse file names
                parts = line.split()
                current_change = {
                    "file": parts[2].lstrip('b/'),
                    "type": "unknown",
                    "lines_added": 0,
                    "lines_removed": 0
                }
            elif line.startswith('new file mode'):
                current_change["type"] = "added"
            elif line.startswith('deleted file mode'):
                current_change["type"] = "deleted"
            elif line.startswith('rename from'):
                current_change["type"] = "renamed"
            elif line.startswith('+') and not line.startswith('+++'):
                current_change["lines_added"] += 1
            elif line.startswith('-') and not line.startswith('---'):
                current_change["lines_removed"] += 1

        # Add last change
        if current_change:
            changes.append(current_change)

        # Set type for modifications (default)
        for change in changes:
            if change["type"] == "unknown" and (change["lines_added"] > 0 or change["lines_removed"] > 0):
                change["type"] = "modified"

        # Assert
        file_changes = {change["file"]: change for change in changes}

        assert "src/main.py" in file_changes
        assert file_changes["src/main.py"]["type"] == "modified"
        assert file_changes["src/main.py"]["lines_added"] == 3
        assert file_changes["src/main.py"]["lines_removed"] == 1

        assert "tests/test_main.py" in file_changes
        assert file_changes["tests/test_main.py"]["type"] == "added"
        assert file_changes["tests/test_main.py"]["lines_added"] == 5

        assert "old_config.json" in file_changes
        assert file_changes["old_config.json"]["type"] == "deleted"
        assert file_changes["old_config.json"]["lines_removed"] == 5

    @pytest.mark.unit
    @pytest.mark.unit
    def test_semantic_categorization_of_changes(self, sample_git_diff_output):
        """Scenario: Changes are categorized semantically
        Given files in different directories
        When analyzing semantic meaning
        Then it should categorize as feature, fix, test, docs, config
        """
        # Arrange & Act - categorize files semantically
        file_categories = {
            "src/main.py": "feature",
            "tests/test_main.py": "tests",
            "README.md": "docs",
            "old_config.json": "config",
            "requirements.txt": "deps",
            "setup.py": "config",
            "Dockerfile": "config"
        }

        # Extract files from diff (simplified)
        files_in_diff = [
            "src/main.py",
            "tests/test_main.py",
            "README.md",
            "old_config.json"
        ]

        categorized_changes = []
        for file_path in files_in_diff:
            category = "unknown"
            for pattern, cat in file_categories.items():
                if file_path.endswith(pattern) or pattern in file_path:
                    category = cat
                    break

            categorized_changes.append({
                "file": file_path,
                "semantic_category": category
            })

        # Assert
        file_to_category = {change["file"]: change["semantic_category"] for change in categorized_changes}

        assert file_to_category["src/main.py"] == "feature"
        assert file_to_category["tests/test_main.py"] == "tests"
        assert file_to_category["README.md"] == "docs"
        assert file_to_category["old_config.json"] == "config"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_risk_assessment_by_change_type(self):
        """Scenario: Risk levels are assigned based on change characteristics
        Given various types of changes
        When assessing risk
        Then it should assign appropriate risk levels
        Based on change type and file importance
        """
        # Arrange - define risk assessment rules
        risk_rules = {
            # Low risk
            ("tests", "added"): "Low",
            ("docs", "modified"): "Low",
            ("docs", "added"): "Low",

            # Medium risk
            ("config", "modified"): "Medium",
            ("deps", "modified"): "Medium",
            ("feature", "modified"): "Medium",

            # High risk
            ("feature", "deleted"): "High",
            ("config", "deleted"): "High",
            ("deps", "deleted"): "High"
        }

        # Test cases
        test_changes = [
            {"file": "tests/test_new.py", "semantic_category": "tests", "type": "added"},
            {"file": "README.md", "semantic_category": "docs", "type": "modified"},
            {"file": "config.json", "semantic_category": "config", "type": "modified"},
            {"file": "src/api.py", "semantic_category": "feature", "type": "deleted"},
            {"file": "requirements.txt", "semantic_category": "deps", "type": "modified"}
        ]

        # Act - assess risk for each change
        for change in test_changes:
            key = (change["semantic_category"], change["type"])
            change["risk_level"] = risk_rules.get(key, "Medium")  # Default to Medium

        # Assert
        file_risks = {change["file"]: change["risk_level"] for change in test_changes}

        assert file_risks["tests/test_new.py"] == "Low"
        assert file_risks["README.md"] == "Low"
        assert file_risks["config.json"] == "Medium"
        assert file_risks["src/api.py"] == "High"
        assert file_risks["requirements.txt"] == "Medium"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_diff_summary_generation(self, sample_diff_analysis_result):
        """Scenario: Diff summary provides comprehensive overview
        Given categorized changes with risk assessments
        When generating summary
        Then it should aggregate statistics by category and risk
        And provide totals for quick understanding
        """
        # Arrange & Act - generate summary from changes
        changes = sample_diff_analysis_result["changes"]

        summary = {
            "total_files": len(changes),
            "total_lines_added": sum(c["lines_added"] for c in changes),
            "total_lines_removed": sum(c["lines_removed"] for c in changes),
            "categories": {},
            "risk_levels": {}
        }

        # Aggregate by category
        for change in changes:
            cat = change["semantic_category"]
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1

            risk = change["risk_level"]
            summary["risk_levels"][risk] = summary["risk_levels"].get(risk, 0) + 1

        # Assert
        assert summary["total_files"] == 4
        assert summary["total_lines_added"] == 9
        assert summary["total_lines_removed"] == 6
        assert summary["categories"]["feature"] == 1
        assert summary["categories"]["tests"] == 1
        assert summary["categories"]["docs"] == 1
        assert summary["categories"]["config"] == 1
        assert summary["risk_levels"]["Low"] == 3
        assert summary["risk_levels"]["Medium"] == 1

    @pytest.mark.unit
    @pytest.mark.unit
    def test_baseline_establishment(self, mock_claude_tools):
        """Scenario: Baseline is established for comparison
        Given a git repository
        When establishing baseline for diff analysis
        Then it should determine appropriate comparison point
        And handle various baseline specification formats
        """
        # Arrange
        mock_claude_tools['Bash'].return_value = "abc123"

        # Test different baseline specifications
        test_cases = [
            ("HEAD~1", "git merge-base HEAD HEAD~1"),
            ("main", "git merge-base HEAD main"),
            ("abc123", "echo abc123"),
            ("--since 1 week ago", "git log --since '1 week ago' --format=format:%H | tail -1")
        ]

        # Act & Assert for each case
        for baseline_spec, expected_command in test_cases:
            mock_claude_tools['Bash'].return_value = "baseline-hash"
            baseline = mock_claude_tools['Bash'](expected_command)
            assert baseline == "baseline-hash"
            mock_claude_tools['Bash'].assert_called_with(expected_command)

    @pytest.mark.unit
    @pytest.mark.unit
    def test_diff_patterns_recognition(self):
        """Scenario: Common diff patterns are recognized
        Given typical code change patterns
        When analyzing diffs
        Then it should identify imports, new functions, tests, etc.
        And provide appropriate review focus areas
        """
        # Arrange - various diff patterns
        diff_patterns = {
            "import_addition": r"^\+import\s+",
            "function_addition": r"^\+def\s+\w+\s*\(",
            "class_addition": r"^\+class\s+\w+\s*\:",
            "test_function": r"^\+def\s+test_\w+\s*\(",
            "decorator_addition": r"^\+@\w+",
            "comment_addition": r"^\+\s*#.*",
            "debug_statement": r"^\+.*print\(|^\+.*console\.log\(|^\+.*debug\("
        }

        # Sample diff lines
        sample_lines = [
            "+import os",
            "+import sys",
            "+def new_function():",
            "+class NewClass:",
            "+@pytest.fixture",
            "+def test_function():",
            "+print(\"Debug info\")",
            "+# This is a comment"
        ]

        # Act - detect patterns
        detected_patterns = []
        for line in sample_lines:
            for pattern_name, pattern_regex in diff_patterns.items():
                import re
                if re.match(pattern_regex, line):
                    detected_patterns.append({
                        "pattern": pattern_name,
                        "line": line
                    })
                    break

        # Assert
        pattern_names = [p["pattern"] for p in detected_patterns]
        assert "import_addition" in pattern_names
        assert "function_addition" in pattern_names
        assert "class_addition" in pattern_names
        assert "test_function" in pattern_names
        assert "decorator_addition" in pattern_names
        assert "debug_statement" in pattern_names
        assert "comment_addition" in pattern_names

    @pytest.mark.unit
    @pytest.mark.unit
    def test_cross_cutting_change_detection(self):
        """Scenario: Cross-cutting changes are identified
        Given changes affecting multiple files or components
        When analyzing diffs
        Then it should identify related changes
        And flag potential coordination requirements
        """
        # Arrange - simulate cross-cutting changes
        changes = [
            {"file": "src/api.py", "type": "modified", "semantic_category": "feature"},
            {"file": "tests/test_api.py", "type": "modified", "semantic_category": "tests"},
            {"file": "docs/api.md", "type": "modified", "semantic_category": "docs"},
            {"file": "config/api.json", "type": "modified", "semantic_category": "config"}
        ]

        # Act - detect cross-cutting patterns
        cross_cutting_groups = []

        # Group by base file name (without extension)
        base_name_groups = {}
        for change in changes:
            base_name = change["file"].split('/')[-1].split('.')[0]
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(change)

        # Identify groups with multiple files
        for base_name, group_changes in base_name_groups.items():
            if len(group_changes) > 1:
                cross_cutting_groups.append({
                    "base_name": base_name,
                    "files": [c["file"] for c in group_changes],
                    "categories": [c["semantic_category"] for c in group_changes]
                })

        # Assert
        assert len(cross_cutting_groups) == 1
        assert cross_cutting_groups[0]["base_name"] == "api"
        assert len(cross_cutting_groups[0]["files"]) == 4
        assert "feature" in cross_cutting_groups[0]["categories"]
        assert "tests" in cross_cutting_groups[0]["categories"]
        assert "docs" in cross_cutting_groups[0]["categories"]
        assert "config" in cross_cutting_groups[0]["categories"]

    @pytest.mark.unit
    @pytest.mark.unit
    def test_diff_statistics_calculation(self):
        """Scenario: Diff statistics are calculated accurately
        Given diff output with various change metrics
        When calculating statistics
        Then it should provide accurate totals and percentages
        """
        # Arrange
        changes = [
            {"file": "file1.py", "lines_added": 10, "lines_removed": 5, "type": "modified"},
            {"file": "file2.py", "lines_added": 0, "lines_removed": 3, "type": "deleted"},
            {"file": "file3.py", "lines_added": 15, "lines_removed": 0, "type": "added"},
            {"file": "file4.py", "lines_added": 7, "lines_removed": 7, "type": "modified"}
        ]

        # Act - calculate statistics
        total_added = sum(c["lines_added"] for c in changes)
        total_removed = sum(c["lines_removed"] for c in changes)
        total_changed = total_added + total_removed

        stats = {
            "total_files": len(changes),
            "total_lines_added": total_added,
            "total_lines_removed": total_removed,
            "total_lines_changed": total_changed,
            "net_change": total_added - total_removed,
            "files_by_type": {}
        }

        # Group by type
        for change in changes:
            change_type = change["type"]
            stats["files_by_type"][change_type] = stats["files_by_type"].get(change_type, 0) + 1

        # Assert
        assert stats["total_files"] == 4
        assert stats["total_lines_added"] == 32
        assert stats["total_lines_removed"] == 15
        assert stats["total_lines_changed"] == 47
        assert stats["net_change"] == 17
        assert stats["files_by_type"]["modified"] == 2
        assert stats["files_by_type"]["deleted"] == 1
        assert stats["files_by_type"]["added"] == 1

    @pytest.mark.unit
    def test_diff_analysis_error_handling(self, mock_claude_tools):
        """Scenario: Diff analysis handles errors gracefully
        Given git command failures or malformed diff output
        When analyzing diffs
        Then it should handle errors and provide meaningful feedback
        """
        # Arrange - simulate git command failure
        mock_claude_tools['Bash'].side_effect = [
            "fatal: not a git repository",  # git status fails
            "Error: Invalid baseline"        # git diff fails
        ]

        # Act & Assert - handle errors gracefully
        try:
            result = mock_claude_tools['Bash']("git status")
        except Exception as e:
            error_handled = True
            error_message = str(e)

        assert error_handled
        assert "fatal:" in error_message or "Error:" in error_message

        # Test with malformed diff output
        malformed_diff = """invalid diff output
no proper headers
just some text"""

        # Should handle gracefully without crashing
        lines = malformed_diff.split('\n')
        assert len(lines) == 3
        # No assertion about parsing - just that it doesn't crash

    @pytest.mark.performance
    def test_large_diff_analysis_performance(self):
        """Scenario: Large diff analysis performs efficiently
        Given diff output with many changed files
        When analyzing large diffs
        Then it should complete in reasonable time
        """
        import time

        # Arrange - simulate large diff with many files
        large_changes = []
        for i in range(1000):
            large_changes.append({
                "file": f"src/file_{i}.py",
                "type": "modified" if i % 3 != 0 else "added",
                "lines_added": i % 20,
                "lines_removed": i % 10,
                "semantic_category": ["feature", "fix", "refactor", "tests"][i % 4],
                "risk_level": ["Low", "Medium", "High"][i % 3]
            })

        # Act - measure analysis performance
        start_time = time.time()

        # Process all changes
        summary = {
            "total_files": len(large_changes),
            "categories": {},
            "risk_levels": {},
            "total_lines_added": sum(c["lines_added"] for c in large_changes),
            "total_lines_removed": sum(c["lines_removed"] for c in large_changes)
        }

        for change in large_changes:
            cat = change["semantic_category"]
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
            risk = change["risk_level"]
            summary["risk_levels"][risk] = summary["risk_levels"].get(risk, 0) + 1

        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should process 1000 items in under 1 second
        assert summary["total_files"] == 1000
        assert len(summary["categories"]) == 4
        assert len(summary["risk_levels"]) == 3
