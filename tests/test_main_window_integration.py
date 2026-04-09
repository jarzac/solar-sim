"""Integration tests for MainWindow signal wiring and shared state."""

from __future__ import annotations

from datetime import UTC, date, datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QSlider,
)

from solar_sim.app import MainWindow
from solar_sim.physics import create_default_solar_system
from solar_sim.ui_canvas import SimulationCanvas
from solar_sim.ui_controls import slider_index_for_speed_multiplier


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _gravity_spinbox(panel: MainWindow) -> QDoubleSpinBox:
    """Return the gravity multiplier spin box."""
    spins = panel.findChildren(QDoubleSpinBox)
    assert len(spins) >= 1
    return spins[0]


def _speed_slider(panel: MainWindow) -> QSlider:
    """Return the discrete simulation-speed slider."""
    slider = panel.findChild(QSlider)
    assert slider is not None
    return slider


def _check_boxes(panel: MainWindow) -> tuple[QCheckBox, QCheckBox, QCheckBox]:
    """Return (show_orbits, show_labels, perspective) check boxes in creation order."""
    boxes = panel.findChildren(QCheckBox)
    assert len(boxes) >= 3
    return boxes[0], boxes[1], boxes[2]


def test_gravity_spinbox_updates_system_and_settings() -> None:
    """Gravity multiplier should sync to SimulationSettings and SolarSystem."""
    _ = _qapp()
    window = MainWindow()
    try:
        gravity = _gravity_spinbox(window)
        gravity.setValue(3.25)
        assert window.settings.gravity_multiplier == 3.25
        assert window.system.gravity_multiplier == 3.25
    finally:
        window.close()


def test_speed_slider_updates_settings() -> None:
    """Discrete speed slider should update SimulationSettings time scale."""
    _ = _qapp()
    window = MainWindow()
    try:
        slider = _speed_slider(window)
        slider.setValue(slider_index_for_speed_multiplier(5_000.0))
        assert window.settings.time_scale_seconds_per_second == 5_000.0
    finally:
        window.close()


def test_speed_preset_button_updates_slider_and_settings() -> None:
    """Speed preset buttons should stay in sync with the slider and settings."""
    _ = _qapp()
    window = MainWindow()
    try:
        slider = _speed_slider(window)
        preset = next(
            button for button in window.findChildren(QPushButton) if button.text() == "100×"
        )
        preset.click()
        assert slider.value() == slider_index_for_speed_multiplier(100.0)
        assert window.settings.time_scale_seconds_per_second == 100.0
    finally:
        window.close()


def test_speed_slider_can_select_100000x() -> None:
    """The speed slider should support the highest configured 100000x value."""
    _ = _qapp()
    window = MainWindow()
    try:
        slider = _speed_slider(window)
        slider.setValue(slider_index_for_speed_multiplier(100_000.0))
        assert slider.value() == slider.maximum()
        assert window.settings.time_scale_seconds_per_second == 100_000.0
    finally:
        window.close()


def test_show_orbits_and_labels_checkboxes_update_settings() -> None:
    """Orbit path and label toggles should update SimulationSettings."""
    _ = _qapp()
    window = MainWindow()
    try:
        orbits_box, labels_box, _persp = _check_boxes(window)
        orbits_box.setChecked(False)
        labels_box.setChecked(False)
        assert window.settings.show_orbits is False
        assert window.settings.show_labels is False
    finally:
        window.close()


def test_perspective_checkbox_updates_projection_mode() -> None:
    """Perspective checkbox should set orthographic or perspective on shared settings."""
    _ = _qapp()
    window = MainWindow()
    try:
        _o, _l, perspective = _check_boxes(window)
        assert window.settings.projection_mode == "perspective"
        perspective.setChecked(False)
        assert window.settings.projection_mode == "orthographic"
        perspective.setChecked(True)
        assert window.settings.projection_mode == "perspective"
    finally:
        window.close()


def test_canvas_uses_same_settings_object_as_main_window() -> None:
    """SimulationCanvas should render from the same SimulationSettings instance."""
    _ = _qapp()
    window = MainWindow()
    try:
        canvas = window.findChild(SimulationCanvas)
        assert canvas is not None
        assert canvas.settings is window.settings
    finally:
        window.close()


def test_stop_start_updates_canvas_running_flag() -> None:
    """Pause/resume should propagate to SimulationCanvas set_running."""
    _ = _qapp()
    window = MainWindow()
    try:
        canvas = window.findChild(SimulationCanvas)
        assert canvas is not None
        assert canvas._is_running is True

        buttons = window.findChildren(QPushButton)
        sim_btn = next(b for b in buttons if b.text() in ("Start", "Stop"))
        sim_btn.click()
        assert canvas._is_running is False

        sim_btn.click()
        assert canvas._is_running is True
    finally:
        window.close()


def test_restart_rebuilds_system_for_current_start_date() -> None:
    """Restart should recreate SolarSystem seeded by the selected start date."""
    _ = _qapp()
    window = MainWindow()
    try:
        canvas = window.findChild(SimulationCanvas)
        assert canvas is not None
        canvas._timer.stop()

        date_edit = window.findChild(QDateEdit)
        assert date_edit is not None
        date_edit.setDate(QDate(2005, 6, 15))

        restart_btn = next(b for b in window.findChildren(QPushButton) if b.text() == "Restart")
        restart_btn.click()

        assert window.settings.start_date == date(2005, 6, 15)
        assert window.system.simulation_time_s == 0.0

        epoch = datetime(2005, 6, 15, tzinfo=UTC)
        reference = create_default_solar_system(epoch)
        earth_actual = next(b for b in window.system.bodies if b.name == "Earth")
        earth_ref = next(b for b in reference.bodies if b.name == "Earth")
        assert earth_actual.position_m == earth_ref.position_m
        assert canvas.system is window.system
    finally:
        window.close()


def test_restart_rebinds_selected_body_by_name() -> None:
    """Restart should preserve target selection when the recreated body name still exists."""
    _ = _qapp()
    window = MainWindow()
    try:
        canvas = window.findChild(SimulationCanvas)
        assert canvas is not None
        canvas._timer.stop()

        earth_before = next(body for body in window.system.bodies if body.name == "Earth")
        canvas.select_body_by_name("Earth")
        assert canvas._selected_body() is earth_before

        restart_btn = next(b for b in window.findChildren(QPushButton) if b.text() == "Restart")
        restart_btn.click()

        earth_after = next(body for body in window.system.bodies if body.name == "Earth")
        assert earth_after is not earth_before
        assert canvas.system is window.system
        assert canvas._selected_body_name == "Earth"
        assert canvas._selected_body() is earth_after
        assert canvas._camera_focus_point() == earth_after.position_m
    finally:
        window.close()


def test_projection_mode_visible_to_canvas_render_path() -> None:
    """Settings projection_mode should match canvas.settings after UI toggle."""
    _ = _qapp()
    window = MainWindow()
    try:
        canvas = window.findChild(SimulationCanvas)
        assert canvas is not None
        _o, _l, perspective = _check_boxes(window)

        perspective.setChecked(False)
        assert canvas.settings.projection_mode == "orthographic"

        perspective.setChecked(True)
        assert canvas.settings.projection_mode == "perspective"
    finally:
        window.close()
