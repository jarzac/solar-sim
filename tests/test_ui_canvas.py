"""Unit tests for simulation canvas gesture and wheel input handling."""

from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QPointingDevice
from PySide6.QtWidgets import QApplication

from solar_sim.config import SimulationSettings
from solar_sim.math3d import Vector3
from solar_sim.physics import CelestialBody, SolarSystem
from solar_sim.ui_canvas import SimulationCanvas


class _FakeDelta:
    """Simple 2D delta object used by fake input events."""

    def __init__(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    def x(self) -> float:
        """Return x component."""
        return self._x

    def y(self) -> float:
        """Return y component."""
        return self._y

    def isNull(self) -> bool:  # noqa: N802
        """Return whether both components are zero."""
        return self._x == 0.0 and self._y == 0.0


class _FakeDevice:
    """Simple pointing device double."""

    def __init__(self, device_type: object) -> None:
        self._device_type = device_type

    def type(self) -> object:
        """Return configured device type."""
        return self._device_type


class _FakeWheelEvent:
    """Wheel event double with only accessed APIs."""

    def __init__(
        self,
        *,
        device: object | None,
        pixel_delta: _FakeDelta | None = None,
        angle_delta: _FakeDelta | None = None,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> None:
        self._device = device
        self._pixel_delta = pixel_delta or _FakeDelta(0.0, 0.0)
        self._angle_delta = angle_delta or _FakeDelta(0.0, 0.0)
        self._modifiers = modifiers
        self.accepted = False

    def pointingDevice(self) -> object | None:  # noqa: N802
        """Return pointing device."""
        return self._device

    def pixelDelta(self) -> _FakeDelta:  # noqa: N802
        """Return pixel delta."""
        return self._pixel_delta

    def angleDelta(self) -> _FakeDelta:  # noqa: N802
        """Return angle delta."""
        return self._angle_delta

    def accept(self) -> None:
        """Mark event as accepted."""
        self.accepted = True

    def modifiers(self) -> Qt.KeyboardModifier:
        """Return keyboard modifiers for this event."""
        return self._modifiers


class _FakeNativeGestureEvent:
    """Native gesture event double with only accessed APIs."""

    def __init__(
        self,
        gesture_type: Qt.NativeGestureType,
        *,
        delta: QPointF | None = None,
        value: float = 0.0,
    ) -> None:
        self._gesture_type = gesture_type
        self._delta = delta or QPointF(0.0, 0.0)
        self._value = value
        self.accepted = False

    def type(self) -> QEvent.Type:
        """Report native gesture event type."""
        return QEvent.Type.NativeGesture

    def gestureType(self) -> Qt.NativeGestureType:  # noqa: N802
        """Return configured native gesture type."""
        return self._gesture_type

    def delta(self) -> QPointF:
        """Return configured gesture delta."""
        return self._delta

    def value(self) -> float:
        """Return configured scalar gesture value."""
        return self._value

    def accept(self) -> None:
        """Mark event as accepted."""
        self.accepted = True


def _make_canvas(
    system: SolarSystem | None = None,
    settings: SimulationSettings | None = None,
) -> SimulationCanvas:
    """Create a simulation canvas with a configurable test system."""
    app = QApplication.instance() or QApplication([])
    _ = app
    if system is None:
        sun = CelestialBody(
            name="Sun",
            mass_kg=1.0,
            radius_m=1.0,
            color_hex="#ffffff",
            position_m=Vector3(0.0, 0.0, 0.0),
            velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
        )
        system = SolarSystem([sun])
    if settings is None:
        settings = SimulationSettings()
    return SimulationCanvas(system, settings)


def _two_body_canvas() -> tuple[SimulationCanvas, CelestialBody, CelestialBody]:
    """Create a deterministic two-body canvas for selection tests."""
    earth = CelestialBody(
        name="Earth",
        mass_kg=5.0,
        radius_m=12.0,
        color_hex="#5da9ff",
        position_m=Vector3(100.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    mars = CelestialBody(
        name="Mars",
        mass_kg=1.0,
        radius_m=9.0,
        color_hex="#d97b53",
        position_m=Vector3(-80.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    canvas = _make_canvas(
        SolarSystem([earth, mars]),
        SimulationSettings(meters_per_pixel=1.0, projection_mode="orthographic"),
    )
    canvas.camera.yaw_radians = 0.0
    canvas.camera.pitch_radians = 0.0
    canvas.resize(1000, 800)
    return canvas, earth, mars


def _crowded_label_canvas() -> tuple[SimulationCanvas, CelestialBody, CelestialBody]:
    """Create a canvas whose default label positions overlap."""
    mercury = CelestialBody(
        name="Mercury",
        mass_kg=1.0,
        radius_m=6.0,
        color_hex="#c9c9c9",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    venus = CelestialBody(
        name="Venus",
        mass_kg=1.0,
        radius_m=6.0,
        color_hex="#f2d27b",
        position_m=Vector3(14.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    canvas = _make_canvas(
        SolarSystem([mercury, venus]),
        SimulationSettings(meters_per_pixel=1.0, projection_mode="orthographic"),
    )
    canvas.camera.yaw_radians = 0.0
    canvas.camera.pitch_radians = 0.0
    canvas.resize(1000, 800)
    return canvas, mercury, venus


def test_touchpad_wheel_event_with_missing_device_returns_false() -> None:
    """Missing pointing device should not be treated as touchpad."""
    canvas = _make_canvas()
    event = _FakeWheelEvent(device=None)
    assert canvas._is_touchpad_wheel_event(event) is False


def test_touchpad_wheel_is_skipped_right_after_native_gesture() -> None:
    """Touchpad wheel orbit should be deduplicated after native gesture."""
    canvas = _make_canvas()
    touchpad = _FakeDevice(canvas._TOUCHPAD_DEVICE_TYPE)
    event = _FakeWheelEvent(device=touchpad, pixel_delta=_FakeDelta(6.0, 4.0))
    call_count = 0

    def _record_orbit(_x: float, _y: float) -> None:
        nonlocal call_count
        call_count += 1

    canvas._apply_trackpad_orbit = _record_orbit  # type: ignore[method-assign]
    canvas._last_native_gesture_time_s = perf_counter()

    canvas.wheelEvent(event)

    assert call_count == 0
    assert event.accepted is True


def test_touchpad_wheel_orbits_when_dedup_window_elapsed() -> None:
    """Touchpad wheel orbit should run when dedup window has elapsed."""
    canvas = _make_canvas()
    touchpad = _FakeDevice(canvas._TOUCHPAD_DEVICE_TYPE)
    event = _FakeWheelEvent(device=touchpad, pixel_delta=_FakeDelta(7.0, -3.0))
    calls: list[tuple[float, float]] = []

    def _record_orbit(x: float, y: float) -> None:
        calls.append((x, y))

    canvas._apply_trackpad_orbit = _record_orbit  # type: ignore[method-assign]
    canvas._last_native_gesture_time_s = (
        perf_counter() - canvas._NATIVE_GESTURE_WHEEL_DEDUP_WINDOW_S - 0.05
    )

    canvas.wheelEvent(event)

    assert calls == [(7.0, -3.0)]
    assert event.accepted is True


def test_native_zoom_gesture_updates_camera_zoom() -> None:
    """Native zoom gesture should change camera zoom factor."""
    canvas = _make_canvas()
    before = canvas.camera.zoom_factor
    native_event = _FakeNativeGestureEvent(
        Qt.NativeGestureType.ZoomNativeGesture,
        value=0.4,
    )

    handled = canvas.event(native_event)

    assert handled is True
    assert native_event.accepted is True
    assert canvas.camera.zoom_factor > before


def test_screen_projection_is_centered_on_system_center_of_mass() -> None:
    """A body's projected x should be relative to system barycenter."""
    app = QApplication.instance() or QApplication([])
    _ = app
    body_a = CelestialBody(
        name="A",
        mass_kg=2.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(4.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    body_b = CelestialBody(
        name="B",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(-2.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    canvas = SimulationCanvas(
        SolarSystem([body_a, body_b]),
        SimulationSettings(meters_per_pixel=1.0, projection_mode="orthographic"),
    )
    canvas.camera.yaw_radians = 0.0
    canvas.camera.pitch_radians = 0.0
    canvas.resize(1000, 800)

    center_of_mass = (
        (body_a.position_m.x * body_a.mass_kg) + (body_b.position_m.x * body_b.mass_kg)
    ) / 3.0
    point_a = canvas._to_screen_point(body_a.position_m)
    expected_x = (canvas.width() * 0.5) + (body_a.position_m.x - center_of_mass)
    assert point_a.x() == expected_x


def test_camera_focus_defaults_to_system_center_of_mass_without_selection() -> None:
    """No selection should preserve the existing center-of-mass camera pivot."""
    canvas, earth, mars = _two_body_canvas()

    expected_focus_x = (
        (earth.position_m.x * earth.mass_kg) + (mars.position_m.x * mars.mass_kg)
    ) / (earth.mass_kg + mars.mass_kg)

    assert canvas._selected_body() is None
    assert canvas._camera_focus_point() == Vector3(expected_focus_x, 0.0, 0.0)


def test_select_body_by_name_updates_selected_target_state() -> None:
    """Selecting by name should resolve the matching live body."""
    canvas, earth, _mars = _two_body_canvas()

    canvas.select_body_by_name("Earth")

    assert canvas._selected_body_name == "Earth"
    assert canvas._selected_body() is earth


def test_left_click_near_body_selects_expected_target() -> None:
    """Left click hit testing should select the clicked body."""
    canvas, earth, _mars = _two_body_canvas()
    click_position = canvas._to_screen_point(earth.position_m)
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        click_position,
        click_position,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    canvas.mousePressEvent(event)

    assert canvas._selected_body() is earth


def test_clicking_empty_space_clears_selection() -> None:
    """Left-clicking empty canvas space should clear any active selection."""
    canvas, earth, _mars = _two_body_canvas()
    canvas.select_body_by_name(earth.name)
    empty_position = QPointF(20.0, 30.0)
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        empty_position,
        empty_position,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    canvas.mousePressEvent(event)

    assert canvas._selected_body() is None
    assert canvas._selected_body_name is None


def test_selected_body_becomes_camera_pivot() -> None:
    """Selected target should stay centered as the live camera focus point."""
    canvas, earth, _mars = _two_body_canvas()

    canvas.select_body_by_name(earth.name)

    focus = canvas._camera_focus_point()
    earth_screen = canvas._to_screen_point(earth.position_m)
    assert focus == earth.position_m
    assert earth_screen.x() == canvas.width() * 0.5
    assert earth_screen.y() == canvas.height() * 0.5


def test_selected_target_follows_body_motion() -> None:
    """Selection should continue tracking the same named body as it moves."""
    canvas, earth, _mars = _two_body_canvas()
    canvas.select_body_by_name(earth.name)

    earth.position_m = Vector3(240.0, 80.0, 0.0)

    assert canvas._camera_focus_point() == earth.position_m
    assert canvas._to_screen_point(earth.position_m) == QPointF(500.0, 400.0)


def test_selection_indicator_rect_exists_only_for_selected_body() -> None:
    """Selection rectangle helper should reflect current selected-body state."""
    canvas, earth, _mars = _two_body_canvas()

    assert canvas._current_selection_indicator_rect() is None

    canvas.select_body_by_name(earth.name)
    earth_rect = canvas._current_selection_indicator_rect()

    assert earth_rect is not None
    assert earth_rect.width() >= canvas._SELECTION_BOX_MIN_SIZE_PX
    assert earth_rect.contains(canvas._to_screen_point(earth.position_m))


def test_non_overlapping_labels_keep_default_near_body_placement() -> None:
    """Isolated labels should keep the default upper-right candidate."""
    canvas, earth, mars = _two_body_canvas()

    placements = canvas._resolve_label_placements(canvas.fontMetrics())
    by_name = {placement.body_name: placement for placement in placements}

    assert by_name["Earth"].candidate_index == 0
    assert by_name["Earth"].connector_required is False
    assert by_name["Earth"].rect.left() > by_name["Earth"].body_center.x()
    assert by_name["Earth"].rect.bottom() < by_name["Earth"].body_center.y()
    assert by_name["Mars"].candidate_index == 0


def test_overlapping_labels_are_reassigned_to_alternate_positions() -> None:
    """Crowded labels should move away from the default overlapping position."""
    canvas, mercury, venus = _crowded_label_canvas()

    placements = canvas._resolve_label_placements(canvas.fontMetrics())
    by_name = {placement.body_name: placement for placement in placements}
    default_mercury_rect = canvas._label_candidate_rect(
        by_name["Mercury"].body_center,
        canvas._body_screen_radius_px(mercury),
        mercury.name,
        canvas.fontMetrics(),
        0,
    )
    default_venus_rect = canvas._label_candidate_rect(
        by_name["Venus"].body_center,
        canvas._body_screen_radius_px(venus),
        venus.name,
        canvas.fontMetrics(),
        0,
    )

    assert default_mercury_rect.intersects(default_venus_rect)
    assert any(placement.candidate_index != 0 for placement in placements)
    assert not by_name["Mercury"].rect.intersects(by_name["Venus"].rect)


def test_connector_state_is_enabled_only_for_displaced_labels() -> None:
    """Connector lines should be requested only when a label leaves its default slot."""
    canvas, _mercury, _venus = _crowded_label_canvas()

    placements = canvas._resolve_label_placements(canvas.fontMetrics())

    assert any(placement.connector_required for placement in placements)
    assert all(
        placement.connector_required == (placement.candidate_index != 0)
        for placement in placements
    )


def test_label_placement_is_deterministic_for_same_input() -> None:
    """The same body arrangement should resolve to the same candidate choices."""
    canvas_a, _mercury_a, _venus_a = _crowded_label_canvas()
    canvas_b, _mercury_b, _venus_b = _crowded_label_canvas()

    placements_a = canvas_a._resolve_label_placements(canvas_a.fontMetrics())
    placements_b = canvas_b._resolve_label_placements(canvas_b.fontMetrics())

    assert [(p.body_name, p.candidate_index) for p in placements_a] == [
        (p.body_name, p.candidate_index) for p in placements_b
    ]


def test_repeated_layout_evaluation_stays_stable_for_crowded_labels() -> None:
    """Re-evaluating the same crowded view should not flip label sides."""
    canvas, _mercury, _venus = _crowded_label_canvas()

    placements_first = canvas._resolve_label_placements(canvas.fontMetrics())
    placements_second = canvas._resolve_label_placements(canvas.fontMetrics())

    assert [(p.body_name, p.candidate_index) for p in placements_first] == [
        (p.body_name, p.candidate_index) for p in placements_second
    ]


def test_wheel_zoom_steps_prefers_angle_delta() -> None:
    """_wheel_zoom_steps should map Qt angle delta to wheel steps."""
    canvas = _make_canvas()
    event = _FakeWheelEvent(
        device=None,
        angle_delta=_FakeDelta(0.0, 240.0),
    )
    assert canvas._wheel_zoom_steps(event) == 2.0


def test_wheel_zoom_steps_falls_back_to_pixel_delta() -> None:
    """When angle delta is zero, pixel delta should drive zoom steps."""
    canvas = _make_canvas()
    event = _FakeWheelEvent(
        device=None,
        angle_delta=_FakeDelta(0.0, 0.0),
        pixel_delta=_FakeDelta(0.0, 80.0),
    )
    assert canvas._wheel_zoom_steps(event) == 2.0


def test_apply_trackpad_orbit_noop_when_delta_zero() -> None:
    """Zero pan delta should not change camera state."""
    canvas = _make_canvas()
    yaw_before = canvas.camera.yaw_radians
    pitch_before = canvas.camera.pitch_radians
    canvas._apply_trackpad_orbit(0.0, 0.0)
    assert canvas.camera.yaw_radians == yaw_before
    assert canvas.camera.pitch_radians == pitch_before


def test_mouse_wheel_zooms_without_touchpad_device() -> None:
    """Non-touchpad wheel events should use angle delta for zoom."""
    canvas = _make_canvas()
    mouse = _FakeDevice(QPointingDevice.DeviceType.Mouse)
    event = _FakeWheelEvent(device=mouse, angle_delta=_FakeDelta(0.0, 120.0))
    before = canvas.camera.zoom_factor
    canvas.wheelEvent(event)
    assert canvas.camera.zoom_factor > before
    assert event.accepted is True


def test_touchpad_scroll_uses_angle_when_pixel_delta_null() -> None:
    """Touchpad may send angle deltas without pixel deltas for orbit."""
    canvas = _make_canvas()
    touchpad = _FakeDevice(canvas._TOUCHPAD_DEVICE_TYPE)
    event = _FakeWheelEvent(
        device=touchpad,
        pixel_delta=_FakeDelta(0.0, 0.0),
        angle_delta=_FakeDelta(8.0, -8.0),
    )
    calls: list[tuple[float, float]] = []

    def _record_orbit(x: float, y: float) -> None:
        calls.append((x, y))

    canvas._apply_trackpad_orbit = _record_orbit  # type: ignore[method-assign]
    canvas._last_native_gesture_time_s = None

    canvas.wheelEvent(event)

    assert calls == [(1.0, -1.0)]
    assert event.accepted is True


def test_native_pan_gesture_applies_orbit_delta() -> None:
    """Pan native gesture should forward signed deltas to trackpad orbit."""
    canvas = _make_canvas()
    native_event = _FakeNativeGestureEvent(
        Qt.NativeGestureType.PanNativeGesture,
        delta=QPointF(5.0, -3.0),
    )
    calls: list[tuple[float, float]] = []

    def _record_orbit(x: float, y: float) -> None:
        calls.append((x, y))

    canvas._apply_trackpad_orbit = _record_orbit  # type: ignore[method-assign]

    handled = canvas.event(native_event)

    assert handled is True
    assert calls == [(5.0, -3.0)]
    assert native_event.accepted is True


def test_native_rotate_gesture_adjusts_yaw() -> None:
    """Rotate native gesture should change yaw via orbit_by_drag."""
    canvas = _make_canvas()
    yaw_before = canvas.camera.yaw_radians
    pitch_before = canvas.camera.pitch_radians
    native_event = _FakeNativeGestureEvent(
        Qt.NativeGestureType.RotateNativeGesture,
        value=0.5,
    )

    handled = canvas.event(native_event)

    assert handled is True
    assert canvas.camera.yaw_radians != yaw_before
    assert canvas.camera.pitch_radians == pitch_before


def test_set_running_false_skips_simulation_step() -> None:
    """When paused, timer tick should not advance simulation time."""
    canvas = _make_canvas()
    canvas.set_running(True)
    canvas._tick()
    t1 = canvas.system.simulation_time_s
    canvas.set_running(False)
    canvas._tick()
    assert canvas.system.simulation_time_s == t1


def test_alt_touchpad_scroll_zooms_instead_of_orbit() -> None:
    """Holding Alt/Option should force wheel input to zoom."""
    canvas = _make_canvas()
    touchpad = _FakeDevice(canvas._TOUCHPAD_DEVICE_TYPE)
    event = _FakeWheelEvent(
        device=touchpad,
        pixel_delta=_FakeDelta(0.0, 40.0),
        modifiers=Qt.KeyboardModifier.AltModifier,
    )
    orbit_calls = 0

    def _record_orbit(_x: float, _y: float) -> None:
        nonlocal orbit_calls
        orbit_calls += 1

    canvas._apply_trackpad_orbit = _record_orbit  # type: ignore[method-assign]
    before = canvas.camera.zoom_factor

    canvas.wheelEvent(event)

    assert canvas.camera.zoom_factor > before
    assert orbit_calls == 0
    assert event.accepted is True
