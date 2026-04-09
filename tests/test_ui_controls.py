"""Unit tests for ControlPanel signals and public helpers."""

from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDoubleSpinBox,
    QLabel,
    QPushButton,
    QSlider,
)

from solar_sim.config import DEFAULT_TIME_SCALE_SECONDS_PER_SECOND
from solar_sim.ui_controls import (
    TIME_SPEED_MULTIPLIERS,
    ControlPanel,
    format_speed_multiplier,
    slider_index_for_speed_multiplier,
    speed_multiplier_for_slider_index,
)


def _qapp() -> QApplication:
    """Return shared QApplication for widget tests."""
    return QApplication.instance() or QApplication([])


def _speed_label(panel: ControlPanel) -> QLabel:
    """Return the dynamic speed readout label."""
    return next(label for label in panel.findChildren(QLabel) if label.text().startswith("Speed:"))


def test_gravity_spinbox_emits_multiplier() -> None:
    """Changing gravity should emit gravity_multiplier_changed with the new value."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[float] = []
    panel.gravity_multiplier_changed.connect(received.append)

    spin_boxes = panel.findChildren(QDoubleSpinBox)
    assert len(spin_boxes) >= 1
    gravity = spin_boxes[0]
    gravity.setValue(2.5)

    assert received == [2.5]


def test_speed_slider_emits_mapped_multiplier() -> None:
    """Changing the discrete speed slider should emit the mapped multiplier."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[float] = []
    panel.time_scale_changed.connect(received.append)

    slider = panel.findChild(QSlider)
    assert slider is not None
    slider.setValue(slider_index_for_speed_multiplier(5_000.0))

    assert received == [5_000.0]


def test_speed_preset_button_sets_slider_and_emits_value() -> None:
    """Preset buttons should update the slider, label, and emitted multiplier."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[float] = []
    panel.time_scale_changed.connect(received.append)

    slider = panel.findChild(QSlider)
    label = _speed_label(panel)
    assert slider is not None
    preset = next(button for button in panel.findChildren(QPushButton) if button.text() == "100×")

    preset.click()

    assert slider.value() == slider_index_for_speed_multiplier(100.0)
    assert label.text() == "Speed: 100×"
    assert received == [100.0]


def test_speed_slider_reaches_100000x_and_updates_label() -> None:
    """Top-end slider position should map to 100000x and update the readout."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[float] = []
    panel.time_scale_changed.connect(received.append)

    slider = panel.findChild(QSlider)
    label = _speed_label(panel)
    assert slider is not None
    slider.setValue(slider_index_for_speed_multiplier(100_000.0))

    assert slider.value() == len(TIME_SPEED_MULTIPLIERS) - 1
    assert label.text() == "Speed: 100000×"
    assert received == [100_000.0]


def test_speed_label_formats_default_multiplier() -> None:
    """Default control label should match the configured startup speed."""
    _ = _qapp()
    panel = ControlPanel()

    label = _speed_label(panel)
    assert label.text() == format_speed_multiplier(DEFAULT_TIME_SCALE_SECONDS_PER_SECOND)


def test_speed_label_formats_large_values_without_separator() -> None:
    """Large multiplier labels should keep compact multiplier formatting."""
    assert format_speed_multiplier(10_000.0) == "Speed: 10000×"
    assert format_speed_multiplier(100_000.0) == "Speed: 100000×"


def test_speed_mapping_helpers_match_configured_levels() -> None:
    """Discrete slider helpers should round-trip configured speed levels."""
    for index, multiplier in enumerate(TIME_SPEED_MULTIPLIERS):
        assert speed_multiplier_for_slider_index(index) == multiplier
        assert slider_index_for_speed_multiplier(multiplier) == index

    assert 10_000.0 in TIME_SPEED_MULTIPLIERS
    assert TIME_SPEED_MULTIPLIERS[-1] == 100_000.0


def test_show_orbits_checkbox_emits_bool() -> None:
    """Orbit paths checkbox should emit show_orbits_changed."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[bool] = []
    panel.show_orbits_changed.connect(received.append)

    boxes = panel.findChildren(QCheckBox)
    orbit_box = next(cb for cb in boxes if cb.text() == "Show orbit paths")
    orbit_box.setChecked(False)

    assert received == [False]


def test_perspective_checkbox_emits_bool() -> None:
    """Perspective view checkbox should emit perspective_view_changed."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[bool] = []
    panel.perspective_view_changed.connect(received.append)

    boxes = panel.findChildren(QCheckBox)
    persp_box = next(cb for cb in boxes if cb.text() == "Perspective view")
    persp_box.setChecked(False)

    assert received == [False]


def test_start_stop_button_toggles_running_signal() -> None:
    """Start/Stop should emit simulation_running_changed with toggled state."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[bool] = []
    panel.simulation_running_changed.connect(received.append)

    buttons = panel.findChildren(QPushButton)
    sim_button = next(b for b in buttons if b.text() in ("Start", "Stop"))
    assert sim_button.text() == "Stop"
    sim_button.click()

    assert sim_button.text() == "Start"
    assert received == [False]

    sim_button.click()
    assert sim_button.text() == "Stop"
    assert received == [False, True]


def test_restart_button_emits_restart_requested() -> None:
    """Restart should emit restart_requested without arguments."""
    _ = _qapp()
    panel = ControlPanel()
    count = 0

    def _on_restart() -> None:
        nonlocal count
        count += 1

    panel.restart_requested.connect(_on_restart)

    buttons = panel.findChildren(QPushButton)
    restart_btn = next(b for b in buttons if b.text() == "Restart")
    restart_btn.click()

    assert count == 1


def test_set_simulation_running_updates_button_label() -> None:
    """set_simulation_running should sync button text without emitting running signal."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[bool] = []
    panel.simulation_running_changed.connect(received.append)

    panel.set_simulation_running(False)
    buttons = panel.findChildren(QPushButton)
    sim_button = next(b for b in buttons if b.text() in ("Start", "Stop"))
    assert sim_button.text() == "Start"
    assert received == []

    panel.set_simulation_running(True)
    assert sim_button.text() == "Stop"


def test_set_start_date_updates_date_edit() -> None:
    """set_start_date should set the QDateEdit value."""
    _ = _qapp()
    panel = ControlPanel()
    target = QDate(2019, 7, 20)
    panel.set_start_date(target)
    date_edit = panel.findChild(QDateEdit)
    assert date_edit is not None
    assert date_edit.date() == target


def test_start_date_change_emits_iso_string() -> None:
    """Changing the date field should emit start_date_changed with ISO date."""
    _ = _qapp()
    panel = ControlPanel()
    received: list[str] = []
    panel.start_date_changed.connect(received.append)

    date_edit = panel.findChild(QDateEdit)
    assert date_edit is not None
    date_edit.setDate(QDate(2030, 1, 15))

    assert received[-1] == "2030-01-15"
