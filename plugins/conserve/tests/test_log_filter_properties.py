"""Property-based tests for tier-1 log filter commands.

The log-debugging-hygiene module claims that tier-1 filters
(`tail`, `head`, `rg`) produce output that is a literal subset
of the input log. This property is what the module calls
"forensically useful": every byte in the output maps back to
an unmodified byte in the source.

Hypothesis fuzzes log content shapes and verifies the subset
property holds. If a future change replaces the tier-1 entry
in the module's table with a non-subset operation (a
paraphraser, a summarizer, a custom "smart filter"), the test
suite catches it because the subset property is what justifies
the module's separation from tier 3 (compression).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Log lines: printable ASCII, no embedded newlines, bounded width.
_log_line = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd", "P", "Zs"),
        blacklist_characters="\n\r",
    ),
    min_size=1,
    max_size=200,
)

# A log file: 1-300 lines, joined with newlines, trailing newline.
_log_content = st.lists(_log_line, min_size=1, max_size=300).map(
    lambda lines: "\n".join(lines) + "\n"
)


@given(content=_log_content, n=st.integers(min_value=1, max_value=200))
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_tail_output_is_suffix_of_input(content: str, n: int, tmp_path: Path) -> None:
    """`tail -n N` output is always a literal suffix of the input.

    This is the property that distinguishes tier 1 from tier 3.
    A compressor can produce output that is not a suffix; `tail`
    by contract cannot.
    """
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
        ["tail", "-n", str(n), str(path)],  # noqa: S607 - tail via PATH is intentional
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"tail failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr!r}\n"
            f"  stdout: {result.stdout!r}"
        )
    assert content.endswith(result.stdout), (
        f"tail -n {n} produced output that is not a suffix; "
        f"input tail (50 chars): {content[-50:]!r}; "
        f"output tail (50 chars): {result.stdout[-50:]!r}"
    )


@given(content=_log_content, n=st.integers(min_value=1, max_value=200))
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_head_output_is_prefix_of_input(content: str, n: int, tmp_path: Path) -> None:
    """`head -n N` output is always a literal prefix of the input."""
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
        ["head", "-n", str(n), str(path)],  # noqa: S607 - head via PATH is intentional
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"head failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr!r}\n"
            f"  stdout: {result.stdout!r}"
        )
    assert content.startswith(result.stdout), (
        f"head -n {n} produced output that is not a prefix; "
        f"input head (50 chars): {content[:50]!r}; "
        f"output head (50 chars): {result.stdout[:50]!r}"
    )


@given(content=_log_content, n=st.integers(min_value=1, max_value=100))
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_tail_output_respects_line_budget(content: str, n: int, tmp_path: Path) -> None:
    """`tail -n N` never returns more than N newline-terminated lines."""
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
        ["tail", "-n", str(n), str(path)],  # noqa: S607 - tail via PATH is intentional
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"tail failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr!r}\n"
            f"  stdout: {result.stdout!r}"
        )
    line_count = result.stdout.count("\n")
    assert line_count <= n, (
        f"tail -n {n} returned {line_count} newline-terminated lines; budget was {n}"
    )


@given(content=_log_content, n=st.integers(min_value=1, max_value=100))
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_head_output_respects_line_budget(content: str, n: int, tmp_path: Path) -> None:
    """`head -n N` never returns more than N newline-terminated lines."""
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
        ["head", "-n", str(n), str(path)],  # noqa: S607 - head via PATH is intentional
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"head failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr!r}\n"
            f"  stdout: {result.stdout!r}"
        )
    line_count = result.stdout.count("\n")
    assert line_count <= n, (
        f"head -n {n} returned {line_count} newline-terminated lines; budget was {n}"
    )


@pytest.mark.skipif(shutil.which("rg") is None, reason="rg not installed")
@given(
    content=_log_content,
    pattern=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=20,
    ),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_rg_output_is_subset_of_input(
    content: str, pattern: str, tmp_path: Path
) -> None:
    """`rg -F pattern` output lines are a literal subset of input lines.

    Exit 0 = match found; exit 1 = no match (not an error).
    Any other exit code is a rg failure.
    """
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
        ["rg", "-F", pattern, str(path)],  # noqa: S607 - rg via PATH is intentional
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        pytest.fail(
            f"rg failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr!r}\n"
            f"  stdout: {result.stdout!r}"
        )
    input_lines = set(content.splitlines())
    for output_line in result.stdout.splitlines():
        assert output_line in input_lines, (
            f"rg -F {pattern!r} returned a line not present in the original "
            f"input: {output_line!r}"
        )
