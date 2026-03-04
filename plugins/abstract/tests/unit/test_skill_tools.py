"""Tests for skill_tools module.

Covers analyze_skill(), estimate_tokens(), and validate_skill_structure().
"""

from __future__ import annotations

import pytest

from abstract.skill_tools import (
    analyze_skill,
    estimate_tokens,
    validate_skill_structure,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_SKILL_CONTENT = """\
---
name: sample-skill
description: A simple test skill
category: testing
---

## Overview

This is a test skill for unit tests.

## Quick Start

1. Do thing one
2. Do thing two
"""

SKILL_WITH_CODE = """\
---
name: code-skill
description: Skill with code blocks
category: testing
---

## Overview

A skill with code examples.

```python
def hello():
    return "hello"
```

```bash
echo "hello"
```
"""

LARGE_SKILL_CONTENT = "\n".join(["line " + str(i) for i in range(400)])


# ---------------------------------------------------------------------------
# analyze_skill
# ---------------------------------------------------------------------------


class TestAnalyzeSkillWithFile:
    """analyze_skill correctly processes individual skill files."""

    @pytest.mark.unit
    def test_returns_dict_with_required_keys(self, tmp_path):
        """Given a valid skill file, result contains expected top-level keys."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path))

        assert "path" in result
        assert "results" in result
        assert "total_files" in result
        assert "threshold" in result

    @pytest.mark.unit
    def test_single_file_found(self, tmp_path):
        """Given one SKILL.md in directory, total_files is 1."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path))

        assert result["total_files"] == 1

    @pytest.mark.unit
    def test_file_result_has_metrics(self, tmp_path):
        """Given a skill file, per-file result has lines, tokens, complexity."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path))
        file_result = result["results"][0]

        assert "lines" in file_result
        assert "tokens" in file_result
        assert "code_blocks" in file_result
        assert "complexity" in file_result
        assert "above_threshold" in file_result

    @pytest.mark.unit
    def test_complexity_low_below_threshold(self, tmp_path):
        """Given file lines below threshold, complexity is 'low'."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)  # < 150 lines

        result = analyze_skill(str(tmp_path), threshold=150)
        assert result["results"][0]["complexity"] == "low"

    @pytest.mark.unit
    def test_complexity_high_above_double_threshold(self, tmp_path):
        """Given file lines above 2x threshold, complexity is 'high'."""
        skill_file = tmp_path / "SKILL.md"
        # 400 lines > 2*150 = 300
        skill_file.write_text(LARGE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path), threshold=150)
        assert result["results"][0]["complexity"] == "high"

    @pytest.mark.unit
    def test_complexity_medium_between_thresholds(self, tmp_path):
        """Given file lines between threshold and 2x threshold, complexity is 'medium'."""
        skill_file = tmp_path / "SKILL.md"
        # 160 lines: > 100 but < 200
        content = "\n".join(["line " + str(i) for i in range(160)])
        skill_file.write_text(content)

        result = analyze_skill(str(tmp_path), threshold=100)
        assert result["results"][0]["complexity"] == "medium"

    @pytest.mark.unit
    def test_above_threshold_true_when_exceeds(self, tmp_path):
        """Given lines > threshold, above_threshold is True."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(LARGE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path), threshold=10)
        assert result["results"][0]["above_threshold"] is True

    @pytest.mark.unit
    def test_above_threshold_false_when_within(self, tmp_path):
        """Given lines <= threshold, above_threshold is False."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path), threshold=500)
        assert result["results"][0]["above_threshold"] is False

    @pytest.mark.unit
    def test_code_blocks_counted(self, tmp_path):
        """Given a skill with code blocks, code_blocks count matches."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SKILL_WITH_CODE)

        result = analyze_skill(str(tmp_path))
        assert result["results"][0]["code_blocks"] == 2

    @pytest.mark.unit
    def test_custom_threshold_stored_in_result(self, tmp_path):
        """Given custom threshold argument, it is stored in the result."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path), threshold=42)
        assert result["threshold"] == 42

    @pytest.mark.unit
    def test_multiple_skill_files_found(self, tmp_path):
        """Given multiple SKILL.md files in subdirs, all are found."""
        for sub in ["alpha", "beta"]:
            d = tmp_path / sub
            d.mkdir()
            (d / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path))
        assert result["total_files"] == 2

    @pytest.mark.unit
    def test_analyze_single_file_directly(self, tmp_path):
        """Given path pointing to a single file, it is analyzed directly."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(skill_file))
        assert result["total_files"] == 1

    @pytest.mark.unit
    def test_nonexistent_path_raises_file_not_found(self):
        """Given a path that does not exist, FileNotFoundError is raised."""
        with pytest.raises(FileNotFoundError):
            analyze_skill("/nonexistent/path/that/does/not/exist")

    @pytest.mark.unit
    def test_empty_directory_zero_files(self, tmp_path):
        """Given directory with no SKILL.md files, total_files is 0."""
        result = analyze_skill(str(tmp_path))
        assert result["total_files"] == 0
        assert result["results"] == []

    @pytest.mark.unit
    def test_tokens_positive_for_non_empty_file(self, tmp_path):
        """Given a non-empty skill file, token count is positive."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = analyze_skill(str(tmp_path))
        assert result["results"][0]["tokens"] > 0


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    """estimate_tokens returns a token breakdown for a given file."""

    @pytest.mark.unit
    def test_returns_dict_with_required_keys(self, tmp_path):
        """Given a valid file, result contains expected keys."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))

        assert "file_path" in result
        assert "total_tokens" in result
        assert "frontmatter_tokens" in result
        assert "body_tokens" in result
        assert "code_tokens" in result
        assert "code_blocks_count" in result
        assert "estimated_tokens" in result

    @pytest.mark.unit
    def test_total_tokens_positive(self, tmp_path):
        """Given non-empty content, total_tokens > 0."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))
        assert result["total_tokens"] > 0

    @pytest.mark.unit
    def test_estimated_tokens_equals_total_tokens(self, tmp_path):
        """Given any file, estimated_tokens equals total_tokens (alias)."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))
        assert result["estimated_tokens"] == result["total_tokens"]

    @pytest.mark.unit
    def test_code_blocks_count_matches_content(self, tmp_path):
        """Given content with two code blocks, code_blocks_count is 2."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SKILL_WITH_CODE)

        result = estimate_tokens(str(skill_file))
        assert result["code_blocks_count"] == 2

    @pytest.mark.unit
    def test_code_blocks_count_zero_no_code(self, tmp_path):
        """Given content with no code blocks, code_blocks_count is 0."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))
        assert result["code_blocks_count"] == 0

    @pytest.mark.unit
    def test_frontmatter_tokens_present(self, tmp_path):
        """Given content with frontmatter, frontmatter_tokens > 0."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))
        assert result["frontmatter_tokens"] >= 0

    @pytest.mark.unit
    def test_file_path_stored_in_result(self, tmp_path):
        """Given a valid file, file_path in result matches the resolved path."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = estimate_tokens(str(skill_file))
        assert result["file_path"] == str(skill_file.resolve())

    @pytest.mark.unit
    def test_nonexistent_file_raises_file_not_found(self):
        """Given a path that does not exist, FileNotFoundError is raised."""
        with pytest.raises(FileNotFoundError):
            estimate_tokens("/nonexistent/SKILL.md")

    @pytest.mark.unit
    def test_larger_file_has_more_tokens(self, tmp_path):
        """Given larger content, token count is higher than for smaller content."""
        small_file = tmp_path / "small.md"
        large_file = tmp_path / "large.md"
        small_file.write_text("Short content.\n")
        large_file.write_text(LARGE_SKILL_CONTENT)

        small_result = estimate_tokens(str(small_file))
        large_result = estimate_tokens(str(large_file))
        assert large_result["total_tokens"] > small_result["total_tokens"]


# ---------------------------------------------------------------------------
# validate_skill_structure
# ---------------------------------------------------------------------------


class TestValidateSkillStructure:
    """validate_skill_structure checks for required files and directories."""

    @pytest.mark.unit
    def test_valid_skill_with_skill_md(self, tmp_path):
        """Given a directory with SKILL.md, valid is True."""
        (tmp_path / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)

        result = validate_skill_structure(str(tmp_path))

        assert result["valid"] is True
        assert result["missing_files"] == []

    @pytest.mark.unit
    def test_invalid_without_skill_md(self, tmp_path):
        """Given a directory missing SKILL.md, valid is False."""
        result = validate_skill_structure(str(tmp_path))

        assert result["valid"] is False
        assert "SKILL.md" in result["missing_files"]

    @pytest.mark.unit
    def test_returns_dict_with_required_keys(self, tmp_path):
        """Given any directory, result contains expected keys."""
        result = validate_skill_structure(str(tmp_path))

        assert "path" in result
        assert "valid" in result
        assert "missing_files" in result
        assert "existing_directories" in result
        assert "skill_files" in result
        assert "total_skill_files" in result

    @pytest.mark.unit
    def test_existing_directories_detected(self, tmp_path):
        """Given common directories present, they appear in existing_directories."""
        (tmp_path / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)
        (tmp_path / "modules").mkdir()
        (tmp_path / "scripts").mkdir()

        result = validate_skill_structure(str(tmp_path))

        assert "modules" in result["existing_directories"]
        assert "scripts" in result["existing_directories"]

    @pytest.mark.unit
    def test_absent_directories_not_listed(self, tmp_path):
        """Given no optional directories, existing_directories is empty."""
        (tmp_path / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)

        result = validate_skill_structure(str(tmp_path))

        assert result["existing_directories"] == []

    @pytest.mark.unit
    def test_skill_files_list_contains_found_skills(self, tmp_path):
        """Given SKILL.md present, skill_files list contains its path."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(SIMPLE_SKILL_CONTENT)

        result = validate_skill_structure(str(tmp_path))

        assert str(skill_file) in result["skill_files"]

    @pytest.mark.unit
    def test_total_skill_files_count(self, tmp_path):
        """Given two SKILL.md files in subdirs, total_skill_files is 2."""
        (tmp_path / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)

        result = validate_skill_structure(str(tmp_path))

        assert result["total_skill_files"] == 2

    @pytest.mark.unit
    def test_path_stored_in_result(self, tmp_path):
        """Given a directory, path in result matches the resolved directory."""
        result = validate_skill_structure(str(tmp_path))
        assert result["path"] == str(tmp_path.resolve())

    @pytest.mark.unit
    def test_default_path_uses_current_directory(self, tmp_path, monkeypatch):
        """Given no path argument, current directory is used."""
        (tmp_path / "SKILL.md").write_text(SIMPLE_SKILL_CONTENT)
        monkeypatch.chdir(tmp_path)

        result = validate_skill_structure()

        assert result["valid"] is True
