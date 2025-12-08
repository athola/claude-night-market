# plugins/abstract/scripts/performance_benchmark.py
import time
import statistics
from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.test_skill_wrapper import TestSkillWrapper

def benchmark_wrapper(iterations: int = 1000) -> Dict:
    """Benchmark wrapper performance"""
    wrapper = TestSkillWrapper()

    times: List[float] = []

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
        "max": max(times)
    }

if __name__ == "__main__":
    result = benchmark_wrapper()
    print(f"Performance Results ({result['iterations']} iterations):")
    print(f"Mean: {result['mean']*1000:.2f}ms")
    print(f"P95: {result['p95']*1000:.2f}ms")
    print(f"Max: {result['max']*1000:.2f}ms")