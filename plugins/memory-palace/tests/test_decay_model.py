"""Tests for quality decay model for knowledge entries.

Tests the DecayModel which implements time-based quality decay
with different decay curves based on entry maturity.
"""

from datetime import UTC, datetime, timedelta

import pytest
from memory_palace.corpus.decay_model import (
    DECAY_CONFIG,
    DecayCurve,
    DecayModel,
    DecayState,
)


class TestDecayCurve:
    """Test DecayCurve enum and configuration."""

    def test_decay_curves_defined(self) -> None:
        """Should have all expected decay curves."""
        assert DecayCurve.LINEAR is not None
        assert DecayCurve.EXPONENTIAL is not None
        assert DecayCurve.LOGARITHMIC is not None


class TestDecayConfig:
    """Test decay configuration for maturity levels."""

    def test_all_maturity_levels_configured(self) -> None:
        """Should have config for all maturity levels."""
        assert "seedling" in DECAY_CONFIG
        assert "growing" in DECAY_CONFIG
        assert "evergreen" in DECAY_CONFIG

    def test_config_has_required_fields(self) -> None:
        """Each config should have half_life_days and curve."""
        for maturity, config in DECAY_CONFIG.items():
            assert "half_life_days" in config, f"{maturity} missing half_life_days"
            assert "curve" in config, f"{maturity} missing curve"

    def test_half_life_ordering(self) -> None:
        """Seedlings should decay faster than evergreen."""
        assert (
            DECAY_CONFIG["seedling"]["half_life_days"]
            < DECAY_CONFIG["growing"]["half_life_days"]
        )
        assert (
            DECAY_CONFIG["growing"]["half_life_days"]
            < DECAY_CONFIG["evergreen"]["half_life_days"]
        )

    def test_decay_curve_types(self) -> None:
        """Decay curves should be DecayCurve enum values."""
        for config in DECAY_CONFIG.values():
            assert isinstance(config["curve"], DecayCurve)


class TestDecayState:
    """Test DecayState dataclass."""

    def test_create_decay_state(self) -> None:
        """Should create decay state with all fields."""
        state = DecayState(
            entry_id="entry-1",
            maturity="growing",
            decay_factor=0.75,
            days_since_validation=10,
            status="fresh",
        )
        assert state.entry_id == "entry-1"
        assert state.maturity == "growing"
        assert state.decay_factor == 0.75
        assert state.days_since_validation == 10
        assert state.status == "fresh"

    def test_valid_statuses(self) -> None:
        """Status should be one of the valid values."""
        valid_statuses = ["fresh", "stale", "critical", "archived"]
        for status in valid_statuses:
            state = DecayState(
                entry_id="test",
                maturity="growing",
                decay_factor=0.5,
                days_since_validation=0,
                status=status,
            )
            assert state.status == status


