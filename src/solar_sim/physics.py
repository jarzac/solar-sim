"""Physics entities and time-stepping for the solar system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import cos, pi, sin, sqrt

from solar_sim.math3d import Vector3

GRAVITATIONAL_CONSTANT = 6.67430e-11
ASTRONOMICAL_UNIT_METERS = 149_597_870_700.0
JULIAN_DAY_UNIX_EPOCH = 2_440_587.5
JULIAN_DAY_J2000 = 2_451_545.0
DAYS_PER_JULIAN_CENTURY = 36_525.0


@dataclass(frozen=True, slots=True)
class OrbitalElements:
    """Keplerian elements and secular rates from JPL DE440 approximation."""

    semi_major_axis_au: float
    semi_major_axis_au_per_century: float
    eccentricity: float
    eccentricity_per_century: float
    inclination_deg: float
    inclination_deg_per_century: float
    mean_longitude_deg: float
    mean_longitude_deg_per_century: float
    longitude_perihelion_deg: float
    longitude_perihelion_deg_per_century: float
    longitude_ascending_node_deg: float
    longitude_ascending_node_deg_per_century: float


@dataclass(frozen=True, slots=True)
class TrailPoint:
    """A timestamped position sample used for orbit trail fading."""

    position_m: Vector3
    simulation_time_s: float


@dataclass(slots=True)
class CelestialBody:
    """A simulated body with physical and display properties."""

    name: str
    mass_kg: float
    radius_m: float
    color_hex: str
    position_m: Vector3
    velocity_m_per_s: Vector3
    orbital_period_s: float | None = None
    trail_sample_period_s: float = 0.0
    trail: list[TrailPoint] = field(default_factory=list)
    _last_trail_sample_time_s: float = field(default=0.0, repr=False)


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
        self.simulation_time_s = 0.0

    def set_gravity_multiplier(self, value: float) -> None:
        """Update the gravity multiplier."""
        self.gravity_multiplier = max(0.0, value)

    def compute_accelerations(self, positions: list[Vector3] | None = None) -> list[Vector3]:
        """Compute acceleration vectors for each body from Newtonian gravity."""
        pos = positions if positions is not None else [body.position_m for body in self.bodies]
        accelerations = [Vector3(0.0, 0.0, 0.0) for _ in self.bodies]
        g_scaled = GRAVITATIONAL_CONSTANT * self.gravity_multiplier

        for i, _body_i in enumerate(self.bodies):
            ax = 0.0
            ay = 0.0
            az = 0.0
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
                az += accel_mag * direction.z
            accelerations[i] = Vector3(ax, ay, az)

        return accelerations

    def step(self, dt_seconds: float) -> None:
        """Advance simulation state using velocity-Verlet integration."""
        if dt_seconds <= 0.0:
            return

        initial_positions = [body.position_m for body in self.bodies]
        initial_velocities = [body.velocity_m_per_s for body in self.bodies]
        initial_accelerations = self.compute_accelerations(initial_positions)

        next_positions: list[Vector3] = []
        for pos, vel, acc in zip(
            initial_positions,
            initial_velocities,
            initial_accelerations,
            strict=True,
        ):
            next_positions.append(pos + vel * dt_seconds + acc * (0.5 * dt_seconds * dt_seconds))

        next_accelerations = self.compute_accelerations(next_positions)
        self.simulation_time_s += dt_seconds

        for idx, body in enumerate(self.bodies):
            body.position_m = next_positions[idx]
            body.velocity_m_per_s = initial_velocities[idx] + (
                initial_accelerations[idx] + next_accelerations[idx]
            ) * (0.5 * dt_seconds)

            should_append = (
                len(body.trail) == 0
                or body.trail_sample_period_s <= 0.0
                or (self.simulation_time_s - body._last_trail_sample_time_s)
                >= body.trail_sample_period_s
            )
            if should_append:
                body.trail.append(TrailPoint(body.position_m, self.simulation_time_s))
                body._last_trail_sample_time_s = self.simulation_time_s

            if body.orbital_period_s is not None and body.orbital_period_s > 0.0:
                cutoff_time = self.simulation_time_s - body.orbital_period_s
                body.trail = [
                    point for point in body.trail if point.simulation_time_s >= cutoff_time
                ]

            if len(body.trail) > self.trail_limit:
                body.trail = body.trail[-self.trail_limit :]


def _wrap_degrees(value: float) -> float:
    """Normalize angle to [0, 360) degrees."""
    wrapped = value % 360.0
    if wrapped < 0.0:
        return wrapped + 360.0
    return wrapped


def _to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * (pi / 180.0)


def _orbital_period_seconds(semi_major_axis_au: float, central_mass_kg: float) -> float:
    """Return sidereal period from semi-major axis using Kepler's third law."""
    a_m = semi_major_axis_au * ASTRONOMICAL_UNIT_METERS
    mu = GRAVITATIONAL_CONSTANT * central_mass_kg
    return 2.0 * pi * sqrt((a_m * a_m * a_m) / mu)


