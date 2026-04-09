"""Unit tests for gravity and integration logic."""

from datetime import UTC, datetime
from math import isclose

import pytest

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


def test_solar_system_requires_at_least_one_body() -> None:
    """Empty body list should raise ValueError."""
    with pytest.raises(ValueError, match="at least one"):
        SolarSystem([])


def test_step_non_positive_dt_is_noop() -> None:
    """Zero or negative dt should not advance time or positions."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(3.0, 4.0, 5.0),
        velocity_m_per_s=Vector3(1.0, 0.0, 0.0),
    )
    system = SolarSystem([body])
    pos_before = Vector3(body.position_m.x, body.position_m.y, body.position_m.z)
    system.step(0.0)
    assert system.simulation_time_s == 0.0
    assert body.position_m == pos_before

    system.step(-1.0)
    assert system.simulation_time_s == 0.0
    assert body.position_m == pos_before


def test_set_gravity_multiplier_clamps_negative() -> None:
    """SolarSystem.set_gravity_multiplier should clamp to zero."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([body])
    system.set_gravity_multiplier(-2.0)
    assert system.gravity_multiplier == 0.0


def test_zero_gravity_multiplier_zeroes_accelerations() -> None:
    """With gravity multiplier zero, pairwise gravity should vanish."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=1.0,
        color_hex="#fff000",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.9722e24,
        radius_m=1.0,
        color_hex="#00aaff",
        position_m=Vector3(ASTRONOMICAL_UNIT_METERS, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([sun, earth])
    system.set_gravity_multiplier(0.0)
    accs = system.compute_accelerations()
    assert accs[0].magnitude() == 0.0
    assert accs[1].magnitude() == 0.0


def test_gravity_multiplier_scales_acceleration() -> None:
    """Doubling gravity multiplier should double acceleration magnitude."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=1.0,
        color_hex="#fff000",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.9722e24,
        radius_m=1.0,
        color_hex="#00aaff",
        position_m=Vector3(ASTRONOMICAL_UNIT_METERS, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([sun, earth])
    mag_one = system.compute_accelerations()[1].magnitude()
    system.set_gravity_multiplier(2.0)
    mag_two = system.compute_accelerations()[1].magnitude()
    assert isclose(mag_two / mag_one, 2.0, rel_tol=1e-12)


def test_overlapping_positions_skip_pairwise_term() -> None:
    """Zero distance between distinct bodies should skip that pair (no NaNs)."""
    a = CelestialBody(
        name="A",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(1.0, 2.0, 3.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    b = CelestialBody(
        name="B",
        mass_kg=2.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(1.0, 2.0, 3.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([a, b])
    accs = system.compute_accelerations()
    assert accs[0].magnitude() == 0.0
    assert accs[1].magnitude() == 0.0


def test_compute_accelerations_respects_custom_positions() -> None:
    """Optional positions list should be used instead of body positions."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=1.0,
        color_hex="#fff000",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.9722e24,
        radius_m=1.0,
        color_hex="#00aaff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([sun, earth])
    acc_at_au = system.compute_accelerations(
        [Vector3(0.0, 0.0, 0.0), Vector3(ASTRONOMICAL_UNIT_METERS, 0.0, 0.0)]
    )[1]
    assert acc_at_au.x < 0.0
    assert isclose(acc_at_au.y, 0.0, abs_tol=1e-12)


def test_two_body_acceleration_ratio_matches_mass_ratio() -> None:
    """|a1|/|a2| should equal m2/m1 for two isolated masses on the x-axis."""
    m1 = 3.0e26
    m2 = 2.0e24
    r = 4.0e11
    b1 = CelestialBody(
        name="Heavy",
        mass_kg=m1,
        radius_m=1.0,
        color_hex="#fff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    b2 = CelestialBody(
        name="Light",
        mass_kg=m2,
        radius_m=1.0,
        color_hex="#fff",
        position_m=Vector3(r, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([b1, b2])
    acc1, acc2 = system.compute_accelerations()
    assert isclose(acc1.magnitude() / acc2.magnitude(), m2 / m1, rel_tol=1e-9)
    assert acc1.x > 0.0
    assert acc2.x < 0.0


def test_trail_sampling_throttles_when_period_positive() -> None:
    """Trail append should respect trail_sample_period_s when set above zero."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(1.0, 0.0, 0.0),
        orbital_period_s=None,
        trail_sample_period_s=10.0,
    )
    system = SolarSystem([body], trail_limit=100)
    for _ in range(10):
        system.step(1.0)
    assert len(body.trail) == 1

    system.step(1.0)
    assert len(body.trail) == 2


def test_trail_without_orbital_period_not_cut_by_age() -> None:
    """With orbital_period_s None, trail should only be bounded by trail_limit."""
    body = CelestialBody(
        name="Probe",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(1.0, 0.0, 0.0),
        orbital_period_s=None,
        trail_sample_period_s=0.0,
    )
    system = SolarSystem([body], trail_limit=5)
    for _ in range(10):
        system.step(1.0)
    assert len(body.trail) == 5


def test_create_default_solar_system_accepts_none_epoch() -> None:
    """None epoch should use current UTC (smoke: Sun + planets + Moon)."""
    system = create_default_solar_system(None)
    assert len(system.bodies) == 10
    assert system.bodies[0].name == "Sun"


def test_default_system_includes_moon_near_earth() -> None:
    """Moon should orbit Earth at approximately the mean semi-major axis."""
    system = create_default_solar_system(datetime(2026, 1, 1, tzinfo=UTC))
    earth = next(body for body in system.bodies if body.name == "Earth")
    moon = next(body for body in system.bodies if body.name == "Moon")
    separation_m = (moon.position_m - earth.position_m).magnitude()
    assert isclose(separation_m, 384_399_000.0, rel_tol=1e-9)
    assert moon.orbital_period_s is not None
    assert moon.orbital_period_s > 0.0
