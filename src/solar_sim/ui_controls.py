"""UI controls for simulation settings."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    """Left-side settings panel with live simulation controls."""

    gravity_multiplier_changed = Signal(float)
    time_scale_changed = Signal(float)
    show_orbits_changed = Signal(bool)
    show_labels_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create control widgets and wire signals."""
        super().__init__(parent)

        gravity_input = QDoubleSpinBox(self)
        gravity_input.setDecimals(2)
        gravity_input.setRange(0.0, 10.0)
        gravity_input.setSingleStep(0.1)
        gravity_input.setValue(1.0)
        gravity_input.valueChanged.connect(self.gravity_multiplier_changed.emit)

        time_scale_input = QDoubleSpinBox(self)
        time_scale_input.setDecimals(0)
        time_scale_input.setRange(1.0, 5_000_000.0)
        time_scale_input.setSingleStep(1_000.0)
        time_scale_input.setValue(86_400.0)
        time_scale_input.valueChanged.connect(self.time_scale_changed.emit)

        show_orbits_input = QCheckBox("Show orbit paths", self)
        show_orbits_input.setChecked(True)
        show_orbits_input.toggled.connect(self.show_orbits_changed.emit)

        show_labels_input = QCheckBox("Show planet labels", self)
        show_labels_input.setChecked(True)
        show_labels_input.toggled.connect(self.show_labels_changed.emit)

        form = QFormLayout()
        form.addRow("Gravity multiplier", gravity_input)
        form.addRow("Sim seconds / real second", time_scale_input)
        form.addRow(show_orbits_input)
        form.addRow(show_labels_input)

        group = QGroupBox("Simulation Controls", self)
        group.setLayout(form)

        root = QVBoxLayout()
        root.addWidget(group)
        root.addStretch(1)
        self.setLayout(root)

        self.setMinimumWidth(280)