def _julian_day_from_datetime(moment: datetime) -> float:
    """Convert UTC datetime to Julian day."""
    unix_seconds = moment.timestamp()
    return JULIAN_DAY_UNIX_EPOCH + (unix_seconds / 86_400.0)


def _evaluate_elements(base: OrbitalElements, julian_centuries: float) -> OrbitalElements:
    """Evaluate time-varying orbital elements at a given Julian century offset."""
    t = julian_centuries
    return OrbitalElements(
        semi_major_axis_au=base.semi_major_axis_au + (base.semi_major_axis_au_per_century * t),
        semi_major_axis_au_per_century=base.semi_major_axis_au_per_century,
        eccentricity=base.eccentricity + (base.eccentricity_per_century * t),
        eccentricity_per_century=base.eccentricity_per_century,
        inclination_deg=base.inclination_deg + (base.inclination_deg_per_century * t),
        inclination_deg_per_century=base.inclination_deg_per_century,
        mean_longitude_deg=base.mean_longitude_deg + (base.mean_longitude_deg_per_century * t),
        mean_longitude_deg_per_century=base.mean_longitude_deg_per_century,
        longitude_perihelion_deg=base.longitude_perihelion_deg
        + (base.longitude_perihelion_deg_per_century * t),
        longitude_perihelion_deg_per_century=base.longitude_perihelion_deg_per_century,
        longitude_ascending_node_deg=base.longitude_ascending_node_deg
        + (base.longitude_ascending_node_deg_per_century * t),
        longitude_ascending_node_deg_per_century=base.longitude_ascending_node_deg_per_century,
    )


def _solve_kepler(mean_anomaly_rad: float, eccentricity: float) -> float:
    """Solve Kepler's equation M = E - e sin(E) using Newton iteration."""
    eccentric_anomaly = mean_anomaly_rad
    for _ in range(12):
        value = eccentric_anomaly - (eccentricity * sin(eccentric_anomaly)) - mean_anomaly_rad
        derivative = 1.0 - (eccentricity * cos(eccentric_anomaly))
        if derivative == 0.0:
            break
        step = value / derivative
        eccentric_anomaly -= step
        if abs(step) < 1e-12:
            break
    return eccentric_anomaly


def _unit_vector3(vector: Vector3) -> Vector3:
    """Return a unit vector, raising if the input is effectively zero."""
    magnitude = vector.magnitude()
    if magnitude < 1e-300:
        msg = "Cannot normalize a zero-length vector."
        raise ValueError(msg)
    return vector / magnitude


# Earth–Moon: mean semi-major axis and sidereal month (circular-orbit approximation).
_MOON_SEMI_MAJOR_M = 384_399_000.0
_MOON_SIDEREAL_ORBITAL_PERIOD_S = 27.321661 * 86_400.0
_MOON_MASS_KG = 7.342e22
_MOON_RADIUS_M = 1_737_400.0


