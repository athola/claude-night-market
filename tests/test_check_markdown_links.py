# ruff: noqa: D101,D102,D103
"""BDD/TDD tests for check-markdown-links.py script.

Tests follow the Given-When-Then pattern for:
1. Heading slugification (GitHub-style)
2. Link extraction from markdown
3. Anchor validation
4. Broken link detection
5. File checking workflow
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Import the functions from the script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from importlib.util import module_from_spec, spec_from_file_location

# Load the script as a module (handles the hyphenated name)
SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "check-markdown-links.py"
)
spec = spec_from_file_location("check_markdown_links", SCRIPT_PATH)
assert spec is not None and spec.loader is not None, "Failed to load script spec"
check_markdown_links = module_from_spec(spec)
spec.loader.exec_module(check_markdown_links)

slugify_heading = check_markdown_links.slugify_heading
extract_headings = check_markdown_links.extract_headings
extract_links = check_markdown_links.extract_links
check_file = check_markdown_links.check_file


class TestSlugifyHeading:
    """Tests for GitHub-style heading slugification."""

    @pytest.mark.unit
    def test_converts_to_lowercase(self) -> None:
        """Given uppercase heading, should return lowercase slug."""
        assert slugify_heading("Hello World") == "hello-world"

    @pytest.mark.unit
    def test_replaces_spaces_with_hyphens(self) -> None:
        """Given heading with spaces, should replace with hyphens."""
        assert slugify_heading("hello world test") == "hello-world-test"

    @pytest.mark.unit
    def test_removes_special_characters(self) -> None:
        """Given heading with special chars, should remove them."""
        result = slugify_heading("Hello! World? @#$%")
        assert result == "hello-world"

    @pytest.mark.unit
    def test_handles_backticks(self) -> None:
        """Given heading with backticks, should keep content inside."""
        result = slugify_heading("Using `code` in headings")
        assert result == "using-code-in-headings"

    @pytest.mark.unit
    def test_collapses_multiple_hyphens(self) -> None:
        """Given text creating multiple hyphens, should collapse them."""
        result = slugify_heading("hello   world")
        assert result == "hello-world"

    @pytest.mark.unit
    def test_strips_leading_trailing_hyphens(self) -> None:
        """Given text creating leading/trailing hyphens, should strip."""
        result = slugify_heading("--hello world--")
        assert result == "hello-world"

    @pytest.mark.unit
    def test_handles_underscores(self) -> None:
        """Given heading with underscores, should convert to hyphens."""
        result = slugify_heading("hello_world_test")
        assert result == "hello-world-test"

    @pytest.mark.unit
    def test_preserves_unicode_letters(self) -> None:
        """Given heading with unicode letters, should preserve them."""
        result = slugify_heading("Cafe Resume")
        assert "cafe" in result or "resume" in result


class TestExtractHeadings:
    """Tests for extracting heading anchors from markdown."""

    @pytest.mark.unit
    def test_extracts_h1_headings(self) -> None:
        """Given markdown with # headings, should extract slugs."""
        content = "# First Heading\n\nSome content.\n\n# Second Heading"
        headings = extract_headings(content)
        assert "first-heading" in headings
        assert "second-heading" in headings

    @pytest.mark.unit
    def test_extracts_various_levels(self) -> None:
        """Given markdown with various heading levels, should extract all."""
        content = "# H1\n## H2\n### H3\n#### H4"
        headings = extract_headings(content)
        assert "h1" in headings
        assert "h2" in headings
        assert "h3" in headings
        assert "h4" in headings

    @pytest.mark.unit
    def test_handles_trailing_hashes(self) -> None:
        """Given headings with trailing hashes, should extract correctly."""
        content = "# Heading Title ###"
        headings = extract_headings(content)
        assert "heading-title" in headings

    @pytest.mark.unit
    def test_returns_empty_set_for_no_headings(self) -> None:
        """Given markdown without headings, should return empty set."""
        content = "Just some paragraph text.\n\nMore text."
        headings = extract_headings(content)
        assert headings == set()


