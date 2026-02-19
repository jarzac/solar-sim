"""Unit tests for mutable simulation settings."""

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

