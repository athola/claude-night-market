"""
Feature: corpus-quality metrics (build increment 5)

As the tome research engine
I want diversity and efficiency measured over a finding set
So that the creativity and performance dimensions have deterministic
proxies.
"""

from __future__ import annotations

import pytest
from tome.metrics.corpus import dedup_ratio, findings_per_1k_tokens, source_diversity

from tests.factories import make_finding


class TestSourceDiversity:
    @pytest.mark.unit
    def test_single_channel_has_zero_diversity(self) -> None:
        findings = [make_finding(0.5, channel="code") for _ in range(3)]
        assert source_diversity(findings) == pytest.approx(0.0)

    @pytest.mark.unit
    def test_even_split_two_channels(self) -> None:
        findings = [
            make_finding(0.5, channel="code"),
            make_finding(0.5, channel="academic"),
        ]
        # Herfindahl = 0.5^2 + 0.5^2 = 0.5; diversity = 1 - 0.5 = 0.5
        assert source_diversity(findings) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_empty_is_zero(self) -> None:
        assert source_diversity([]) == 0.0


class TestEfficiency:
    @pytest.mark.unit
    def test_dedup_ratio(self) -> None:
        assert dedup_ratio(before=10, after=7) == pytest.approx(0.3)

    @pytest.mark.unit
    def test_dedup_ratio_zero_before_is_zero(self) -> None:
        assert dedup_ratio(before=0, after=0) == 0.0

    @pytest.mark.unit
    def test_findings_per_1k_tokens(self) -> None:
        assert findings_per_1k_tokens(count=20, tokens=4000) == pytest.approx(5.0)

    @pytest.mark.unit
    def test_findings_per_1k_tokens_zero_tokens_is_zero(self) -> None:
        assert findings_per_1k_tokens(count=5, tokens=0) == 0.0
