"""Tests for token estimation utilities."""

from pathlib import Path

import pytest

from leyline import tokens


@pytest.mark.unit
class TestTokenEstimation:
    """Feature: Token estimation heuristics."""

    @pytest.mark.bdd
    def test_estimate_file_tokens_respects_ratios(self, tmp_path: Path) -> None:
        """Scenario: Estimating tokens from file size and extension."""
        file_path = tmp_path / "sample.py"
        file_path.write_text("a" * 32)

        expected = (
            int(32 / tokens.FILE_TOKEN_RATIOS["code"]) + tokens.FILE_OVERHEAD_TOKENS
        )

        assert tokens.estimate_file_tokens(file_path) == expected

    @pytest.mark.bdd
    def test_iter_source_files_skips_excluded_dirs(self, tmp_path: Path) -> None:
        """Scenario: Skipping cache directories and filtering extensions."""
        repo_root = tmp_path / "project"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        (repo_root / "src").mkdir()

        (repo_root / ".git" / "ignored.py").write_text("print('ignore')")
        expected_file = repo_root / "src" / "main.py"
        expected_text = repo_root / "src" / "notes.txt"
        expected_file.write_text("print('ok')")
        expected_text.write_text("notes")
        (repo_root / "src" / "binary.bin").write_text("bin")

        found = {path.name for path in tokens._iter_source_files(repo_root)}

        assert found == {"main.py", "notes.txt"}

    def test_estimate_tokens_uses_heuristic_when_no_encoder(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Scenario: Falling back to heuristic estimation without tiktoken."""
        file_path = tmp_path / "sample.md"
        file_path.write_text("b" * 40)

        monkeypatch.setattr(tokens, "_get_encoder", lambda: None)

        prompt = "abcd"
        expected = int(len(prompt) / tokens.FILE_TOKEN_RATIOS["default"])
        expected += tokens.estimate_file_tokens(file_path)

        assert tokens.estimate_tokens([str(file_path)], prompt=prompt) == expected