class TestExtractLinks:
    """Tests for extracting markdown links."""

    @pytest.mark.unit
    def test_extracts_relative_links(self) -> None:
        """Given markdown with relative links, should extract them."""
        content = "See [the guide](./guide.md) for details."
        links = extract_links(content)
        assert len(links) == 1
        assert links[0][0] == "./guide.md"
        assert links[0][1] == 1  # Line number

    @pytest.mark.unit
    def test_extracts_anchor_links(self) -> None:
        """Given markdown with anchor links, should extract them."""
        content = "Jump to [the section](#my-section)."
        links = extract_links(content)
        assert len(links) == 1
        assert links[0][0] == "#my-section"

    @pytest.mark.unit
    def test_skips_external_links(self) -> None:
        """Given markdown with http links, should skip them."""
        content = "Visit [example](https://example.com) for more."
        links = extract_links(content)
        # Should not include external links
        external_links = [link for link in links if link[0].startswith("http")]
        assert len(external_links) == 0

    @pytest.mark.unit
    def test_skips_mailto_links(self) -> None:
        """Given markdown with mailto links, should skip them."""
        content = "Email [us](mailto:test@example.com)."
        links = extract_links(content)
        mailto_links = [link for link in links if link[0].startswith("mailto")]
        assert len(mailto_links) == 0

    @pytest.mark.unit
    def test_skips_image_links(self) -> None:
        """Given markdown with image syntax, should skip images."""
        content = "![Alt text](image.png)\n[Real link](doc.md)"
        links = extract_links(content)
        # Should only have the real link, not the image
        assert len(links) == 1
        assert links[0][0] == "doc.md"

    @pytest.mark.unit
    def test_extracts_links_with_anchors(self) -> None:
        """Given links with anchors, should include the anchor."""
        content = "See [section](./doc.md#section-name)."
        links = extract_links(content)
        assert len(links) == 1
        assert links[0][0] == "./doc.md#section-name"

    @pytest.mark.unit
    def test_returns_correct_line_numbers(self) -> None:
        """Given links on different lines, should return correct line nums."""
        content = "Line 1\n[Link 1](a.md)\nLine 3\n[Link 2](b.md)"
        links = extract_links(content)
        assert len(links) == 2
        assert links[0][1] == 2  # Line 2
        assert links[1][1] == 4  # Line 4

    @pytest.mark.unit
    def test_skips_links_in_fenced_code_blocks(self) -> None:
        """Given links inside fenced code blocks, should skip them."""
        content = """Before
```markdown
[template](placeholder_link)
```
[Real link](real.md)
"""
        links = extract_links(content)
        assert len(links) == 1
        assert links[0][0] == "real.md"

    @pytest.mark.unit
    def test_skips_links_in_tilde_code_blocks(self) -> None:
        """Given links inside tilde code blocks, should skip them."""
        content = """Before
~~~bash
[ignored](fake.md)
~~~
[Real](doc.md)
"""
        links = extract_links(content)
        assert len(links) == 1
        assert links[0][0] == "doc.md"


