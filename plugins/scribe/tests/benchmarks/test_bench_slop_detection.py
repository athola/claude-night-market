"""Performance benchmarks for slop-detector pattern matching.

Run with:
    cd plugins/scribe && uv run python -m pytest tests/benchmarks/ -v -m benchmark
    cd plugins/scribe && uv run python tests/benchmarks/test_bench_slop_detection.py

Skip in CI:
    pytest -m "not benchmark"
"""

from __future__ import annotations

import re
import sys
import time

import pytest

# ---------------------------------------------------------------------------
# Pattern lists from vocabulary-patterns.md
# ---------------------------------------------------------------------------

TIER1_PATTERNS: list[str] = [
    r"\bdelve\b",
    r"\bembark\b",
    r"\btapestry\b",
    r"\brealm\b",
    r"\bbeacon\b",
    r"\bmultifaceted\b",
    r"\bpivotal\b",
    r"\bnuanced\b",
    r"\bmeticulous(?:ly)?\b",
    r"\bintricate\b",
    r"\bshowcasing\b",
    r"\bleveraging\b",
    r"\bstreamline\b",
    r"\bunleash\b",
]

TIER1_NEW_PATTERNS: list[str] = [
    r"\bunderscore[sd]?\b",
    r"\bbolster\b",
    r"\bfoster\b",
    r"\bseamless(?:ly)?\b",
    r"\binvaluable\b",
    r"\bvibrant\b",
    r"\binterplay\b",
    r"\bfacet[s]?\b",
    r"\bendeavor[s]?\b",
    r"\baptly\b",
    r"\btirelessly\b",
    r"\bvividly\b",
]

PHRASE_PATTERNS: list[str] = [
    r"in today's fast-paced",
    r"cannot be overstated",
    r"it's worth noting",
    r"at its core",
    r"a testament to",
    r"unlock the (?:full )?potential",
    r"embark on (?:a |the )?journey",
    r"nestled in the heart",
    r"treasure trove",
    r"game[- ]changer",
    r"it's important to (?:note|remember|understand) that",
    r"generally speaking",
    r"from a broader perspective",
    r"one might argue",
    r"it could be said",
    r"there is growing evidence",
    r"areas for improvement",
    r"invaluable resource",
    r"underscores the importance",
]

CONCLUSION_STARTERS: list[str] = [
    r"^Overall,",
    r"^In conclusion,",
    r"^In summary,",
    r"^Ultimately,",
    r"^To sum up,",
]

HIGH_FREQ_SHIFT_WORDS: list[str] = [
    "across",
    "additionally",
    "comprehensive",
    "crucial",
    "enhancing",
    "exhibited",
    "insights",
    "notably",
    "particularly",
    "within",
]

# ---------------------------------------------------------------------------
# Compiled pattern objects (module-level, compiled once)
# ---------------------------------------------------------------------------

