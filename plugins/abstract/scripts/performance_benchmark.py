# plugins/abstract/scripts/performance_benchmark.py
"""Performance benchmarking utilities for Abstract plugin components.

This module provides tools for measuring and analyzing performance characteristics
of various plugin operations.
"""

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.test_skill_wrapper import TestSkillWrapper


def benchmark_wrapper(iterations: int = 1000) -> dict:
    """Benchmark wrapper performance."""
    wrapper = TestSkillWrapper()

    times: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        wrapper.execute({"skill-path": "test", "phase": "red"})
        end = time.perf_counter()
        times.append(end - start)

    return {
        "iterations": iterations,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
        "max": max(times),
    }


if __name__ == "__main__":
    result = benchmark_wrapper()
