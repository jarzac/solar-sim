"""Configuration models for simulation and rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

ProjectionMode = Literal["orthographic", "perspective"]


@dataclass(slots=True)
class SimulationSettings:
    """Mutable simulation settings controlled by the UI."""

    gravity_multiplier: float = 1.0
    time_scale_seconds_per_second: float = 864_000.0
    show_orbits: bool = True
    show_labels: bool = True
    projection_mode: ProjectionMode = "perspective"
    meters_per_pixel: float = 6.0e9
    start_date: date = field(default_factory=date.today)

    def set_gravity_multiplier(self, value: float) -> None:
        """Set gravity multiplier with a hard lower bound."""
        self.gravity_multiplier = max(0.0, value)

    def set_time_scale(self, value: float) -> None:
        """Set simulation speed with a hard lower bound."""
        self.time_scale_seconds_per_second = max(1.0, value)

    def set_show_orbits(self, enabled: bool) -> None:
        """Enable or disable orbit path rendering."""
        self.show_orbits = enabled

    def set_show_labels(self, enabled: bool) -> None:
        """Enable or disable body label rendering."""
        self.show_labels = enabled

    def set_projection_mode(self, mode: ProjectionMode) -> None:
        """Set rendering projection mode."""
        self.projection_mode = mode

    def set_start_date(self, value: date) -> None:
        """Set the simulation epoch date."""
        self.start_date = value
