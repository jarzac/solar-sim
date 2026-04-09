"""UI controls for simulation settings."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from solar_sim.config import DEFAULT_TIME_SCALE_SECONDS_PER_SECOND

TIME_SPEED_MULTIPLIERS = (
    1.0,
    2.0,
    5.0,
    10.0,
    20.0,
    50.0,
    100.0,
    200.0,
    500.0,
    1_000.0,
    2_000.0,
    5_000.0,
    10_000.0,
    100_000.0,
)
DEFAULT_TIME_SPEED_INDEX = TIME_SPEED_MULTIPLIERS.index(DEFAULT_TIME_SCALE_SECONDS_PER_SECOND)


def speed_multiplier_for_slider_index(index: int) -> float:
    """Return the configured speed multiplier for a slider index."""
    clamped_index = max(0, min(len(TIME_SPEED_MULTIPLIERS) - 1, index))
    return TIME_SPEED_MULTIPLIERS[clamped_index]


def slider_index_for_speed_multiplier(multiplier: float) -> int:
    """Return the closest discrete slider index for a multiplier value."""
    closest_index = 0
    closest_distance = abs(TIME_SPEED_MULTIPLIERS[0] - multiplier)
    for index, candidate in enumerate(TIME_SPEED_MULTIPLIERS[1:], start=1):
        distance = abs(candidate - multiplier)
        if distance < closest_distance:
            closest_index = index
            closest_distance = distance
    return closest_index


def format_speed_multiplier(multiplier: float) -> str:
    """Return a human-readable speed label."""
    return f"Speed: {int(multiplier):,}×".replace(",", "")


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
        self._speed_preset_buttons: dict[float, QPushButton] = {}

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

        self._speed_label = QLabel(self)
        self._speed_slider = QSlider(Qt.Orientation.Horizontal, self)
        self._speed_slider.setMinimum(0)
        self._speed_slider.setMaximum(len(TIME_SPEED_MULTIPLIERS) - 1)
        self._speed_slider.setSingleStep(1)
        self._speed_slider.setPageStep(1)
        self._speed_slider.setTickInterval(1)
        self._speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        self._speed_slider.setValue(DEFAULT_TIME_SPEED_INDEX)

        speed_presets = QHBoxLayout()
        speed_presets.setContentsMargins(0, 0, 0, 0)
        for multiplier in (1.0, 10.0, 100.0, 1_000.0):
            button = QPushButton(f"{int(multiplier)}×", self)
            button.clicked.connect(
                lambda _checked=False, value=multiplier: self._set_speed_multiplier(value)
            )
            self._speed_preset_buttons[multiplier] = button
            speed_presets.addWidget(button)

        speed_controls = QWidget(self)
        speed_layout = QVBoxLayout()
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.addWidget(self._speed_label)
        speed_layout.addWidget(self._speed_slider)
        speed_layout.addLayout(speed_presets)
        speed_controls.setLayout(speed_layout)
        self._sync_speed_widgets(speed_multiplier_for_slider_index(self._speed_slider.value()))

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
        form.addRow("Speed", speed_controls)
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

    def _sync_speed_widgets(self, multiplier: float) -> None:
        """Synchronize visible speed controls to a multiplier value."""
        self._speed_label.setText(format_speed_multiplier(multiplier))
        for preset_multiplier, button in self._speed_preset_buttons.items():
            button.setEnabled(preset_multiplier != multiplier)

    def _set_speed_multiplier(self, multiplier: float) -> None:
        """Update the slider to the nearest discrete multiplier."""
        self._speed_slider.setValue(slider_index_for_speed_multiplier(multiplier))

    def _on_speed_slider_changed(self, index: int) -> None:
        """Emit the mapped time scale when the discrete speed slider changes."""
        multiplier = speed_multiplier_for_slider_index(index)
        self._sync_speed_widgets(multiplier)
        self.time_scale_changed.emit(multiplier)

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
