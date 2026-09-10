"""Characterization tests for prompt and file-context composition.

Written green before ``delegation_executor.py`` was split, so the split
had a contract to keep. They pin behavior, not location: the import line
is the only thing that moved with the code, and it now names
``delegation_prompt`` so deleting that module turns these red.
"""

import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import delegation_prompt as prompt_module  # noqa: E402 - sys.path set above
from delegation_prompt import (  # noqa: E402 - sys.path set above
    _compose_prompt_with_files,
    _inline_context,
    _iter_context_files,
    _prompt_argv,
)
from delegation_services import ServiceConfig  # noqa: E402 - sys.path set above

_BASE = ServiceConfig(name="probe", command="probe", auth_method="none")


def _service(**overrides: Any) -> ServiceConfig:
    """Vary one provider without restating its required fields."""
    return replace(_BASE, **overrides)


class TestPromptArgv:
    """Contract for prompt argv."""

    def test_positional_provider_escapes_a_dash_prompt_with_double_dash(self) -> None:
        """Every positional CLI reads a leading dash as its own flag and prints help at exit 0, which looks like an answer to a caller."""
        assert _prompt_argv(_service(prompt_flag=None), "-x") == ["--", "-x"]
        assert _prompt_argv(_service(prompt_flag=None), "hi") == ["hi"]

    def test_flag_provider_attaches_a_dash_prompt_to_its_long_flag(self) -> None:
        """`--` protects the next positional, not a flag's operand, so the value must be attached with `=`."""
        service = _service(prompt_flag="-p", prompt_long_flag="--prompt")
        assert _prompt_argv(service, "-x") == ["--prompt=-x"]
        assert _prompt_argv(service, "hi") == ["-p", "hi"]

    def test_flag_provider_without_a_long_flag_refuses_a_dash_prompt(self) -> None:
        """A refusal that names the missing config, never a bare prompt.

        No third escape form exists, and a bare dash prompt is read by the
        CLI as its own flag and answered with a help page at exit 0.
        """
        with pytest.raises(ValueError, match="prompt_long_flag"):
            _prompt_argv(_service(prompt_flag="-p"), "-x")


class TestContextFiles:
    """Contract for context files."""

    def test_skips_vcs_and_venv_directories_and_sorts(self, tmp_path: Path) -> None:
        """Sorted so the same directory yields the same prompt on every run, which is what makes a delegation reproducible."""
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "a.py").write_text("a")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "x.js").write_text("x")
        names = [p.name for p in _iter_context_files([str(tmp_path)])]
        assert names == ["a.py", "b.py"]


class TestInlineContext:
    """Contract for inline context."""

    def test_each_file_is_fenced_with_begin_and_end_markers(
        self, tmp_path: Path
    ) -> None:
        """The markers are what a CLI with no `@path` syntax has instead of file references."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        block = _inline_context([str(one)])
        assert block.startswith(f"--- BEGIN FILE: {one} ---\nalpha")
        assert block.endswith(f"--- END FILE: {one} ---")
        assert "truncated" not in block

    def test_budget_overflow_truncates_the_file_and_says_so(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Linux caps one argv entry at 128 KiB, and a silently dropped file is worse than a labeled cut."""
        big = tmp_path / "big.txt"
        big.write_text("x" * 5000)
        monkeypatch.setattr(prompt_module, "MAX_INLINE_CONTEXT_BYTES", 1500)
        block = _inline_context([str(big)])
        assert "[file truncated at" in block
        assert block.rstrip().endswith("1 file(s) included]")
        assert "[context truncated at 1500 bytes" in block


class TestComposePromptWithFiles:
    """Contract for compose prompt with files."""

    def test_reference_provider_gets_at_paths_and_a_dir_glob(
        self, tmp_path: Path
    ) -> None:
        """A path that does not exist is left out rather than passed as a reference the CLI would then fail on."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        sub = tmp_path / "sub"
        sub.mkdir()
        composed = _compose_prompt_with_files(
            _service(inline_files=False), "go", [str(one), str(sub), "/nope"]
        )
        assert composed == f"@{one} @{sub}/**/* go"

    def test_inline_provider_gets_content_before_the_prompt(
        self, tmp_path: Path
    ) -> None:
        """Context first, so the instruction the model reads last is the user's."""
        one = tmp_path / "one.txt"
        one.write_text("alpha")
        composed = _compose_prompt_with_files(
            _service(inline_files=True), "go", [str(one)]
        )
        assert composed.startswith("--- BEGIN FILE:")
        assert composed.endswith("\n\ngo")

    def test_no_readable_files_leaves_the_prompt_alone(self) -> None:
        """Both conventions collapse to the bare prompt, so a bad path degrades to a plain delegation rather than an error."""
        assert (
            _compose_prompt_with_files(_service(inline_files=True), "go", ["/nope"])
            == "go"
        )
        assert (
            _compose_prompt_with_files(_service(inline_files=False), "go", ["/nope"])
            == "go"
        )