_TIER1_COMBINED = re.compile(
    r"(" + "|".join(TIER1_PATTERNS + TIER1_NEW_PATTERNS) + r")",
    re.IGNORECASE,
)
_PHRASE_COMBINED = re.compile(
    r"(" + "|".join(PHRASE_PATTERNS) + r")",
    re.IGNORECASE,
)
_CONCLUSION_COMBINED = re.compile(
    r"(" + "|".join(CONCLUSION_STARTERS) + r")",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Text generators
# ---------------------------------------------------------------------------


def generate_clean_text(word_count: int) -> str:
    """Produce text with zero slop words."""
    base = (
        "The system processes requests and returns results. "
        "Each request goes through validation before storage. "
        "Results return within fifty milliseconds for most queries. "
        "Complex aggregations may take longer depending on data volume. "
        "The cache layer sits between the API and the database. "
        "Failures are logged with structured error codes. "
        "Retries use exponential backoff with a hard limit of five attempts. "
    )
    words = base.split()
    cycle = (words * ((word_count // len(words)) + 1))[:word_count]
    return " ".join(cycle)


def generate_sloppy_text(word_count: int) -> str:
    """Produce text with roughly 10% slop density."""
    base = (
        "Let us delve into this multifaceted realm of documentation. "
        "This comprehensive solution leverages cutting-edge technology. "
        "In today's fast-paced world we must unleash the full potential. "
        "It is a testament to our nuanced and meticulous approach. "
        "The system processes requests and returns results efficiently. "
        "Each request is validated before storage in the database. "
        "Results return quickly for standard queries processed daily. "
        "We must streamline this process to beacon the future forward. "
        "This tapestry of features showcases our pivotal architecture. "
        "The cache layer handles data retrieval from the backend. "
    )
    words = base.split()
    cycle = (words * ((word_count // len(words)) + 1))[:word_count]
    return " ".join(cycle)


def generate_mixed_text(word_count: int) -> str:
    """Produce text with roughly 2% slop density (realistic prose)."""
    base = (
        "The system processes requests and returns results. "
        "Each request goes through validation before storage. "
        "Results return within fifty milliseconds for standard queries. "
        "Complex aggregations may take longer depending on data volume. "
        "The cache layer sits between the API and database layer. "
        "Failures are logged with structured error codes always. "
        "Retries use exponential backoff up to five attempts total. "
        "This pivotal component handles authentication tokens securely. "
        "Configuration is loaded once at startup and cached in memory. "
        "The system processes requests and returns results correctly. "
        "Each request goes through validation before being stored. "
        "Results return within fifty milliseconds for most queries. "
        "Complex joins may take longer depending on index coverage. "
        "The cache layer reduces round-trips to the database server. "
        "Error handling follows a consistent pattern throughout code. "
        "The pipeline is meticulous about input sanitization always. "
        "Retries use exponential backoff with jitter added always. "
        "Configuration values are validated at load time every start. "
        "Logs include request IDs for distributed tracing purposes. "
        "Deployments run health checks before accepting live traffic. "
    )
    words = base.split()
    cycle = (words * ((word_count // len(words)) + 1))[:word_count]
    return " ".join(cycle)


# ---------------------------------------------------------------------------
# Scoring pipeline
# ---------------------------------------------------------------------------


def count_tier1_matches(text: str) -> int:
    """Return number of tier-1 pattern matches in text."""
    return len(_TIER1_COMBINED.findall(text))


def count_phrase_matches(text: str) -> int:
    """Return number of phrase pattern matches in text."""
    return len(_PHRASE_COMBINED.findall(text))


def count_conclusion_matches(text: str) -> int:
    """Return number of conclusion-starter matches in text."""
    return len(_CONCLUSION_COMBINED.findall(text))


def count_cooccurrence(text: str) -> int:
    """Count how many high-frequency shift words appear in text."""
    lower = text.lower()
    return sum(1 for w in HIGH_FREQ_SHIFT_WORDS if w in lower)


def calculate_vocabulary_score(text: str) -> float:
    """Return slop score 0-10 for text using vocabulary and phrase patterns."""
    word_count = len(text.split())
    if word_count == 0:
        return 0.0
    tier1 = count_tier1_matches(text)
    phrases = count_phrase_matches(text)
    raw = (tier1 * 3) + (phrases * 3)
    normalized = (raw / word_count) * 100
    return min(10.0, normalized)


def run_full_pipeline(text: str) -> tuple[float, int, int, int, int]:
    """Run all detection passes and return (score, tier1, phrases, conclusions, cooccurrence)."""
    tier1 = count_tier1_matches(text)
    phrases = count_phrase_matches(text)
    conclusions = count_conclusion_matches(text)
    cooc = count_cooccurrence(text)
    score = calculate_vocabulary_score(text)
    return score, tier1, phrases, conclusions, cooc


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------


def _bench(label: str, fn, text: str, target_ms: float, iterations: int = 10) -> bool:
    """Time fn(text) over iterations, print result, return True if within target."""
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn(text)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    avg_ms = sum(times) / len(times)
    word_count = len(text.split())
    passed = avg_ms <= target_ms
    status = "PASS" if passed else "FAIL"
    print(
        f"  {status}  {label:<55}  {word_count:>6} words  "
        f"{avg_ms:6.2f}ms  (target <{target_ms:.0f}ms)"
    )
    return passed


def _bench_compile(
    label: str, patterns: list[str], target_ms: float, iterations: int = 100
) -> bool:
    """Time pattern compilation and return True if within target."""
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        combined = re.compile(r"(" + "|".join(patterns) + r")", re.IGNORECASE)
        _ = combined
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    avg_ms = sum(times) / len(times)
    passed = avg_ms <= target_ms
    status = "PASS" if passed else "FAIL"
    print(
        f"  {status}  {label:<55}  {'N/A':>6}        "
        f"{avg_ms:6.2f}ms  (target <{target_ms:.0f}ms)"
    )
    return passed


def run_standalone_benchmarks() -> int:
    """Run all benchmarks and return exit code (0=all passed, 1=any failed)."""
    small = generate_clean_text(80)
    medium_clean = generate_clean_text(1000)
    large_clean = generate_clean_text(10000)
    medium_sloppy = generate_sloppy_text(1000)
    large_sloppy = generate_sloppy_text(10000)
    medium_mixed = generate_mixed_text(1000)
    large_mixed = generate_mixed_text(10000)

    results: list[bool] = []

    print("\n" + "=" * 80)
    print("Slop-Detector Benchmark Suite")
    print("=" * 80)

    print("\n-- Pattern compilation --")
    results.append(
        _bench_compile(
            "tier1 combined compile", TIER1_PATTERNS + TIER1_NEW_PATTERNS, target_ms=2.0
        )
    )
    results.append(
        _bench_compile("phrase combined compile", PHRASE_PATTERNS, target_ms=2.0)
    )

    print("\n-- Tier-1 matching --")
    results.append(
        _bench(
            "tier1 match: small clean (<100w)",
            count_tier1_matches,
            small,
            target_ms=10.0,
        )
    )
    results.append(
        _bench(
            "tier1 match: medium clean (~1000w)",
            count_tier1_matches,
            medium_clean,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "tier1 match: large clean (~10000w)",
            count_tier1_matches,
            large_clean,
            target_ms=200.0,
        )
    )
    results.append(
        _bench(
            "tier1 match: medium sloppy (~1000w)",
            count_tier1_matches,
            medium_sloppy,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "tier1 match: large sloppy (~10000w)",
            count_tier1_matches,
            large_sloppy,
            target_ms=200.0,
        )
    )

    print("\n-- Phrase matching --")
    results.append(
        _bench(
            "phrase match: small clean (<100w)",
            count_phrase_matches,
            small,
            target_ms=10.0,
        )
    )
    results.append(
        _bench(
            "phrase match: medium clean (~1000w)",
            count_phrase_matches,
            medium_clean,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "phrase match: large clean (~10000w)",
            count_phrase_matches,
            large_clean,
            target_ms=200.0,
        )
    )
    results.append(
        _bench(
            "phrase match: medium sloppy (~1000w)",
            count_phrase_matches,
            medium_sloppy,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "phrase match: large sloppy (~10000w)",
            count_phrase_matches,
            large_sloppy,
            target_ms=200.0,
        )
    )

    print("\n-- Full scoring pipeline --")
    results.append(
        _bench(
            "pipeline: small clean (<100w)", run_full_pipeline, small, target_ms=10.0
        )
    )
    results.append(
        _bench(
            "pipeline: medium clean (~1000w)",
            run_full_pipeline,
            medium_clean,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "pipeline: large clean (~10000w)",
            run_full_pipeline,
            large_clean,
            target_ms=200.0,
        )
    )
    results.append(
        _bench(
            "pipeline: medium sloppy (~1000w)",
            run_full_pipeline,
            medium_sloppy,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "pipeline: large sloppy (~10000w)",
            run_full_pipeline,
            large_sloppy,
            target_ms=200.0,
        )
    )
    results.append(
        _bench(
            "pipeline: medium mixed (~1000w)",
            run_full_pipeline,
            medium_mixed,
            target_ms=50.0,
        )
    )
    results.append(
        _bench(
            "pipeline: large mixed (~10000w)",
            run_full_pipeline,
            large_mixed,
            target_ms=200.0,
        )
    )

    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} benchmarks within target")
    print("=" * 80 + "\n")

    return 0 if passed == total else 1


# ---------------------------------------------------------------------------
# pytest-based benchmark tests
# ---------------------------------------------------------------------------


@pytest.mark.benchmark
def test_tier1_small_within_target(sample_small_text: str) -> None:
    """Tier-1 matching on small text must complete in under 10ms."""
    t0 = time.perf_counter()
    count_tier1_matches(sample_small_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 10.0, f"tier1 small took {elapsed_ms:.2f}ms, target <10ms"


@pytest.mark.benchmark
def test_tier1_medium_within_target(sample_medium_text: str) -> None:
    """Tier-1 matching on medium text must complete in under 50ms."""
    t0 = time.perf_counter()
    count_tier1_matches(sample_medium_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"tier1 medium took {elapsed_ms:.2f}ms, target <50ms"


@pytest.mark.benchmark
def test_tier1_large_within_target(sample_large_text: str) -> None:
    """Tier-1 matching on large text must complete in under 200ms."""
    t0 = time.perf_counter()
    count_tier1_matches(sample_large_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 200.0, f"tier1 large took {elapsed_ms:.2f}ms, target <200ms"


@pytest.mark.benchmark
def test_phrase_small_within_target(sample_small_text: str) -> None:
    """Phrase matching on small text must complete in under 10ms."""
    t0 = time.perf_counter()
    count_phrase_matches(sample_small_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 10.0, f"phrase small took {elapsed_ms:.2f}ms, target <10ms"


@pytest.mark.benchmark
def test_phrase_medium_within_target(sample_medium_text: str) -> None:
    """Phrase matching on medium text must complete in under 50ms."""
    t0 = time.perf_counter()
    count_phrase_matches(sample_medium_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"phrase medium took {elapsed_ms:.2f}ms, target <50ms"


@pytest.mark.benchmark
def test_phrase_large_within_target(sample_large_text: str) -> None:
    """Phrase matching on large text must complete in under 200ms."""
    t0 = time.perf_counter()
    count_phrase_matches(sample_large_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 200.0, f"phrase large took {elapsed_ms:.2f}ms, target <200ms"


@pytest.mark.benchmark
def test_pipeline_small_within_target(sample_small_text: str) -> None:
    """Full pipeline on small text must complete in under 10ms."""
    t0 = time.perf_counter()
    run_full_pipeline(sample_small_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 10.0, f"pipeline small took {elapsed_ms:.2f}ms, target <10ms"


@pytest.mark.benchmark
def test_pipeline_medium_within_target(sample_medium_text: str) -> None:
    """Full pipeline on medium text must complete in under 50ms."""
    t0 = time.perf_counter()
    run_full_pipeline(sample_medium_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"pipeline medium took {elapsed_ms:.2f}ms, target <50ms"


@pytest.mark.benchmark
def test_pipeline_large_within_target(sample_large_text: str) -> None:
    """Full pipeline on large text must complete in under 200ms."""
    t0 = time.perf_counter()
    run_full_pipeline(sample_large_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 200.0, f"pipeline large took {elapsed_ms:.2f}ms, target <200ms"


@pytest.mark.benchmark
def test_pipeline_sloppy_medium_within_target(sloppy_medium_text: str) -> None:
    """Full pipeline on sloppy medium text must complete in under 50ms."""
    t0 = time.perf_counter()
    run_full_pipeline(sloppy_medium_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, (
        f"pipeline sloppy medium took {elapsed_ms:.2f}ms, target <50ms"
    )


@pytest.mark.benchmark
def test_pipeline_sloppy_large_within_target(sloppy_large_text: str) -> None:
    """Full pipeline on sloppy large text must complete in under 200ms."""
    t0 = time.perf_counter()
    run_full_pipeline(sloppy_large_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 200.0, (
        f"pipeline sloppy large took {elapsed_ms:.2f}ms, target <200ms"
    )


@pytest.mark.benchmark
def test_pattern_compilation_tier1() -> None:
    """Tier-1 combined pattern compilation must complete in under 2ms."""
    t0 = time.perf_counter()
    pat = re.compile(
        r"(" + "|".join(TIER1_PATTERNS + TIER1_NEW_PATTERNS) + r")",
        re.IGNORECASE,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert pat is not None
    assert elapsed_ms < 2.0, f"tier1 compile took {elapsed_ms:.2f}ms, target <2ms"


@pytest.mark.benchmark
def test_pattern_compilation_phrases() -> None:
    """Phrase combined pattern compilation must complete in under 2ms."""
    t0 = time.perf_counter()
    pat = re.compile(
        r"(" + "|".join(PHRASE_PATTERNS) + r")",
        re.IGNORECASE,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert pat is not None
    assert elapsed_ms < 2.0, f"phrase compile took {elapsed_ms:.2f}ms, target <2ms"


@pytest.mark.benchmark
def test_sloppy_text_score_above_threshold(sloppy_medium_text: str) -> None:
    """Sloppy text must score above 0.5 (detection sanity check)."""
    score = calculate_vocabulary_score(sloppy_medium_text)
    assert score > 0.5, f"sloppy text scored {score:.2f}, expected >0.5"


@pytest.mark.benchmark
def test_clean_text_score_below_threshold(sample_medium_text: str) -> None:
    """Clean text must score below 0.5 (false-positive sanity check)."""
    score = calculate_vocabulary_score(sample_medium_text)
    assert score < 0.5, f"clean text scored {score:.2f}, expected <0.5"


@pytest.mark.benchmark
def test_generate_clean_text_word_count() -> None:
    """generate_clean_text produces the requested word count (within 5%)."""
    for target in (80, 1000, 10000):
        text = generate_clean_text(target)
        actual = len(text.split())
        assert abs(actual - target) <= max(5, target // 20), (
            f"generate_clean_text({target}) produced {actual} words"
        )


@pytest.mark.benchmark
def test_generate_sloppy_text_word_count() -> None:
    """generate_sloppy_text produces the requested word count (within 5%)."""
    for target in (80, 1000, 10000):
        text = generate_sloppy_text(target)
        actual = len(text.split())
        assert abs(actual - target) <= max(5, target // 20), (
            f"generate_sloppy_text({target}) produced {actual} words"
        )


@pytest.mark.benchmark
def test_generate_mixed_text_word_count() -> None:
    """generate_mixed_text produces the requested word count (within 5%)."""
    for target in (80, 1000, 10000):
        text = generate_mixed_text(target)
        actual = len(text.split())
        assert abs(actual - target) <= max(5, target // 20), (
            f"generate_mixed_text({target}) produced {actual} words"
        )


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(run_standalone_benchmarks())
