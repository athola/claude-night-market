"""Shared fixtures for slop-detector benchmark tests."""

from __future__ import annotations

import pytest


def _make_clean_words(n: int) -> str:
    """Return n words of clean, slop-free prose."""
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
    cycle = (words * ((n // len(words)) + 1))[:n]
    return " ".join(cycle)


def _make_sloppy_words(n: int) -> str:
    """Return n words with roughly 10% slop density."""
    base = (
        "Let us delve into this multifaceted realm of documentation. "
        "This comprehensive solution leverages cutting-edge technology. "
        "In today's fast-paced world we must unleash the full potential. "
        "It is a testament to our nuanced and meticulous approach. "
        "The system processes requests and returns results efficiently. "
        "Each request is validated before storage in the database. "
        "Results return quickly for standard queries. "
        "We must streamline this process to beacon the future. "
        "This tapestry of features showcases our pivotal architecture. "
        "The cache layer handles data retrieval from the backend. "
    )
    words = base.split()
    cycle = (words * ((n // len(words)) + 1))[:n]
    return " ".join(cycle)


def _make_mixed_words(n: int) -> str:
    """Return n words with roughly 2% slop density (realistic prose)."""
    base = (
        "The system processes requests and returns results. "
        "Each request goes through validation before storage. "
        "Results return within fifty milliseconds for standard queries. "
        "Complex aggregations may take longer depending on data volume. "
        "The cache layer sits between the API and database. "
        "Failures are logged with structured error codes. "
        "Retries use exponential backoff up to five attempts. "
        "This pivotal component handles authentication tokens. "
        "Configuration is loaded once at startup and cached. "
        "The system processes requests and returns results correctly. "
        "Each request goes through validation before being stored. "
        "Results return within fifty milliseconds for most queries. "
        "Complex joins may take longer depending on index coverage. "
        "The cache layer reduces round-trips to the database. "
        "Error handling follows a consistent pattern throughout. "
        "The pipeline is meticulous about input sanitization. "
        "Retries use exponential backoff with jitter added. "
        "Configuration values are validated at load time always. "
        "Logs include request IDs for distributed tracing purposes. "
        "Deployments run health checks before accepting live traffic. "
    )
    words = base.split()
    cycle = (words * ((n // len(words)) + 1))[:n]
    return " ".join(cycle)


@pytest.fixture(scope="session")
def sample_small_text() -> str:
    """Clean text fixture under 100 words."""
    return _make_clean_words(80)


@pytest.fixture(scope="session")
def sample_medium_text() -> str:
    """Clean text fixture around 1000 words."""
    return _make_clean_words(1000)


@pytest.fixture(scope="session")
def sample_large_text() -> str:
    """Clean text fixture around 10000 words."""
    return _make_clean_words(10000)


@pytest.fixture(scope="session")
def sloppy_small_text() -> str:
    """High-slop text fixture under 100 words."""
    return _make_sloppy_words(80)


@pytest.fixture(scope="session")
def sloppy_medium_text() -> str:
    """High-slop text fixture around 1000 words."""
    return _make_sloppy_words(1000)


@pytest.fixture(scope="session")
def sloppy_large_text() -> str:
    """High-slop text fixture around 10000 words."""
    return _make_sloppy_words(10000)


@pytest.fixture(scope="session")
def mixed_medium_text() -> str:
    """Realistic mixed text fixture around 1000 words."""
    return _make_mixed_words(1000)


@pytest.fixture(scope="session")
def mixed_large_text() -> str:
    """Realistic mixed text fixture around 10000 words."""
    return _make_mixed_words(10000)
