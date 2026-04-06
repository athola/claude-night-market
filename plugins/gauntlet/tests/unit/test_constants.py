"""Unit tests for gauntlet shared constants."""

from __future__ import annotations

from gauntlet.constants import SECURITY_KEYWORDS


class TestSecurityKeywords:
    """Feature: Shared security keyword set for blast radius and flow analysis.

    As a gauntlet analyst
    I want a curated set of security-sensitive keywords
    So that blast_radius and flows can flag security-relevant code.
    """

    def test_is_frozenset(self) -> None:
        """SECURITY_KEYWORDS should be immutable."""
        assert isinstance(SECURITY_KEYWORDS, frozenset)

    def test_contains_core_auth_terms(self) -> None:
        """Core authentication terms must be present."""
        for term in ("auth", "login", "password", "token", "session"):
            assert term in SECURITY_KEYWORDS, f"Missing: {term}"

    def test_contains_crypto_terms(self) -> None:
        """Cryptography terms must be present."""
        for term in ("crypt", "encrypt", "decrypt", "hash", "sign", "verify"):
            assert term in SECURITY_KEYWORDS, f"Missing: {term}"

    def test_contains_data_access_terms(self) -> None:
        """Data access terms must be present."""
        for term in ("sql", "query", "execute", "sanitize"):
            assert term in SECURITY_KEYWORDS, f"Missing: {term}"

    def test_all_entries_are_lowercase(self) -> None:
        """All keywords should be lowercase for case-insensitive matching."""
        for kw in SECURITY_KEYWORDS:
            assert kw == kw.lower(), f"Not lowercase: {kw}"

    def test_not_empty(self) -> None:
        """Set must contain a meaningful number of keywords."""
        assert len(SECURITY_KEYWORDS) >= 10
