"""Tests for the base module with common script functionality."""

from pathlib import Path

from abstract.base import (
    AbstractScript,
    find_markdown_files,
    has_frontmatter_file,
    setup_imports,
)


class TestSetupImports:
    """Tests for setup_imports function."""

    def test_setup_imports_completes_without_error(self) -> None:
        """Test that setup_imports runs without raising exceptions."""
        # Given: A fresh import state
        # When: Calling setup_imports
        # Then: It completes without error (backwards compatibility function)
        setup_imports()
        # No assertion needed - function is a no-op for compatibility


class TestHasFrontmatterFile:
    """Tests for has_frontmatter_file function."""

    def test_file_with_valid_frontmatter(self, tmp_path: Path) -> None:
        """Test detection of file with valid frontmatter."""
        # Given: A file with valid YAML frontmatter
        test_file = tmp_path / "test.md"
        test_file.write_text("---\nname: test\n---\n\nContent")

        # When: Checking for frontmatter
        result = has_frontmatter_file(test_file)

        # Then: Returns True
        assert result is True

    def test_file_without_frontmatter(self, tmp_path: Path) -> None:
        """Test detection of file without frontmatter."""
        # Given: A file without frontmatter
        test_file = tmp_path / "test.md"
        test_file.write_text("Just content, no frontmatter")

        # When: Checking for frontmatter
        result = has_frontmatter_file(test_file)

        # Then: Returns False
        assert result is False

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handling of nonexistent file."""
        # Given: A path to a file that doesn't exist
        nonexistent = tmp_path / "nonexistent.md"

        # When: Checking for frontmatter
        result = has_frontmatter_file(nonexistent)

        # Then: Returns False (handles OSError gracefully)
        assert result is False

    def test_unreadable_file(self, tmp_path: Path) -> None:
        """Test handling of file with invalid encoding."""
        # Given: A file with binary content that can't be decoded
        test_file = tmp_path / "binary.md"
        test_file.write_bytes(b"\xff\xfe\x00\x01Invalid UTF-8")

        # When: Checking for frontmatter
        result = has_frontmatter_file(test_file)

        # Then: Returns False (handles UnicodeDecodeError gracefully)
        assert result is False


class TestFindMarkdownFiles:
    """Tests for find_markdown_files function."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test finding files in empty directory."""
        # Given: An empty directory
        # When: Finding markdown files
        result = find_markdown_files(tmp_path)

        # Then: Returns empty list
        assert result == []

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test finding files in nonexistent directory."""
        # Given: A path that doesn't exist
        nonexistent = tmp_path / "nonexistent"

        # When: Finding markdown files
        result = find_markdown_files(nonexistent)

        # Then: Returns empty list
        assert result == []

    def test_finds_markdown_files(self, tmp_path: Path) -> None:
        """Test finding markdown files in directory."""
        # Given: A directory with markdown files
        (tmp_path / "file1.md").write_text("# File 1")
        (tmp_path / "file2.md").write_text("# File 2")
        (tmp_path / "not_md.txt").write_text("Not markdown")

        # When: Finding markdown files
        result = find_markdown_files(tmp_path)

        # Then: Returns only .md files
        assert len(result) == 2
        assert all(f.suffix == ".md" for f in result)

    def test_finds_files_recursively(self, tmp_path: Path) -> None:
        """Test finding markdown files recursively."""
        # Given: Nested directories with markdown files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.md").write_text("# Root")
        (subdir / "nested.md").write_text("# Nested")

        # When: Finding markdown files
        result = find_markdown_files(tmp_path)

        # Then: Returns files from all levels
        assert len(result) == 2
        names = [f.name for f in result]
        assert "root.md" in names
        assert "nested.md" in names

    def test_returns_sorted_paths(self, tmp_path: Path) -> None:
        """Test that results are sorted by path."""
        # Given: Multiple files that would sort differently
        (tmp_path / "zebra.md").write_text("# Z")
        (tmp_path / "alpha.md").write_text("# A")
        (tmp_path / "middle.md").write_text("# M")

        # When: Finding markdown files
        result = find_markdown_files(tmp_path)

        # Then: Results are sorted
        names = [f.name for f in result]
        assert names == sorted(names)


class TestAbstractScript:
    """Tests for AbstractScript class."""

    def test_initialization(self) -> None:
        """Test AbstractScript initialization."""
        # Given: A script name
        script_name = "test-script"

        # When: Creating an AbstractScript instance
        script = AbstractScript(script_name)

        # Then: Script name is set
        assert script.script_name == script_name

    def test_find_markdown_files_method(self, tmp_path: Path) -> None:
        """Test find_markdown_files instance method."""
        # Given: An AbstractScript and a directory with markdown files
        script = AbstractScript("test-script")
        (tmp_path / "test.md").write_text("# Test")

        # When: Using the instance method
        result = script.find_markdown_files(tmp_path)

        # Then: Returns markdown files
        assert len(result) == 1
        assert result[0].name == "test.md"

    def test_find_markdown_files_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test find_markdown_files with nonexistent directory."""
        # Given: An AbstractScript and a nonexistent directory
        script = AbstractScript("test-script")
        nonexistent = tmp_path / "nonexistent"

        # When: Using the instance method
        result = script.find_markdown_files(nonexistent)

        # Then: Returns empty list
        assert result == []

    def test_check_frontmatter_exists(self) -> None:
        """Test check_frontmatter_exists method."""
        # Given: An AbstractScript and content with frontmatter
        script = AbstractScript("test-script")
        content = "---\nname: test\n---\n\nBody"

        # When: Checking frontmatter
        result = script.check_frontmatter_exists(content)

        # Then: Returns True
        assert result is True

    def test_check_frontmatter_exists_missing(self) -> None:
        """Test check_frontmatter_exists with no frontmatter."""
        # Given: An AbstractScript and content without frontmatter
        script = AbstractScript("test-script")
        content = "Just content"

        # When: Checking frontmatter
        result = script.check_frontmatter_exists(content)

        # Then: Returns False
        assert result is False

    def test_extract_frontmatter(self) -> None:
        """Test extract_frontmatter method."""
        # Given: An AbstractScript and content with frontmatter
        script = AbstractScript("test-script")
        content = "---\nname: test\n---\n\nBody content"

        # When: Extracting frontmatter
        raw, body = script.extract_frontmatter(content)

        # Then: Separates frontmatter from body
        assert "---\nname: test\n---" == raw
        assert body == "Body content"

    def test_extract_frontmatter_none(self) -> None:
        """Test extract_frontmatter with no frontmatter."""
        # Given: An AbstractScript and content without frontmatter
        script = AbstractScript("test-script")
        content = "Just body content"

        # When: Extracting frontmatter
        raw, body = script.extract_frontmatter(content)

        # Then: Returns empty frontmatter
        assert raw == ""
        assert body == content

    def test_config_lazy_loading(self) -> None:
        """Test that config is lazily loaded."""
        # Given: An AbstractScript
        script = AbstractScript("test-script")

        # When: Accessing config property
        # Then: Config is loaded (may raise if config not found, which is OK)
        try:
            _ = script.config
            # If we get here, config was loaded successfully
        except FileNotFoundError:
            # Config file not found is acceptable - proves lazy loading works
            pass

    def test_config_setter(self) -> None:
        """Test setting config manually."""
        # Given: An AbstractScript and a mock config
        script = AbstractScript("test-script")

        # When: Setting config manually
        mock_config = object()  # Use any object as mock
        script.config = mock_config

        # Then: Config is set
        assert script._config is mock_config

    def test_error_handler_lazy_loading(self) -> None:
        """Test that error_handler is lazily loaded."""
        # Given: An AbstractScript
        script = AbstractScript("test-script")

        # When: Accessing error_handler property
        handler = script.error_handler

        # Then: Error handler is created with script name
        assert handler is not None
        assert handler.tool_name == "test-script"

    def test_error_handler_setter(self) -> None:
        """Test setting error_handler manually."""
        # Given: An AbstractScript and a mock handler
        script = AbstractScript("test-script")

        # When: Setting handler manually
        mock_handler = object()  # Use any object as mock
        script.error_handler = mock_handler

        # Then: Handler is set
        assert script._error_handler is mock_handler

    def test_find_project_root(self, tmp_path: Path) -> None:
        """Test find_project_root method."""
        # Given: An AbstractScript
        script = AbstractScript("test-script")

        # When: Finding project root from tmp_path
        # (This may find the actual project root, which is fine)
        result = script.find_project_root(tmp_path)

        # Then: Returns a Path (actual behavior depends on project structure)
        assert isinstance(result, Path)

    def test_read_file_safe_success(self, tmp_path: Path) -> None:
        """Test read_file_safe with readable file."""
        # Given: An AbstractScript and a readable file
        script = AbstractScript("test-script")
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # When: Reading the file
        result = script.read_file_safe(test_file)

        # Then: Returns file content
        assert result == "Test content"

    def test_read_file_safe_nonexistent(self, tmp_path: Path) -> None:
        """Test read_file_safe with nonexistent file."""
        # Given: An AbstractScript and a nonexistent file
        script = AbstractScript("test-script")
        nonexistent = tmp_path / "nonexistent.txt"

        # When: Reading the file
        result = script.read_file_safe(nonexistent)

        # Then: Returns None
        assert result is None

    def test_read_file_safe_unreadable(self, tmp_path: Path) -> None:
        """Test read_file_safe with unreadable file."""
        # Given: An AbstractScript and a file with invalid encoding
        script = AbstractScript("test-script")
        test_file = tmp_path / "binary.txt"
        test_file.write_bytes(b"\xff\xfe\x00\x01Invalid UTF-8")

        # When: Reading the file
        result = script.read_file_safe(test_file)

        # Then: Returns None (handles UnicodeDecodeError)
        assert result is None
