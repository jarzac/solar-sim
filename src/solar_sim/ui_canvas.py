"""Rendering widget for the solar system simulation."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from solar_sim.config import SimulationSettings
from solar_sim.math2d import Vector2
from solar_sim.physics import CelestialBody, SolarSystem


class SimulationCanvas(QWidget):
    """Widget that updates and draws the simulation world."""

    @staticmethod
    def _draw_trail(
        painter: QPainter,
        body: CelestialBody,
        project: Callable[[Vector2], QPointF],
    ) -> None:
        """Draw body trail in screen space."""
        if len(body.trail) < 2:
            return
        points = [project(pos) for pos in body.trail]
        for p0, p1 in zip(points, points[1:], strict=False):
            painter.drawLine(p0, p1)

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
        self._last_tick = perf_counter()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self.setMinimumSize(960, 720)

    def _tick(self) -> None:
        """Advance physics according to configured time scale."""
        now = perf_counter()
        dt_real = max(0.0, now - self._last_tick)
        self._last_tick = now
        dt_sim = dt_real * self.settings.time_scale_seconds_per_second
        self.system.step(dt_sim)
        self.update()

    def _to_screen_point(self, position_m: Vector2) -> QPointF:
        """Convert world meters to screen coordinates."""
        cx = self.width() * 0.5
        cy = self.height() * 0.5
        scale = self.settings.meters_per_pixel
        return QPointF(cx + (position_m.x / scale), cy + (position_m.y / scale))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        """Paint all bodies, labels, and optional orbit trails."""
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#070b16"))

        if self.settings.show_orbits:
            trail_pen = QPen(QColor(120, 130, 180, 120))
            trail_pen.setWidth(1)
            painter.setPen(trail_pen)
            for body in self.system.bodies:
                self._draw_trail(painter, body, self._to_screen_point)

        painter.setPen(Qt.PenStyle.NoPen)
        for body in self.system.bodies:
            center = self._to_screen_point(body.position_m)
            radius_px = max(2.0, body.radius_m / self.settings.meters_per_pixel)
            painter.setBrush(QColor(body.color_hex))
            painter.drawEllipse(center, radius_px, radius_px)

            if self.settings.show_labels and body.name != "Sun":
                painter.setPen(QColor("#f0f4ff"))
                painter.drawText(center + QPointF(8.0, -8.0), body.name)
                painter.setPen(Qt.PenStyle.NoPen)
