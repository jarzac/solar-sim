"""Application composition and window wiring."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import cast

from PySide6.QtCore import QDate
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from solar_sim.config import ProjectionMode, SimulationSettings
from solar_sim.physics import SolarSystem, create_default_solar_system
from solar_sim.ui_canvas import SimulationCanvas
from solar_sim.ui_controls import ControlPanel


def load_app_icon() -> QIcon:
    """Return the packaged application icon if available."""
    icon_path = Path(__file__).parent / "assets" / "saturn.svg"
    icon = QIcon(str(icon_path))
    if icon.isNull():
        return QIcon()
    return icon


class MainWindow(QMainWindow):
    """Main desktop window containing controls and simulation canvas."""

    def __init__(self) -> None:
        """Build the app layout and connect signals."""
        super().__init__()
        self.setWindowTitle("Solar Sim")

        self.settings = SimulationSettings()
        self.system = self._create_system_for_start_date()

        self._panel = ControlPanel(self)
        self._canvas = SimulationCanvas(self.system, self.settings, self)

        self._panel.gravity_multiplier_changed.connect(self._on_gravity_changed)
        self._panel.time_scale_changed.connect(self._on_time_scale_changed)
        self._panel.show_orbits_changed.connect(self._on_show_orbits_changed)
        self._panel.show_labels_changed.connect(self._on_show_labels_changed)
        self._panel.perspective_view_changed.connect(self._on_perspective_view_changed)
        self._panel.simulation_running_changed.connect(self._on_simulation_running_changed)
        self._panel.restart_requested.connect(self._on_restart_requested)
        self._panel.start_date_changed.connect(self._on_start_date_changed)
        self._panel.set_start_date(
            QDate(
                self.settings.start_date.year,
                self.settings.start_date.month,
                self.settings.start_date.day,
            )
        )

        root = QWidget(self)
        layout = QHBoxLayout()
        layout.addWidget(self._panel)
        layout.addWidget(self._canvas, 1)
        root.setLayout(layout)
        self.setCentralWidget(root)
        self.resize(1440, 900)

    def _on_gravity_changed(self, value: float) -> None:
        """Synchronize gravity settings with simulation core."""
        self.settings.set_gravity_multiplier(value)
        self.system.set_gravity_multiplier(self.settings.gravity_multiplier)

    def _on_time_scale_changed(self, value: float) -> None:
        """Handle UI updates to simulation speed."""
        self.settings.set_time_scale(value)

    def _on_show_orbits_changed(self, enabled: bool) -> None:
        """Handle orbit-path visibility updates."""
        self.settings.set_show_orbits(enabled)

    def _on_show_labels_changed(self, enabled: bool) -> None:
        """Handle label visibility updates."""
        self.settings.set_show_labels(enabled)

    def _on_perspective_view_changed(self, enabled: bool) -> None:
        """Switch between orthographic and perspective projection."""
        mode: ProjectionMode = "perspective" if enabled else "orthographic"
        self.settings.set_projection_mode(mode)

    def _on_simulation_running_changed(self, running: bool) -> None:
        """Handle simulation pause/resume."""
        self._canvas.set_running(running)

    def _on_restart_requested(self) -> None:
        """Reset the simulation back to a fresh solar-system state."""
        self.system = self._create_system_for_start_date()
        self.system.set_gravity_multiplier(self.settings.gravity_multiplier)
        self._canvas.set_system(self.system)
        self._canvas.set_running(True)
        self._panel.set_simulation_running(True)

    def _on_start_date_changed(self, value: str) -> None:
        """Update simulation epoch date used for initial and restart state."""
        self.settings.set_start_date(date.fromisoformat(value))

    def _create_system_for_start_date(self) -> SolarSystem:
        """Create system state seeded by configured start date."""
        epoch_utc = datetime.combine(self.settings.start_date, datetime.min.time(), tzinfo=UTC)
        return create_default_solar_system(epoch_utc)


def run() -> int:
    """Start the Qt event loop and return process status."""
    app_instance = QApplication.instance()
    app = QApplication([]) if app_instance is None else cast(QApplication, app_instance)

    icon = load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    return app.exec()
