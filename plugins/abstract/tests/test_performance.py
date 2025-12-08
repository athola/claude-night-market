# plugins/abstract/tests/test_performance.py
import time
from src.test_skill_wrapper import TestSkillWrapper

def test_wrapper_performance_overhead():
    """Ensure wrapper overhead is under 10ms"""

    wrapper = TestSkillWrapper()

    start_time = time.perf_counter()

    # Execute wrapper 100 times
    for _ in range(100):
        wrapper.execute({
            "skill-path": "test/skill",
            "phase": "red"
        })

    end_time = time.perf_counter()
    avg_time = (end_time - start_time) / 100

    # Should be under 10ms overhead
    assert avg_time < 0.01, f"Wrapper overhead too high: {avg_time:.3f}s"