"""Unit tests for mutable simulation settings."""

from datetime import date

from solar_sim.config import SimulationSettings


def test_set_gravity_multiplier_clamps_to_zero() -> None:
    """Gravity multiplier should never drop below zero."""
    settings = SimulationSettings()
    settings.set_gravity_multiplier(-5.0)
    assert settings.gravity_multiplier == 0.0


def test_set_time_scale_has_minimum() -> None:
    """Time scale should clamp to one simulated second per real second."""
    settings = SimulationSettings()
    settings.set_time_scale(0.0)
    assert settings.time_scale_seconds_per_second == 1.0


def test_toggle_flags_are_mutable() -> None:
    """Orbit and label toggles should reflect assigned values."""
    settings = SimulationSettings(show_orbits=True, show_labels=True)
    settings.set_show_orbits(False)
    settings.set_show_labels(False)
    assert settings.show_orbits is False
    assert settings.show_labels is False


def test_projection_mode_updates() -> None:
    """Projection mode should switch between orthographic and perspective."""
    settings = SimulationSettings()
    settings.set_projection_mode("perspective")
    assert settings.projection_mode == "perspective"


def test_defaults_match_ui_expectations() -> None:
    """Default settings should match startup control defaults."""
    settings = SimulationSettings()
    assert settings.time_scale_seconds_per_second == 864_000.0
    assert settings.projection_mode == "perspective"


def test_start_date_updates() -> None:
    """Start date setter should update simulation epoch date."""
    settings = SimulationSettings()
    value = date(2024, 1, 7)
    settings.set_start_date(value)
    assert settings.start_date == value


def test_set_projection_mode_orthographic() -> None:
    """Projection mode should accept orthographic literal."""
    settings = SimulationSettings()
    settings.set_projection_mode("orthographic")
    assert settings.projection_mode == "orthographic"


def test_meters_per_pixel_default() -> None:
    """Default scale should match canvas projection defaults."""
    settings = SimulationSettings()
    assert settings.meters_per_pixel == 6.0e9


def test_set_time_scale_accepts_upper_range() -> None:
    """Time scale setter should allow large values up to UI maximum."""
    settings = SimulationSettings()
    settings.set_time_scale(5_000_000.0)
    assert settings.time_scale_seconds_per_second == 5_000_000.0


def test_set_gravity_multiplier_accepts_zero() -> None:
    """Gravity multiplier zero is valid (free-fall off)."""
    settings = SimulationSettings()
    settings.set_gravity_multiplier(0.0)
    assert settings.gravity_multiplier == 0.0
