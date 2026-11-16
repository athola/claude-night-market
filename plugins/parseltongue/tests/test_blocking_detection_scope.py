"""Blocking-call detection sees only what runs on the event loop.

A nested function handed to run_in_executor runs on a worker thread, and
a sync helper that does no I/O does not block. Both were reported as
blocking the loop, so the correct offload pattern read as a defect.
"""

from __future__ import annotations

import asyncio
import textwrap

import pytest

from parseltongue.analysis.async_analysis.blocking_detection import (
    detect_blocking_calls,
)


def _patterns(code: str) -> dict:
    return asyncio.run(detect_blocking_calls(textwrap.dedent(code)))[
        "blocking_patterns"
    ]


def test_sleep_inside_an_offloaded_nested_function_is_not_reported() -> None:
    patterns = _patterns(
        """
        import asyncio, time

        async def main():
            def blocking():
                time.sleep(1)
            await asyncio.get_running_loop().run_in_executor(None, blocking)
        """
    )
    assert "time_sleep" not in patterns


def test_call_to_a_pure_sync_helper_is_not_reported() -> None:
    patterns = _patterns(
        """
        def add(a, b):
            return a + b

        async def main():
            return add(1, 2)
        """
    )
    assert "sync_function_call" not in patterns


@pytest.mark.parametrize(
    ("helper_body", "pattern"),
    [
        ("time.sleep(1)", "time_sleep"),
        ("requests.get('https://x')", "requests"),
        ("open('f').read()", "file_io"),
    ],
)
def test_call_to_a_blocking_sync_helper_is_reported(
    helper_body: str, pattern: str
) -> None:
    patterns = _patterns(
        f"""
        import time, requests

        def helper():
            {helper_body}

        async def main():
            helper()
        """
    )
    assert patterns["sync_function_call"]["function_name"] == "helper"
    assert pattern in patterns
