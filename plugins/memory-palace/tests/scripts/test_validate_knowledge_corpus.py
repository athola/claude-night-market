#!/usr/bin/env python3
"""Tests for validate_knowledge_corpus.py script.

Tests the YAML frontmatter validation for knowledge corpus entries.
"""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from validate_knowledge_corpus import extract_frontmatter, validate_entry


class TestExtractFrontmatter:
    """Test YAML frontmatter extraction from markdown content."""

    def test_extracts_valid_frontmatter(self) -> None:
        """Given markdown with valid frontmatter, returns parsed dict."""
        content = """---
title: Test Entry
source: test
palace: engineering
district: testing
maturity: seedling
tags:
  - test
  - validation
queries:
  - how to test
  - testing patterns
  - validation approaches
---

# Content here
"""
        result = extract_frontmatter(content)
        assert result is not None
        assert result["title"] == "Test Entry"
        assert result["maturity"] == "seedling"
        assert len(result["tags"]) == 2
        assert len(result["queries"]) == 3

    def test_returns_none_for_missing_frontmatter(self) -> None:
        """Given markdown without frontmatter, returns None."""
        content = "# Just a heading\n\nSome content."
        result = extract_frontmatter(content)
        assert result is None

    def test_returns_none_for_malformed_yaml(self) -> None:
        """Given markdown with invalid YAML, returns None."""
        content = """---
title: Bad YAML
  indentation: wrong
---

Content
"""
        result = extract_frontmatter(content)
        assert result is None

    def test_returns_none_for_unclosed_frontmatter(self) -> None:
        """Given markdown with unclosed frontmatter, returns None."""
        # Note: No --- after the YAML content, and no --- anywhere in body
        content = """---
title: Missing closing delimiter
maturity: seedling

Content without any triple dashes to close the frontmatter
"""
        result = extract_frontmatter(content)
        assert result is None


class TestValidateEntry:
    """Test validation of knowledge corpus entries."""

    def test_valid_entry_returns_no_errors(self, tmp_path: Path) -> None:
        """Given a valid entry, returns empty error list."""
        entry = tmp_path / "valid-entry.md"
        entry.write_text("""---
title: Valid Entry
source: https://example.com
palace: engineering
district: best-practices
maturity: evergreen
tags:
  - testing
  - validation
queries:
  - how to validate entries
  - entry validation best practices
  - knowledge corpus structure
---

# Valid Entry

Content here.
""")

        errors = validate_entry(entry)
        assert errors == []

    def test_missing_frontmatter_reports_error(self, tmp_path: Path) -> None:
        """Given entry without frontmatter, reports error."""
        entry = tmp_path / "no-frontmatter.md"
        entry.write_text("# No Frontmatter\n\nJust content.")

        errors = validate_entry(entry)
        assert len(errors) == 1
        assert "Missing or invalid YAML frontmatter" in errors[0]

    def test_missing_required_fields_reports_error(self, tmp_path: Path) -> None:
        """Given entry with missing required fields, reports errors."""
        entry = tmp_path / "incomplete.md"
        entry.write_text("""---
title: Incomplete Entry
source: test
---

Missing palace, district, maturity, tags, queries.
""")

        errors = validate_entry(entry)
        assert len(errors) >= 1
        # Should mention missing fields
        assert any("Missing required fields" in e for e in errors)

    def test_invalid_maturity_reports_error(self, tmp_path: Path) -> None:
        """Given entry with invalid maturity value, reports error."""
        entry = tmp_path / "bad-maturity.md"
        entry.write_text("""---
title: Bad Maturity
source: test
palace: engineering
district: testing
maturity: invalid_value
tags:
  - test
queries:
  - query 1
  - query 2
  - query 3
---

Content.
""")

        errors = validate_entry(entry)
        assert any("Invalid maturity" in e for e in errors)
        assert any(
            "seedling" in e or "budding" in e or "evergreen" in e for e in errors
        )

    def test_tags_not_list_reports_error(self, tmp_path: Path) -> None:
        """Given entry with non-list tags, reports error."""
        entry = tmp_path / "bad-tags.md"
        entry.write_text("""---
title: Bad Tags
source: test
palace: engineering
district: testing
maturity: seedling
tags: just-a-string
queries:
  - query 1
  - query 2
  - query 3
---

Content.
""")

        errors = validate_entry(entry)
        assert any("'tags' must be a list" in e for e in errors)

    def test_queries_not_list_reports_error(self, tmp_path: Path) -> None:
        """Given entry with non-list queries, reports error."""
        entry = tmp_path / "bad-queries.md"
        entry.write_text("""---
title: Bad Queries
source: test
palace: engineering
district: testing
maturity: seedling
tags:
  - test
queries: not-a-list
---

Content.
""")

        errors = validate_entry(entry)
        assert any("'queries' must be a list" in e for e in errors)

    def test_insufficient_queries_warns(self, tmp_path: Path) -> None:
        """Given entry with fewer than 3 queries, reports warning."""
        entry = tmp_path / "few-queries.md"
        entry.write_text("""---
title: Few Queries
source: test
palace: engineering
district: testing
maturity: seedling
tags:
  - test
queries:
  - only one query
---

Content.
""")

        errors = validate_entry(entry)
        assert any("at least 3 entries" in e for e in errors)

    def test_all_valid_maturity_values_accepted(self, tmp_path: Path) -> None:
        """Given valid maturity values, no maturity error reported."""
        for maturity in ["seedling", "budding", "evergreen"]:
            entry = tmp_path / f"maturity-{maturity}.md"
            entry.write_text(f"""---
title: {maturity.title()} Entry
source: test
palace: engineering
district: testing
maturity: {maturity}
tags:
  - test
queries:
  - query 1
  - query 2
  - query 3
---

Content.
""")

            errors = validate_entry(entry)
            maturity_errors = [e for e in errors if "maturity" in e.lower()]
            assert not maturity_errors, f"Unexpected maturity error for '{maturity}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
