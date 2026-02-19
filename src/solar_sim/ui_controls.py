"""UI controls for simulation settings."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    """Left-side settings panel with live simulation controls."""

    gravity_multiplier_changed = Signal(float)
    time_scale_changed = Signal(float)
    show_orbits_changed = Signal(bool)
    show_labels_changed = Signal(bool)
    perspective_view_changed = Signal(bool)
    simulation_running_changed = Signal(bool)
    restart_requested = Signal()
    start_date_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create control widgets and wire signals."""
        super().__init__(parent)
        self._is_simulation_running = True

        gravity_input = QDoubleSpinBox(self)
        gravity_input.setDecimals(2)
        gravity_input.setRange(0.0, 10.0)
        gravity_input.setSingleStep(0.1)
        gravity_input.setValue(1.0)
        gravity_input.valueChanged.connect(self.gravity_multiplier_changed.emit)

        self._start_date_input = QDateEdit(self)
        self._start_date_input.setCalendarPopup(True)
        self._start_date_input.setDisplayFormat("yyyy-MM-dd")
        self._start_date_input.setDate(QDate.currentDate())
        self._start_date_input.dateChanged.connect(
            lambda value: self.start_date_changed.emit(value.toString(Qt.DateFormat.ISODate))
        )

        time_scale_input = QDoubleSpinBox(self)
        time_scale_input.setDecimals(0)
        time_scale_input.setRange(1.0, 5_000_000.0)
        time_scale_input.setSingleStep(1_000.0)
        time_scale_input.setValue(864_000.0)
        time_scale_input.valueChanged.connect(self.time_scale_changed.emit)

        show_orbits_input = QCheckBox("Show orbit paths", self)
        show_orbits_input.setChecked(True)
        show_orbits_input.toggled.connect(self.show_orbits_changed.emit)

        show_labels_input = QCheckBox("Show planet labels", self)
        show_labels_input.setChecked(True)
        show_labels_input.toggled.connect(self.show_labels_changed.emit)

        perspective_view_input = QCheckBox("Perspective view", self)
        perspective_view_input.setChecked(True)
        perspective_view_input.toggled.connect(self.perspective_view_changed.emit)

        self._start_stop_button = QPushButton("Stop", self)
        self._start_stop_button.clicked.connect(self._on_start_stop_clicked)

        restart_button = QPushButton("Restart", self)
        restart_button.clicked.connect(self.restart_requested.emit)

        form = QFormLayout()
        form.addRow("Gravity multiplier", gravity_input)
        form.addRow("Start date", self._start_date_input)
        form.addRow("Sim seconds / real second", time_scale_input)
        form.addRow(show_orbits_input)
        form.addRow(show_labels_input)
        form.addRow(perspective_view_input)
        form.addRow("Simulation", self._start_stop_button)
        form.addRow("", restart_button)

        group = QGroupBox("Simulation Controls", self)
        group.setLayout(form)

        root = QVBoxLayout()
        root.addWidget(group)
        root.addStretch(1)
        self.setLayout(root)

        self.setMinimumWidth(280)

    def _on_start_stop_clicked(self) -> None:
        """Toggle simulation run/pause state."""
        self._is_simulation_running = not self._is_simulation_running
        self._start_stop_button.setText("Stop" if self._is_simulation_running else "Start")
        self.simulation_running_changed.emit(self._is_simulation_running)

    def set_simulation_running(self, running: bool) -> None:
        """Synchronize button state with external simulation state."""
        self._is_simulation_running = running
        self._start_stop_button.setText("Stop" if self._is_simulation_running else "Start")

    def set_start_date(self, value: QDate) -> None:
        """Synchronize start date field with external state."""
        self._start_date_input.setDate(value)
