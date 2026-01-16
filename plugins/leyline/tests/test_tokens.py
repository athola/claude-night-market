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

    @pytest.mark.bdd
    def test_estimate_file_tokens_json_ratio(self, tmp_path: Path) -> None:
        """Scenario: JSON files use json token ratio.

        Given a JSON file
        When estimating tokens
        Then it should use the json ratio (3.6 chars per token).
        """
        file_path = tmp_path / "config.json"
        file_path.write_text("a" * 36)

        expected = (
            int(36 / tokens.FILE_TOKEN_RATIOS["json"]) + tokens.FILE_OVERHEAD_TOKENS
        )

        assert tokens.estimate_file_tokens(file_path) == expected

    @pytest.mark.bdd
    def test_estimate_file_tokens_default_ratio(self, tmp_path: Path) -> None:
        """Scenario: Unknown extensions use default token ratio.

        Given a file with unknown extension
        When estimating tokens
        Then it should use the default ratio (4.0 chars per token).
        """
        file_path = tmp_path / "data.xyz"
        file_path.write_text("a" * 40)

        expected = (
            int(40 / tokens.FILE_TOKEN_RATIOS["default"]) + tokens.FILE_OVERHEAD_TOKENS
        )

        assert tokens.estimate_file_tokens(file_path) == expected

    @pytest.mark.bdd
    def test_estimate_file_tokens_oserror_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: OSError when accessing file returns zero tokens.

        Given a non-existent file path
        When estimating tokens
        Then it should return 0 without raising.
        """
        file_path = tmp_path / "nonexistent.py"

        assert tokens.estimate_file_tokens(file_path) == 0

    @pytest.mark.bdd
    def test_estimate_tokens_with_directory(self, tmp_path: Path, monkeypatch) -> None:
        """Scenario: Estimating tokens for a directory of files.

        Given a directory with source files
        When estimating tokens without encoder
        Then it should sum tokens from all source files.
        """
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("a" * 32)
        (src_dir / "utils.py").write_text("b" * 32)

        monkeypatch.setattr(tokens, "_get_encoder", lambda: None)

        result = tokens.estimate_tokens([str(src_dir)], prompt="")

        # Should include tokens from both files
        expected = tokens.estimate_file_tokens(src_dir / "main.py")
        expected += tokens.estimate_file_tokens(src_dir / "utils.py")

        assert result == expected

    @pytest.mark.bdd
    def test_get_encoder_returns_none_when_tiktoken_unavailable(
        self, monkeypatch
    ) -> None:
        """Scenario: Encoder returns None when tiktoken is not available.

        Given tiktoken is not installed
        When getting the encoder
        Then it should return None.
        """
        # Clear the LRU cache first
        tokens._get_encoder.cache_clear()
        monkeypatch.setattr(tokens, "tiktoken", None)

        result = tokens._get_encoder()

        assert result is None
        # Clear cache for other tests
        tokens._get_encoder.cache_clear()

    @pytest.mark.bdd
    def test_estimate_with_heuristic_handles_oserror(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Scenario: Heuristic estimation handles inaccessible files gracefully.

        Given a file path that causes OSError
        When estimating with heuristic
        Then it should skip the file and continue.
        """
        monkeypatch.setattr(tokens, "_get_encoder", lambda: None)

        # Use a path that doesn't exist but won't raise until accessed
        result = tokens.estimate_tokens(["/nonexistent/path/file.py"], prompt="test")

        # Should just return prompt tokens, no error
        expected = int(len("test") / tokens.FILE_TOKEN_RATIOS["default"])
        assert result == expected


@pytest.mark.unit
class TestTokenEncoderPath:
    """Feature: Token estimation with tiktoken encoder."""

    @pytest.mark.bdd
    def test_encode_file_with_tiktoken_handles_oserror(self, tmp_path: Path) -> None:
        """Scenario: Encoding non-existent file returns zero.

        Given a file that doesn't exist
        When encoding with tiktoken
        Then it should return 0.
        """

        class MockEncoder:
            def encode(self, text: str) -> list[int]:
                return [1] * len(text)

        result = tokens._encode_file_with_tiktoken(
            MockEncoder(), tmp_path / "nonexistent.py"
        )

        assert result == 0

    @pytest.mark.bdd
    def test_encode_file_with_tiktoken_success(self, tmp_path: Path) -> None:
        """Scenario: Encoding existing file returns token count plus overhead.

        Given a file with content
        When encoding with tiktoken
        Then it should return token count plus overhead.
        """
        file_path = tmp_path / "test.py"
        file_path.write_text("hello world")

        class MockEncoder:
            def encode(self, text: str) -> list[int]:
                return list(range(len(text.split())))

        result = tokens._encode_file_with_tiktoken(MockEncoder(), file_path)

        # 2 words -> 2 tokens + overhead
        assert result == 2 + tokens.FILE_OVERHEAD_TOKENS

    @pytest.mark.bdd
    def test_estimate_with_encoder_processes_files(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Scenario: Encoder estimation processes files and directories.

        Given files and directories
        When estimating with encoder
        Then it should process all source files.
        """
        file_path = tmp_path / "single.py"
        file_path.write_text("code")

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("more code")

        class MockEncoder:
            def encode(self, text: str) -> list[int]:
                return list(range(len(text)))

        result = tokens._estimate_with_encoder(
            MockEncoder(), [str(file_path), str(src_dir)], "prompt"
        )

        # prompt(6) + single.py(4 + overhead) + main.py(9 + overhead)
        assert result == 6 + (4 + tokens.FILE_OVERHEAD_TOKENS) + (
            9 + tokens.FILE_OVERHEAD_TOKENS
        )

    @pytest.mark.bdd
    def test_estimate_tokens_uses_encoder_when_available(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Scenario: estimate_tokens uses encoder path when tiktoken available.

        Given tiktoken is available
        When estimating tokens
        Then it should use the encoder path.
        """
        file_path = tmp_path / "test.py"
        file_path.write_text("test content")

        class MockEncoder:
            def encode(self, text: str) -> list[int]:
                return [1, 2, 3]  # Fixed 3 tokens

        # Clear cache before monkeypatching
        tokens._get_encoder.cache_clear()
        monkeypatch.setattr(tokens, "_get_encoder", lambda: MockEncoder())

        result = tokens.estimate_tokens([str(file_path)], prompt="hi")

        # prompt(3) + file(3 + overhead)
        assert result == 3 + 3 + tokens.FILE_OVERHEAD_TOKENS
        # Note: can't call cache_clear() after monkeypatch replaces the function