def _moon_celestial_body(earth: CelestialBody) -> CelestialBody:
    """Build the Moon from Earth's heliocentric state (simple Earth-orbit model).

    Earth orbital elements follow the JPL approximate recipe; those positions are
    effectively Earth–Moon barycenter–like. Adding the Moon offset from Earth is
    a standard small-body refinement for visualization.
    """
    r_e = earth.position_m
    v_e = earth.velocity_m_per_s
    h_vec = r_e.cross(v_e)
    h_mag = h_vec.magnitude()
    r_hat = _unit_vector3(r_e)
    if h_mag < 1e20:
        n = Vector3(0.0, 0.0, 1.0)
        tangential = _unit_vector3(n.cross(r_hat))
    else:
        n = h_vec / h_mag
        tangential = _unit_vector3(n.cross(r_hat))
    r_rel = tangential * _MOON_SEMI_MAJOR_M
    bitangent = _unit_vector3(n.cross(tangential))
    v_mag = sqrt(GRAVITATIONAL_CONSTANT * earth.mass_kg / _MOON_SEMI_MAJOR_M)
    v_rel = bitangent * v_mag
    trail_sample_period_s = _MOON_SIDEREAL_ORBITAL_PERIOD_S / 1_500.0
    return CelestialBody(
        name="Moon",
        mass_kg=_MOON_MASS_KG,
        radius_m=_MOON_RADIUS_M,
        color_hex="#c8c8c8",
        position_m=r_e + r_rel,
        velocity_m_per_s=v_e + v_rel,
        orbital_period_s=_MOON_SIDEREAL_ORBITAL_PERIOD_S,
        trail_sample_period_s=trail_sample_period_s,
    )


def _state_vectors_from_elements(
    elements: OrbitalElements,
    central_mass_kg: float,
) -> tuple[Vector3, Vector3]:
    """Return heliocentric state vectors from orbital elements."""
    a_m = elements.semi_major_axis_au * ASTRONOMICAL_UNIT_METERS
    e = elements.eccentricity
    i_rad = _to_radians(elements.inclination_deg)
    longitude_ascending_node_rad = _to_radians(_wrap_degrees(elements.longitude_ascending_node_deg))
    longitude_perihelion_rad = _to_radians(_wrap_degrees(elements.longitude_perihelion_deg))
    argument_perihelion_rad = longitude_perihelion_rad - longitude_ascending_node_rad
    mean_anomaly_rad = _to_radians(
        _wrap_degrees(elements.mean_longitude_deg - elements.longitude_perihelion_deg)
    )
    eccentric_anomaly_rad = _solve_kepler(mean_anomaly_rad, e)
    sqrt_one_minus_e2 = sqrt(1.0 - (e * e))

    x_perifocal = a_m * (cos(eccentric_anomaly_rad) - e)
    y_perifocal = a_m * sqrt_one_minus_e2 * sin(eccentric_anomaly_rad)

    mu = GRAVITATIONAL_CONSTANT * central_mass_kg
    mean_motion = sqrt(mu / (a_m * a_m * a_m))
    denom = 1.0 - (e * cos(eccentric_anomaly_rad))
    d_e_dt = mean_motion / denom
    vx_perifocal = -a_m * sin(eccentric_anomaly_rad) * d_e_dt
    vy_perifocal = a_m * sqrt_one_minus_e2 * cos(eccentric_anomaly_rad) * d_e_dt

    cos_omega = cos(argument_perihelion_rad)
    sin_omega = sin(argument_perihelion_rad)
    cos_node = cos(longitude_ascending_node_rad)
    sin_node = sin(longitude_ascending_node_rad)
    cos_i = cos(i_rad)
    sin_i = sin(i_rad)

    # Rotation from perifocal frame to heliocentric ecliptic frame.
    m11 = (cos_node * cos_omega) - (sin_node * sin_omega * cos_i)
    m12 = -(cos_node * sin_omega) - (sin_node * cos_omega * cos_i)
    m21 = (sin_node * cos_omega) + (cos_node * sin_omega * cos_i)
    m22 = -(sin_node * sin_omega) + (cos_node * cos_omega * cos_i)
    m31 = sin_omega * sin_i
    m32 = cos_omega * sin_i

    position = Vector3(
        (m11 * x_perifocal) + (m12 * y_perifocal),
        (m21 * x_perifocal) + (m22 * y_perifocal),
        (m31 * x_perifocal) + (m32 * y_perifocal),
    )
    velocity = Vector3(
        (m11 * vx_perifocal) + (m12 * vy_perifocal),
        (m21 * vx_perifocal) + (m22 * vy_perifocal),
        (m31 * vx_perifocal) + (m32 * vy_perifocal),
    )
    return position, velocity


