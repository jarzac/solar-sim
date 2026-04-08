"""Unit tests for camera interaction and projection behavior."""

from math import isclose, isnan, pi

from solar_sim.camera import CameraState
from solar_sim.math3d import Vector3


def test_zoom_changes_effective_scale() -> None:
    """Zooming in should reduce meters-per-pixel scale."""
    camera = CameraState(zoom_factor=1.0)
    base_scale = 6.0e9
    camera.zoom_by_wheel_steps(1.0)
    assert camera.effective_meters_per_pixel(base_scale) < base_scale


def test_zoom_is_clamped() -> None:
    """Zoom factor should be bounded by configured limits."""
    camera = CameraState(zoom_factor=1.0, min_zoom=0.5, max_zoom=2.0)
    camera.zoom_by_wheel_steps(100.0)
    assert camera.zoom_factor == 2.0
    camera.zoom_by_wheel_steps(-200.0)
    assert camera.zoom_factor == 0.5


def test_orbit_drag_updates_angles_and_clamps_pitch() -> None:
    """Middle-drag input should update yaw and clamp pitch."""
    camera = CameraState(pitch_radians=0.0, min_pitch_radians=-0.5, max_pitch_radians=0.5)
    camera.orbit_by_drag(100.0, -200.0)
    assert camera.yaw_radians > 0.0
    assert camera.pitch_radians == 0.5


def test_yaw_rotation_affects_projection_direction() -> None:
    """A quarter-turn yaw should rotate x-axis world points into +y."""
    camera = CameraState(yaw_radians=pi * 0.5, pitch_radians=0.0)
    x, y, z = camera.rotate_world_point_3d(Vector3(10.0, 0.0, 0.0))
    assert isclose(x, 0.0, abs_tol=1e-10)
    assert isclose(y, 10.0, abs_tol=1e-10)
    assert isclose(z, 0.0, abs_tol=1e-10)


def test_perspective_and_orthographic_project_differently() -> None:
    """Perspective projection should scale by depth while orthographic does not."""
    camera = CameraState(yaw_radians=0.0, pitch_radians=0.8)
    viewport_w = 1000.0
    viewport_h = 800.0
    scale = 1.0
    center_x = viewport_w * 0.5

    near_point = Vector3(1000.0, 1000.0, 0.0)
    far_point = Vector3(1000.0, -1000.0, 0.0)

    ortho_near = camera.project_to_screen(
        near_point,
        viewport_w,
        viewport_h,
        scale,
        "orthographic",
    )
    ortho_far = camera.project_to_screen(
        far_point,
        viewport_w,
        viewport_h,
        scale,
        "orthographic",
    )
    assert isclose(ortho_near.x - center_x, ortho_far.x - center_x, rel_tol=1e-12)

    persp_near = camera.project_to_screen(
        near_point,
        viewport_w,
        viewport_h,
        scale,
        "perspective",
    )
    persp_far = camera.project_to_screen(
        far_point,
        viewport_w,
        viewport_h,
        scale,
        "perspective",
    )
    assert (persp_near.x - center_x) > (persp_far.x - center_x)


def test_world_origin_maps_to_viewport_center_orthographic() -> None:
    """Origin in camera space should map to the viewport center in orthographic mode."""
    camera = CameraState(yaw_radians=0.0, pitch_radians=0.0)
    screen = camera.project_to_screen(
        Vector3(0.0, 0.0, 0.0),
        800.0,
        600.0,
        2.0e9,
        "orthographic",
    )
    assert isclose(screen.x, 400.0)
    assert isclose(screen.y, 300.0)


def test_zoom_by_wheel_steps_zero_leaves_zoom_unchanged() -> None:
    """Zero wheel steps should not change zoom factor."""
    camera = CameraState(zoom_factor=2.5)
    camera.zoom_by_wheel_steps(0.0)
    assert camera.zoom_factor == 2.5


def test_perspective_projection_stays_finite_for_extreme_depth() -> None:
    """Perspective branch should clamp denominator so projection never divides by ~0."""
    camera = CameraState(yaw_radians=0.0, pitch_radians=0.0)
    # Push z far enough that (focal_length_px - z_px) would be negative without clamp.
    screen = camera.project_to_screen(
        Vector3(0.0, 0.0, 1.5e12),
        1000.0,
        800.0,
        1.0e9,
        "perspective",
    )
    assert not isnan(screen.x)
    assert not isnan(screen.y)


def test_pitch_rotates_world_z_into_screen_y() -> None:
    """Non-zero pitch should mix y and z in camera space before projection."""
    camera = CameraState(yaw_radians=0.0, pitch_radians=pi * 0.5)
    x, y, z = camera.rotate_world_point_3d(Vector3(0.0, 0.0, 10.0))
    assert isclose(x, 0.0, abs_tol=1e-10)
    assert isclose(y, -10.0, abs_tol=1e-10)
    assert isclose(z, 0.0, abs_tol=1e-10)
