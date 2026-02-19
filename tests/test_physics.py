"""Unit tests for gravity and integration logic."""

from math import isclose

from solar_sim.math2d import Vector2
from solar_sim.physics import (
    ASTRONOMICAL_UNIT_METERS,
    GRAVITATIONAL_CONSTANT,
    CelestialBody,
    SolarSystem,
)


def test_acceleration_magnitude_matches_newtonian_solution() -> None:
    """Acceleration on Earth should match GM/r^2 from the sun."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=696_340_000.0,
        color_hex="#fff000",
        position_m=Vector2(0.0, 0.0),
        velocity_m_per_s=Vector2(0.0, 0.0),
    )
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.9722e24,
        radius_m=6_371_000.0,
        color_hex="#00aaff",
        position_m=Vector2(ASTRONOMICAL_UNIT_METERS, 0.0),
        velocity_m_per_s=Vector2(0.0, 0.0),
    )
    system = SolarSystem([sun, earth])

    accelerations = system.compute_accelerations()
    earth_acc = accelerations[1]
    expected = GRAVITATIONAL_CONSTANT * sun.mass_kg / (ASTRONOMICAL_UNIT_METERS**2)

    assert isclose(earth_acc.magnitude(), expected, rel_tol=1e-6)
    assert earth_acc.x < 0.0
    assert isclose(earth_acc.y, 0.0, abs_tol=1e-12)


def test_single_body_moves_linearly_without_external_force() -> None:
    """A lone body should preserve velocity and move linearly."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector2(0.0, 0.0),
        velocity_m_per_s=Vector2(10.0, -4.0),
    )
    system = SolarSystem([body], trail_limit=10)
    system.step(2.0)

    assert body.position_m == Vector2(20.0, -8.0)
    assert body.velocity_m_per_s == Vector2(10.0, -4.0)


def test_trail_is_capped_by_limit() -> None:
    """Trail history should not grow beyond configured cap."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector2(0.0, 0.0),
        velocity_m_per_s=Vector2(1.0, 0.0),
    )
    system = SolarSystem([body], trail_limit=3)
    for _ in range(10):
        system.step(1.0)

    assert len(body.trail) == 3

