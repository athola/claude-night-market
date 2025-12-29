"""Performance tests."""

from scripts.performance_benchmark import benchmark_wrapper


def test_performance_metrics() -> None:
    """Test performance metrics collection."""
    iterations = 50
    result = benchmark_wrapper(iterations=iterations)

    assert result["iterations"] == iterations
    assert isinstance(result["mean"], float)
    assert isinstance(result["median"], float)
    assert isinstance(result["p95"], float)
    assert isinstance(result["max"], float)
    assert result["max"] >= result["p95"] >= result["median"] >= 0
    assert result["max"] >= result["mean"] >= 0