def create_default_solar_system(epoch_utc: datetime | None = None) -> SolarSystem:
    """Create an approximate solar system with inclined elliptical planet orbits and the Moon."""
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.9885e30,
        radius_m=696_340_000.0,
        color_hex="#ffcc66",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )

    # JPL: "Keplerian Elements for Approximate Positions of the Major Planets"
    # (valid 1800 AD to 2050 AD, ecliptic/equinox J2000).
    planet_specs: list[tuple[str, float, float, str, OrbitalElements]] = [
        (
            "Mercury",
            3.3011e23,
            2_439_700.0,
            "#c9c9c9",
            OrbitalElements(
                0.38709927,
                0.00000037,
                0.20563593,
                0.00001906,
                7.00497902,
                -0.00594749,
                252.25032350,
                149472.67411175,
                77.45779628,
                0.16047689,
                48.33076593,
                -0.12534081,
            ),
        ),
        (
            "Venus",
            4.8675e24,
            6_051_800.0,
            "#f2d27b",
            OrbitalElements(
                0.72333566,
                0.00000390,
                0.00677672,
                -0.00004107,
                3.39467605,
                -0.00078890,
                181.97909950,
                58517.81538729,
                131.60246718,
                0.00268329,
                76.67984255,
                -0.27769418,
            ),
        ),
        (
            "Earth",
            5.9722e24,
            6_371_000.0,
            "#5da9ff",
            OrbitalElements(
                1.00000261,
                0.00000562,
                0.01671123,
                -0.00004392,
                -0.00001531,
                -0.01294668,
                100.46457166,
                35999.37244981,
                102.93768193,
                0.32327364,
                0.0,
                0.0,
            ),
        ),
        (
            "Mars",
            6.4171e23,
            3_389_500.0,
            "#d97b53",
            OrbitalElements(
                1.52371034,
                0.00001847,
                0.09339410,
                0.00007882,
                1.84969142,
                -0.00813131,
                -4.55343205,
                19140.30268499,
                -23.94362959,
                0.44441088,
                49.55953891,
                -0.29257343,
            ),
        ),
        (
            "Jupiter",
            1.8982e27,
            69_911_000.0,
            "#d6b48f",
            OrbitalElements(
                5.20288700,
                -0.00011607,
                0.04838624,
                -0.00013253,
                1.30439695,
                -0.00183714,
                34.39644051,
                3034.74612775,
                14.72847983,
                0.21252668,
                100.47390909,
                0.20469106,
            ),
        ),
        (
            "Saturn",
            5.6834e26,
            58_232_000.0,
            "#e8d6a8",
            OrbitalElements(
                9.53667594,
                -0.00125060,
                0.05386179,
                -0.00050991,
                2.48599187,
                0.00193609,
                49.95424423,
                1222.49362201,
                92.59887831,
                -0.41897216,
                113.66242448,
                -0.28867794,
            ),
        ),
        (
            "Uranus",
            8.6810e25,
            25_362_000.0,
            "#9adbf7",
            OrbitalElements(
                19.18916464,
                -0.00196176,
                0.04725744,
                -0.00004397,
                0.77263783,
                -0.00242939,
                313.23810451,
                428.48202785,
                170.95427630,
                0.40805281,
                74.01692503,
                0.04240589,
            ),
        ),
        (
            "Neptune",
            1.02413e26,
            24_622_000.0,
            "#547bf0",
            OrbitalElements(
                30.06992276,
                0.00026291,
                0.00859048,
                0.00005105,
                1.77004347,
                0.00035372,
                -55.12002969,
                218.45945325,
                44.96476227,
                -0.32241464,
                131.78422574,
                -0.00508664,
            ),
        ),
    ]

    now_utc = epoch_utc if epoch_utc is not None else datetime.now(UTC)
    julian_day = _julian_day_from_datetime(now_utc)
    julian_centuries = (julian_day - JULIAN_DAY_J2000) / DAYS_PER_JULIAN_CENTURY
    planets: list[CelestialBody] = []
    for name, mass_kg, radius_m, color_hex, base_elements in planet_specs:
        elements = _evaluate_elements(base_elements, julian_centuries)
        position, velocity = _state_vectors_from_elements(elements, sun.mass_kg)
        orbital_period_s = _orbital_period_seconds(elements.semi_major_axis_au, sun.mass_kg)
        trail_sample_period_s = orbital_period_s / 1_500.0
        planets.append(
            CelestialBody(
                name=name,
                mass_kg=mass_kg,
                radius_m=radius_m,
                color_hex=color_hex,
                position_m=position,
                velocity_m_per_s=velocity,
                orbital_period_s=orbital_period_s,
                trail_sample_period_s=trail_sample_period_s,
            )
        )
        if name == "Earth":
            planets.append(_moon_celestial_body(planets[-1]))

    return SolarSystem([sun, *planets])
