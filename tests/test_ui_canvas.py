"""Unit tests for simulation canvas gesture and wheel input handling."""

from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import QEvent, QPointF, Qt
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


def _make_canvas() -> SimulationCanvas:
    """Create a simulation canvas with a minimal one-body system."""
    app = QApplication.instance() or QApplication([])
    _ = app
    sun = CelestialBody(
        name="Sun",
        mass_kg=1.0,
        radius_m=1.0,
        color_hex="#ffffff",
        position_m=Vector3(0.0, 0.0, 0.0),
        velocity_m_per_s=Vector3(0.0, 0.0, 0.0),
    )
    system = SolarSystem([sun])
    return SimulationCanvas(system, SimulationSettings())


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
