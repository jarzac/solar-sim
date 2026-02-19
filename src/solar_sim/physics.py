"""Physics entities and time-stepping for the solar system."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import pi
from typing import cast

from solar_sim.math2d import Vector2

GRAVITATIONAL_CONSTANT = 6.67430e-11
ASTRONOMICAL_UNIT_METERS = 149_597_870_700.0


@dataclass(slots=True)
class CelestialBody:
    """A simulated body with physical and display properties."""

    name: str
    mass_kg: float
    radius_m: float
    color_hex: str
    position_m: Vector2
    velocity_m_per_s: Vector2
    trail: list[Vector2] = field(default_factory=list)


class SolarSystem:
    """N-body Newtonian simulation with velocity-Verlet integration."""

    def __init__(
        self,
        bodies: list[CelestialBody],
        *,
        gravity_multiplier: float = 1.0,
        trail_limit: int = 2_000,
    ) -> None:
        """Initialize simulation state."""
        if len(bodies) == 0:
            msg = "SolarSystem requires at least one body."
            raise ValueError(msg)
        self.bodies = bodies
        self.gravity_multiplier = gravity_multiplier
        self.trail_limit = trail_limit

    def set_gravity_multiplier(self, value: float) -> None:
        """Update the gravity multiplier."""
        self.gravity_multiplier = max(0.0, value)

    def compute_accelerations(self, positions: list[Vector2] | None = None) -> list[Vector2]:
        """Compute acceleration vectors for each body from Newtonian gravity."""
        pos = positions if positions is not None else [body.position_m for body in self.bodies]
        accelerations = [Vector2(0.0, 0.0) for _ in self.bodies]
        g_scaled = GRAVITATIONAL_CONSTANT * self.gravity_multiplier

        for i, _body_i in enumerate(self.bodies):
            ax = 0.0
            ay = 0.0
            for j, body_j in enumerate(self.bodies):
                if i == j:
                    continue
                delta = pos[j] - pos[i]
                dist = delta.magnitude()
                if dist == 0.0:
                    continue
                accel_mag = g_scaled * body_j.mass_kg / (dist * dist)
                direction = delta / dist
                ax += accel_mag * direction.x
                ay += accel_mag * direction.y
            accelerations[i] = Vector2(ax, ay)

        return accelerations

    def step(self, dt_seconds: float) -> None:
        """Advance simulation state using velocity-Verlet integration."""
        if dt_seconds <= 0.0:
            return

        initial_positions = [body.position_m for body in self.bodies]
        initial_velocities = [body.velocity_m_per_s for body in self.bodies]
        initial_accelerations = self.compute_accelerations(initial_positions)

        next_positions: list[Vector2] = []
        for pos, vel, acc in zip(
            initial_positions,
            initial_velocities,
            initial_accelerations,
            strict=True,
        ):
            next_positions.append(pos + vel * dt_seconds + acc * (0.5 * dt_seconds * dt_seconds))

        next_accelerations = self.compute_accelerations(next_positions)

        for idx, body in enumerate(self.bodies):
            body.position_m = next_positions[idx]
            body.velocity_m_per_s = initial_velocities[idx] + (
                initial_accelerations[idx] + next_accelerations[idx]
            ) * (0.5 * dt_seconds)
            body.trail.append(body.position_m)
            if len(body.trail) > self.trail_limit:
                body.trail = body.trail[-self.trail_limit :]


def _orbit_speed(semi_major_axis_m: float) -> float:
    """Return circular orbit speed around the sun approximation."""
    solar_mu = GRAVITATIONAL_CONSTANT * 1.9885e30
    return cast(float, (solar_mu / semi_major_axis_m) ** 0.5)


def _days_to_seconds(days: float) -> float:
    """Convert days to seconds."""
    return days * 24.0 * 60.0 * 60.0


def create_default_solar_system() -> SolarSystem:
    """Create an approximate real-scale solar system in the ecliptic plane."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=696_340_000.0,
        color_hex="#ffcc66",
        position_m=Vector2(0.0, 0.0),
        velocity_m_per_s=Vector2(0.0, 0.0),
    )

    # Distances and body sizes are approximate physical values.
    orbit_specs = [
        ("Mercury", 3.3011e23, 2_439_700.0, "#c9c9c9", 0.387 * ASTRONOMICAL_UNIT_METERS, 88.0),
        ("Venus", 4.8675e24, 6_051_800.0, "#f2d27b", 0.723 * ASTRONOMICAL_UNIT_METERS, 224.7),
        ("Earth", 5.9722e24, 6_371_000.0, "#5da9ff", 1.0 * ASTRONOMICAL_UNIT_METERS, 365.25),
        ("Mars", 6.4171e23, 3_389_500.0, "#d97b53", 1.524 * ASTRONOMICAL_UNIT_METERS, 687.0),
        ("Jupiter", 1.8982e27, 69_911_000.0, "#d6b48f", 5.203 * ASTRONOMICAL_UNIT_METERS, 4331.0),
        ("Saturn", 5.6834e26, 58_232_000.0, "#e8d6a8", 9.537 * ASTRONOMICAL_UNIT_METERS, 10_747.0),
        ("Uranus", 8.6810e25, 25_362_000.0, "#9adbf7", 19.191 * ASTRONOMICAL_UNIT_METERS, 30_589.0),
        (
            "Neptune",
            1.02413e26,
            24_622_000.0,
            "#547bf0",
            30.07 * ASTRONOMICAL_UNIT_METERS,
            59_800.0,
        ),
    ]

    planets: list[CelestialBody] = []
    for name, mass_kg, radius_m, color_hex, orbit_radius_m, orbital_days in orbit_specs:
        angle = 2.0 * pi * (_days_to_seconds(30.0) / _days_to_seconds(orbital_days))
        x = orbit_radius_m
        y = orbit_radius_m * 0.05 * angle  # Small spread so labels overlap less at t=0.
        speed = _orbit_speed(orbit_radius_m)
        planets.append(
            CelestialBody(
                name=name,
                mass_kg=mass_kg,
                radius_m=radius_m,
                color_hex=color_hex,
                position_m=Vector2(x, y),
                velocity_m_per_s=Vector2(-speed * 0.02, speed),
            )
        )

    return SolarSystem([sun, *planets])
