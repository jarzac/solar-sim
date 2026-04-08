# Technical audit snapshot

**Last reviewed:** 2026-04-08  
**Scope:** Repository state as of this date: `src/solar_sim`, `tests/`, `pyproject.toml`, CI, and top-level docs.

This file is a concise reference for future maintainers: what the code does, where to look, and known tradeoffs. It is not a substitute for reading `README.md` or `AGENTS.md`.

## Product and packaging

- **PyPI-style name / install:** `solar-system-sim` (`pyproject.toml` `[project]`).
- **Import package:** `solar_sim`.
- **Entry points:** `python -m solar_sim` → `solar_sim.__main__:main`; console script `solar-sim` → same `main()`.

## CI

GitHub Actions (`.github/workflows/ci.yml`): Ubuntu, Python 3.12, `pip install -e ".[dev]"`, then `ruff check .`, `mypy src`, `pytest -q`.

## Architecture (source of truth)

| Area | Module(s) | Notes |
|------|-----------|--------|
| App shell | `app.py` | `MainWindow`: wires `ControlPanel` + `SimulationCanvas`, `SimulationSettings`, `SolarSystem`; restart calls `create_default_solar_system` with `settings.start_date` at UTC midnight. |
| Physics | `physics.py` | N-body gravity, velocity–Verlet `step`, trail sampling and orbital-period-based trail trimming. Default bodies: Sun + Mercury–Neptune from JPL approximate Keplerian tables (see file header and `OrbitalElements` docstring). |
| Settings | `config.py` | `SimulationSettings`: gravity, time scale, booleans, `projection_mode`, `meters_per_pixel`, `start_date`. |
| Camera | `camera.py` | `CameraState`: zoom, yaw/pitch, orthographic vs perspective projection to pixel space. |
| Canvas | `ui_canvas.py` | Timer-driven `step` + `paintEvent`; center-of-mass offset before projection; wheel / native gesture / middle-button orbit; simulation clock overlay; grid. |
| Controls | `ui_controls.py` | Form labels match behavior (e.g. “Sim seconds / real second”, “Perspective view”). |

## Input handling (canvas)

- **Mouse wheel:** zoom steps via `CameraState.zoom_by_wheel_steps` (after Qt angle delta / 120).
- **Touchpad `QWheelEvent`:** classified via `QPointingDevice`; if touchpad, scroll deltas map to orbit unless **Alt** is held (then zoom via `_wheel_zoom_steps`).
- **Native gestures:** `QEvent.NativeGesture` — pan → orbit; zoom → zoom; rotate → horizontal `orbit_by_drag` only.
- **Dedup:** After handling pan/zoom/rotate native gestures, wheel events within `_NATIVE_GESTURE_WHEEL_DEDUP_WINDOW_S` (0.08 s) may be skipped to reduce double counting. This is heuristic; timing can vary by OS/hardware.

## Testing

- `tests/test_physics.py` — gravity, integration, element-related behavior.
- `tests/test_config.py` — settings mutators.
- `tests/test_camera.py` — zoom, orbit, projection modes.
- `tests/test_ui_canvas.py` — input fakes, gesture/dedup/alt paths, center-of-mass projection check (requires `PySide6` / `QApplication`).

## Documentation alignment

- **README.md** — User and developer setup, features, controls, layout, limitations; should stay consistent with `physics.py` body list and `ui_controls.py` labels.
- **AGENTS.md** — Engineering rules (SI units, separation of UI/physics, test commands).

## Known tradeoffs (not bugs by default)

1. **Touchpad dedup window** — Fixed 0.08 s; may need tuning if a platform stacks events differently.
2. **View center** — Uses mass-weighted center of all bodies, not the Sun’s position; README documents this.
3. **Ephemeris** — Approximate elements for seeding; long-term accuracy is not the same as a full DE ephemeris integration.
