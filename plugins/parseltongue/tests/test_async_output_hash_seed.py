"""The async analyzers' JSON must not depend on PYTHONHASHSEED (PAR-3).

`list(set(...))` ordered these lists by string hash, so the same source
produced different output from one run to the next.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

_SOURCE = """
import asyncio

async def alpha():
    try:
        await asyncio.wait_for(x(), timeout=1)
    except ValueError:
        return None
    except KeyError:
        pass
    except OSError:
        pass
    except TypeError:
        pass
    await asyncio.gather(a(), b())
    asyncio.create_task(c())
    async with asyncio.TaskGroup() as tg:
        pass

async def bravo():
    await asyncio.wait_for(x(), timeout=1)
    await asyncio.gather(a(), b())
    asyncio.create_task(c())
    async with asyncio.TaskGroup() as tg:
        pass

async def charlie():
    await asyncio.wait_for(x(), timeout=1)
    await asyncio.gather(a(), b())
    asyncio.create_task(c())
    async with asyncio.TaskGroup() as tg:
        pass

async def delta():
    await asyncio.wait_for(x(), timeout=1)
    await asyncio.gather(a(), b())
    asyncio.create_task(c())
    async with asyncio.TaskGroup() as tg:
        pass
"""

_PROBE = """
import asyncio, json, sys
from parseltongue.analysis.async_analysis.error_timeout import (
    analyze_error_handling, analyze_timeouts,
)
from parseltongue.analysis.async_analysis.function_analysis import (
    analyze_concurrency_patterns,
)
src = sys.stdin.read()
errors = asyncio.run(analyze_error_handling(src))["error_handling"]["functions"]
timeouts = asyncio.run(analyze_timeouts(src))["timeout_analysis"]["wait_for_usage"]
patterns = asyncio.run(analyze_concurrency_patterns(src))["concurrency_patterns"]
print(json.dumps({
    "exception_types": errors["alpha"]["exception_types"],
    "wait_for_usage": timeouts["functions"],
    "gather_usage": patterns["gather_usage"]["functions"],
    "create_task_usage": patterns["create_task_usage"]["functions"],
    "task_group_usage": patterns["task_group_usage"]["functions"],
}))
"""


def _run(seed: str) -> str:
    return subprocess.run(
        [sys.executable, "-c", _PROBE],
        input=_SOURCE,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONHASHSEED": seed},
    ).stdout


@pytest.mark.unit
def test_async_analyzer_lists_do_not_depend_on_hash_seed() -> None:
    outputs = {_run(seed) for seed in ("1", "2", "3", "4", "5", "6", "7", "8")}
    assert len(outputs) == 1
