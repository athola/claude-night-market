"""Version and blocking-call checks judge what the code actually does."""

from __future__ import annotations

import asyncio
import sys

import pytest

from parseltongue.analysis.async_analysis.blocking_detection import (
    detect_blocking_calls,
)
from parseltongue.analysis.compatibility_checker import CompatibilityChecker


def _minimum(code: str) -> str:
    return CompatibilityChecker().check_compatibility(code)["minimum_version"]


@pytest.mark.unit
def test_union_annotations_under_future_annotations_run_on_3_7() -> None:
    """With the future import, `int | None` is never evaluated at runtime."""
    code = "from __future__ import annotations\ndef f(x: int | None) -> None: ...\n"
    assert _minimum(code) != "3.10"


@pytest.mark.unit
def test_union_annotations_without_the_future_import_need_3_10() -> None:
    """Without it the annotation is evaluated at definition time."""
    assert _minimum("def f(x: int | None) -> None: ...\n") == "3.10"


@pytest.mark.unit
@pytest.mark.parametrize(
    "code",
    [
        "import tomllib\n",
        "from datetime import UTC\n",
        "import datetime\nnow = datetime.UTC\n",
        pytest.param(
            "try:\n    pass\nexcept* ValueError:\n    pass\n",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 11), reason="except* parses on 3.11+ only"
            ),
        ),
    ],
)
def test_3_11_features_raise_the_minimum(code: str) -> None:
    """These ran as compatible with 3.8."""
    assert _minimum(code) == "3.11"


def _blocking(code: str) -> dict:
    return asyncio.run(detect_blocking_calls(code))["blocking_patterns"]


@pytest.mark.unit
def test_a_bare_sleep_imported_from_asyncio_is_not_blocking() -> None:
    """`from asyncio import sleep` then `await sleep(1)` was reported as time.sleep."""
    code = "from asyncio import sleep\nasync def f():\n    await sleep(1)\n"
    assert "time_sleep" not in _blocking(code)


@pytest.mark.unit
def test_a_bare_sleep_imported_from_time_is_blocking() -> None:
    code = "from time import sleep\nasync def f():\n    sleep(1)\n"
    assert "time_sleep" in _blocking(code)


@pytest.mark.unit
def test_a_method_sharing_a_sync_function_name_is_not_that_function() -> None:
    """`client.close()` is not a call to a module-level `def close()`."""
    code = "def close():\n    pass\nasync def f(client):\n    await client.close()\n"
    assert "sync_function_call" not in _blocking(code)
