"""Tests for _create_structure — ATT-001 data-driven backbone.

ATT-001: Three near-identical _create_*_structure helpers totalled ~186
lines. This test drives the single replacement: _create_structure(dirs,
files, dry_run) that all three will delegate to.
"""

from __future__ import annotations

# tests/conftest.py already puts scripts/ on sys.path, and pytest imports it
# before collecting this module. Repeating that here forced the import below
# past the top of the file, which is the only reason it needed an E402 waiver.
from attune_init import _create_structure


class TestCreateStructureHelper:
    """_create_structure must exist as the data-driven backbone."""

    def test_import_succeeds(self):
        """Confirm _create_structure is exported from attune_init."""
        assert callable(_create_structure)

    def test_creates_directories(self, tmp_path):
        """Each directory in dirs is created on disk."""
        d1 = tmp_path / "src"
        d2 = tmp_path / "tests"
        _create_structure([d1, d2], [], dry_run=False)
        assert d1.exists()
        assert d2.exists()

    def test_creates_file_with_content(self, tmp_path):
        """A file in the files spec is written with its content."""
        src = tmp_path / "src"
        src.mkdir()
        f = src / "__init__.py"
        _create_structure([], [(f, "# hello\n")], dry_run=False)
        assert f.exists()
        assert f.read_text() == "# hello\n"

    def test_skips_existing_files(self, tmp_path):
        """An existing file is not overwritten."""
        src = tmp_path / "src"
        src.mkdir()
        f = src / "__init__.py"
        f.write_text("# original\n")
        _create_structure([], [(f, "# replacement\n")], dry_run=False)
        assert f.read_text() == "# original\n"

    def test_dry_run_does_not_create_dirs(self, tmp_path, capsys):
        """In dry_run mode, directories are announced but not created."""
        d = tmp_path / "src"
        _create_structure([d], [], dry_run=True)
        assert not d.exists()
        captured = capsys.readouterr()
        assert "[DRY RUN] Would create directory:" in captured.out

    def test_dry_run_does_not_create_files(self, tmp_path, capsys):
        """In dry_run mode, files are announced but not created."""
        d = tmp_path / "src"
        d.mkdir()
        f = d / "main.rs"
        _create_structure([], [(f, "fn main() {}\n")], dry_run=True)
        assert not f.exists()
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