class TestDecayModel:
    """Test DecayModel functionality."""

    @pytest.fixture
    def model(self) -> DecayModel:
        """Create a fresh DecayModel instance."""
        return DecayModel()

    def test_calculate_decay_fresh_entry(self, model: DecayModel) -> None:
        """Entry validated today should have no decay."""
        state = model.calculate_decay(
            entry_id="entry-1",
            maturity="growing",
            last_validated=datetime.now(UTC),
        )
        assert state.decay_factor == pytest.approx(1.0, abs=0.01)
        assert state.days_since_validation == 0
        assert state.status == "fresh"

    def test_calculate_decay_seedling_half_life(self, model: DecayModel) -> None:
        """Seedling at half-life should have ~0.5 decay factor."""
        half_life = DECAY_CONFIG["seedling"]["half_life_days"]
        last_validated = datetime.now(UTC) - timedelta(days=half_life)

        state = model.calculate_decay(
            entry_id="entry-1",
            maturity="seedling",
            last_validated=last_validated,
        )
        assert state.decay_factor == pytest.approx(0.5, abs=0.1)

    def test_calculate_decay_growing_half_life(self, model: DecayModel) -> None:
        """Growing at half-life should have ~0.5 decay factor."""
        half_life = DECAY_CONFIG["growing"]["half_life_days"]
        last_validated = datetime.now(UTC) - timedelta(days=half_life)

        state = model.calculate_decay(
            entry_id="entry-1",
            maturity="growing",
            last_validated=last_validated,
        )
        assert state.decay_factor == pytest.approx(0.5, abs=0.1)

    def test_calculate_decay_evergreen_half_life(self, model: DecayModel) -> None:
        """Evergreen at half-life should have ~0.5 decay factor."""
        half_life = DECAY_CONFIG["evergreen"]["half_life_days"]
        last_validated = datetime.now(UTC) - timedelta(days=half_life)

        state = model.calculate_decay(
            entry_id="entry-1",
            maturity="evergreen",
            last_validated=last_validated,
        )
        assert state.decay_factor == pytest.approx(0.5, abs=0.15)

    def test_decay_factor_range(self, model: DecayModel) -> None:
        """Decay factor should always be between 0.0 and 1.0."""
        # Very old entry
        ancient = datetime.now(UTC) - timedelta(days=365)
        state = model.calculate_decay("entry-1", "seedling", ancient)
        assert 0.0 <= state.decay_factor <= 1.0

        # Future date (shouldn't happen but handle gracefully)
        future = datetime.now(UTC) + timedelta(days=1)
        state2 = model.calculate_decay("entry-2", "seedling", future)
        assert 0.0 <= state2.decay_factor <= 1.0

    def test_status_thresholds(self, model: DecayModel) -> None:
        """Status should reflect decay severity."""
        now = datetime.now(UTC)

        # Fresh: recently validated
        fresh = model.calculate_decay("e1", "growing", now)
        assert fresh.status == "fresh"

        # Stale/Critical: some decay (45 days with 30-day half-life = ~0.35 factor)
        stale_date = now - timedelta(days=45)
        stale = model.calculate_decay("e2", "growing", stale_date)
        assert stale.status in ["fresh", "stale", "critical"]

        # Critical: severe decay
        critical_date = now - timedelta(days=120)
        critical = model.calculate_decay("e3", "seedling", critical_date)
        assert critical.status in ["stale", "critical", "archived"]

    def test_validate_entry(self, model: DecayModel) -> None:
        """Should record validation and reset decay."""
        now = datetime.now(UTC)
        model.validate_entry("entry-1", now)

        state = model.calculate_decay(
            entry_id="entry-1",
            maturity="growing",
            last_validated=now,
        )
        assert state.decay_factor == pytest.approx(1.0, abs=0.01)

    def test_get_validation_date(self, model: DecayModel) -> None:
        """Should retrieve last validation date."""
        now = datetime.now(UTC)
        model.validate_entry("entry-1", now)

        validation_date = model.get_validation_date("entry-1")
        assert validation_date is not None
        assert validation_date == now

    def test_get_validation_date_unknown_entry(self, model: DecayModel) -> None:
        """Should return None for unknown entries."""
        validation_date = model.get_validation_date("nonexistent")
        assert validation_date is None

    def test_get_stale_entries(self, model: DecayModel) -> None:
        """Should identify entries needing attention."""
        now = datetime.now(UTC)

        # Register entries with different validation dates
        model.validate_entry("fresh-1", now)
        model.validate_entry("stale-1", now - timedelta(days=60))
        model.validate_entry("critical-1", now - timedelta(days=180))

        stale = model.get_stale_entries(
            entries=[
                {"id": "fresh-1", "maturity": "growing"},
                {"id": "stale-1", "maturity": "growing"},
                {"id": "critical-1", "maturity": "seedling"},
            ],
            threshold=0.5,
        )

        # Should include entries with decay below threshold
        entry_ids = [s.entry_id for s in stale]
        assert "fresh-1" not in entry_ids
        assert "critical-1" in entry_ids or len(stale) > 0

    def test_linear_decay_curve(self, model: DecayModel) -> None:
        """Linear decay should decrease uniformly."""
        factor1 = model._apply_decay_curve(10, 100, DecayCurve.LINEAR)
        factor2 = model._apply_decay_curve(20, 100, DecayCurve.LINEAR)
        factor3 = model._apply_decay_curve(30, 100, DecayCurve.LINEAR)

        # Linear: equal decrements
        diff1 = factor1 - factor2
        diff2 = factor2 - factor3
        assert diff1 == pytest.approx(diff2, abs=0.01)

    def test_exponential_decay_curve(self, model: DecayModel) -> None:
        """Exponential decay should follow half-life pattern."""
        half_life = 30
        factor_at_half_life = model._apply_decay_curve(
            half_life, half_life, DecayCurve.EXPONENTIAL
        )
        assert factor_at_half_life == pytest.approx(0.5, abs=0.05)

        factor_at_double = model._apply_decay_curve(
            half_life * 2, half_life, DecayCurve.EXPONENTIAL
        )
        assert factor_at_double == pytest.approx(0.25, abs=0.05)

    def test_logarithmic_decay_curve(self, model: DecayModel) -> None:
        """Logarithmic decay should follow expected pattern."""
        half_life = 90

        # At half-life, both should be around 0.5
        exp_hl = model._apply_decay_curve(half_life, half_life, DecayCurve.EXPONENTIAL)
        log_hl = model._apply_decay_curve(half_life, half_life, DecayCurve.LOGARITHMIC)

        # Exponential hits exactly 0.5 at half-life
        assert exp_hl == pytest.approx(0.5, abs=0.01)
        # Logarithmic has different curve but should be in reasonable range
        assert 0.3 <= log_hl <= 0.7

    def test_archive_threshold(self, model: DecayModel) -> None:
        """Entries below archive threshold should be marked archived."""
        ancient = datetime.now(UTC) - timedelta(days=500)
        model.validate_entry("ancient-1", ancient)

        state = model.calculate_decay("ancient-1", "seedling", ancient)
        # With such old date, should be archived or critical
        assert state.status in ["critical", "archived"]

    def test_export_validation_state(self, model: DecayModel) -> None:
        """Should export validation state as serializable data."""
        now = datetime.now(UTC)
        model.validate_entry("entry-1", now)
        model.validate_entry("entry-2", now - timedelta(days=10))

        exported = model.export_state()
        assert isinstance(exported, dict)
        assert "entry-1" in exported
        assert "entry-2" in exported

    def test_import_validation_state(self, model: DecayModel) -> None:
        """Should import validation state from serializable data."""
        now = datetime.now(UTC)
        state_data = {
            "entry-1": now.isoformat(),
            "entry-2": (now - timedelta(days=5)).isoformat(),
        }

        model.import_state(state_data)
        assert model.get_validation_date("entry-1") is not None
        assert model.get_validation_date("entry-2") is not None
