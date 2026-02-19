"""Application composition and window wiring."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from solar_sim.config import SimulationSettings
from solar_sim.physics import create_default_solar_system
from solar_sim.ui_canvas import SimulationCanvas
from solar_sim.ui_controls import ControlPanel


class MainWindow(QMainWindow):
    """Main desktop window containing controls and simulation canvas."""

    def __init__(self) -> None:
        """Build the app layout and connect signals."""
        super().__init__()
        self.setWindowTitle("Solar System Simulation")

        self.settings = SimulationSettings()
        self.system = create_default_solar_system()

        panel = ControlPanel(self)
        canvas = SimulationCanvas(self.system, self.settings, self)

        panel.gravity_multiplier_changed.connect(self._on_gravity_changed)
        panel.time_scale_changed.connect(self._on_time_scale_changed)
        panel.show_orbits_changed.connect(self._on_show_orbits_changed)
        panel.show_labels_changed.connect(self._on_show_labels_changed)

        root = QWidget(self)
        layout = QHBoxLayout()
        layout.addWidget(panel)
        layout.addWidget(canvas, 1)
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


def run() -> int:
    """Start the Qt event loop and return process status."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    window = MainWindow()
    window.show()
    return app.exec()