class TestCheckFile:
    """Tests for the file checking workflow."""

    @pytest.fixture
    def temp_docs(self, tmp_path: Path) -> Path:
        """Create a temporary docs directory structure."""
        docs = tmp_path / "docs"
        docs.mkdir()
        return docs

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_valid_internal_links_pass(self, temp_docs: Path) -> None:
        """Given file with valid internal links, should return no errors."""
        # Create target file
        (temp_docs / "target.md").write_text("# Target Doc\n\nContent here.")

        # Create source file with valid link
        source = temp_docs / "source.md"
        source.write_text("See [target](target.md) for more.")

        errors = check_file(source, temp_docs)
        assert errors == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_broken_file_link_detected(self, temp_docs: Path) -> None:
        """Given file with broken link, should return error."""
        source = temp_docs / "source.md"
        source.write_text("See [missing](nonexistent.md) for more.")

        errors = check_file(source, temp_docs)
        assert len(errors) == 1
        assert "broken link" in errors[0].lower()
        assert "nonexistent.md" in errors[0]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_valid_anchor_links_pass(self, temp_docs: Path) -> None:
        """Given file with valid anchor links, should return no errors."""
        source = temp_docs / "source.md"
        source.write_text("# My Heading\n\nJump to [heading](#my-heading).")

        errors = check_file(source, temp_docs)
        assert errors == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_broken_anchor_detected(self, temp_docs: Path) -> None:
        """Given file with broken anchor, should return error."""
        source = temp_docs / "source.md"
        source.write_text("# My Heading\n\nJump to [missing](#nonexistent).")

        errors = check_file(source, temp_docs)
        assert len(errors) == 1
        assert "broken anchor" in errors[0].lower()
        assert "#nonexistent" in errors[0]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cross_file_anchor_validation(self, temp_docs: Path) -> None:
        """Given link to anchor in another file, should validate it."""
        # Create target with heading
        (temp_docs / "target.md").write_text("# Target Section\n\nContent.")

        # Create source with link to that anchor
        source = temp_docs / "source.md"
        source.write_text("See [section](target.md#target-section).")

        errors = check_file(source, temp_docs)
        assert errors == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_broken_cross_file_anchor_detected(self, temp_docs: Path) -> None:
        """Given broken anchor in cross-file link, should detect it."""
        # Create target without the expected heading
        (temp_docs / "target.md").write_text("# Different Heading\n\nContent.")

        # Create source with link to non-existent anchor
        source = temp_docs / "source.md"
        source.write_text("See [section](target.md#missing-section).")

        errors = check_file(source, temp_docs)
        assert len(errors) == 1
        assert "broken anchor" in errors[0].lower()
        assert "#missing-section" in errors[0]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_absolute_path_links(self, temp_docs: Path) -> None:
        """Given absolute path links, should resolve from root."""
        # Create target in subdirectory
        subdir = temp_docs / "subdir"
        subdir.mkdir()
        (subdir / "target.md").write_text("# Target\n\nContent.")

        # Create source with absolute path link
        source = temp_docs / "source.md"
        source.write_text("See [target](/subdir/target.md).")

        errors = check_file(source, temp_docs)
        assert errors == []


class TestScriptExecution:
    """Tests for the main script execution."""

    @pytest.fixture
    def temp_repo(self, tmp_path: Path) -> Path:
        """Create a temporary repo-like directory."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()  # Make it look like a repo
        return repo

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_script_returns_zero_for_valid_links(self, temp_repo: Path) -> None:
        """Given repo with valid links, script should return 0."""
        # Create a valid markdown file
        (temp_repo / "README.md").write_text("# Readme\n\nSee [section](#readme).")

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(temp_repo / "README.md")],
            capture_output=True,
            text=True,
            check=False,
            cwd=temp_repo,
        )
        assert result.returncode == 0
        assert "no broken links" in result.stdout.lower()

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_script_returns_one_for_broken_links(self, temp_repo: Path) -> None:
        """Given repo with broken links, script should return 1."""
        # Create a markdown file with broken link
        (temp_repo / "README.md").write_text("See [missing](nonexistent.md).")

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(temp_repo / "README.md")],
            capture_output=True,
            text=True,
            check=False,
            cwd=temp_repo,
        )
        assert result.returncode == 1
        assert "broken" in result.stdout.lower()

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_script_reports_error_count(self, temp_repo: Path) -> None:
        """Given multiple broken links, script should report count."""
        # Create file with multiple broken links
        (temp_repo / "README.md").write_text(
            "See [a](a.md) and [b](b.md) and [c](c.md)."
        )

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(temp_repo / "README.md")],
            capture_output=True,
            text=True,
            check=False,
            cwd=temp_repo,
        )
        assert result.returncode == 1
        assert "3 broken link" in result.stdout.lower()
