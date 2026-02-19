"""Unit tests for gravity and integration logic."""

from datetime import UTC, datetime
from math import isclose

from solar_sim.math3d import Vector3
from solar_sim.physics import (
    ASTRONOMICAL_UNIT_METERS,
    GRAVITATIONAL_CONSTANT,
    CelestialBody,
    SolarSystem,
    create_default_solar_system,
)


def test_acceleration_magnitude_matches_newtonian_solution() -> None:
    """Acceleration on Earth should match GM/r^2 from the sun."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=696_340_000.0,
        color_hex="#fff000",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.9722e24,
        radius_m=6_371_000.0,
        color_hex="#00aaff",
        position_m=Vector3(ASTRONOMICAL_UNIT_METERS, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([sun, earth])

    accelerations = system.compute_accelerations()
    earth_acc = accelerations[1]
    expected = GRAVITATIONAL_CONSTANT * sun.mass_kg / (ASTRONOMICAL_UNIT_METERS**2)

    assert isclose(earth_acc.magnitude(), expected, rel_tol=1e-6)
    assert earth_acc.x < 0.0
    assert isclose(earth_acc.y, 0.0, abs_tol=1e-12)
    assert isclose(earth_acc.z, 0.0, abs_tol=1e-12)


def test_single_body_moves_linearly_without_external_force() -> None:
    """A lone body should preserve velocity and move linearly."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(10.0, -4.0, 2.0),
    )
    system = SolarSystem([body], trail_limit=10)
    system.step(2.0)

    assert body.position_m == Vector3(20.0, -8.0, 4.0)
    assert body.velocity_m_per_s == Vector3(10.0, -4.0, 2.0)


def test_trail_is_capped_by_limit() -> None:
    """Trail history should not grow beyond configured cap."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(1.0, 0.0, 0.0),
    )
    system = SolarSystem([body], trail_limit=3)
    for _ in range(10):
        system.step(1.0)

    assert len(body.trail) == 3


def test_trail_expires_after_one_orbit_duration() -> None:
    """Trail points older than one orbital period should be removed."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(1.0, 0.0, 0.0),
        orbital_period_s=5.0,
    )
    system = SolarSystem([body], trail_limit=100)
    for _ in range(12):
        system.step(1.0)

    assert len(body.trail) <= 6
    assert all((system.simulation_time_s - point.simulation_time_s) <= 5.0 for point in body.trail)


def test_default_system_includes_orbital_inclination() -> None:
    """At least one planet should have a non-zero z position."""
    system = create_default_solar_system(datetime(2026, 1, 1, tzinfo=UTC))
    assert any(abs(body.position_m.z) > 1.0e9 for body in system.bodies[1:])


def test_default_system_distances_reflect_elliptic_orbits() -> None:
    """Initial heliocentric distances should not all match circular radii."""
    system = create_default_solar_system(datetime(2026, 1, 1, tzinfo=UTC))
    earth = next(body for body in system.bodies if body.name == "Earth")
    earth_distance_au = earth.position_m.magnitude() / ASTRONOMICAL_UNIT_METERS
    assert not isclose(earth_distance_au, 1.0, rel_tol=1e-4)


def test_default_planets_have_orbital_period_for_fading() -> None:
    """Planets should have orbital periods set for trail fade timing."""
    system = create_default_solar_system(datetime(2026, 1, 1, tzinfo=UTC))
    for body in system.bodies:
        if body.name == "Sun":
            continue
        assert body.orbital_period_s is not None
        assert body.orbital_period_s > 0.0
