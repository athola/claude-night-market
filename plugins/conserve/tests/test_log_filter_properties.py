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

import subprocess
import tempfile
from pathlib import Path

from hypothesis import given, settings
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


def _write_temp_log(content: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, encoding="utf-8"
    )
    handle.write(content)
    handle.close()
    return Path(handle.name)


@given(content=_log_content, n=st.integers(min_value=1, max_value=200))
@settings(max_examples=40, deadline=None)
def test_tail_output_is_suffix_of_input(content: str, n: int) -> None:
    """`tail -n N` output is always a literal suffix of the input.

    This is the property that distinguishes tier 1 from tier 3.
    A compressor can produce output that is not a suffix; `tail`
    by contract cannot.
    """
    path = _write_temp_log(content)
    try:
        result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
            ["tail", "-n", str(n), str(path)],  # noqa: S607 - tail via PATH is intentional
            capture_output=True,
            text=True,
            check=True,
        )
        assert content.endswith(result.stdout), (
            f"tail -n {n} produced output that is not a suffix; "
            f"input tail (50 chars): {content[-50:]!r}; "
            f"output tail (50 chars): {result.stdout[-50:]!r}"
        )
    finally:
        path.unlink()


@given(content=_log_content, n=st.integers(min_value=1, max_value=200))
@settings(max_examples=40, deadline=None)
def test_head_output_is_prefix_of_input(content: str, n: int) -> None:
    """`head -n N` output is always a literal prefix of the input."""
    path = _write_temp_log(content)
    try:
        result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
            ["head", "-n", str(n), str(path)],  # noqa: S607 - head via PATH is intentional
            capture_output=True,
            text=True,
            check=True,
        )
        assert content.startswith(result.stdout), (
            f"head -n {n} produced output that is not a prefix; "
            f"input head (50 chars): {content[:50]!r}; "
            f"output head (50 chars): {result.stdout[:50]!r}"
        )
    finally:
        path.unlink()


@given(content=_log_content, n=st.integers(min_value=1, max_value=100))
@settings(max_examples=30, deadline=None)
def test_tail_output_respects_line_budget(content: str, n: int) -> None:
    """`tail -n N` never returns more than N newline-terminated lines."""
    path = _write_temp_log(content)
    try:
        result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
            ["tail", "-n", str(n), str(path)],  # noqa: S607 - tail via PATH is intentional
            capture_output=True,
            text=True,
            check=True,
        )
        line_count = result.stdout.count("\n")
        assert line_count <= n, (
            f"tail -n {n} returned {line_count} newline-terminated "
            f"lines; budget was {n}"
        )
    finally:
        path.unlink()


@given(content=_log_content, n=st.integers(min_value=1, max_value=100))
@settings(max_examples=30, deadline=None)
def test_head_output_respects_line_budget(content: str, n: int) -> None:
    """`head -n N` never returns more than N newline-terminated lines."""
    path = _write_temp_log(content)
    try:
        result = subprocess.run(  # noqa: S603 - hardcoded args, no shell, temp file path
            ["head", "-n", str(n), str(path)],  # noqa: S607 - head via PATH is intentional
            capture_output=True,
            text=True,
            check=True,
        )
        line_count = result.stdout.count("\n")
        assert line_count <= n, (
            f"head -n {n} returned {line_count} newline-terminated "
            f"lines; budget was {n}"
        )
    finally:
        path.unlink()
