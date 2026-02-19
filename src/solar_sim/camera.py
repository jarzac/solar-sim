"""Camera controls and projection helpers for the simulation canvas."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

from solar_sim.config import ProjectionMode
from solar_sim.math2d import Vector2
from solar_sim.math3d import Vector3


@dataclass(slots=True)
class CameraState:
    """Mutable camera state for zooming and orbiting around the origin."""

    zoom_factor: float = 1.0
    yaw_radians: float = 0.0
    pitch_radians: float = 0.35
    min_zoom: float = 0.1
    max_zoom: float = 25.0
    min_pitch_radians: float = -(pi * 0.5)
    max_pitch_radians: float = pi * 0.5
    perspective_focal_length_px: float = 1200.0
    perspective_min_denominator_px: float = 60.0

    def effective_meters_per_pixel(self, base_meters_per_pixel: float) -> float:
        """Return effective world scale after zoom is applied."""
        return base_meters_per_pixel / self.zoom_factor

    def zoom_by_wheel_steps(self, steps: float) -> None:
        """Update zoom from mouse-wheel steps with clamping."""
        next_zoom = self.zoom_factor * (1.15**steps)
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, next_zoom))

    def orbit_by_drag(self, delta_x_pixels: float, delta_y_pixels: float) -> None:
        """Rotate and tilt camera based on middle-mouse drag delta."""
        sensitivity = 0.006
        self.yaw_radians += delta_x_pixels * sensitivity
        next_pitch = self.pitch_radians - (delta_y_pixels * sensitivity)
        self.pitch_radians = max(self.min_pitch_radians, min(self.max_pitch_radians, next_pitch))

    def rotate_world_point_3d(self, point_m: Vector3) -> tuple[float, float, float]:
        """Return rotated coordinates in camera space."""
        cos_yaw = cos(self.yaw_radians)
        sin_yaw = sin(self.yaw_radians)
        x_yaw = (point_m.x * cos_yaw) - (point_m.y * sin_yaw)
        y_yaw = (point_m.x * sin_yaw) + (point_m.y * cos_yaw)
        z_yaw = point_m.z

        cos_pitch = cos(self.pitch_radians)
        sin_pitch = sin(self.pitch_radians)
        y_pitch = (y_yaw * cos_pitch) - (z_yaw * sin_pitch)
        z_pitch = (y_yaw * sin_pitch) + (z_yaw * cos_pitch)
        return (x_yaw, y_pitch, z_pitch)

    def project_to_screen(
        self,
        point_m: Vector3,
        viewport_width_px: float,
        viewport_height_px: float,
        base_meters_per_pixel: float,
        projection_mode: ProjectionMode,
    ) -> Vector2:
        """Project world-space meters to screen-space pixels."""
        x_m, y_m, z_m = self.rotate_world_point_3d(point_m)
        scale = self.effective_meters_per_pixel(base_meters_per_pixel)
        cx = viewport_width_px * 0.5
        cy = viewport_height_px * 0.5
        x_px = x_m / scale
        y_px = y_m / scale

        if projection_mode == "perspective":
            z_px = z_m / scale
            denom = max(
                self.perspective_min_denominator_px,
                self.perspective_focal_length_px - z_px,
            )
            factor = self.perspective_focal_length_px / denom
            x_px *= factor
            y_px *= factor

        return Vector2(cx + x_px, cy + y_px)
