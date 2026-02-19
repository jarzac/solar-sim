"""Rendering widget for the solar system simulation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from time import perf_counter

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QWidget

from solar_sim.camera import CameraState
from solar_sim.config import SimulationSettings
from solar_sim.math3d import Vector3
from solar_sim.physics import ASTRONOMICAL_UNIT_METERS, CelestialBody, SolarSystem


class SimulationCanvas(QWidget):
    """Widget that updates and draws the simulation world."""

    GRID_HALF_SIZE_AU = 36.0
    GRID_STEP_AU = 2.0

    def _simulation_datetime(self) -> datetime:
        """Return the current simulation datetime in UTC."""
        base = datetime.combine(self.settings.start_date, datetime.min.time(), tzinfo=UTC)
        return base + timedelta(seconds=self.system.simulation_time_s)

    def _draw_simulation_clock(self, painter: QPainter) -> None:
        """Draw current simulation datetime in the top-left corner."""
        sim_time = self._simulation_datetime()
        text = f"Sim Date: {sim_time:%Y-%m-%d %H:%M:%S} UTC"

        box = QRectF(14.0, 14.0, 315.0, 32.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(8, 12, 22, 185))
        painter.drawRoundedRect(box, 6.0, 6.0)

        painter.setPen(QColor("#dfe7ff"))
        painter.drawText(box.adjusted(10.0, 0.0, -8.0, 0.0), Qt.AlignmentFlag.AlignVCenter, text)

    def _draw_trail(
        self,
        painter: QPainter,
        body: CelestialBody,
        project: Callable[[Vector3], QPointF],
    ) -> None:
        """Draw body trail in screen space with age-based fading."""
        if len(body.trail) < 2:
            return

        current_time = self.system.simulation_time_s
        fade_duration_s = body.orbital_period_s
        base_color = QColor(120, 130, 180)

        for p0, p1 in zip(body.trail, body.trail[1:], strict=False):
            if fade_duration_s is not None and fade_duration_s > 0.0:
                age_s = current_time - p0.simulation_time_s
                if age_s >= fade_duration_s:
                    continue
                fade_ratio = max(0.0, 1.0 - (age_s / fade_duration_s))
                alpha = max(0, min(160, int(160 * fade_ratio)))
            else:
                alpha = 120

            if alpha == 0:
                continue

            pen = QPen(base_color)
            pen.setWidth(1)
            pen.setColor(QColor(base_color.red(), base_color.green(), base_color.blue(), alpha))
            painter.setPen(pen)
            painter.drawLine(project(p0.position_m), project(p1.position_m))

    def __init__(
        self,
        system: SolarSystem,
        settings: SimulationSettings,
        parent: QWidget | None = None,
    ) -> None:
        """Create canvas timer and bind simulation state."""
        super().__init__(parent)
        self.system = system
        self.settings = settings
        self.camera = CameraState()
        self._last_tick = perf_counter()
        self._is_running = True
        self._orbit_dragging = False
        self._last_drag_position: QPointF | None = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self.setMinimumSize(960, 720)

    def _tick(self) -> None:
        """Advance physics according to configured time scale."""
        now = perf_counter()
        dt_real = max(0.0, now - self._last_tick)
        self._last_tick = now
        if not self._is_running:
            return
        dt_sim = dt_real * self.settings.time_scale_seconds_per_second
        self.system.step(dt_sim)
        self.update()

    def set_running(self, running: bool) -> None:
        """Set whether simulation time should advance."""
        self._is_running = running
        self._last_tick = perf_counter()
        self.update()

    def set_system(self, system: SolarSystem) -> None:
        """Replace the active system state, used by restart."""
        self.system = system
        self._last_tick = perf_counter()
        self.update()

    def _to_screen_point(self, position_m: Vector3) -> QPointF:
        """Convert world meters to screen coordinates."""
        screen = self.camera.project_to_screen(
            position_m,
            self.width(),
            self.height(),
            self.settings.meters_per_pixel,
            self.settings.projection_mode,
        )
        return QPointF(screen.x, screen.y)

    def _draw_segment(self, painter: QPainter, start_m: Vector3, end_m: Vector3) -> None:
        """Draw a line segment defined in world-space coordinates."""
        painter.drawLine(self._to_screen_point(start_m), self._to_screen_point(end_m))

    def _draw_solar_plane_grid(self, painter: QPainter) -> None:
        """Draw a square grid representing the solar-system orbital plane."""
        half_size_m = self.GRID_HALF_SIZE_AU * ASTRONOMICAL_UNIT_METERS
        step_m = self.GRID_STEP_AU * ASTRONOMICAL_UNIT_METERS
        line_count = int((half_size_m * 2.0) / step_m)

        border_pen = QPen(QColor(125, 145, 190, 170))
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        self._draw_segment(
            painter,
            Vector3(-half_size_m, -half_size_m, 0.0),
            Vector3(half_size_m, -half_size_m, 0.0),
        )
        self._draw_segment(
            painter,
            Vector3(half_size_m, -half_size_m, 0.0),
            Vector3(half_size_m, half_size_m, 0.0),
        )
        self._draw_segment(
            painter,
            Vector3(half_size_m, half_size_m, 0.0),
            Vector3(-half_size_m, half_size_m, 0.0),
        )
        self._draw_segment(
            painter,
            Vector3(-half_size_m, half_size_m, 0.0),
            Vector3(-half_size_m, -half_size_m, 0.0),
        )

        for idx in range(line_count + 1):
            offset = -half_size_m + (idx * step_m)
            is_major = idx % 5 == 0
            alpha = 120 if is_major else 65
            width = 2 if is_major else 1

            grid_pen = QPen(QColor(105, 125, 170, alpha))
            grid_pen.setWidth(width)
            painter.setPen(grid_pen)

            self._draw_segment(
                painter,
                Vector3(offset, -half_size_m, 0.0),
                Vector3(offset, half_size_m, 0.0),
            )
            self._draw_segment(
                painter,
                Vector3(-half_size_m, offset, 0.0),
                Vector3(half_size_m, offset, 0.0),
            )

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        """Zoom in or out based on mouse wheel movement."""
        steps = event.angleDelta().y() / 120.0
        if steps != 0.0:
            self.camera.zoom_by_wheel_steps(steps)
            self.update()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Start orbit interaction when middle mouse button is pressed."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._orbit_dragging = True
            self._last_drag_position = event.position()
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Rotate/tilt camera while middle button is held and dragged."""
        if self._orbit_dragging and self._last_drag_position is not None:
            current = event.position()
            delta_x = current.x() - self._last_drag_position.x()
            delta_y = current.y() - self._last_drag_position.y()
            self.camera.orbit_by_drag(delta_x, delta_y)
            self._last_drag_position = current
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """End orbit interaction when middle mouse button is released."""
        if event.button() == Qt.MouseButton.MiddleButton and self._orbit_dragging:
            self._orbit_dragging = False
            self._last_drag_position = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Paint all bodies, labels, and optional orbit trails."""
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#070b16"))
        self._draw_simulation_clock(painter)
        self._draw_solar_plane_grid(painter)

        if self.settings.show_orbits:
            for body in self.system.bodies:
                self._draw_trail(painter, body, self._to_screen_point)

        painter.setPen(Qt.PenStyle.NoPen)
        effective_scale = self.camera.effective_meters_per_pixel(self.settings.meters_per_pixel)
        for body in self.system.bodies:
            center = self._to_screen_point(body.position_m)
            radius_px = max(2.0, body.radius_m / effective_scale)
            painter.setBrush(QColor(body.color_hex))
            painter.drawEllipse(center, radius_px, radius_px)

            if self.settings.show_labels and body.name != "Sun":
                painter.setPen(QColor("#f0f4ff"))
                painter.drawText(center + QPointF(8.0, -8.0), body.name)
                painter.setPen(Qt.PenStyle.NoPen)
